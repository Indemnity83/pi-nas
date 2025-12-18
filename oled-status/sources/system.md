# System Source

Fetches system information from various sources with TTL-based caching.

## Usage

```python
ctx.system.get(key, ttl_s=10.0)
```

## Keys

### `ip`
Primary IPv4 address of the system.

```python
"192.168.1.100"
```

Returns `"unknown"` if unable to determine IP.

### `uptime`
System uptime in seconds.

```python
12847.52  # ~3.5 hours
```

Returns `None` if unable to read uptime.

### `power_throttled`
Raspberry Pi power/throttle status flags (parsed from `vcgencmd get_throttled`).

```python
{
    # Current state
    "under_voltage": False,         # Currently experiencing under-voltage
    "freq_capped": False,           # ARM frequency currently capped
    "throttled": False,             # Currently throttled
    "soft_temp_limit": False,       # Soft temperature limit active

    # Historical flags (since boot)
    "under_voltage_occurred": True, # Under-voltage has occurred
    "freq_capped_occurred": False,  # Frequency capping has occurred
    "throttled_occurred": False,    # Throttling has occurred
    "soft_temp_limit_occurred": False,  # Soft temp limit has occurred

    # Raw value
    "raw": "0x50005"               # Raw hex value from vcgencmd
}
```

All flags default to `False` and raw defaults to `"0x0"` if unable to read.

### `cpu_temp`
CPU temperature from `vcgencmd` (Raspberry Pi).

```python
47.8  # Temperature in Celsius
```

Returns `None` if unable to read temperature.

## Notes

- IP address is determined by connecting to 8.8.8.8 (no actual data sent)
- Uptime read from `/proc/uptime`
- Power throttle flags are Raspberry Pi specific (requires `vcgencmd`)
- CPU temp is Raspberry Pi specific (requires `vcgencmd`)
- Suggested TTL: 5-30 seconds depending on update frequency needed
