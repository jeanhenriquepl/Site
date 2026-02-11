import json
import os
import unittest
from agent.inventory_agent import load_config, save_config, create_default_config, CONFIG_FILE, DEFAULT_CONFIG

class TestAgentConfig(unittest.TestCase):
    def setUp(self):
        # Remove config file if it exists
        if os.path.exists(CONFIG_FILE):
            os.remove(CONFIG_FILE)

    def tearDown(self):
        # Clean up
        if os.path.exists(CONFIG_FILE):
            os.remove(CONFIG_FILE)

    def test_load_default_config(self):
        """Test that default config is created and loaded if file doesn't exist"""
        config = load_config()
        self.assertEqual(config, DEFAULT_CONFIG)
        self.assertTrue(os.path.exists(CONFIG_FILE))

    def test_save_and_load_config(self):
        """Test saving and loading custom config"""
        custom_config = DEFAULT_CONFIG.copy()
        custom_config["api_url"] = "http://test-server.com"
        
        save_config(custom_config)
        loaded_config = load_config()
        self.assertEqual(loaded_config["api_url"], "http://test-server.com")

if __name__ == '__main__':
    unittest.main()
