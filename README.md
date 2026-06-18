# purr

A cat that shows off. Prints a text file one page at a time, animating each
page with a [terminaltexteffects](https://github.com/ChrisBuilds/terminaltexteffects) effect.

## Install

```
pip install terminaltexteffects
```

Binary [to follow.....](https://drive.google.com/file/d/1OfA6SuR0EQYFHHdfIp9p33g4BycZ7oi1/view?usp=sharing)

Requires Python 3.9+.

## Usage

```
python purr.py FILE                random effect per page
python purr.py FILE -e decrypt     use a named effect
cat FILE | python purr.py          read piped text from stdin
python purr.py --list              list all 37 effects
```

After each page animates, press any key for the next page, `q` / `Esc` to quit.

Text can come from a file argument or be piped in (`cat FILE | purr`, or
`git log | purr -e matrix`). Keystrokes for paging are read from the terminal,
not stdin, so paging still works while stdin carries the piped text. If both a
file and a pipe are present, the file wins.

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

## Building purr.exe

Run `build.bat` (installs PyInstaller if needed):

```
build.bat
```

Produces a standalone `dist\purr.exe` that takes the same command-line
parameters and needs no Python install. Note: `--collect-submodules` in the
script is required because purr loads effect modules dynamically — without it
the exe would have no effects. First launch is a little slow (one-file exes
self-extract).
