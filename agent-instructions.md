# Hazel performance analysis: agent instructions

How Matthew and his agent write the **Hazel performance analysis** series: what it is for, who reads it, and how a report is made, checked and published. Read this before writing or changing a report.

## Purpose and audience

The series explains Hazel's performance to **people outside our working loop**: Cyrus, the Hazel team, and anyone else who follows the work. Each report takes one question and answers it with measurements. Is it really that slow? Where does the time go? What fixed it, and what's left? The questions often come from a meeting with Cyrus, or from the dashboard's next steps.

The series is **not our working record.** That is `hazel-work-notes` (public, but written for the two of us): the Hazel Work Dashboard, its snapshots, its tickets and our work notes. So:

- **Write for a reader who wasn't there.** Say what the slide, the branch or the measurement is. Never rely on what was said in chat.
- **No working chatter:** no to-do lists for ourselves, no local ports or `localhost` links, no "we tried X at 3 am". A dead end belongs in a report only when it teaches the reader something ("tried and not kept", with its numbers).
- **The dashboard links here; only the series index links back.** The index has one line linking the Hazel Work Dashboard (Matthew, 2026-10-14): http://localhost:8000/ when the index is served locally, the published dashboard (http://matthewhammer.org/hazel/work-dashboard/) when it is published, as the dashboard's menu links the local or the published series. A report may cite a ticket's question, but its links go to PRs, commits, #2609's findings and other reports.

## Scope

- Hazel's performance in the browser: the editor, statics, the evaluator and its worker, and livelits. Most of all on the livelits branches, [#2635](https://github.com/hazelgrove/hazel/pull/2635) (livelits × modular editors) and [#2597](https://github.com/hazelgrove/hazel/pull/2597) (the full livelits branch), and on `dev`.
- One question per report. A finding that answers a different question becomes its own report, or a finding on [hazelgrove/hazel#2609](https://github.com/hazelgrove/hazel/issues/2609), the performance tracking issue.
- The plain-JS games (Messed Up Dress Up) appear as the baseline Hazel is measured against: what a toy costs when it isn't user-defined Hazel code.

## Where things are

| What | Where |
|---|---|
| This repository | https://github.com/matthewhammer/hazel-performance-analysis (public), checked out at `~/hazel-perf-report`. |
| The reports | `NNN/index.html`, with images in `NNN/img/`. `^report(1)` is the root `index.html` (it began as a single report). |
| The series index | `series/index.html`, a card per report. `series/NNN` are links to the reports. |
| Patches tried and not kept | `patches/`, named for what they do. |
| Local preview | `series/` served at http://localhost:8131/series/ (launch entry `perf-report`). |
| Published | https://matthewhammer.org/hazel/performance-analysis/ (HTTPS since 2026-10-15; old http:// links redirect). |

## Writing a report

- **Start from the question,** in the subtitle, and say where it came from.
- **Short answers first,** in the headline box: numbered, each a bold claim with its key number. A reader who stops there should have the answer.
- **Show the data in pictures, especially at the top.** Wherever a picture says it faster than a table, draw it: bar charts of times before and after, a timeline of where a change's time goes, before-and-after pictures, a diagram of what runs where. Above all in the short answers: each key finding gets a figure beside it when it can, so a reader who only looks at the top sees the answer. `^report(1)` is the model: its number cards, the animated race of one slider release against Dress Up, the pipeline diagram, and screenshots with captions. Draw figures from the measured numbers, label each bar or mark with its value, give every figure alt text and a caption that says what it shows, and keep the table of numbers too, below the figure. A thumbnail on the series index does not count: the figures belong in the report.
- **Then the sections,** each with an `id` so it can be linked, for example `#really`, `#why`, `#fix`, `#next` and `#method`. End with **What next** and **How this was put together**.
- **Every number says what was measured, on which build (a commit id), how, and how many runs.** One run is not a trend: say so, or run more. Name the baseline, and give the noise floor when comparing.
- **Every report carries its data, twice** (Matthew's rule, 2026-10-14; `^report(14)` is the model). (1) **Embedded:** every number behind the report's figures and tables, as JSON in a `<script type="application/json" id="report-data">` element at the end of the page (escape `</` as `<\/`), with enough description to read it without the prose: the build (PR and commit), the browser, what each measure is and its unit, each run's raw readings, and the patch or driver that made them. A reader or an agent that fetches the page alone has the dataset. (2) **Files:** the same numbers as files in `NNN/data/` (and the drivers in `NNN/drivers/`, the patches in `patches/`), linked from How this was put together; link folders on GitHub (`https://github.com/matthewhammer/hazel-performance-analysis/tree/main/NNN/data`), since the published site has no folder listings. Say in the method section that both exist. Raw files too big to keep (a heap profile) are summarized in `data/`, and the method says so.
- **Steps are not time.** A count of evaluation steps can disagree with the clock, in either direction (`^report(6)`'s update). Time a change before claiming it.
- **Profiled times run long,** sometimes by half. Prefer shares of a profile, and quote unprofiled times next to them.
- **Name the mechanism, not the abstraction.** Write "the page redraws the whole code view for every message", not a category name.
- **Credit other people's work** by name, with the commit. Several fixes in the series are Andrew Blinn's, from #2469.
- **Link plainly:** PRs as `hazelgrove/hazel#N` with a phrase saying what each is, commits by their 10-character id, findings on #2609 by number, and other reports relatively (`../004/`).
- **Our own numbers in our own syntax** (Matthew's, 2026-10-14). The series is made of **reports**; "issue" is GitHub's word, kept for GitHub's issues (the tracking issue #2609). A report is `^report(N)` and a ticket on the work dashboard `^ticket(N)`: no leading zeros, so they can pass 999, shown in monospace with `^report(` and `)` in bold. Write them that way in prose and in chat. Run `python3 tools/report_refs.py NNN/index.html` on a new or changed page (idempotent, like add_steps): it turns a written "report 013" into the chip, links it (`../NNN/`, or `NNN/` from the series index), and adds the chips' style. The folders keep their three digits (`013/`).
- **Every PR or issue number is a link** (Matthew's rule, 2026-10-14), in every report, the series index and `^report(1)`'s page, tables included. Run `python3 tools/link_prs.py NNN/index.html` on a new report before publishing (idempotent, like add_steps; run it again after regenerating, and on any page you change). It links each bare `#N` or `owner/repo#N` to GitHub as `/pull/N` or `/issues/N` (asking GitHub which, remembered in `tools/pr_kinds.json`), and gives every such link a card on hover or focus: title, state, author, dates and comments, asked of GitHub live once per page load, falling back to what GitHub said when the page was built (`tools/pr_cards.html`, inserted between `pr-cards` markers).
- **Matthew's kids are M and N,** never by name.
- **Every "What next" step gets a link and a ticket button.** Run `python3 tools/add_steps.py NNN/index.html` on a new report before publishing (it is idempotent, so run it again after regenerating). Each step of the list after `<h2 id="next">` gets an anchor (`#step-N`) and a "copy for a ticket" button that copies `Mint a ticket for this step: Hazel performance analysis, ^report(N), What next, step N: "...". URL`, for Matthew to paste to Claude. Steps have no ticket numbers in the report: a ticket is minted, in the work notes, only when he asks.
- **Every page gets the theme switch.** Run `python3 tools/add_theme.py NNN/index.html` on a new report (idempotent, like add_steps). It adds a button, top right, cycling Auto / Light / Dark, remembered per site; the page's CSS must define its dark colours under both `@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) ... }` and `:root[data-theme="dark"]`. A drawing shown with `<img>` follows the system theme, not the switch: give a theme-aware SVG a light and a dark copy with `python3 tools/theme_variants.py NNN/img/thumb.svg` and show both, as `img.light` and `img.dark` (009's card in `series/index.html`). Thumbnails are transparent, or dark-friendly, except 002 to 004, which show the app as it looks.
- **When adding a report, read the others.** Link back to what it builds on. Where it explains or corrects an earlier report, add a dated note there (below).

## Corrections and updates

A published report's story is never rewritten. **Pictures that only illustrate what it already says** (a diagram of a structure it describes, a figure of numbers it already gives) **go into the report in place**, with no dated update: they do not change the story (Matthew, 2026-10-14). They still wait for his review before they are published. To correct or extend the story itself:

- add a **dated update box** under the short answers (`Update, later on 2026-10-12: ...`) when the change matters to its answers;
- add a **dated note after each claim it explains or supersedes**, linking where the new answer is;
- add an **Update section** (`#update`) with the numbers, when there is more than a note's worth.

## Publishing

A report is drafted here and previewed locally. **Matthew reviews it and says when to publish.** While it waits for him, say so in the Hazel Work Dashboard's current-ticket note (where the draft is, the local URL, the commit), as `~/hazel-work-notes/agent-instructions.md` describes: he reads the published dashboard from other computers to see that he is the one holding it up. Then:

1. Copy the report, and any reports with new dated notes, to `~/matthewhammer.github.io/hazel/performance-analysis/`. Update the series index there with the new card.
2. Give the card a thumbnail that says the report's point at a glance: a transparent SVG, `NNN/img/thumb.svg`, with its light colours in plain rules and its dark ones in one `@media (prefers-color-scheme: dark)` block, split with `tools/theme_variants.py` into `thumb-light.svg` and `thumb-dark.svg`, both in the card as `img.light` and `img.dark`. Check both on a white and on a dark card. Only a picture of the app itself (002 to 004) stays a PNG on a light ground.
3. List it on the homepage's Hazel page (http://matthewhammer.org/hazel/, "Matthew Hammer and Hazel"): `python3 tools/hazel_page.py` rewrites that page's list of reports from the series index's cards (idempotent).
4. Push, wait for the Pages run, and check the live pages over HTTPS.
5. Commit here too, saying what was published, and push. This repository is public, so what is pushed is published as well: push a draft only once Matthew has seen it.

Ask before posting to GitHub, for example a finding on #2609. Post with `gh ... --body-file` and a quoted heredoc.
