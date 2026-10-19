#!/usr/bin/env python3
"""Republish an agenda report after a change (Matthew, 2026-10-19: agendas are public from now on).
  python3 tools/publish_agenda.py NNN ["what changed"]
Regenerates NNN/ from NNN/data/agenda.json (NNN/drivers/genNNN.py, then report_refs, link_prs, add_theme and
theme_variants), copies it into ~/matthewhammer.github.io/hazel/reports/NNN/, and commits and pushes
both repositories, committing only the agenda's own files. Its series card is added once, by hand, when the agenda
is first published."""
import os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.expanduser("~/matthewhammer.github.io")
nnn = f"{int(sys.argv[1]):03d}"
what = sys.argv[2] if len(sys.argv) > 2 else "updated"
TRAILER = "\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"


def run(*cmd, cwd=ROOT):
    print("$", " ".join(cmd))
    subprocess.run(cmd, cwd=cwd, check=True)


run("python3", f"{nnn}/drivers/gen{nnn}.py")
for tool in ("report_refs", "link_prs", "add_theme"):
    run("python3", f"tools/{tool}.py", f"{nnn}/index.html")
run("python3", "tools/theme_variants.py", f"{nnn}/img/thumb.svg")

dest = os.path.join(SITE, "hazel", "reports", nnn)
if not os.path.isdir(dest):
    sys.exit(f"{dest} does not exist: publish the agenda the first time by hand (its series card, the Hazel page)")
run("git", "pull", "-q", "--rebase", cwd=SITE)
run("cp", "-r", f"{nnn}/index.html", f"{nnn}/img", f"{nnn}/data", f"{nnn}/drivers", dest + "/")
msg = f"^report({int(nnn)}), the agenda: {what}"
# Pushing this repository publishes every commit not yet pushed, and drafts (reports Matthew has not read) may be
# among them (2026-10-19: report 21's draft went out with an agenda update). So push it only when the agenda's
# commit is the only one waiting; otherwise leave it local and say so. The homepage is pushed either way.
waiting = subprocess.run(["git", "rev-list", "--count", "origin/main..HEAD"], cwd=ROOT,
                         capture_output=True, text=True).stdout.strip()
for repo, path in ((ROOT, nnn), (SITE, f"hazel/reports/{nnn}")):
    run("git", "add", path, cwd=repo)
    if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=repo).returncode:
        run("git", "commit", "-q", "-m", msg + TRAILER, cwd=repo)
        if repo == SITE:
            run("git", "pull", "-q", "--rebase", cwd=SITE)
        if repo == ROOT and waiting != "0":
            print(f"not pushing {ROOT}: {waiting} other commit(s) wait unpushed (drafts?); the agenda's commit stays local too")
            continue
        run("git", "push", "-q", "origin", "HEAD", cwd=repo)
print(f"published: https://matthewhammer.org/hazel/reports/{nnn}/ (live after the Pages build, about 2 minutes)")
