import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import technocore_monitor as monitor


VALID_PAYLOAD = {
    "room": "lobby",
    "count": 3,
    "first_seq": 10,
    "last_seq": 12,
    "messages": [
        {
            "seq": 10,
            "ts": "2026-08-25T12:00:00Z",
            "from": "did:key:z6Mkg8C9FoYgGsy27okoRdQ8dxGfo3FF8VL3Xa4Zn1SsRYaE",
            "text": "hello",
        },
        {"seq": 11, "from": "human", "text": "hi"},
        {
            "seq": 12,
            "ts": "2026-08-25T12:00:02Z",
            "from": "did:key:z6MkqNsiJwQmTB8AWqkdviKdh5DvmkVYD38AuK28DRTVmjy3",
            "text": "status",
        },
    ],
}


class MonitorTests(unittest.TestCase):
    def test_analyze_valid_payload(self):
        report = monitor.analyze_room(VALID_PAYLOAD, "lobby")
        self.assertEqual(report["received_messages"], 3)
        self.assertEqual(report["verified_did_messages"], 2)
        self.assertEqual(report["anonymous_or_unverified_messages"], 1)
        self.assertEqual(report["timestamped_messages"], 2)
        self.assertEqual(report["malformed_messages_or_fields"], 0)
        self.assertEqual(report["warnings"], [])

    def test_duplicate_and_malformed_records_are_reported(self):
        payload = {
            **VALID_PAYLOAD,
            "count": 2,
            "last_seq": 11,
            "messages": [
                {"seq": 11, "from": "human", "text": "a"},
                {"seq": 11, "from": "human", "text": ""},
            ],
        }
        report = monitor.analyze_room(payload, "lobby")
        self.assertEqual(report["duplicate_sequences"], [11])
        self.assertGreaterEqual(report["malformed_messages_or_fields"], 1)
        self.assertTrue(any("duplicate" in warning for warning in report["warnings"]))

    def test_room_and_response_validation(self):
        with self.assertRaises(monitor.MonitorError):
            monitor.validate_room("Bad Room")
        with self.assertRaises(monitor.MonitorError):
            monitor.validate_response({**VALID_PAYLOAD, "room": "other"}, "lobby")

    def test_markdown_report_contains_key_metrics(self):
        report = monitor.analyze_room(VALID_PAYLOAD, "lobby")
        markdown = monitor.report_markdown(report)
        self.assertIn("Verified DID messages", markdown)
        self.assertIn("Sequence range", markdown)
        self.assertIn("lobby", markdown)

    def test_fetch_room_against_local_server(self):
        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            payload = monitor.fetch_room(
                "lobby",
                base_url=f"http://127.0.0.1:{server.server_port}",
                limit=3,
            )
            self.assertEqual(payload["last_seq"], 12)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        body = json.dumps(VALID_PAYLOAD).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        return


if __name__ == "__main__":
    unittest.main()
