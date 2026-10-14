
"""Regression tests for a non-invasive JeeLink diagnostic callback.

These tests use a simulated receiver. They verify the callback
contract without requiring Home Assistant or a physical JeeLink.
"""

import unittest
from dataclasses import dataclass


@dataclass
class FakeSensor:
    """Minimal representation of a decoded LaCrosse sensor."""

    radio_id: int
    temperature: float
    humidity: int
    new_battery: bool = False


class FakeReceiver:
    """Simulate the register_all callback mechanism."""

    def __init__(self):
        self.callbacks = []

    def register_all(self, callback):
        self.callbacks.append(callback)

    def receive(self, sensor):
        for callback in self.callbacks:
            callback(sensor)


class DiagnosticCallback:
    """Observe a sensor and forward it unchanged."""

    def __init__(self, original_callback):
        self.original_callback = original_callback
        self.observed_ids = []

    def __call__(self, sensor):
        self.observed_ids.append(sensor.radio_id)
        self.original_callback(sensor)


class TestDiagnosticCallback(unittest.TestCase):

    def setUp(self):
        self.receiver = FakeReceiver()
        self.received = []

        self.diagnostic = DiagnosticCallback(
            self.received.append
        )

        self.receiver.register_all(self.diagnostic)

    def test_known_sensor_is_forwarded(self):
        sensor = FakeSensor(
            radio_id=10,
            temperature=21.1,
            humidity=53,
        )

        self.receiver.receive(sensor)

        self.assertEqual(self.received, [sensor])
        self.assertEqual(self.diagnostic.observed_ids, [10])

    def test_unknown_sensor_is_forwarded(self):
        sensor = FakeSensor(
            radio_id=8,
            temperature=12.6,
            humidity=106,
        )

        self.receiver.receive(sensor)

        self.assertEqual(self.received, [sensor])
        self.assertEqual(self.diagnostic.observed_ids, [8])

    def test_battery_flag_is_preserved(self):
        sensor = FakeSensor(
            radio_id=60,
            temperature=21.1,
            humidity=56,
            new_battery=True,
        )

        self.receiver.receive(sensor)

        self.assertIs(self.received[0], sensor)
        self.assertTrue(self.received[0].new_battery)

    def test_multiple_sensors_keep_order(self):
        sensors = [
            FakeSensor(10, 21.1, 53),
            FakeSensor(8, 12.6, 106),
            FakeSensor(60, 21.1, 56),
        ]

        for sensor in sensors:
            self.receiver.receive(sensor)

        self.assertEqual(self.received, sensors)
        self.assertEqual(
            self.diagnostic.observed_ids,
            [10, 8, 60],
        )

    def test_sensor_object_is_not_modified(self):
        sensor = FakeSensor(
            radio_id=55,
            temperature=57.1,
            humidity=106,
        )

        original_values = (
            sensor.radio_id,
            sensor.temperature,
            sensor.humidity,
            sensor.new_battery,
        )

        self.receiver.receive(sensor)

        current_values = (
            sensor.radio_id,
            sensor.temperature,
            sensor.humidity,
            sensor.new_battery,
        )

        self.assertEqual(current_values, original_values)
        self.assertIs(self.received[0], sensor)


if __name__ == "__main__":
    unittest.main()
