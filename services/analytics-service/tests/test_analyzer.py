import unittest

from app.analyzer import analyze_telemetry


class TelemetryAnalysisTests(unittest.TestCase):
    def analyze(self, device_type, value):
        return analyze_telemetry({
            "device_id": "test-device",
            "type": device_type,
            "value": value,
            "event_id": "event-1"
        })

    def test_temperature_warning_and_critical_thresholds(self):
        warning = self.analyze("temperature", 41)
        upper_warning = self.analyze("temperature", 60)
        critical = self.analyze("temperature", 61)

        self.assertEqual(warning["severity"], "warning")
        self.assertEqual(upper_warning["severity"], "warning")
        self.assertEqual(critical["severity"], "critical")
        self.assertEqual(critical["event_id"], "event-1")

    def test_low_air_quality_is_critical(self):
        result = self.analyze("air_quality", 20)

        self.assertEqual(result["status"], "anomaly")
        self.assertEqual(result["severity"], "critical")

    def test_normal_temperature_does_not_raise_alert(self):
        result = self.analyze("temperature", 25)

        self.assertEqual(result["status"], "normal")
