# Slider responsiveness in Hazel livelits

A report, `index.html`, on why a livelit slider change isn't immediate yet: every performance problem found in fall 2026, its fix, and where the remaining time in a slider release goes, compared with the plain HTML/JS Dress Up app.

Open `index.html` in a browser. Screenshots are in `img/`.

Measured 2026-10-09 and 10 on hazelgrove/hazel#2635 (livelits × modular editors), dev builds, headless Firefox. The measuring scripts are untracked in `~/hazel-livelits-modular/scripts`:
- `slider_timing.py`: release-to-redraw wall time;
- `profile_interaction.py`: Firefox CPU profile per interaction;
- `worker_sizes.py`: eval-worker message sizes;
- `lost_update.py`: the Shirt and Pants lost-click diagnostic.

The issue behind it is hazelgrove/hazel#2609, findings 10 and 11.
