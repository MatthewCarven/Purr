#!/usr/bin/env python3
"""purr — a cat that shows off.

Prints a text file one page at a time, animating each page with a
terminaltexteffects effect. Like `more`, but theatrical.

Usage:
    purr.py FILE                 random effect per page
    purr.py FILE -e decrypt      named effect
    cat FILE | purr.py           read piped text from stdin
    purr.py --list               show available effects

Requires: pip install terminaltexteffects
"""

import argparse
import importlib
import inspect
import os
import pkgutil
import random
import shutil
import sys

QUIT_KEYS = {"q", "\x03", "\x1b"}  # q, Ctrl-C, Esc


# --------------------------------------------------------------------------- effects

def discover_effects():
    """Map short effect name -> module name, e.g. 'rain' -> 'effect_rain'."""
    import terminaltexteffects.effects as fx_pkg
    return {
        m.name.removeprefix("effect_"): m.name
        for m in pkgutil.iter_modules(fx_pkg.__path__)
    }


def load_effect_class(module_name):
    """Import one effect module and return its effect class."""
    from terminaltexteffects.engine.base_effect import BaseEffect
    mod = importlib.import_module(f"terminaltexteffects.effects.{module_name}")
    for _, cls in inspect.getmembers(mod, inspect.isclass):
        if issubclass(cls, BaseEffect) and cls is not BaseEffect \
                and cls.__module__ == mod.__name__:
            return cls
    raise RuntimeError(f"No effect class found in {module_name}")


# --------------------------------------------------------------------------- input

class KeyPoller:
    """Single-key reads without echo: poll() non-blocking, wait() blocking."""

    def __enter__(self):
        self.fd = None
        if os.name != "nt":
            import termios
            import tty
            try:
                self.fd = open("/dev/tty", "rb", buffering=0)
                self._old = termios.tcgetattr(self.fd)
                tty.setcbreak(self.fd.fileno())
            except OSError:
                self.fd = None
        return self

    def __exit__(self, *exc):
        if self.fd is not None:
            import termios
            termios.tcsetattr(self.fd, termios.TCSADRAIN, self._old)
            self.fd.close()

    @staticmethod
    def _decode(ch):
        return ch.decode(errors="ignore").lower()

    def poll(self):
        """Return a pressed key, or '' if none is waiting."""
        if os.name == "nt":
            import msvcrt
            if not msvcrt.kbhit():
                return ""
            ch = msvcrt.getch()
            if ch in (b"\x00", b"\xe0"):    # arrow/function key prefix
                msvcrt.getch()
                return ""
            return self._decode(ch)
        if self.fd is None:
            return ""
        import select
        ready, _, _ = select.select([self.fd], [], [], 0)
        return self._decode(self.fd.read(1)) if ready else ""

    def wait(self):
        """Block until a key is pressed; return it ('' if no tty)."""
        if os.name == "nt":
            import msvcrt
            ch = msvcrt.getch()
            if ch in (b"\x00", b"\xe0"):
                msvcrt.getch()
                return ""
            return self._decode(ch)
        if self.fd is None:
            return ""
        return self._decode(self.fd.read(1))


# --------------------------------------------------------------------------- paging

def wrap_lines(raw_lines, width):
    """Expand tabs and hard-wrap so every line fits the terminal width."""
    out = []
    for line in raw_lines:
        line = line.rstrip("\n").expandtabs(4)
        if not line:
            out.append("")
            continue
        while len(line) > width:
            out.append(line[:width])
            line = line[width:]
        out.append(line)
    return out


def paginate(lines, page_height):
    return [lines[i:i + page_height] for i in range(0, len(lines), page_height)]


def clear_screen():
    print("\x1b[2J\x1b[H", end="", flush=True)


# --------------------------------------------------------------------------- main

def run_effect(effect_cls, text, frame_rate, keys):
    """Animate one page.

    During the animation: first keypress drops the frame-rate delay
    (fast-forward), second keypress jumps straight to the finished page.
    q/Esc/Ctrl-C quits. Returns "quit" or None.
    """
    effect = effect_cls(text)
    effect.terminal_config.wrap_text = False  # pre-wrapped
    if frame_rate:
        effect.terminal_config.frame_rate = frame_rate
    frames = iter(effect)  # explicit iterator so we can reach its terminal
    skip = False
    last = None
    with effect.terminal_output() as terminal:
        for frame in frames:
            key = keys.poll()
            if key in QUIT_KEYS:
                return "quit"
            if key:
                if getattr(frames.terminal, "_frame_rate", 0):
                    frames.terminal._frame_rate = 0   # 1st press: fast-forward
                else:
                    skip = True                       # 2nd press: skip to end
            if skip:
                last = frame                          # consume silently
            else:
                terminal.print(frame)
        if last is not None:
            terminal.print(last)                      # draw the finished page
    return None


def main():
    parser = argparse.ArgumentParser(
        prog="purr",
        description="Print a file page by page with terminal text effects.")
    parser.add_argument("file", nargs="?", help="text file to display")
    parser.add_argument("-e", "--effect", metavar="NAME", default="random",
                        help="effect name (default: random per page)")
    parser.add_argument("-l", "--list", action="store_true",
                        help="list available effects and exit")
    parser.add_argument("-p", "--page-lines", type=int, metavar="N",
                        help="lines per page (default: terminal height - 1)")
    parser.add_argument("-f", "--frame-rate", type=int, metavar="FPS",
                        help="override effect frame rate")
    args = parser.parse_args()

    try:
        effects = discover_effects()
    except ImportError:
        sys.exit("purr: terminaltexteffects is not installed.\n"
                 "      pip install terminaltexteffects")

    if args.list:
        print("\n".join(sorted(effects)))
        return

    chosen = args.effect.lower()
    if chosen != "random" and chosen not in effects:
        sys.exit(f"purr: unknown effect '{args.effect}'. Available:\n  "
                 + "  ".join(sorted(effects)))

    # Source the text: a named file, or stdin when piped (cat file | purr).
    if args.file:
        try:
            with open(args.file, encoding="utf-8", errors="replace") as f:
                raw = f.readlines()
        except OSError as e:
            sys.exit(f"purr: {e}")
        src = args.file
    elif not sys.stdin.isatty():
        raw = sys.stdin.readlines()
        src = "<stdin>"
    else:
        parser.error("a file is required (or pipe text in, or use --list)")

    if not raw:
        sys.exit(f"purr: {src} is empty")

    # Not a terminal (piped/redirected): behave like plain cat.
    if not sys.stdout.isatty():
        sys.stdout.writelines(raw)
        return

    if os.name == "nt":
        os.system("")  # enable ANSI escape processing on Windows consoles

    size = shutil.get_terminal_size()
    width = size.columns if size.columns > 0 else 80
    page_height = args.page_lines or max(size.lines - 1, 1)
    pages = paginate(wrap_lines(raw, width), page_height)

    with KeyPoller() as keys:
        for i, page in enumerate(pages, 1):
            name = random.choice(list(effects)) if chosen == "random" else chosen
            clear_screen()
            try:
                result = run_effect(load_effect_class(effects[name]),
                                    "\n".join(page), args.frame_rate, keys)
            except KeyboardInterrupt:
                print("\x1b[0m")
                return
            if result == "quit":
                print("\x1b[0m")
                return
            last = i == len(pages)
            status = (f"\x1b[2m-- {name} · page {i}/{len(pages)} · "
                      + ("end --" if last else "any key: next · q: quit --")
                      + "\x1b[0m")
            print(status, end="", flush=True)
            if last:
                print()
                break
            if keys.wait() in QUIT_KEYS:
                print()
                break


if __name__ == "__main__":
    main()
