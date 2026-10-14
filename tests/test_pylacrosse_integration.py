
"""Tests against the real pylacrosse sensor parser."""

import unittest

from pylacrosse import LaCrosseSensor


class TestRealPylacrosseParser(unittest.TestCase):
    """Verify actual pylacrosse parsing behavior."""

    @staticmethod
    def parse(line):
        return LaCrosseSensor(line)

    def test_known_sensor_10(self):
        sensor = self.parse("OK 9 10 1 4 184 53")

        self.assertEqual(sensor.sensorid, 10)
        self.assertAlmostEqual(sensor.temperature, 20.8)
        self.assertEqual(sensor.humidity, 53)
        self.assertFalse(sensor.new_battery)
        self.assertFalse(sensor.low_battery)

    def test_unknown_sensor_8(self):
        sensor = self.parse("OK 9 8 1 4 102 106")

        self.assertEqual(sensor.sensorid, 8)
        self.assertAlmostEqual(sensor.temperature, 12.6)
        self.assertEqual(sensor.humidity, 106)

    def test_unknown_sensor_55(self):
        sensor = self.parse("OK 9 55 1 6 35 106")

        self.assertEqual(sensor.sensorid, 55)
        self.assertAlmostEqual(sensor.temperature, 57.1)
        self.assertEqual(sensor.humidity, 106)

    def test_new_battery_flag(self):
        sensor = self.parse("OK 9 60 129 4 184 56")

        self.assertEqual(sensor.sensorid, 60)
        self.assertTrue(sensor.new_battery)
        self.assertFalse(sensor.low_battery)

    def test_low_battery_flag(self):
        sensor = self.parse("OK 9 60 1 4 184 184")

        self.assertTrue(sensor.low_battery)
        self.assertEqual(sensor.humidity, 56)

    def test_trailing_text_is_accepted(self):
        """Document existing prefix-matching behavior."""
        sensor = self.parse(
            "OK 9 10 1 4 184 53 UNEXPECTED_DATA"
        )

        self.assertEqual(sensor.sensorid, 10)
        self.assertAlmostEqual(sensor.temperature, 20.8)

    def test_out_of_range_radio_id_is_accepted(self):
        """Document absence of radio-ID range validation."""
        sensor = self.parse("OK 9 300 1 4 184 53")

        self.assertEqual(sensor.sensorid, 300)

    def test_incomplete_packet_has_no_sensor_id(self):
        sensor = self.parse("OK 9 10 1 4")

        self.assertFalse(hasattr(sensor, "sensorid"))


if __name__ == "__main__":
    unittest.main()
