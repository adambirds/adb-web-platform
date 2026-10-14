# Local CMS demo image fixtures

These are original screenshots of fictional HTML/CSS websites and editorial
covers. They are development fixtures, not real client projects. The demo seed
command stores them in the regular CMS image fields, so public pages exercise
the same media path as real portfolio and article entries.

`concept.html` is the source. Open it in a browser with these query parameters:

- `kind=studio`, `goods`, `editorial` or `local`, plus `name` for a project;
- `kind=blog`, plus `title` for an editorial cover.

Render at 1800 × 1000 pixels to reproduce the bundled PNGs. Project numbers match
`PROJECTS` in `seed_web_designs_demo.py`; article numbers match `ARTICLES`.

Normal seeding preserves existing images and edited copy. Use `--refresh-images`
to deliberately replace this command's reserved Web Designs demo images. It keeps
text edits and other CMS entries. The development restrictions and `--clear`
cleanup behavior are unchanged.
