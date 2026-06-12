# purr

A cat that shows off. Prints a text file one page at a time, animating each
page with a [terminaltexteffects](https://github.com/ChrisBuilds/terminaltexteffects) effect.

## Install

```
pip install terminaltexteffects
```

Binary to follow.....

Requires Python 3.9+.

## Usage

```
python purr.py FILE                random effect per page
python purr.py FILE -e decrypt     use a named effect
python purr.py --list              list all 37 effects
```

After each page animates, press any key for the next page, `q` / `Esc` to quit.

## Keys during an animation

| Press | Effect |
|-------|--------|
| any key | fast-forward — frame-rate delay removed, frames play at full speed |
| any key again | skip — jump straight to the finished page |
| `q` / `Esc` / `Ctrl-C` | quit immediately |

### Options

| Flag | Meaning |
|------|---------|
| `-e, --effect NAME` | effect to use (default `random` — new pick each page) |
| `-l, --list` | print available effect names |
| `-p, --page-lines N` | lines per page (default: terminal height − 1) |
| `-f, --frame-rate FPS` | speed up / slow down the animation |

### Notes

- Piped or redirected output (`purr.py file.txt > out.txt`) skips effects and
  behaves like plain `cat` — animations only make sense on a live terminal.
- Some effects (blackhole, fireworks, rings) are slow on tall pages; bump
  `-f 200` or shrink `-p` if one drags.
- Good first effects to try: `decrypt`, `matrix`, `beams`, `burn`, `slide`,
  `wipe`, `print`.
