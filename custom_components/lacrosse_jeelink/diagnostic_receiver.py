
"""Optional raw telegram diagnostics for LaCrosse JeeLink.

Based on the receive flow of pylacrosse 0.4.

The receiver preserves the original callback behavior while
providing debug logging of received serial telegrams.

Raw diagnostics are only active when the integration explicitly
uses DiagnosticLaCrosse.
"""

from __future__ import annotations

import logging

import pylacrosse

_LOGGER = logging.getLogger(__name__)


class DiagnosticLaCrosse(pylacrosse.LaCrosse):
    """LaCrosse receiver with optional raw telegram diagnostics."""

    def _refresh(self) -> None:
        """Receive, diagnose and decode JeeLink telegrams."""

        sensor_class = pylacrosse.LaCrosseSensor

        while not self._stopevent.isSet():
            line = self._serial.readline()

            # Preserve compatibility with pylacrosse 0.4,
            # which may return either str or bytes.
            try:
                line = line.encode().decode("utf-8")
            except AttributeError:
                line = line.decode("utf-8")

            # Serial timeouts can return empty lines.
            # They are normal and do not need logging.
            if not line.strip():
                continue

            matched = sensor_class.re_reading.match(line)

            if _LOGGER.isEnabledFor(logging.DEBUG):
                if matched:
                    _LOGGER.debug(
                        "JeeLink raw telegram: %r",
                        line.strip(),
                    )
                else:
                    _LOGGER.debug(
                        "JeeLink unrecognized telegram: %r",
                        line.strip(),
                    )

            # Preserve pylacrosse behavior:
            # unrecognized packets are not parsed.
            if not matched:
                continue

            sensor = sensor_class(line)

            # Preserve the original sensor cache.
            self.sensors[sensor.sensorid] = sensor

            # Preserve the global discovery callback.
            if self._callback:
                self._callback(
                    sensor,
                    self._callback_data,
                )

            # Preserve sensor-specific callbacks.
            if sensor.sensorid in self._registry:
                for callback, user_data in self._registry[
                    sensor.sensorid
                ]:
                    callback(sensor, user_data)
