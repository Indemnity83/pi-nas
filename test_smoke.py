#!/usr/bin/env python3
"""
Smoke tests for oled-status.

Verifies imports, formatters, and basic functionality without requiring hardware.
Run with: python test_smoke.py
"""

import sys
import time


def test_imports():
    """Test that all modules can be imported without errors."""
    print("Testing imports...")

    # Check for required dependencies first
    missing_deps = []
    try:
        import PIL
    except ImportError:
        missing_deps.append("PIL/Pillow")

    try:
        import requests
    except ImportError:
        missing_deps.append("requests")

    try:
        import RPi.GPIO
    except ImportError:
        missing_deps.append("RPi.GPIO")

    if missing_deps:
        print(f"  ⚠ Missing dependencies (expected on non-Pi): {', '.join(missing_deps)}")
        print(f"  ℹ Run on Raspberry Pi with dependencies installed for full test")
        return None  # Neither pass nor fail, just skip

    try:
        import config
        import context
        import render
        from sources import base, glances, mdadm, system
        from pages import home, network
        from pages import system as page_system
        from pages import storage, raid, temps
        print("  ✓ All imports successful")
        return True
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_formatters():
    """Test formatting functions with known inputs."""
    print("\nTesting formatters...")

    try:
        from formatters import fmt_bytes, fmt_temp, fmt_rate, fmt_time
    except ImportError as e:
        print(f"  ⚠ Skipping (missing dependencies): {e}")
        return None

    tests = [
        # fmt_bytes (note: B and K use no decimals, M+ use 1 decimal)
        (fmt_bytes(0), "0B", "fmt_bytes(0)"),
        (fmt_bytes(1023), "1023B", "fmt_bytes(1023)"),
        (fmt_bytes(1024), "1K", "fmt_bytes(1024)"),
        (fmt_bytes(1048576), "1.0M", "fmt_bytes(1048576)"),
        (fmt_bytes(1073741824), "1.0G", "fmt_bytes(1GB)"),
        (fmt_bytes(None), "N/A", "fmt_bytes(None)"),

        # fmt_temp
        (fmt_temp(45.0), "  45.0C", "fmt_temp(45.0) - normal"),
        (fmt_temp(55.0), "! 55.0C", "fmt_temp(55.0) - warning"),
        (fmt_temp(65.0), "!!65.0C", "fmt_temp(65.0) - hot"),
        (fmt_temp(None), "N/A", "fmt_temp(None)"),

        # fmt_rate
        (fmt_rate(512), "512K/s", "fmt_rate(512)"),
        (fmt_rate(1024), "1.0M/s", "fmt_rate(1024)"),
        (fmt_rate(1048576), "1.0G/s", "fmt_rate(1048576)"),
        (fmt_rate(None), "N/A", "fmt_rate(None)"),

        # fmt_time
        (fmt_time(59), "0m", "fmt_time(59s)"),
        (fmt_time(60), "1m", "fmt_time(60s)"),
        (fmt_time(3661), "1h 1m", "fmt_time(1h 1m)"),
        (fmt_time(90000), "1d 1h", "fmt_time(25h)"),
        (fmt_time(None), "N/A", "fmt_time(None)"),
    ]

    failed = []
    for result, expected, desc in tests:
        if result == expected:
            print(f"  ✓ {desc}")
        else:
            print(f"  ✗ {desc}: expected '{expected}', got '{result}'")
            failed.append(desc)

    if failed:
        print(f"\n  Failed {len(failed)}/{len(tests)} tests")
        return False
    else:
        print(f"  ✓ All {len(tests)} formatter tests passed")
        return True


def test_caching():
    """Test that the caching mechanism works correctly."""
    print("\nTesting caching logic...")
    from sources.base import CachedDataSource

    class TestSource(CachedDataSource):
        def __init__(self):
            super().__init__()
            self.fetch_count = 0

        def _fetch(self, key):
            self.fetch_count += 1
            return f"data_{key}_{self.fetch_count}"

    source = TestSource()

    # Test 1: First fetch should call _fetch
    result1 = source.get("test", ttl_s=1.0)
    if source.fetch_count != 1:
        print(f"  ✗ First fetch failed: fetch_count={source.fetch_count}, expected 1")
        return False
    print("  ✓ First fetch calls _fetch()")

    # Test 2: Second fetch within TTL should use cache
    result2 = source.get("test", ttl_s=1.0)
    if source.fetch_count != 1:
        print(f"  ✗ Cache miss: fetch_count={source.fetch_count}, expected 1")
        return False
    if result1 != result2:
        print(f"  ✗ Cached value mismatch: {result1} != {result2}")
        return False
    print("  ✓ Second fetch uses cache")

    # Test 3: After TTL expires, should fetch again
    time.sleep(1.1)
    result3 = source.get("test", ttl_s=1.0)
    if source.fetch_count != 2:
        print(f"  ✗ TTL expiry failed: fetch_count={source.fetch_count}, expected 2")
        return False
    print("  ✓ TTL expiry triggers new fetch")

    # Test 4: Different keys should be cached separately
    result4 = source.get("other", ttl_s=1.0)
    if source.fetch_count != 3:
        print(f"  ✗ Different key failed: fetch_count={source.fetch_count}, expected 3")
        return False
    print("  ✓ Different keys cached separately")

    # Test 5: Cache invalidation works
    source.invalidate("test")
    result5 = source.get("test", ttl_s=1.0)
    if source.fetch_count != 4:
        print(f"  ✗ Cache invalidation failed: fetch_count={source.fetch_count}, expected 4")
        return False
    print("  ✓ Cache invalidation works")

    print("  ✓ All caching tests passed")
    return True


def test_context():
    """Test that context initializes correctly."""
    print("\nTesting context initialization...")

    try:
        from context import Context
    except ImportError as e:
        print(f"  ⚠ Skipping (missing dependencies): {e}")
        return None

    try:
        ctx = Context()

        # Check that all sources exist
        if not hasattr(ctx, 'glances'):
            print("  ✗ Context missing 'glances' source")
            return False
        if not hasattr(ctx, 'mdadm'):
            print("  ✗ Context missing 'mdadm' source")
            return False
        if not hasattr(ctx, 'system'):
            print("  ✗ Context missing 'system' source")
            return False

        print("  ✓ Context has all required sources")

        # Check that sources have get method
        if not hasattr(ctx.glances, 'get'):
            print("  ✗ glances source missing 'get' method")
            return False

        print("  ✓ Sources have get() method")
        print("  ✓ Context initialization successful")
        return True
    except Exception as e:
        print(f"  ✗ Context initialization failed: {e}")
        return False


def test_config():
    """Test that configuration values are sensible."""
    print("\nTesting configuration...")

    try:
        import config
    except ImportError as e:
        print(f"  ⚠ Skipping (missing dependencies): {e}")
        return None

    checks = [
        (config.SCREEN_W > 0, "SCREEN_W > 0"),
        (config.SCREEN_H > 0, "SCREEN_H > 0"),
        (config.NAV_TIMEOUT > 0, "NAV_TIMEOUT > 0"),
        (config.DISPLAY_INTERVAL > 0, "DISPLAY_INTERVAL > 0"),
        (config.L1 < config.L2 < config.L3, "Line positions ordered correctly"),
    ]

    failed = []
    for check, desc in checks:
        if check:
            print(f"  ✓ {desc}")
        else:
            print(f"  ✗ {desc}")
            failed.append(desc)

    if failed:
        print(f"\n  Failed {len(failed)}/{len(checks)} config checks")
        return False
    else:
        print(f"  ✓ All {len(checks)} config checks passed")
        return True


def test_alarms():
    """Test alarm state management."""
    print("\nTesting alarm state logic...")

    try:
        from alarms import AlarmState
    except ImportError as e:
        print(f"  ⚠ Skipping (missing dependencies): {e}")
        return None

    # Test with very short cooldown for testing
    alarm_state = AlarmState(cooldown_seconds=0.1)

    # Test 1: First alert should trigger
    if not alarm_state.should_alert("test_alarm"):
        print("  ✗ First alert should return True")
        return False
    print("  ✓ First alert triggers")

    # Test 2: Immediate second alert should not trigger (in cooldown)
    if alarm_state.should_alert("test_alarm"):
        print("  ✗ Second alert should be blocked by cooldown")
        return False
    print("  ✓ Cooldown prevents immediate re-alert")

    # Test 3: After cooldown, should trigger again
    time.sleep(0.15)
    if not alarm_state.should_alert("test_alarm"):
        print("  ✗ Alert should trigger after cooldown expires")
        return False
    print("  ✓ Alert triggers after cooldown expires")

    # Test 4: Different alarms have independent cooldowns
    alarm_state.should_alert("alarm1")
    if not alarm_state.should_alert("alarm2"):
        print("  ✗ Different alarms should have independent cooldowns")
        return False
    print("  ✓ Different alarms tracked independently")

    # Test 5: Clear alarm state
    alarm_state.should_alert("alarm3")
    alarm_state.clear("alarm3")
    if not alarm_state.should_alert("alarm3"):
        print("  ✗ Cleared alarm should trigger immediately")
        return False
    print("  ✓ Clear() resets alarm state")

    print("  ✓ All alarm state tests passed")
    return True


def main():
    """Run all smoke tests."""
    print("=" * 60)
    print("OLED Status - Smoke Tests")
    print("=" * 60)

    results = []

    results.append(("Imports", test_imports()))
    results.append(("Formatters", test_formatters()))
    results.append(("Caching", test_caching()))
    results.append(("Alarms", test_alarms()))
    results.append(("Context", test_context()))
    results.append(("Config", test_config()))

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    for name, passed in results:
        if passed is None:
            status = "⚠ SKIP"
        elif passed:
            status = "✓ PASS"
        else:
            status = "✗ FAIL"
        print(f"{status:8} {name}")

    # Count results
    passed_count = sum(1 for r in results if r[1] is True)
    failed_count = sum(1 for r in results if r[1] is False)
    skipped_count = sum(1 for r in results if r[1] is None)

    print("=" * 60)
    if failed_count > 0:
        print(f"✗ {failed_count} test(s) failed, {skipped_count} skipped")
        return 1
    elif skipped_count == len(results):
        print(f"⚠ All tests skipped (run on Raspberry Pi for full test)")
        return 0
    else:
        print(f"✓ All runnable tests passed! ({skipped_count} skipped)")
        return 0


if __name__ == "__main__":
    sys.exit(main())
