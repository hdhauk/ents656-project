import unittest
import cfg


class TestParseConfig(unittest.TestCase):
    def test_read_json(self):
        config = cfg.read_json("test_files/golden_config.json")
        self.assertIn("distances_m", config)
        self.assertIn("base_station", config)
        self.assertIn("small_cell", config)
        self.assertIn("user", config)
        self.assertIn("speed_m/s", config["user"])
        self.assertIn("path_loss", config)


if __name__ == '__main__':
    unittest.main()
