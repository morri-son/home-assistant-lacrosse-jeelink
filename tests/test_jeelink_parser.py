
"""Regression tests for the pylacrosse Jeelink packet format.

These tests intentionally reproduce the upstream parser behavior.
No Home Assistant installation or physical Jeelink is required.

Run with:
    python -m unittest discover -s tests -v
"""

from __future__ import annotations

import re
import unittest


# Pattern used by pylacrosse.LaCrosseSensor.
UPSTREAM_PATTERN = re.compile(
    r"OK (\d+) (\d+) (\d+) (\d+) (\d+) (\d+)"
)

# Candidate stricter pattern for future validation.
STRICT_PATTERN = re.compile(
    r"OK (\d+) (\d+) (\d+) (\d+) (\d+) (\d+)"
)


def decode_upstream(line: str) -> dict | None:
    """Reproduce the relevant pylacrosse decoding logic."""
    match = UPSTREAM_PATTERN.match(line)

    if match is None:
        return None

    data = [
        int(value)
        for value in match.group().split()[1:]
    ]

    return {
        "radio_id": data[1],
        "sensor_type": data[2] & 0x7F,
        "new_battery": bool(data[2] & 0x80),
        "temperature": (
            data[3] * 256 + data[4] - 1000
        ) / 10,
        "humidity": data[5] & 0x7F,
        "low_battery": bool(data[5] & 0x80),
    }


def decode_strict(line: str) -> dict | None:
    """Prototype validation before decoding a packet."""
    match = STRICT_PATTERN.fullmatch(line.strip())

    if match is None:
        return None

    values = [int(value) for value in match.groups()]

    # The six fields are expected to represent bytes.
    if any(value < 0 or value > 255 for value in values):
        return None

    return decode_upstream(line.strip())


class TestJeelinkParser(unittest.TestCase):
    """Compare upstream behavior with candidate validation."""

    def test_normal_packet(self):
        packet = "OK 9 10 1 4 184 53"

        result = decode_upstream(packet)

        self.assertIsNotNone(result)
        self.assertEqual(result["radio_id"], 10)
        self.assertEqual(result["temperature"], 20.8)
        self.assertEqual(result["humidity"], 53)

    def test_unknown_id_8(self):
        packet = "OK 9 8 1 4 102 106"

        result = decode_upstream(packet)

        self.assertIsNotNone(result)
        self.assertEqual(result["radio_id"], 8)
        self.assertEqual(result["temperature"], 12.6)
        self.assertEqual(result["humidity"], 106)

    def test_unknown_id_55(self):
        packet = "OK 9 55 1 6 35 106"

        result = decode_upstream(packet)

        self.assertIsNotNone(result)
        self.assertEqual(result["radio_id"], 55)
        self.assertEqual(result["temperature"], 57.1)

    def test_incomplete_packet(self):
        packet = "OK 9 10 1 4 184"

        self.assertIsNone(decode_upstream(packet))
        self.assertIsNone(decode_strict(packet))

    def test_trailing_text(self):
        packet = "OK 9 10 1 4 184 53 INVALID"

        # Upstream accepts a valid prefix.
        self.assertIsNotNone(decode_upstream(packet))

        # Strict validation rejects trailing data.
        self.assertIsNone(decode_strict(packet))

    def test_out_of_range_radio_id(self):
        packet = "OK 9 300 1 4 184 53"

        # Upstream accepts this numeric value.
        self.assertEqual(
            decode_upstream(packet)["radio_id"],
            300,
        )

        # Strict byte validation rejects it.
        self.assertIsNone(decode_strict(packet))

    def test_invalid_temperature_byte(self):
        packet = "OK 9 10 1 999 184 53"

        self.assertIsNotNone(decode_upstream(packet))
        self.assertIsNone(decode_strict(packet))

    def test_battery_flags(self):
        packet = "OK 9 10 129 4 184 181"

        result = decode_upstream(packet)

        self.assertTrue(result["new_battery"])
        self.assertTrue(result["low_battery"])
        self.assertEqual(result["humidity"], 53)

    def test_valid_packet_passes_strict_validation(self):
        packet = "OK 9 10 1 4 184 53"

        self.assertEqual(
            decode_strict(packet),
            decode_upstream(packet),
        )


if __name__ == "__main__":
    unittest.main()
