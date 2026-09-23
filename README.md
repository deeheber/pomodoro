# Pomodoro

A minimal macOS terminal timer. Python 3 is the only requirement; no packages to install.

```sh
./pomodoro
```

The default is 60 minutes. Use the arrow keys to choose a duration and Enter to start.
When time is up, the app plays a sound and opens a macOS popup.

Press `?` for controls, run `./pomodoro --help` for usage, or
`./pomodoro --manual` for the [user manual](USER_MANUAL.md).

Run tests with `python3 -m unittest discover -s tests -v`.
