#!/usr/bin/env python3
"""^report(18): why #2635's CI is red. Collects everything the report says from GitHub and git, into 018/data/.

  python3 collect018.py <logs dir> <hazel checkout> <out dir>

<logs dir> keeps each Fast or Full checks job's log as GitHub gives it (fetched with
`gh api repos/hazelgrove/hazel/actions/jobs/<job>/logs` when missing). <hazel checkout> needs the
commits named below (git fetch origin dev modular-editors integration/livelits-splicerefs-full
integration/livelits-modular-editors). Run on 2026-10-19 between 09:40 and 09:55 MDT."""
import json, os, re, subprocess, sys, time

logs, repo, out = sys.argv[1:4]
os.makedirs(logs, exist_ok=True)
REPO = "hazelgrove/hazel"


def sh(*args, cwd=None):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True).stdout


def gh(path):
    for attempt in range(5):  # GitHub answers 502 now and then
        try:
            got = json.loads(sh("gh", "api", path))
            if "message" not in got or len(got) > 2:
                return got
        except json.JSONDecodeError:
            pass
        time.sleep(3 * (attempt + 1))
    raise RuntimeError("GitHub did not answer: " + path)


def git(*args):
    return sh("git", *args, cwd=repo).strip()


# Every CI run on #2635's branch, oldest last, as GitHub lists them.
runs = []
for page in range(1, 5):
    got = gh(f"repos/{REPO}/actions/runs?branch=integration/livelits-modular-editors&per_page=100&page={page}")["workflow_runs"]
    runs += [{"run": r["id"], "head": r["head_sha"][:10], "conclusion": r["conclusion"] or r["status"], "created": r["created_at"]}
             for r in got if r["name"] == "CI"]
    if len(got) < 100:
        break

ANSI = re.compile(r"\x1b\[[0-9;]*m")


def job_log(job):
    p = os.path.join(logs, f"job{job}.log")
    if not os.path.exists(p) or os.path.getsize(p) == 0:
        with open(p, "w") as f:
            f.write(sh("gh", "api", f"repos/{REPO}/actions/jobs/{job}/logs"))
    return ANSI.sub("", open(p, encoding="utf-8", errors="replace").read())


def jobs_of(run):
    return {j["name"]: j["id"] for j in gh(f"repos/{REPO}/actions/runs/{run}/jobs")["jobs"]}


def read_suite(text):
    """The suite's verdict, and each failing test with its first failed assertion."""
    m = re.search(r"(\d+) failures! in ([\d.]+)s\. (\d+) tests run", text)
    ok = re.search(r"Test Successful in ([\d.]+)s\. (\d+) tests run", text)
    fails, seen = [], set()
    rows = re.findall(r"│ \[FAIL\]\s+(\S+)\s+(\d+)\s+(.*?)\.\.\.", text)
    for group, n, name in rows:
        if (group, n) in seen:
            continue
        seen.add((group, n))
        fails.append({"group": group, "n": int(n), "name": name.strip()})
    # The failed assertions, in the order alcotest prints them (one block per failing test).
    lines, asserts = text.split("\n"), []
    for i, l in enumerate(lines):
        m2 = re.match(r"\S+Z FAIL (.*)", l)
        if m2:
            near = "\n".join(lines[i + 1:i + 5])
            e, r = re.search(r"Expected: `(.*?)'", near), re.search(r"Received: `(.*?)'", near)
            asserts.append({"check": m2.group(1).strip()[:400], "expected": e and e.group(1), "received": r and r.group(1)})
    for f, a in zip(fails, asserts):
        f.update(a)
    if m:
        return {"failures": int(m.group(1)), "seconds": float(m.group(2)), "tests": int(m.group(3)), "failing": fails}
    if ok:
        return {"failures": 0, "seconds": float(ok.group(1)), "tests": int(ok.group(2)), "failing": []}
    return {"failures": None, "failing": fails}


# The failing runs read (GitHub lists the newest first): the newest, every sixth after it, the one before the 10-17 update, and the oldest.
failed = [r for r in runs if r["conclusion"] == "failure"]
sample_ids = {failed[-1]["run"]} | {r["run"] for i, r in enumerate(failed) if (i + 1) % 6 == 0} | {failed[0]["run"]}
sample_ids |= {r["run"] for r in failed if r["head"] == "438812718b"}
sampled = []
for r in sorted((r for r in runs if r["run"] in sample_ids), key=lambda r: r["created"]):
    js = jobs_of(r["run"])
    entry = dict(r)
    for name in ("checks / Fast checks", "checks / Full tests"):
        short = "fast" if "Fast" in name else "full"
        if name in js and (short == "fast" or r["head"] == "9e7258b55b"):
            entry[short] = {"job": js[name], **read_suite(job_log(js[name]))}
    sampled.append(entry)

# The parents, at the commits that matter, and #2469 today.
parents = {}
for key, run, label in [("2597", 38744490569, "#2597, integration/livelits-splicerefs-full, at f8ae6f2b9c"),
                        ("2469_merged", 39084361379, "#2469, modular-editors, at c349058154 (contains 19fef7c9bb, what #2635 merged on 10-17)"),
                        ("2469_today", 39275903283, "#2469, modular-editors, at a41b292007 (2026-10-19 08:12 MDT)"),
                        ("2687", 39195250645, "#2687 (Andrew's stdlib branch, into modular-editors), at 5cf71f2d30: modular editors + Modules II parts 1-2 + DefStatics' per-member path ported onto Modules II (00bc805ca1)")]:
    meta = gh(f"repos/{REPO}/actions/runs/{run}")
    js = jobs_of(run)
    e = {"label": label, "run": run, "head": meta["head_sha"][:10], "created": meta["created_at"], "conclusion": meta["conclusion"] or meta["status"]}
    for name in ("checks / Fast checks", "checks / Full tests"):
        short = "fast" if "Fast" in name else "full"
        j = gh(f"repos/{REPO}/actions/jobs/{js[name]}")
        if j["status"] == "completed":
            e[short] = {"job": js[name], **read_suite(job_log(js[name]))}
        else:
            e[short] = {"job": js[name], "status": j["status"]}
    parents[key] = e

# Both parents' CI runs over the same days, for the timeline.
lanes = {}
for key, branch in [("2469", "modular-editors"), ("2597", "integration/livelits-splicerefs-full"), ("2687", "stdlib")]:
    got_all = []
    for page in range(1, 6):
        got = gh(f"repos/{REPO}/actions/runs?branch={branch}&per_page=100&page={page}")["workflow_runs"]
        got_all += [{"run": r["id"], "head": r["head_sha"][:10], "conclusion": r["conclusion"] or r["status"], "created": r["created_at"]}
                    for r in got if r["name"] == "CI" and r["created_at"] >= "2026-10-01"]
        if len(got) < 100 or got[-1]["created_at"] < "2026-10-01":
            break
    lanes[key] = {"branch": branch, "runs": got_all}

# Where each failing test's file lives.
REFS = {"dev": "origin/dev", "#2597 (f8ae6f2b9c)": "f8ae6f2b9c", "#2469 merged (19fef7c9bb)": "19fef7c9bb",
        "#2635 first run (42f1ab0be7)": "42f1ab0be7", "#2635 now (9e7258b55b)": "9e7258b55b"}
files = {}
for label, ref in REFS.items():
    names = git("ls-tree", "-r", "--name-only", ref, "test").split("\n")
    files[label] = {
        "defstatics_tests": sorted(n for n in names if re.search(r"DefStaticsParity|ModRoot|TypeDeps|LabelBench", n)),
        "table_decorations_test": bool(git("grep", "-l", "TableDecorations", ref, "--", "test")),
    }

facts = {
    "dev_head": git("rev-parse", "--short=10", "origin/dev"),
    "full_head": git("rev-parse", "--short=10", "f8ae6f2b9c"),
    "full_in_2635": subprocess.run(["git", "merge-base", "--is-ancestor", "f8ae6f2b9c", "9e7258b55b"], cwd=repo).returncode == 0,
    "merge_base_2635_full": git("merge-base", "f8ae6f2b9c", "9e7258b55b")[:10],
    "full_commits_since_merge": int(git("rev-list", "--count", "3efe8c7e52..f8ae6f2b9c")),
    "full_commits_cherry_picked": sum(1 for l in git("cherry", "9e7258b55b", "f8ae6f2b9c", "3efe8c7e52").split("\n") if l.startswith("-")),
    "conflicted_files_2635_with_full": [l for l in sh("git", "merge-tree", "--write-tree", "--name-only", "f8ae6f2b9c", "9e7258b55b", cwd=repo).split("\n\n")[0].split("\n")[1:] if l],
    "dev_canonical_completion_merge_9b3f18323a_in_dev": subprocess.run(["git", "merge-base", "--is-ancestor", "9b3f18323a", "origin/dev"], cwd=repo).returncode == 0,
    "dev_canonical_completion_merge_9b3f18323a_in_full": subprocess.run(["git", "merge-base", "--is-ancestor", "9b3f18323a", "f8ae6f2b9c"], cwd=repo).returncode == 0,
    "full_dev_base": git("merge-base", "origin/dev", "f8ae6f2b9c")[:10],
    "full_behind_dev": int(git("rev-list", "--count", git("merge-base", "origin/dev", "f8ae6f2b9c") + "..origin/dev")),
    "19fef7c9bb_in_c349058154": subprocess.run(["git", "merge-base", "--is-ancestor", "19fef7c9bb", "c349058154"], cwd=repo).returncode == 0,
    "defstaticsparity_same_c349_and_2635": subprocess.run(["git", "diff", "--quiet", "c349058154", "9e7258b55b", "--", "test/Test_DefStaticsParity.re"], cwd=repo).returncode == 0,
    "modules_ii_parts": {b: {"head": git("rev-parse", "--short=10", f"origin/modules-ii/{b}"),
                             "in_2687_stdlib": subprocess.run(["git", "merge-base", "--is-ancestor", f"origin/modules-ii/{b}", "origin/stdlib"], cwd=repo).returncode == 0,
                             "in_2635": subprocess.run(["git", "merge-base", "--is-ancestor", f"origin/modules-ii/{b}", "9e7258b55b"], cwd=repo).returncode == 0}
                         for b in ("1-sig-types", "2-width-subtyping", "3-abstract-types")},
    "modules_ii_on_2635": git("log", "-1", "--format=%h %cI %s", "c54b1068f9"),
    "port_2687": git("log", "-1", "--format=%h %cI %an %s", "00bc805ca1"),
    "port_2687_message": git("log", "-1", "--format=%B", "00bc805ca1"),
    "defstaticsparity_cases_on_2687": {t: bool(git("grep", "-c", t, "origin/stdlib", "--", "test/Test_DefStaticsParity.re"))
                                       for t in ("the app's path reuses its slot", "a module root's items", "a member retype", "a recursive type export",
                                                 "mega-mod-1k in one module", "the slide corpus")},
    "defstaticsparity_lines_removed_2635_to_2687": [l for l in git("diff", "9e7258b55b", "origin/stdlib", "--", "test/Test_DefStaticsParity.re").split("\n")
                                                    if l.startswith("-") and not l.startswith("---")],
    "gaps_recorded": {c: git("log", "-1", "--format=%h %cI %s", c) for c in ("43089b065d", "11fbc4480d", "8c968efcc4", "9e7258b55b")},
}

os.makedirs(out, exist_ok=True)
for name, val in [("runs-2635.json", runs), ("sampled-runs.json", sampled), ("parents.json", parents), ("parent-runs.json", lanes), ("test-files.json", files), ("git-facts.json", facts)]:
    with open(os.path.join(out, name), "w") as f:
        json.dump(val, f, indent=1, ensure_ascii=False)
for k, v in lanes.items():
    print(k, v["branch"], len(v["runs"]), {c: sum(r["conclusion"] == c for r in v["runs"]) for c in ("success", "failure", "cancelled", "in_progress")})
print(f"{len(runs)} runs; {sum(r['conclusion'] == 'failure' for r in runs)} failed, {sum(r['conclusion'] == 'cancelled' for r in runs)} cancelled, "
      f"{sum(r['conclusion'] == 'success' for r in runs)} green; sampled {len(sampled)}")
for s in sampled:
    f = s.get("fast", {})
    print(s["created"][:10], s["head"], f.get("failures"), f.get("tests"), [x["group"] + " " + str(x["n"]) for x in f.get("failing", [])])
