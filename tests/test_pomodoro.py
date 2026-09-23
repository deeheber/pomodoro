import subprocess
import unittest
from unittest.mock import Mock, patch

from pomodoro import Alerts, DURATIONS, Timer, draw, run


class TimerTests(unittest.TestCase):
    def setUp(self):
        self.now = 1000
        self.timer = Timer(lambda: self.now)

    def test_default_and_duration_choices(self):
        self.assertEqual(self.timer.minutes, 60)
        seen = set()
        for _ in DURATIONS:
            seen.add(self.timer.minutes)
            self.timer.select(1)
        self.assertEqual(seen, {15, 20, 25, 30, 45, 50, 60, 90})
        self.assertEqual(self.timer.minutes, 60)
        self.timer.select(-1)
        self.assertEqual(self.timer.minutes, 50)

    def test_pause_resume_ignores_time_while_paused(self):
        self.timer.start()
        self.now += 20
        self.timer.pause_resume()
        self.now += 5000
        self.assertEqual(self.timer.remaining(), 3580)
        self.assertFalse(self.timer.tick())
        self.timer.pause_resume()
        self.now += 10
        self.assertEqual(self.timer.remaining(), 3570)

    def test_sleep_expiry_fires_once(self):
        self.timer.start()
        self.now += 4000
        self.assertTrue(self.timer.tick())
        self.assertFalse(self.timer.tick())
        self.assertEqual(self.timer.state, "finished")
        self.assertEqual(self.timer.remaining(), 0)

    def test_boundary_and_restart(self):
        self.timer.start()
        self.now += 3599.5
        self.assertFalse(self.timer.tick())
        self.now += 0.5
        self.assertTrue(self.timer.tick())
        self.timer.start()
        self.assertEqual(self.timer.remaining(), 3600)

    def test_reset_preserves_selection_and_cancels_expiry(self):
        self.timer.select(1)
        self.timer.start()
        self.timer.select(1)
        self.assertEqual(self.timer.minutes, 90)
        self.timer.reset()
        self.now += 10000
        self.assertFalse(self.timer.tick())
        self.assertEqual(self.timer.state, "ready")
        self.assertEqual(self.timer.remaining(), 5400)


class InterfaceTests(unittest.TestCase):
    def test_space_at_expiry_still_alerts(self):
        clock = Mock(return_value=1000)
        timer = Timer(clock)
        timer.start()
        clock.return_value = 4599.95
        screen = Mock()

        def press_space_after_deadline():
            clock.return_value = 4600.05
            screen.getch.side_effect = None
            screen.getch.return_value = ord("q")
            return ord(" ")

        screen.getch.side_effect = press_space_after_deadline
        with patch("pomodoro.Timer", return_value=timer), \
                patch("pomodoro.Alerts") as alerts, \
                patch("pomodoro.draw"), \
                patch("pomodoro.curses.curs_set"), \
                patch("pomodoro.curses.use_default_colors"):
            run(screen)
        self.assertEqual(timer.state, "finished")
        alerts.return_value.start.assert_called_once_with(60)

    def test_small_window_shows_controls_for_current_mode(self):
        screen = Mock()
        screen.getmaxyx.return_value = (10, 50)
        for help_open in (False, True):
            with self.subTest(help_open=help_open):
                screen.reset_mock()
                draw(screen, Timer(), Alerts(), help_open)
                controls = next(call.args[2] for call in screen.addnstr.call_args_list
                                if call.args[0] == 2)
                if help_open:
                    self.assertIn("Help", controls)
                    self.assertIn("Esc", controls)
                    self.assertNotIn("pause", controls)
                else:
                    self.assertIn("Space: pause", controls)


class AlertTests(unittest.TestCase):
    @patch("pomodoro.subprocess.Popen")
    def test_cleanup_stops_pending_popup(self, popen):
        sound, popup = Mock(), Mock()
        sound.poll.return_value = 0
        popup.poll.return_value = None
        popen.side_effect = [sound, popup]
        alerts = Alerts()
        alerts.start(60)
        alerts.poll()
        alerts.stop()
        sound.terminate.assert_not_called()
        popup.terminate.assert_called_once()
        popup.wait.assert_called_once()
        self.assertEqual(alerts.processes, [])

    @patch("pomodoro.subprocess.Popen")
    def test_failures_do_not_block_other_alert(self, popen):
        popup = Mock()
        popup.poll.return_value = 1
        popen.side_effect = [OSError("unavailable"), popup]
        alerts = Alerts()
        alerts.start(60)
        alerts.poll()
        alerts.poll()
        self.assertEqual(alerts.errors, ["Sound could not start.", "Popup failed (exit 1)."])

    def test_unresponsive_process_is_killed(self):
        process = Mock()
        process.poll.return_value = None
        process.wait.side_effect = [subprocess.TimeoutExpired("popup", 0.5), 0]
        alerts = Alerts()
        alerts.processes = [("Popup", process)]
        alerts.stop()
        process.kill.assert_called_once()


if __name__ == "__main__":
    unittest.main()
