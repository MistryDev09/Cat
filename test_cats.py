"""
Unit tests for cats.py — all external I/O is mocked.

Run with:
    python -m pytest test_cats.py -v
    python -m unittest test_cats -v
"""

import json
import os
import sys
import tempfile
import unittest
from io import StringIO
from unittest.mock import MagicMock, patch, call

# ---------------------------------------------------------------------------
# Make sure cats.py is importable without triggering side effects.
# cats.py is guarded by `if __name__ == "__main__"`, so a plain import is safe.
# ---------------------------------------------------------------------------
import cats


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_subscribers_file(directory, numbers):
    """Write a subscribers.json into *directory* and return its path."""
    path = os.path.join(directory, "subscribers.json")
    with open(path, "w") as f:
        json.dump({"subscribers": numbers}, f)
    return path


# ===========================================================================
# F — get_cat_fact
# ===========================================================================

class TestGetCatFact(unittest.TestCase):

    @patch("cats.requests.get")
    def test_F01_returns_fact_on_success(self, mock_get):
        """F-01: returns the fact string from a successful API response."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"fact": "Cats sleep 16 hours a day."}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = cats.get_cat_fact()

        self.assertEqual(result, "Cats sleep 16 hours a day.")

    @patch("cats.requests.get")
    def test_F02_exits_on_http_error(self, mock_get):
        """F-02: SystemExit raised when the API returns an HTTP error."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("404 Not Found")
        mock_get.return_value = mock_response

        with self.assertRaises(SystemExit):
            cats.get_cat_fact()

    @patch("cats.requests.get", side_effect=ConnectionError("network down"))
    def test_F03_exits_on_network_error(self, _mock_get):
        """F-03: SystemExit raised on network failure."""
        with self.assertRaises(SystemExit):
            cats.get_cat_fact()


# ===========================================================================
# S — load_subscribers
# ===========================================================================

class TestLoadSubscribers(unittest.TestCase):

    def test_S01_returns_empty_list_when_file_absent(self):
        """S-01: returns [] when subscribers.json does not exist."""
        with patch("cats.SUBSCRIBERS_FILE", "/tmp/nonexistent_subscribers.json"):
            result = cats.load_subscribers()
        self.assertEqual(result, [])

    def test_S02_returns_list_from_valid_file(self):
        """S-02: returns the subscriber list from a well-formed file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = make_subscribers_file(tmpdir, ["+1111", "+2222"])
            with patch("cats.SUBSCRIBERS_FILE", path):
                result = cats.load_subscribers()
        self.assertEqual(result, ["+1111", "+2222"])

    def test_S03_returns_empty_list_when_key_missing(self):
        """S-03: returns [] when the file exists but has no 'subscribers' key."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "subscribers.json")
            with open(path, "w") as f:
                json.dump({}, f)
            with patch("cats.SUBSCRIBERS_FILE", path):
                result = cats.load_subscribers()
        self.assertEqual(result, [])


# ===========================================================================
# W — save_subscribers
# ===========================================================================

class TestSaveSubscribers(unittest.TestCase):

    def test_W01_writes_list_correctly(self):
        """W-01: written file contains the correct JSON structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "subscribers.json")
            with patch("cats.SUBSCRIBERS_FILE", path):
                cats.save_subscribers(["+1111", "+2222"])
            with open(path) as f:
                data = json.load(f)
        self.assertEqual(data, {"subscribers": ["+1111", "+2222"]})

    def test_W02_creates_file_when_absent(self):
        """W-02: file is created if it did not previously exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "subscribers.json")
            self.assertFalse(os.path.exists(path))
            with patch("cats.SUBSCRIBERS_FILE", path):
                cats.save_subscribers(["+3333"])
            self.assertTrue(os.path.exists(path))

    def test_W03_overwrites_existing_file(self):
        """W-03: existing file is replaced with the new list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = make_subscribers_file(tmpdir, ["+old"])
            with patch("cats.SUBSCRIBERS_FILE", path):
                cats.save_subscribers(["+new1", "+new2"])
            with open(path) as f:
                data = json.load(f)
        self.assertEqual(data["subscribers"], ["+new1", "+new2"])


# ===========================================================================
# T — send_fact
# ===========================================================================

class TestSendFact(unittest.TestCase):

    @patch("cats.Client")
    def test_T01_sends_sms_with_correct_params(self, mock_client_cls):
        """T-01: Twilio messages.create called with the right body, from_, and to."""
        env = {
            "TWILIO_ACCOUNT_SID": "ACtest",
            "TWILIO_AUTH_TOKEN": "token",
            "TWILIO_FROM_NUMBER": "+10000000000",
        }
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        with patch.dict(os.environ, env):
            cats.send_fact("Cats purr at 25 Hz.", "+19999999999")

        mock_client.messages.create.assert_called_once_with(
            body="Cat Fact of the Day:\nCats purr at 25 Hz.",
            from_="+10000000000",
            to="+19999999999",
        )

    def test_T02_exits_when_credentials_missing(self):
        """T-02: SystemExit when any Twilio env var is absent."""
        # Remove all three variables from the environment
        clean_env = {k: v for k, v in os.environ.items()
                     if k not in ("TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN",
                                  "TWILIO_FROM_NUMBER")}
        with patch.dict(os.environ, clean_env, clear=True):
            with self.assertRaises(SystemExit):
                cats.send_fact("A fact.", "+19999999999")

    @patch("cats.Client")
    def test_T03_logs_error_on_twilio_failure(self, mock_client_cls):
        """T-03: error is logged but no SystemExit when Twilio raises."""
        env = {
            "TWILIO_ACCOUNT_SID": "ACtest",
            "TWILIO_AUTH_TOKEN": "token",
            "TWILIO_FROM_NUMBER": "+10000000000",
        }
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = Exception("Twilio error")
        mock_client_cls.return_value = mock_client

        with patch.dict(os.environ, env):
            with self.assertLogs("root", level="ERROR") as cm:
                cats.send_fact("A fact.", "+19999999999")  # must not raise

        self.assertTrue(any("Failed to send" in line for line in cm.output))


# ===========================================================================
# B — broadcast
# ===========================================================================

class TestBroadcast(unittest.TestCase):

    @patch("cats.send_fact")
    def test_B01_calls_send_fact_for_each_subscriber(self, mock_send):
        """B-01: send_fact called once per subscriber."""
        cats.broadcast("A fact.", ["+1111", "+2222"])
        self.assertEqual(mock_send.call_count, 2)
        mock_send.assert_any_call("A fact.", "+1111")
        mock_send.assert_any_call("A fact.", "+2222")

    @patch("cats.send_fact")
    def test_B02_logs_warning_with_empty_list(self, mock_send):
        """B-02: warning logged and send_fact never called when list is empty."""
        with self.assertLogs("root", level="WARNING") as cm:
            cats.broadcast("A fact.", [])
        mock_send.assert_not_called()
        self.assertTrue(any("No subscribers" in line for line in cm.output))

    @patch("cats.send_fact")
    def test_B03_continues_after_one_failure(self, mock_send):
        """B-03: delivery to remaining subscribers continues after one failure."""
        mock_send.side_effect = [Exception("fail"), None, None]
        # Should not raise even though the first call fails
        cats.broadcast("A fact.", ["+1111", "+2222", "+3333"])
        self.assertEqual(mock_send.call_count, 3)


# ===========================================================================
# A — CLI --add
# ===========================================================================

class TestCLIAdd(unittest.TestCase):

    def test_A01_adds_new_number(self):
        """A-01: new number is appended and file is saved."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = make_subscribers_file(tmpdir, ["+1111"])
            with patch("cats.SUBSCRIBERS_FILE", path):
                with patch("sys.argv", ["cats.py", "--add", "+2222"]):
                    with patch("sys.stdout", new_callable=StringIO) as mock_out:
                        cats.main()
                with open(path) as f:
                    data = json.load(f)
        self.assertIn("+2222", data["subscribers"])
        self.assertIn("Added", mock_out.getvalue())

    def test_A02_rejects_duplicate(self):
        """A-02: duplicate number is not added; file unchanged."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = make_subscribers_file(tmpdir, ["+1111"])
            with patch("cats.SUBSCRIBERS_FILE", path):
                with patch("sys.argv", ["cats.py", "--add", "+1111"]):
                    with patch("sys.stdout", new_callable=StringIO) as mock_out:
                        cats.main()
                with open(path) as f:
                    data = json.load(f)
        self.assertEqual(data["subscribers"].count("+1111"), 1)
        self.assertIn("already subscribed", mock_out.getvalue())


# ===========================================================================
# R — CLI --remove
# ===========================================================================

class TestCLIRemove(unittest.TestCase):

    def test_R01_removes_existing_number(self):
        """R-01: number is removed and file is saved."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = make_subscribers_file(tmpdir, ["+1111", "+2222"])
            with patch("cats.SUBSCRIBERS_FILE", path):
                with patch("sys.argv", ["cats.py", "--remove", "+1111"]):
                    with patch("sys.stdout", new_callable=StringIO) as mock_out:
                        cats.main()
                with open(path) as f:
                    data = json.load(f)
        self.assertNotIn("+1111", data["subscribers"])
        self.assertIn("Removed", mock_out.getvalue())

    def test_R02_handles_missing_number(self):
        """R-02: removing a non-existent number prints message; file unchanged."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = make_subscribers_file(tmpdir, ["+1111"])
            with patch("cats.SUBSCRIBERS_FILE", path):
                with patch("sys.argv", ["cats.py", "--remove", "+9999"]):
                    with patch("sys.stdout", new_callable=StringIO) as mock_out:
                        cats.main()
                with open(path) as f:
                    data = json.load(f)
        self.assertEqual(data["subscribers"], ["+1111"])
        self.assertIn("not subscribed", mock_out.getvalue())


# ===========================================================================
# L — CLI --list
# ===========================================================================

class TestCLIList(unittest.TestCase):

    def test_L01_prints_each_subscriber(self):
        """L-01: each subscriber number is printed on its own line."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = make_subscribers_file(tmpdir, ["+1111", "+2222"])
            with patch("cats.SUBSCRIBERS_FILE", path):
                with patch("sys.argv", ["cats.py", "--list"]):
                    with patch("sys.stdout", new_callable=StringIO) as mock_out:
                        cats.main()
        output = mock_out.getvalue()
        self.assertIn("+1111", output)
        self.assertIn("+2222", output)

    def test_L02_handles_empty_list(self):
        """L-02: 'No subscribers.' printed when list is empty."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = make_subscribers_file(tmpdir, [])
            with patch("cats.SUBSCRIBERS_FILE", path):
                with patch("sys.argv", ["cats.py", "--list"]):
                    with patch("sys.stdout", new_callable=StringIO) as mock_out:
                        cats.main()
        self.assertIn("No subscribers", mock_out.getvalue())


# ===========================================================================
# D — CLI default (send)
# ===========================================================================

class TestCLIDefault(unittest.TestCase):

    @patch("cats.broadcast")
    @patch("cats.get_cat_fact", return_value="Cats have 32 muscles in each ear.")
    def test_D01_fetches_and_broadcasts(self, mock_get_fact, mock_broadcast):
        """D-01: default run calls get_cat_fact and broadcast exactly once."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = make_subscribers_file(tmpdir, ["+1111", "+2222"])
            with patch("cats.SUBSCRIBERS_FILE", path):
                with patch("sys.argv", ["cats.py"]):
                    cats.main()

        mock_get_fact.assert_called_once()
        mock_broadcast.assert_called_once_with(
            "Cats have 32 muscles in each ear.", ["+1111", "+2222"]
        )


# ===========================================================================

if __name__ == "__main__":
    unittest.main(verbosity=2)
