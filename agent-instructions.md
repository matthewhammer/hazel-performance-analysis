# Hazel performance analysis: agent instructions

How Matthew and his agent write the **Hazel performance analysis** series: what it is for, who reads it, and how an issue is made, checked and published. Read this before writing or changing an issue.

## Purpose and audience

The series explains Hazel's performance to **people outside our working loop**: Cyrus, the Hazel team, and anyone else who follows the work. Each issue takes one question and answers it with measurements. Is it really that slow? Where does the time go? What fixed it, and what's left? The questions often come from a meeting with Cyrus, or from the dashboard's next steps.

The series is **not our working record.** That is `hazel-work-notes`, a private repository: the Hazel Work Dashboard, its snapshots and our next steps, written for the two of us. So:

- **Write for a reader who wasn't there.** Say what the slide, the branch or the measurement is. Never rely on what was said in chat.
- **No working chatter:** no to-do lists for ourselves, no local ports or `localhost` links, no "we tried X at 3 am". A dead end belongs in an issue only when it teaches the reader something ("tried and not kept", with its numbers).
- **The dashboard links here, not the other way round.** An issue may cite a next step's question, but its links go to PRs, commits, #2609's findings and other issues.

## Scope

- Hazel's performance in the browser: the editor, statics, the evaluator and its worker, and livelits. Most of all on the livelits branches, [#2635](https://github.com/hazelgrove/hazel/pull/2635) (livelits × modular editors) and [#2597](https://github.com/hazelgrove/hazel/pull/2597) (the full livelits branch), and on `dev`.
- One question per issue. A finding that answers a different question becomes its own issue, or a finding on [hazelgrove/hazel#2609](https://github.com/hazelgrove/hazel/issues/2609), the performance tracking issue.
- The plain-JS games (Messed Up Dress Up) appear as the baseline Hazel is measured against: what a toy costs when it isn't user-defined Hazel code.

## Where things are

| What | Where |
|---|---|
| This repository | https://github.com/matthewhammer/hazel-performance-analysis (public), checked out at `~/hazel-perf-report`. |
| The issues | `NNN/index.html`, with images in `NNN/img/`. Issue 001 is the root `index.html` (it began as a single report). |
| The series index | `series/index.html`, a card per issue. `series/NNN` are links to the issues. |
| Patches tried and not kept | `patches/`, named for what they do. |
| Local preview | `series/` served at http://localhost:8131/series/ (launch entry `perf-report`). |
| Published | http://matthewhammer.org/hazel/performance-analysis/, HTTP only (the site's certificate is broken). |

## Writing an issue

- **Start from the question,** in the subtitle, and say where it came from.
- **Short answers first,** in the headline box: numbered, each a bold claim with its key number. A reader who stops there should have the answer.
- **Show the data in pictures, especially at the top.** Wherever a picture says it faster than a table, draw it: bar charts of times before and after, a timeline of where a change's time goes, before-and-after pictures, a diagram of what runs where. Above all in the short answers: each key finding gets a figure beside it when it can, so a reader who only looks at the top sees the answer. Issue 001 is the model: its number cards, the animated race of one slider release against Dress Up, the pipeline diagram, and screenshots with captions. Draw figures from the measured numbers, label each bar or mark with its value, give every figure alt text and a caption that says what it shows, and keep the table of numbers too, below the figure. A thumbnail on the series index does not count: the figures belong in the issue.
- **Then the sections,** each with an `id` so it can be linked, for example `#really`, `#why`, `#fix`, `#next` and `#method`. End with **What next** and **How this was put together**.
- **Every number says what was measured, on which build (a commit id), how, and how many runs.** One run is not a trend: say so, or run more. Name the baseline, and give the noise floor when comparing.
- **Steps are not time.** A count of evaluation steps can disagree with the clock, in either direction (issue 006's update). Time a change before claiming it.
- **Profiled times run long,** sometimes by half. Prefer shares of a profile, and quote unprofiled times next to them.
- **Name the mechanism, not the abstraction.** Write "the page redraws the whole code view for every message", not a category name.
- **Credit other people's work** by name, with the commit. Several fixes in the series are Andrew Blinn's, from #2469.
- **Link plainly:** PRs as `hazelgrove/hazel#N` with a phrase saying what each is, commits by their 10-character id, findings on #2609 by number, and other issues relatively (`../004/`).
- **Matthew's kids are M and N,** never by name.
- **Every "What next" step gets a link and a ticket button.** Run `python3 tools/add_steps.py NNN/index.html` on a new issue before publishing (it is idempotent, so run it again after regenerating). Each step of the list after `<h2 id="next">` gets an anchor (`#step-N`) and a "copy for a ticket" button that copies `Mint a ticket for this step: Hazel performance analysis, issue NNN, What next, step N: "...". URL`, for Matthew to paste to Claude. Steps have no ticket numbers in the issue: a ticket is minted, in the work notes, only when he asks.
- **Every page gets the theme switch.** Run `python3 tools/add_theme.py NNN/index.html` on a new issue (idempotent, like add_steps). It adds a button, top right, cycling Auto / Light / Dark, remembered per site; the page's CSS must define its dark colours under both `@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) ... }` and `:root[data-theme="dark"]`. A drawing shown with `<img>` follows the system theme, not the switch: give a theme-aware SVG a light and a dark copy with `python3 tools/theme_variants.py NNN/img/thumb.svg` and show both, as `img.light` and `img.dark` (009's card in `series/index.html`). Thumbnails are transparent, or dark-friendly, except 002 to 004, which show the app as it looks.
- **When adding an issue, read the others.** Link back to what it builds on. Where it explains or corrects an earlier issue, add a dated note there (below).

## Corrections and updates

A published issue is never rewritten. To correct or extend it:

- add a **dated update box** under the short answers (`Update, later on 2026-10-12: ...`) when the change matters to its answers;
- add a **dated note after each claim it explains or supersedes**, linking where the new answer is;
- add an **Update section** (`#update`) with the numbers, when there is more than a note's worth.

## Publishing

An issue is drafted here and previewed locally. **Matthew reviews it and says when to publish.** Then:

1. Copy the issue, and any issues with new dated notes, to `~/matthewhammer.github.io/hazel/performance-analysis/`. Update the series index there with the new card.
2. Give the card a thumbnail (`NNN/img/thumb.png`), rendered in headless Firefox, that says the issue's point at a glance.
3. Push, wait for the Pages run, and check the live pages over HTTP, not HTTPS.
4. Commit here too, saying what was published, and push. This repository is public, so what is pushed is published as well: push a draft only once Matthew has seen it.

Ask before posting to GitHub, for example a finding on #2609. Post with `gh ... --body-file` and a quoted heredoc.
