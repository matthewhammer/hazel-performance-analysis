# ^report(25): the listings laid out on more lines, Hazel-style (one let a line, case arms and if/else on their own lines);
# the same tokens as drivers/r25.mjs's text, which is what was measured. ⟪kind|...⟫ marks a hot spot.
SHARED = """type Cell = (
  col = Int,
  row = Int,
  kind = String,
  ways = [String]
) in
type Globals = (
  lever_L = Bool, lever_R = Bool, wiring = String, draws = [Float],
  pits_on = [Bool], covered = [Bool], hatch = Bool, things = [Thing],
  rooms = [String], exits = [String], out = String, out_room = Int,
  at_col = Int,
  at_row = Int,
  cols = Int,
  rows = Int,
  cells = [Cell]
) in
type Event =
  + Pull(String) + PullBoulder(String) + PullHatch(Int) + PullThing(Int)
  + FallPit(Int) + WayOut(Int)
  + Way(String) in
let no_way = fun (kind, d) : (String, String) ->
  kind == "waterfall" && d == "N" in
let dir = fun d : String ->
  if d == "N" then (0, 0 - 1)
  else if d == "NE" then (1, 0 - 1)
  else if d == "E" then (1, 0)
  else if d == "SE" then (1, 1)
  else if d == "S" then (0, 1)
  else if d == "SW" then (0 - 1, 1)
  else if d == "W" then (0 - 1, 0)
  else if d == "NW" then (0 - 1, 0 - 1)
  else (0, 0) in
let opp = fun d : String ->
  if d == "N" then "S"
  else if d == "NE" then "SW"
  else if d == "E" then "W"
  else if d == "SE" then "NW"
  else if d == "S" then "N"
  else if d == "SW" then "NE"
  else if d == "W" then "E"
  else if d == "NW" then "SE"
  else "" in
let member = fun (s, xs) : (String, [String]) ->
  case xs
  | [] => false
  | x :: rest => x == s || member(s, rest)
  end in
let decide = fun (x, back, c, r) ->
  case x
  | Some(x) =>
    if member(back, x.ways) && !no_way(x.kind, back)
    then GoSquare(c, r, back, Done)
    else Done
  | None => Done
  end in"""
MK = """let mk = fun look ->
  ⟪floor|fun (g, e) : (Globals, Event)⟫ ->
    case e
    | Way(d) =>
      let (dx, dy) = dir(d) in
      let c = g.at_col + dx in
      let r = g.at_row + dy in
      let back = opp(d) in
      if c < 0 || r < 0 || c >= g.cols || r >= g.rows then Done
      else decide(⟪warn|look(g.cells, c, r, g.cols)⟫, back, c, r)
    | _ => Done
    end in"""
SHIPPED = MK + """
let findA = fun (cs, c, r) ⟪bad|: ([Cell], Int, Int)⟫ ->
  case cs
  | [] => None
  | x :: rest =>
    if x.col == c && x.row == r then Some(x)
    else ⟪warn|findA(rest, c, r)⟫
  end in
let shipped = mk(fun (cs, c, r, w) -> findA(cs, c, r)) in"""
NOANN = MK + """
let findU = fun (cs, c, r) ->
  case cs
  | [] => None
  | x :: rest =>
    if x.col == c && x.row == r then Some(x)
    else ⟪warn|findU(rest, c, r)⟫
  end in
let noann = mk(fun (cs, c, r, w) -> findU(cs, c, r)) in"""
INDEX = MK + """
let nthU = fun (cs, i) ->
  case cs
  | [] => None
  | x :: rest =>
    if i == 0 then Some(x)
    else ⟪warn|nthU(rest, i - 1)⟫
  end in
let index = mk(fun (cs, c, r, w) -> nthU(cs, r * w + c)) in"""
HELD = """let held = fun ⟪held|(cells : [Cell])⟫ ->
  fun (n, e) ->
    case e
    | Way(d) =>
      let (dx, dy) = dir(d) in
      let c = n.at_col + dx in
      let r = n.at_row + dy in
      let back = opp(d) in
      if c < 0 || r < 0 || c >= n.cols || r >= n.rows then Done
      else decide(⟪warn|nthU(cells, r * n.cols + c)⟫, back, c, r)
    | _ => Done
    end in"""
IDA = """let idA = ⟪floor|fun (g, e) : (Globals, Event)⟫ -> Done in"""
NEAR = """let near = fun (n, e) ->
  case e
  | Way(d) =>
    let (dx, dy) = dir(d) in
    let c = n.at_col + dx in
    let r = n.at_row + dy in
    let back = opp(d) in
    if c < 0 || r < 0 || c >= n.cols || r >= n.rows then Done
    else decide(findU(⟪good|n.near⟫, c, r), back, c, r)
  | _ => Done
  end in"""
# what held and near need before them (the walks they call), laid out the same way
NTHU = """let nthU = fun (cs, i) ->
  case cs
  | [] => None
  | x :: rest => if i == 0 then Some(x) else nthU(rest, i - 1)
  end in"""
FINDU = """let findU = fun (cs, c, r) ->
  case cs
  | [] => None
  | x :: rest => if x.col == c && x.row == r then Some(x) else findU(rest, c, r)
  end in"""
# the program's start for the tiles: the game's preamble (preamble.hz), the same types laid out
TILE_PREAMBLE = """type Cmd =
  + Done
  + Flip(String, Cmd)
  + Say(String, Cmd)
  + SetPit(Int, Bool, Cmd)
  + DropBoulder(Int, Cmd)
  + LiftBoulder(Int, Cmd)
  + SetHatch(Int, Bool, Cmd)
  + OpenDoor(Int, Bool, Cmd)
  + DropRock(Int, Bool, Cmd)
  + Wait(Int, Cmd)
  + GoRoom(Int, Cmd)
  + GoSquare(Int, Int, String, Cmd) in
type Thing = (
  at = Int, uid = String, kind = String, on = Bool,
  works = [String], does = String, open = Bool, boulder = Bool
) in
""" + SHARED[:SHARED.index("let no_way")]
