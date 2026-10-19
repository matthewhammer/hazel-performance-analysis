#!/usr/bin/env python3
"""Republish an agenda report after a change (Matthew, 2026-10-19: agendas are public from now on).
  python3 tools/publish_agenda.py NNN ["what changed"]
Regenerates NNN/ from NNN/data/agenda.json (NNN/drivers/genNNN.py, then report_refs, link_prs, add_theme and
theme_variants), copies it into ~/matthewhammer.github.io/hazel/performance-analysis/NNN/, and commits and pushes
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

dest = os.path.join(SITE, "hazel", "performance-analysis", nnn)
if not os.path.isdir(dest):
    sys.exit(f"{dest} does not exist: publish the agenda the first time by hand (its series card, the Hazel page)")
run("git", "pull", "-q", "--rebase", cwd=SITE)
run("cp", "-r", f"{nnn}/index.html", f"{nnn}/img", f"{nnn}/data", f"{nnn}/drivers", dest + "/")
msg = f"^report({int(nnn)}), the agenda: {what}"
for repo, path in ((ROOT, nnn), (SITE, f"hazel/performance-analysis/{nnn}")):
    run("git", "add", path, cwd=repo)
    if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=repo).returncode:
        run("git", "commit", "-q", "-m", msg + TRAILER, cwd=repo)
        if repo == SITE:
            run("git", "pull", "-q", "--rebase", cwd=SITE)
        run("git", "push", "-q", "origin", "HEAD", cwd=repo)
print(f"published: https://matthewhammer.org/hazel/performance-analysis/{nnn}/ (live after the Pages build, about 2 minutes)")
