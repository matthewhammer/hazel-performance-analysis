# ^ticket(540): each room's event handler, and its cost in the world's size

Read from the shipped rule texts (kids-choice-games `dress-up/js/25-scripting.js`, 0cc38a1, 2026-10-22). Sizes: N cells in the
world map, T things in a square, W uids a lever works, R rooms in the castle. "Boundary" is what crossing from JS costs per call
before the rule runs: the Globals record converted by `of_js` (each room fills only its own fields; the rest are empty).

| room | event | rule's work | today | boundary today | target | how |
|---|---|---|---|---|---|---|
| Trap | `Pull(side)` | `wire` (first two draws), `pits_open`, two `pit_moves` | O(1) | O(1) | O(1) | already |
| Trap | `PullBoulder(side)` | `nth` on the two-pit lists | O(1) | O(1) | O(1) | already |
| Tree | `PullHatch(n)` | one `SetHatch` | O(1) | O(1) | O(1) | already |
| Square | `PullThing(i)` | `find` the thing at `i` (walk T), then `doors` walks all T things, each asking `member(uid, works)` (walk W) | O(T·W) | O(T), the things list converted | O(W log T) | things held in two maps (by `at`, by `uid`), rebuilt when the square changes; `doors` looks up each of the lever's W uids |
| World | `Way(d)` | `find` the cell at `(c, r)`: walk N | O(N) | O(N), the cells list converted | O(log N) | the cells held in a balanced tree (tree.hz), built when the world changes; held in a closure: needs ^ticket(547) (a held value is otherwise re-evaluated, O(N), at every call from JS) |
| Castle | any event | `index_of(rooms, "dungeon1")` and `"dungeon2"`, on every event, before the case | O(R) | O(R) | O(1) | the two dungeon indices computed when the castle changes, held |
| Castle | `WayOut(n)` | `nth_s(exits, n)`, `index_of(rooms, "trap")`, `length(rooms)` | O(R) | O(R) | O(log R) or O(1) | rooms and exits held as maps, with their length |

Notes:
- R is a castle's rooms (about a dozen at most), so the Castle rows matter for the principle, not for speed.
- Annotated recursive helpers (`find = fun ts : [Thing] -> ...`) push the list type through each tail at every call; #2681's
  memo makes that one lookup a call on the best build, else the walks are quadratic (^report(25), ^report(26)).
- With ^ticket(551)'s handles, a world passed in (not held) crosses in O(1) too, but a tree built in Hazel comes back to JS as
  nested objects (to_js), so passing it back would convert it again: hold it in a closure (547), or add a way to keep a Hazel
  value on the Hazel side under a handle (a follow-up to 551).
