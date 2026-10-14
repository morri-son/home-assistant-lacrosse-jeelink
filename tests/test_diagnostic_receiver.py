
"""Regression tests for the diagnostic JeeLink receiver.

The tests exercise the actual DiagnosticLaCrosse._refresh method
without requiring a serial device or Home Assistant.
"""

import importlib.util
import logging
from pathlib import Path
import threading
import unittest
from unittest.mock import patch

import pylacrosse


RECEIVER_PATH = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / "lacrosse_jeelink"
    / "diagnostic_receiver.py"
)

spec = importlib.util.spec_from_file_location(
    "diagnostic_receiver_under_test",
    RECEIVER_PATH,
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

DiagnosticLaCrosse = module.DiagnosticLaCrosse


class FakeSerial:
    """Return one serial telegram, then stop the receiver."""

    def __init__(self, line, stop_event):
        self.line = line
        self.stop_event = stop_event
        self.read_count = 0

    def readline(self):
        self.read_count += 1
        self.stop_event.set()
        return self.line


class TestDiagnosticReceiver(unittest.TestCase):

    def setUp(self):
        self.receiver = DiagnosticLaCrosse.__new__(
            DiagnosticLaCrosse
        )

        self.receiver._stopevent = threading.Event()
        self.receiver.sensors = {}
        self.receiver._registry = {}
        self.receiver._callback = None
        self.receiver._callback_data = None

    def receive(self, line):
        self.receiver._serial = FakeSerial(
            line,
            self.receiver._stopevent,
        )
        self.receiver._refresh()

    def test_known_sensor(self):
        received = []

        self.receiver._callback = (
            lambda sensor, data: received.append(sensor)
        )

        self.receive(b"OK 9 10 1 4 184 53\n")

        self.assertEqual(len(received), 1)
        self.assertEqual(received[0].sensorid, 10)
        self.assertAlmostEqual(
            received[0].temperature,
            20.8,
        )
        self.assertEqual(received[0].humidity, 53)

    def test_unknown_sensor_is_not_filtered(self):
        self.receive(b"OK 9 8 1 4 102 106\n")

        self.assertIn(8, self.receiver.sensors)
        self.assertAlmostEqual(
            self.receiver.sensors[8].temperature,
            12.6,
        )

    def test_new_battery_flag_is_preserved(self):
        self.receive(b"OK 9 60 129 4 184 56\n")

        self.assertTrue(
            self.receiver.sensors[60].new_battery
        )

    def test_low_battery_flag_is_preserved(self):
        self.receive(b"OK 9 60 1 4 184 184\n")

        self.assertTrue(
            self.receiver.sensors[60].low_battery
        )

    def test_registered_sensor_callback(self):
        received = []

        self.receiver._registry[10] = [
            (
                lambda sensor, data: received.append(
                    (sensor.sensorid, data)
                ),
                "test-data",
            )
        ]

        self.receive(b"OK 9 10 1 4 184 53\n")

        self.assertEqual(
            received,
            [(10, "test-data")],
        )

    def test_invalid_packet_is_ignored(self):
        self.receive(b"INVALID TELEGRAM\n")

        self.assertEqual(self.receiver.sensors, {})

    def test_debug_logging(self):
        with self.assertLogs(
            module._LOGGER,
            level=logging.DEBUG,
        ) as logs:
            self.receive(b"OK 9 55 1 6 35 106\n")

        self.assertTrue(
            any(
                "OK 9 55 1 6 35 106" in message
                for message in logs.output
            )
        )

    def test_no_debug_logging_when_disabled(self):
        with patch.object(
            module._LOGGER,
            "isEnabledFor",
            return_value=False,
        ):
            with patch.object(
                module._LOGGER,
                "debug",
            ) as debug:
                self.receive(b"OK 9 10 1 4 184 53\n")

        debug.assert_not_called()

    def test_serial_is_read_once(self):
        self.receive(b"OK 9 10 1 4 184 53\n")

        self.assertEqual(
            self.receiver._serial.read_count,
            1,
        )


if __name__ == "__main__":
    unittest.main()
