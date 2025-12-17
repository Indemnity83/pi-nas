# Alarm System

Audible alerts using piezo buzzer for critical system conditions.

## Hardware

- **Buzzer**: Active-low piezo buzzer module on GPIO 17
- **PWM Frequency**: 2000 Hz (configurable)
- **Trigger**: PWM pulses create audible tone

## Beep Patterns

| Pattern | Sound | Meaning |
|---------|-------|---------|
| **Short** | Single 100ms beep | Warning (temp 50-59°C, resync started) |
| **Long** | Single 500ms beep | Critical (bad sectors detected) |
| **Double** | Two short beeps | Attention (RAID degraded, power issue) |
| **Triple** | Three short beeps | Urgent (temp ≥60°C) |

## Monitored Conditions

### RAID Status
- **RAID Degraded** → Double beep (5min cooldown)
- **RAID Resync** → Short beep once when starting
- **RAID Healthy** → No alert

### Disk Temperature
Per-disk monitoring with configurable thresholds:
- **≥60°C** → Triple beep (critical, 5min cooldown)
- **50-59°C** → Short beep (warning, 5min cooldown)
- **<50°C** → No alert

### SMART Health
Per-disk monitoring of critical attributes:
- **Reallocated sectors > 0** → Long beep
- **Pending sectors > 0** → Long beep
- **Uncorrectable sectors > 0** → Long beep
- **All zero** → No alert

### Power Status
- **Under-voltage or throttled** → Double beep (5min cooldown)
- **Normal** → No alert

## Cooldown Period

Default: **5 minutes** between repeated alerts for the same condition.

Prevents annoying repeated beeping while issue persists. Each alarm type has independent cooldown tracking.

## Configuration

**In `config.py`:**
```python
BUZZER_PIN = 17  # GPIO pin (BCM mode)
```

**In `alarms.py`:**
```python
AlarmState(cooldown_seconds=300.0)  # 5 minute cooldown
```

**Temperature thresholds:**
```python
# Warning threshold
if temp >= 50.0:
    buzzer.pattern("short")

# Critical threshold
if temp >= 60.0:
    buzzer.pattern("triple")
```

## How It Works

1. `alarms.check(ctx, buzzer)` called every main loop iteration (~200ms)
2. Evaluates all alarm conditions using cached data
3. Tracks last alert time per alarm ID
4. Only beeps if cooldown period has passed
5. Clears alarm state when condition resolves

## Customization

**Add new alarm:**
```python
# In alarms.py check() function
if some_condition:
    if _alarm_state.should_alert("my_alarm_id"):
        buzzer.pattern("double")
else:
    _alarm_state.clear("my_alarm_id")
```

**Add new pattern:**
```python
# In buzzer.py Buzzer.pattern()
patterns = {
    "custom": [(200, 100), (200, 100), (200, 500)],  # 3 beeps with longer pause
}
```

## Testing

**Test buzzer:**
```python
from buzzer import Buzzer
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
buzzer = Buzzer(17)

# Test patterns
buzzer.pattern("short")
buzzer.pattern("long")
buzzer.pattern("double")
buzzer.pattern("triple")

buzzer.cleanup()
GPIO.cleanup()
```

## Disabling Alarms

Comment out the alarm check in `main.py`:
```python
# alarms.check(ctx, buzzer)  # Disabled
```

Or set a very long cooldown to effectively disable:
```python
_alarm_state = AlarmState(cooldown_seconds=86400.0)  # 24 hours
```
