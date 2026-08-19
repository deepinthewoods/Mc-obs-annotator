import os
import sys
import tempfile
import unittest


PYTHON_SERVER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PYTHON_SERVER not in sys.path:
    sys.path.insert(0, PYTHON_SERVER)

from bulk_scanner import BulkScanner
from edl_parser import EdlParser
from marker_filter import MarkerFilter


def edl_event(number, timecode, text):
    return (
        f"{number:03d}  001 V C {timecode} {timecode} {timecode} {timecode}\n"
        f"{text} |C:ResolveColorBlue |M:{text} |D:1\n\n"
    )


class InstanceMarkerParserTests(unittest.TestCase):
    def parse_edl(self, *events):
        content = "TITLE: Instance Test\nFCM: NON-DROP FRAME\n\n" + "".join(events)
        with tempfile.NamedTemporaryFile("w", suffix=".edl", delete=False) as handle:
            handle.write(content)
            path = handle.name
        try:
            return EdlParser().parse(path)["markers"]
        finally:
            os.unlink(path)

    def test_legacy_marker_remains_compatible(self):
        markers = self.parse_edl(edl_event(1, "01:00:00:00", "Combat - Damage Taken"))

        self.assertEqual(len(markers), 1)
        self.assertEqual(markers[0]["text"], "Combat - Damage Taken")
        self.assertEqual(markers[0]["rawText"], "Combat - Damage Taken")
        self.assertIsNone(markers[0]["instance"])
        self.assertEqual(markers[0]["type"], "Combat")
        self.assertEqual(markers[0]["subtype"], "Damage Taken")

    def test_tagged_markers_expose_instance_without_changing_event_text(self):
        markers = self.parse_edl(
            edl_event(1, "01:00:00:00", "[Instance: Main] Combat - Damage Taken"),
            edl_event(2, "01:00:00:00", "[Instance: Camera] Combat - Damage Taken"),
        )

        self.assertEqual(len(markers), 2)
        self.assertEqual([marker["instance"] for marker in markers], ["Main", "Camera"])
        self.assertTrue(all(marker["text"] == "Combat - Damage Taken" for marker in markers))
        self.assertEqual(markers[1]["rawText"], "[Instance: Camera] Combat - Damage Taken")

    def test_instance_filter_and_search_include_legacy_markers(self):
        markers = self.parse_edl(
            edl_event(1, "01:00:00:00", "Start"),
            edl_event(2, "01:00:01:00", "[Instance: Main] New Section"),
            edl_event(3, "01:00:02:00", "[Instance: Camera] New Section"),
        )

        camera = MarkerFilter.apply_filters(markers, {"instances": ["Camera"]})
        legacy = MarkerFilter.apply_filters(markers, {"instances": ["Untagged"]})
        searched = MarkerFilter.apply_filters(markers, {"search": "main"})

        self.assertEqual([marker["instance"] for marker in camera], ["Camera"])
        self.assertEqual([marker["text"] for marker in legacy], ["Start"])
        self.assertEqual([marker["instance"] for marker in searched], ["Main"])


class InstanceMarkerBulkScannerTests(unittest.TestCase):
    def test_start_end_pairs_do_not_cross_instances(self):
        scanner = BulkScanner()
        starts = [
            {"timestampSeconds": 1.0, "text": "Start", "instance": "Main"},
            {"timestampSeconds": 2.0, "text": "Start", "instance": "Camera"},
        ]
        ends = [
            {"timestampSeconds": 3.0, "text": "End", "instance": "Main"},
            {"timestampSeconds": 4.0, "text": "End", "instance": "Camera"},
        ]

        pairs = scanner.pair_start_end_markers(starts, ends)

        self.assertEqual([(pair.start_time, pair.end_time) for pair in pairs], [
            (1.0, 3.0),
            (2.0, 4.0),
        ])


if __name__ == "__main__":
    unittest.main()
