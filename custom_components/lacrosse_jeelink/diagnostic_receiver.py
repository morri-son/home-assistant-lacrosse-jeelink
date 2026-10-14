
"""Optional raw telegram diagnostics for LaCrosse JeeLink.

Based on the receive flow of pylacrosse 0.4.

The receiver preserves the original callback behavior while
providing debug logging of received serial telegrams.

This module is not activated until explicitly used by the
integration.
"""

from __future__ import annotations

import logging

import pylacrosse

_LOGGER = logging.getLogger(__name__)


class DiagnosticLaCrosse(pylacrosse.LaCrosse):
    """LaCrosse receiver with optional raw telegram diagnostics."""

    def _refresh(self) -> None:
        """Receive and decode JeeLink telegrams."""

        sensor_class = pylacrosse.LaCrosseSensor

        while not self._stopevent.isSet():
            line = self._serial.readline()

            try:
                line = line.encode().decode("utf-8")
            except AttributeError:
                line = line.decode("utf-8")

            if _LOGGER.isEnabledFor(logging.DEBUG):
                _LOGGER.debug(
                    "JeeLink raw telegram: %r",
                    line.strip(),
                )

            if not sensor_class.re_reading.match(line):
                continue

            sensor = sensor_class(line)

            self.sensors[sensor.sensorid] = sensor

            if self._callback:
                self._callback(
                    sensor,
                    self._callback_data,
                )

            if sensor.sensorid in self._registry:
                for callback, user_data in self._registry[
                    sensor.sensorid
                ]:
                    callback(sensor, user_data)
