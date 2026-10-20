#!/usr/bin/env python3
"""^report(23): ^report(18), followed up. What happened to #2635's CI and to each of ^report(18)'s next steps since that report
was written (2026-10-19, data as of 09:55 MDT, its update at 12:45 MDT). Collects it from GitHub and git into 023/data/.

  python3 collect023.py <logs dir> <hazel checkout> <out dir>

<logs dir> keeps each Fast or Full checks job's log as GitHub gives it (fetched with
`gh api repos/hazelgrove/hazel/actions/jobs/<job>/logs` when missing). <hazel checkout> needs the branches fetched
(git fetch origin dev modular-editors stdlib integration/livelits-splicerefs-full integration/livelits-modular-editors)."""
import json, os, re, subprocess, sys, time
from datetime import datetime, timezone

logs, repo, out = sys.argv[1:4]
os.makedirs(logs, exist_ok=True)
REPO = "hazelgrove/hazel"
SINCE = "2026-10-19T15:55:00Z"   # ^report(18)'s data: 2026-10-19 09:55 MDT


def sh(*args, cwd=None):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True).stdout


def gh(path):
    for attempt in range(5):  # GitHub answers 502 now and then
        try:
            got = json.loads(sh("gh", "api", path))
            if not (isinstance(got, dict) and "message" in got and len(got) <= 2):
                return got
        except json.JSONDecodeError:
            pass
        time.sleep(3 * (attempt + 1))
    raise RuntimeError("GitHub did not answer: " + path)


def git(*args):
    return sh("git", *args, cwd=repo).strip()


def anc(a, b):
    return subprocess.run(["git", "merge-base", "--is-ancestor", a, b], cwd=repo).returncode == 0


ANSI = re.compile(r"\x1b\[[0-9;]*m")


def job_log(job):
    p = os.path.join(logs, f"job{job}.log")
    if not os.path.exists(p) or os.path.getsize(p) == 0:
        with open(p, "w") as f:
            f.write(sh("gh", "api", f"repos/{REPO}/actions/jobs/{job}/logs"))
    return ANSI.sub("", open(p, encoding="utf-8", errors="replace").read())


def read_suite(text):
    """The suite's verdict: failures, seconds, tests run (as ^report(18) read them)."""
    m = re.search(r"(\d+) failures?! in ([\d.]+)s\. (\d+) tests run", text)   # ("1 failure!" too)
    ok = re.search(r"Test Successful in ([\d.]+)s\. (\d+) tests run", text)
    if m:
        return {"failures": int(m.group(1)), "seconds": float(m.group(2)), "tests": int(m.group(3))}
    if ok:
        return {"failures": 0, "seconds": float(ok.group(1)), "tests": int(ok.group(2))}
    return {"failures": None}


def runs_of(branch, since=SINCE):
    got_all = []
    for page in range(1, 6):
        got = gh(f"repos/{REPO}/actions/runs?branch={branch}&per_page=100&page={page}")["workflow_runs"]
        got_all += [{"run": r["id"], "head": r["head_sha"][:10], "conclusion": r["conclusion"] or r["status"], "created": r["created_at"],
                     "updated": r["updated_at"]} for r in got if r["name"] == "CI" and r["created_at"] >= since]
        if len(got) < 100 or got[-1]["created_at"] < since:
            break
    return got_all


def suites(run):
    jobs = {j["name"]: j for j in gh(f"repos/{REPO}/actions/runs/{run}/jobs")["jobs"]}
    e = {}
    for name in ("checks / Fast checks", "checks / Full tests"):
        short = "fast" if "Fast" in name else "full"
        j = jobs.get(name)
        if not j:
            continue
        e[short] = {"job": j["id"], "status": j["status"], "conclusion": j["conclusion"], "started": j["started_at"], "completed": j["completed_at"]}
        if j["status"] == "completed":
            e[short].update(read_suite(job_log(j["id"])))
    return e


BRANCHES = {"2635": "integration/livelits-modular-editors", "2597": "integration/livelits-splicerefs-full",
            "2469": "modular-editors", "2687": "stdlib"}
lanes = {k: {"branch": b, "runs": runs_of(b)} for k, b in BRANCHES.items()}
# (#2635's runs since ^report(18), each read: Fast checks and Full tests, with their verdicts and test counts)
for r in lanes["2635"]["runs"]:
    if r["conclusion"] in ("success", "failure"):
        r.update(suites(r["run"]))
# (the parents' and #2687's newest finished run, read the same way)
newest = {}
for k in ("2597", "2469", "2687"):
    done = [r for r in lanes[k]["runs"] if r["conclusion"] in ("success", "failure")]
    if done:
        newest[k] = {**done[0], **suites(done[0]["run"])}

prs = {}
for n in (2635, 2699, 2597, 2469, 2687):
    p = gh(f"repos/{REPO}/pulls/{n}")
    prs[str(n)] = {"title": p["title"], "state": p["state"], "merged_at": p["merged_at"], "head": p["head"]["ref"], "head_sha": p["head"]["sha"][:10],
                   "base": p["base"]["ref"], "mergeable": p.get("mergeable"), "mergeable_state": p.get("mergeable_state"), "updated_at": p["updated_at"]}
prs["2699"]["commits"] = [{"sha": c["sha"][:10], "message": c["commit"]["message"].split("\n")[0], "author": c["commit"]["author"]["name"]}
                          for c in gh(f"repos/{REPO}/pulls/2699/commits?per_page=100")]

L, F, D = "origin/integration/livelits-modular-editors", "origin/integration/livelits-splicerefs-full", "origin/dev"
facts = {
    "heads": {k: git("rev-parse", "--short=10", "origin/" + b) for k, b in BRANCHES.items()} | {"dev": git("rev-parse", "--short=10", D)},
    "fixes": {c: {"what": git("log", "-1", "--format=%h %cI %an %s", c), "on_2635": anc(c, L), "on_2597": anc(c, F)}
              for c in ("1131a457e4", "27f100e37c", "223357135a", "cf325d4f61", "90ed4505bf", "5961401df2")},
    "defstatics_on_2597": bool(git("ls-tree", "-r", "--name-only", F, "src/haz3lcore/derived/DefStatics.re")),
    "table_test_input_on_2597": git("grep", "-n", "hidden row error draws no arms", F, "--", "test/Test_Editing.re")[:200],
    "2597_since_report18": [l for l in git("log", "--format=%h %cI %s", "f8ae6f2b9c.." + F).split("\n") if l],
    "conflicts_2635_with_2597": [l for l in sh("git", "merge-tree", "--write-tree", "--name-only", F, L, cwd=repo).split("\n\n")[0].split("\n")[1:] if l],
    "2597_dev_base": git("merge-base", D, F)[:10],
    "2597_behind_dev": int(git("rev-list", "--count", git("merge-base", D, F) + ".." + D)),
    "2635_behind_dev": int(git("rev-list", "--count", git("merge-base", D, L) + ".." + D)),
    "2635_since_report18": [l for l in git("log", "--format=%h %cI %an %s", "9e7258b55b.." + L).split("\n") if l],
}
facts["collected_at"] = datetime.now(timezone.utc).isoformat(timespec="minutes")

os.makedirs(out, exist_ok=True)
for name, val in [("runs.json", lanes), ("newest-parents.json", newest), ("prs.json", prs), ("git-facts.json", facts)]:
    with open(os.path.join(out, name), "w") as f:
        json.dump(val, f, indent=1, ensure_ascii=False)
for k, v in lanes.items():
    print(k, v["branch"], len(v["runs"]), {c: sum(r["conclusion"] == c for r in v["runs"]) for c in ("success", "failure", "cancelled", "in_progress", "queued")})
for r in lanes["2635"]["runs"]:
    print(" 2635", r["created"], r["head"], r["conclusion"], {s: (r[s].get("failures"), r[s].get("tests"), r[s].get("seconds")) for s in ("fast", "full") if s in r})
print(json.dumps({k: (v["head"], v["conclusion"], {s: (v[s].get("failures"), v[s].get("tests")) for s in ("fast", "full") if s in v}) for k, v in newest.items()}))
print(json.dumps(facts["conflicts_2635_with_2597"]), facts["2597_behind_dev"], facts["2635_behind_dev"])
