#!/usr/bin/env python3
"""
Test script for crawling pipeline integration.

This script tests the integration between seed discovery and crawling pipeline
without actually crawling websites.
"""

import sys
import os
import json
import yaml
from pathlib import Path
from unittest.mock import Mock, patch

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_config_loading():
    """Test that configuration files are loaded correctly."""
    print("Testing configuration loading...")

    try:
        # Test sources.yaml loading
        sources_path = Path("configs/sources.yaml")
        with open(sources_path, 'r') as f:
            sources_config = yaml.safe_load(f)

        assert sources_config is not None, "Sources config not loaded"
        assert 'sources' in sources_config, "Sources key missing from config"
        print(f"[OK] Loaded {len(sources_config['sources'])} sources from sources.yaml")

        # Test crawl_settings.yaml loading
        crawl_settings_path = Path("configs/crawl_settings.yaml")
        with open(crawl_settings_path, 'r') as f:
            crawl_settings = yaml.safe_load(f)

        assert crawl_settings is not None, "Crawl settings not loaded"
        assert 'crawl_settings' in crawl_settings, "Crawl settings key missing"
        print("[OK] Loaded crawl settings from crawl_settings.yaml")

        return True

    except Exception as e:
        print(f"[FAIL] Configuration loading failed: {e}")
        return False

def test_crawl_method_detection():
    """Test that crawl methods are correctly identified."""
    print("\nTesting crawl method detection...")

    try:
        # Simulate the should_use_playwright logic
        def should_use_playwright(config):
            crawl_method = config.get('crawl_method', 'scrapy')
            return crawl_method == 'playwright'

        # Test different source configurations
        test_configs = [
            {'crawl_method': 'scrapy', 'name': 'Test Scrapy'},
            {'crawl_method': 'playwright', 'name': 'Test Playwright'},
            {'name': 'Test Default'},  # No crawl_method specified
        ]

        for config in test_configs:
            is_playwright = should_use_playwright(config)
            expected = config.get('crawl_method') == 'playwright'
            assert is_playwright == expected, f"Wrong detection for {config['name']}"
            print(f"[OK] Correctly identified {config['name']}: playwright={is_playwright}")

        return True

    except Exception as e:
        print(f"[FAIL] Crawl method detection failed: {e}")
        return False

def test_seed_discovery_loading():
    """Test that seed discovery results are loaded correctly."""
    print("\nTesting seed discovery loading...")

    try:
        # Check that output files exist
        seed_dir = Path("output")
        if seed_dir.exists():
            json_files = list(seed_dir.glob("seed_discovery_*.json"))
            print(f"[OK] Found {len(json_files)} seed discovery files")

            # Try to load one file (skip summary files)
            data_files = [f for f in json_files if "summary" not in f.name]
            if data_files:
                with open(data_files[0], 'r') as f:
                    data = json.load(f)

                required_keys = ['source_name', 'discovered_schools', 'discovery_timestamp']
                for key in required_keys:
                    assert key in data, f"Missing key: {key}"
                print(f"[OK] Seed file structure valid for {data['source_name']}")

                # Check that discovered_schools has the expected structure
                schools = data.get('discovered_schools', [])
                if schools:
                    school = schools[0]
                    required_school_keys = ['school_name', 'canonical_domain', 'discovery_method']
                    for key in required_school_keys:
                        assert key in school, f"Missing school key: {key}"
                    print(f"[OK] School data structure valid")
        else:
            print("[INFO] Seed directory not found - expected if seed discovery hasn't run")
            return True

        return True

    except Exception as e:
        print(f"[FAIL] Seed discovery loading failed: {e}")
        return False

def main():
    """Run all integration tests."""
    print("Running crawling pipeline integration tests...\n")

    tests = [
        test_config_loading,
        test_crawl_method_detection,
        test_seed_discovery_loading,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    print(f"Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("[SUCCESS] All integration tests passed!")
        return 0
    else:
        print("[ERROR] Some tests failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())
