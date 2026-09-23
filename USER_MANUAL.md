# Pomodoro user manual

## Start on your Mac

You need macOS, Python 3, and a terminal such as Terminal or Ghostty.
No Python packages are required.

Once this project is in a Git repository, clone it using your repository URL:

```sh
git clone <your-repository-url> pomodoro
cd pomodoro
./pomodoro
```

Replace `<your-repository-url>` with the actual URL. If you already have the
folder, open a terminal there and run `./pomodoro`.

## Set a timer

Choose 15, 20, 25, 30, 45, 50, 60, or 90 minutes using the arrow keys.
The selected duration appears in brackets. Each launch starts with 60 selected.
Press Enter to start the countdown.

| Key | Action |
| --- | --- |
| Left / Down | Select the previous duration before starting |
| Right / Up | Select the next duration before starting |
| Enter | Start, or start another session after completion |
| Space | Pause or resume |
| R | Stop the timer and return to duration selection |
| Q or Ctrl-C | Quit |
| ? or H | Open or close help |
| Esc or Enter in help | Return to the timer |

Help does not pause the timer. While help is open, return to the timer before
using pause or reset. Q and Ctrl-C still quit. Completion closes help so you can
see the finished state.

The selected duration stays selected until you change it or close the app.
There are no automatic breaks or saved session history.

## When time is up

The app plays the macOS Glass sound once and opens a "Time's up" popup.
Click OK to dismiss it. Starting another timer, resetting, or quitting also
stops outstanding alerts.

The popup requests focus. Visibility on another desktop or over a full-screen
app depends on macOS behavior; it is not guaranteed. Cross-desktop and full-screen
behavior has not been verified. This is a dialog, not a Notification Center banner.

Sound uses your current output device and system volume. Muting your Mac also
mutes the alert. Keep the terminal process running for alerts to work.

Sleep counts toward the countdown. If time runs out while the Mac is asleep,
the alert runs after it wakes. The app does not wake the Mac or prevent sleep.
Changing the system clock can shorten or extend a running timer. A paused timer
keeps its remaining time until resumed.

## Read help in the terminal

```sh
./pomodoro --help
./pomodoro --manual
```

The manual opens in a terminal pager when available. Use Space to scroll and Q
to exit the usual macOS pager. You can also open USER_MANUAL.md in a text editor.

## Troubleshooting

| Problem | What to do |
| --- | --- |
| Python 3 is missing | Run `python3 --version`. Install Python 3 through your work-approved process if needed. |
| Permission denied when launching | Run `chmod +x pomodoro`, or launch with `python3 pomodoro.py`. |
| Command not found | From the project folder, include the `./` in `./pomodoro`. |
| Terminal is too small | Resize to at least 64 columns by 16 rows. The countdown keeps running during resizing. |
| No sound | Check mute, volume, and your selected audio output, including headphones. |
| No popup | Check other desktops and return to the terminal. Look for a popup error below the controls. Work-device policies may restrict scripts. |
| App says an interactive terminal is required | Run it directly in Terminal or another terminal app, without piping output. |
| Terminal display looks wrong after a forced kill | Run `reset` in that terminal. Normal exit restores terminal settings. |

## Run the tests

From the project folder:

```sh
python3 -m unittest discover -s tests -v
```

Tests use a simulated clock and mocked alerts, so they do not wait for a timer
or play sounds. Actual sound and popup visibility need a check on your Mac.
