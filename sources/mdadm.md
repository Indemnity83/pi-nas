# mdadm Source

Fetches RAID status from sysfs and /proc/mdstat with TTL-based caching.

## Usage

```python
ctx.mdadm.get(key, ttl_s=5.0)
```

## Keys

### `name`
The MD device name (e.g., "md127").

```python
"md127"
```

### `status`
Raw RAID status from system files.

```python
{
    "array_state": "clean",         # From /sys/block/md*/md/array_state
                                    # Values: "clean", "active", "degraded", etc.

    "sync_action": "idle",          # From /sys/block/md*/md/sync_action
                                    # Values: "idle", "resync", "recovery", "check", etc.

    # Progress info (only present during resync/recovery/check):
    "progress": 52.2,               # Percent complete (float)
    "finish_min": 396.1,            # Estimated minutes to finish (float)
    "speed_kps": 99181              # Current speed in K/sec (float)
}
```

## Common array_state Values

- `clean` - Array is healthy and idle
- `active` - Array is active (similar to clean)
- `degraded` - Array is missing a disk
- `readonly` - Array is in read-only mode
- `inactive` - Array is not active

## Common sync_action Values

- `idle` - No background operations
- `resync` - Rebuilding after adding a disk
- `recovery` - Recovering from a failed disk
- `check` - Checking array consistency
- `repair` - Repairing array errors
- `frozen` - Background operations paused

## Notes

- Device name is auto-discovered from `/mnt/storage` mount or `/proc/mdstat`
- Returns empty dict `{}` if no RAID array found
- Progress fields only present when `sync_action` is not "idle" or "frozen"
- Raw values allow pages to interpret state as needed
