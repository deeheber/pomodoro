#!/usr/bin/env python3
import argparse
import curses
import math
from pathlib import Path
import pydoc
import subprocess
import sys
import time

DURATIONS = (15, 20, 25, 30, 45, 50, 60, 90)
DEFAULT = 60
ALERT_SCRIPT = '''
on run argv
    activate
    display dialog (item 1 of argv) with title "Pomodoro" buttons {"OK"} default button "OK" with icon note
end run
'''


class Timer:
    def __init__(self, clock=time.time):
        self.clock = clock
        self.minutes = DEFAULT
        self.state = "ready"
        self.deadline = None
        self.saved = self.minutes * 60

    def select(self, step):
        if self.state == "ready":
            self.minutes = DURATIONS[(DURATIONS.index(self.minutes) + step) % len(DURATIONS)]
            self.saved = self.minutes * 60

    def start(self):
        self.saved = self.minutes * 60
        self.deadline = self.clock() + self.saved
        self.state = "running"

    def remaining(self):
        if self.state == "running":
            return max(0, self.deadline - self.clock())
        return self.saved

    def tick(self):
        if self.state == "running" and self.remaining() <= 0:
            self.state = "finished"
            self.saved = 0
            return True
        return False

    def pause_resume(self):
        if self.state == "running":
            self.saved = self.remaining()
            self.state = "paused"
        elif self.state == "paused":
            self.deadline = self.clock() + self.saved
            self.state = "running"

    def reset(self):
        self.state = "ready"
        self.saved = self.minutes * 60
        self.deadline = None


class Alerts:
    def __init__(self):
        self.processes = []
        self.errors = []

    def start(self, minutes):
        self.stop()
        commands = (
            ("Sound", ["/usr/bin/afplay", "/System/Library/Sounds/Glass.aiff"]),
            ("Popup", ["/usr/bin/osascript", "-e", ALERT_SCRIPT,
                       f"Time's up! Your {minutes}-minute session is complete."]),
        )
        for name, command in commands:
            try:
                process = subprocess.Popen(command, stdin=subprocess.DEVNULL,
                                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.processes.append((name, process))
            except OSError:
                self.errors.append(f"{name} could not start.")

    def poll(self):
        active = []
        for name, process in self.processes:
            code = process.poll()
            if code is None:
                active.append((name, process))
            elif code != 0:
                self.errors.append(f"{name} failed (exit {code}).")
        self.processes = active

    def stop(self):
        for _, process in self.processes:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=0.5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
        self.processes = []
        self.errors = []


HELP = [
    "HELP",
    *(f"{key:<23}{description}" for key, description in (
        ("Left/Right or Up/Down", "Select minutes before starting"),
        ("Enter", "Start / start another session"),
        ("Space", "Pause / resume"),
        ("R", "Reset to duration selection"),
        ("Q or Ctrl-C", "Quit"),
        ("? or H", "Open / close this help"),
    )),
    "",
    "The timer keeps running while help is open.",
    "On completion: a sound and a macOS popup.",
    "Full manual: ./pomodoro --manual",
    "",
    "Esc or Enter returns to the timer.",
]


def draw(screen, timer, alerts, show_help):
    screen.erase()
    height, width = screen.getmaxyx()

    def line(row, text, attr=0):
        if 0 <= row < height and width > 1:
            column = min(2, width - 2)
            try:
                screen.addnstr(row, column, text, max(0, width - column - 1), attr)
            except curses.error:
                pass  # A resize can invalidate coordinates between drawing calls.

    if height < 16 or width < 64:
        line(0, "Enlarge window to 64 x 16.")
        seconds = math.ceil(timer.remaining())
        line(1, f"{timer.state.upper()}  {seconds // 60:02d}:{seconds % 60:02d}")
        line(2, "Help: Esc to return  Q: quit" if show_help
             else "Space: pause  R: reset  Q: quit")
        if alerts.errors:
            line(3, " ".join(alerts.errors))
    elif show_help:
        for row, text in enumerate(HELP, start=1):
            line(row, text, curses.A_BOLD if row == 1 else 0)
    else:
        line(2, "POMODORO", curses.A_BOLD)
        choices = "  ".join(f"[{m}]" if m == timer.minutes else str(m) for m in DURATIONS)
        line(4, choices)
        line(5, "minutes")
        seconds = math.ceil(timer.remaining())
        line(7, f"{seconds // 60:02d}:{seconds % 60:02d}", curses.A_BOLD)
        labels = {"ready": "Ready", "running": "Focus", "paused": "Paused", "finished": "Time's up!"}
        line(9, labels[timer.state])
        line(11, "Arrows: select   Enter: start   Space: pause/resume")
        line(12, "R: reset   Q: quit   ?: help")
        if alerts.errors:
            line(14, " ".join(alerts.errors))
    screen.refresh()


def run(screen):
    try:
        curses.use_default_colors()
    except curses.error:
        pass
    try:
        curses.curs_set(0)
    except curses.error:
        pass
    screen.keypad(True)
    screen.timeout(100)
    timer = Timer()
    alerts = Alerts()
    show_help = False
    try:
        while True:
            alerts.poll()
            draw(screen, timer, alerts, show_help)
            key = screen.getch()
            if timer.tick():
                alerts.start(timer.minutes)
                show_help = False
            if key in (ord("q"), ord("Q")):
                break
            if key in (ord("?"), ord("h"), ord("H")):
                show_help = not show_help
            elif show_help:
                if key in (27, 10, 13, curses.KEY_ENTER):
                    show_help = False
            elif key in (curses.KEY_LEFT, curses.KEY_DOWN):
                timer.select(-1)
            elif key in (curses.KEY_RIGHT, curses.KEY_UP):
                timer.select(1)
            elif key in (10, 13, curses.KEY_ENTER) and timer.state in ("ready", "finished"):
                alerts.stop()
                timer.start()
            elif key == ord(" "):
                timer.pause_resume()
            elif key in (ord("r"), ord("R")):
                alerts.stop()
                timer.reset()
    finally:
        alerts.stop()


def main():
    parser = argparse.ArgumentParser(description="Minimal macOS Pomodoro timer. Default: 60 minutes.",
                                     epilog="In the app: arrows select, Enter starts, Space pauses, R resets, Q quits, ? opens help.")
    parser.add_argument("--manual", action="store_true", help="read the full user manual in a terminal pager")
    args = parser.parse_args()
    if args.manual:
        pydoc.pager(Path(__file__).with_name("USER_MANUAL.md").read_text())
        return 0
    if sys.platform != "darwin":
        parser.error("This app requires macOS for its sound and popup alerts.")
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        parser.error("Run ./pomodoro in an interactive terminal.")
    try:
        curses.wrapper(run)
    except KeyboardInterrupt:
        pass
    except curses.error as error:
        print(f"Could not open the terminal interface: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
