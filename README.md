# Hazel performance analysis

A series of issues on making [Hazel](https://hazel.org) responsive enough for its livelits to feel like plain apps: what we measured, what we found, what we fixed, and what's left. By Matthew Hammer, working with Claude, for Cyrus, the Hazel team and anyone following the work.

**Read it at http://matthewhammer.org/hazel/performance-analysis/** (HTTP only, for now).

| Issue | |
|---|---|
| [001](index.html) | Why a slider isn't instant yet |
| [002](002/) | From a game to a slide deck: Messed Up Dress Up in Hazel |
| [003](003/) | A day of requests from M and N |
| [004](004/) | The witch and her woods, ported to Hazel |
| [005](005/) | Two threads, one picture: the worker, the page, and diffing the view |
| [006](006/) | Catching performance regressions in CI |
| [007](007/) | Five minutes to the first picture |
| [008](008/) | One slider, three ways: what modular editing saves |

The performance tracking issue is [hazelgrove/hazel#2609](https://github.com/hazelgrove/hazel/issues/2609); its findings are cited by number. Most of the work is on [#2635](https://github.com/hazelgrove/hazel/pull/2635) (livelits × modular editors) and [#2597](https://github.com/hazelgrove/hazel/pull/2597) (the full livelits branch).

## What's here

- `NNN/index.html`: an issue, with its images in `NNN/img/`. Issue 001 is the root `index.html`, since the series began as that one report.
- `series/index.html`: the series' index, a card per issue, as published. `series/NNN` link to the issues.
- `patches/`: changes that were tried and not kept, each named for what it does. The issues give their numbers.
- `agent-instructions.md`: how the series is written, for whoever writes the next issue.

To read it locally, serve the repository and open `/series/`:

```
python3 -m http.server 8131
```

then visit http://localhost:8131/series/.
