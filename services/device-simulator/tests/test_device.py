import unittest

from app.device import Device


class DeviceCommandTests(unittest.TestCase):
    def test_street_light_brightness_command(self):
        device = Device("street_light")

        result = device.execute_command("set_lighting", "brightness=35")

        self.assertTrue(result["success"])
        self.assertEqual(result["brightness"], 35)
        self.assertTrue(device.is_on)

    def test_device_maintenance_and_sampling_interval(self):
        device = Device("temperature")

        maintenance = device.execute_command(
            "set_maintenance",
            "enabled=true"
        )
        interval = device.execute_command("set_interval", "seconds=15")

        self.assertEqual(maintenance["status"], "maintenance")
        self.assertEqual(interval["update_interval"], 15)
        self.assertEqual(device.update_interval, 15)

    def test_traffic_light_modes_are_type_checked(self):
        device = Device("traffic_light")

        result = device.execute_command(
            "set_traffic_mode",
            "mode=green"
        )
        invalid = device.execute_command(
            "set_traffic_mode",
            "mode=purple"
        )
        device.type = "temperature"
        rejected = device.execute_command(
            "set_traffic_mode",
            "mode=green"
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["traffic_mode"], "green")
        self.assertFalse(invalid["success"])
        self.assertFalse(rejected["success"])


if __name__ == "__main__":
    unittest.main()
