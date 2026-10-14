#!/usr/bin/env python3
"""Give a report its data, twice: as JSON in the page, and as files.

  python3 tools/report_data.py NNN          (001 is the root index.html)

Reads NNN/data/meta.json, written by hand: what the report measured and
how (the builds and their commits, the browser or runtime, each measure and
its unit, the runs), and which raw files belong with it. Reads every table
in the page, cell by cell, as printed. Writes NNN/data/tables.json, and
embeds {meta, tables, files} in the page as

  <script type="application/json" id="report-data"> ... </script>

between report-data markers at the end of the page; and a line saying so
between data-line markers at the end of the method section (or, for a
report without one, in a short "The data" section of its own). Idempotent:
run it again after changing the page or meta.json. ^report(14) writes its
own (gen014.py) and is the model.
"""
import html, json, os, re, sys
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = "https://github.com/matthewhammer/hazel-performance-analysis"


class Tables(HTMLParser):
    """Every <table>: the heading above it (text and id), its rows of cells."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables, self.head, self.head_id, self.in_head = [], "", None, False
        self.cur, self.row, self.cell, self.depth, self.cap = None, None, None, 0, ""
        self.in_cap = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("h2", "h3") and self.depth == 0:
            self.in_head, self.head, self.head_id = True, "", a.get("id")
        elif tag == "table":
            self.depth += 1
            if self.depth == 1:
                self.cur = {"section": self.head.strip(), "section_id": self.head_id, "rows": []}
        elif self.depth == 1 and tag == "tr":
            self.row = []
        elif self.depth == 1 and tag in ("td", "th"):
            self.cell = {"text": "", "head": tag == "th",
                         "rowspan": int(a.get("rowspan") or 1), "colspan": int(a.get("colspan") or 1)}
        elif tag == "caption" and self.depth == 1:
            self.in_cap = True

    def handle_endtag(self, tag):
        if tag in ("h2", "h3") and self.in_head:
            self.in_head = False
        elif tag == "table":
            if self.depth == 1 and self.cur is not None:
                self.tables.append(self.cur); self.cur = None
            self.depth -= 1
        elif self.depth == 1 and tag in ("td", "th") and self.cell is not None:
            self.row.append(self.cell); self.cell = None
        elif self.depth == 1 and tag == "tr" and self.row is not None:
            if self.row: self.cur["rows"].append(self.row)
            self.row = None
        elif tag == "caption":
            self.in_cap = False

    def handle_data(self, data):
        if self.in_head: self.head += data
        if self.cell is not None: self.cell["text"] += data
        if self.in_cap and self.cur is not None: self.cur["caption"] = (self.cur.get("caption", "") + data)


def clean(t):
    return re.sub(r"\s+", " ", t).strip()


def grid(rows):
    """Cells laid out as the browser does: a cell spanning rows or columns
    repeats its text in each place it covers."""
    out, carry = [], {}   # column -> (text, rows left)
    for r in rows:
        line, col, cells = [], 0, list(r)
        while cells or col in carry:
            if col in carry:
                text, left = carry[col]
                line.append(text)
                if left > 1: carry[col] = (text, left - 1)
                else: del carry[col]
                col += 1
                continue
            c = cells.pop(0)
            for _ in range(c["colspan"]):
                line.append(clean(c["text"]))
                if c["rowspan"] > 1: carry[col] = (clean(c["text"]), c["rowspan"] - 1)
                col += 1
        out.append(line)
    return out


def shape(t):
    """Columns from a header row of <th>s (if the first row is one), then rows of cell text."""
    rows = grid(t["rows"])
    head = None
    if t["rows"] and all(c["head"] for c in t["rows"][0]):
        head, rows = rows[0], rows[1:]
    out = {"section": clean(t["section"]).rstrip("#").strip(), "section_id": t["section_id"]}
    if t.get("caption"): out["caption"] = clean(t["caption"])
    if head: out["columns"] = head
    out["rows"] = rows
    return out


def main(nnn):
    page = os.path.join(ROOT, "index.html" if nnn == "001" else f"{nnn}/index.html")
    ddir = os.path.join(ROOT, "data" if nnn == "001" else f"{nnn}/data")
    tree = f"{REPO}/tree/main/{'data' if nnn == '001' else nnn + '/data'}"
    meta = json.load(open(os.path.join(ddir, "meta.json")))
    text = open(page).read()
    body = re.sub(r"<!-- report-data: begin -->.*?<!-- report-data: end -->", "", text, flags=re.S)
    body = re.sub(r"<script.*?</script>|<style.*?</style>|<svg.*?</svg>", "", body, flags=re.S)
    p = Tables(); p.feed(body)
    tables = [shape(t) for t in p.tables]
    json.dump(tables, open(os.path.join(ddir, "tables.json"), "w"), indent=1, ensure_ascii=False)
    files = sorted(f"data/{f}" for f in os.listdir(ddir) if not f.startswith("."))
    data = {"report": int(nnn), **meta,
            "tables_note": "Every table in the page, cell by cell, as printed (units in the column names or the cells); "
                           "columns are the header row where the table has one.",
            "tables": tables, "files": files, "files_on_github": tree}
    blob = json.dumps(data, indent=1, ensure_ascii=False).replace("</", "<\\/")
    block = ('<!-- report-data: begin -->\n<script type="application/json" id="report-data">\n' + blob +
             '\n</script>\n<!-- report-data: end -->')
    text = re.sub(r"\s*<!-- report-data: begin -->.*?<!-- report-data: end -->", "", text, flags=re.S)
    i = text.rindex("</body>")
    text = text[:i].rstrip() + "\n" + block + "\n" + text[i:]

    line = (f'<li><b>The numbers, for programs too:</b> every table in this report, and what its numbers measure, '
            f'is also in this page as JSON, in its <code>&lt;script type="application/json" id="report-data"&gt;</code> '
            f'element, so a reader or an agent that fetches the page alone has the dataset. The same, with any raw files '
            f'that survive, is in <a href="{tree}"><code>{"data" if nnn == "001" else nnn + "/data"}/</code></a>.</li>')
    text = re.sub(r"\s*<!-- data-line: begin -->.*?<!-- data-line: end -->", "", text, flags=re.S)
    secs = {k: re.search(rf'<h2 id="{k}">.*?(?=<h2 |</main>)', text, re.S) for k in ("method", "measured")}
    home = next((secs[k] for k in ("method", "measured") if secs[k] and "</ul>" in secs[k].group(0)), None)
    if home:
        sec = home.group(0); k = sec.rindex("</ul>")
        sec = sec[:k].rstrip() + "\n  <!-- data-line: begin -->\n  " + line + "\n  <!-- data-line: end -->\n" + sec[k:]
        text = text[:home.start()] + sec + text[home.end():]
    else:
        para = ("<!-- data-line: begin -->\n<h2 id=\"data\">The data</h2>\n<ul>\n  " + line + "\n</ul>\n<!-- data-line: end -->")
        after = secs["measured"] or secs["method"]
        j = after.end() if after else text.rindex("</main>")
        text = text[:j].rstrip() + "\n\n" + para + "\n\n" + text[j:]
    open(page, "w").write(text)
    print(f"{nnn}: {len(tables)} tables, {len(files)} files, {len(blob):,} bytes embedded")


if __name__ == "__main__":
    for a in sys.argv[1:]:
        main(a.strip("/").zfill(3))
