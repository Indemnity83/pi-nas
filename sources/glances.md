# Glances Source

Fetches data from the Glances monitoring API with TTL-based caching.

## Usage

```python
ctx.glances.get(endpoint, ttl_s=10.0)
```

## Endpoints

### `cpu`
CPU usage statistics.

```python
{
    "total": 15.5,      # Total CPU usage %
    "user": 10.2,       # User space %
    "system": 5.3,      # System/kernel %
    ...
}
```

### `load`
System load averages.

```python
{
    "min1": 0.52,       # 1-minute load average
    "min5": 0.48,       # 5-minute load average
    "min15": 0.43       # 15-minute load average
}
```

### `mem`
Memory usage statistics.

```python
{
    "total": 4147220480,    # Total RAM in bytes
    "used": 2048000000,     # Used RAM in bytes
    "free": 2099220480,     # Free RAM in bytes
    "percent": 49.4         # Used percentage
}
```

### `fs`
Filesystem information (list of mounted filesystems).

```python
[
    {
        "device_name": "/dev/md127",
        "mnt_point": "/mnt/storage",
        "size": 7200000000000,      # Total size in bytes
        "used": 3600000000000,      # Used in bytes
        "free": 3600000000000,      # Free in bytes
        "percent": 50.0             # Used percentage
    },
    ...
]
```

### `network`
Network interface statistics (list of interfaces).

```python
[
    {
        "interface_name": "eth0",
        "bytes_sent_rate_per_sec": 1024000,    # Upload rate (bytes/sec)
        "bytes_recv_rate_per_sec": 512000     # Download rate (bytes/sec)
    },
    ...
]
```

### `raid`
RAID array information from Glances.

```python
{
    "md127": {
        "status": "active",
        "type": "raid1",
        "config": "UU",
        "used": 2,
        "available": 2,
        "components": {
            "sda1": "0",
            "sdb1": "1"
        }
    }
}
```

### `diskio`
Disk I/O statistics (list of disks).

```python
[
    {
        "disk_name": "md127",
        "read_bytes_rate_per_sec": 1024000,    # Read rate (bytes/sec)
        "write_bytes_rate_per_sec": 512000    # Write rate (bytes/sec)
    },
    ...
]
```

### `smart`
**Parsed SMART disk health data.**

```python
{
    "sda": {
        "temperature_c": 35.0,              # Temperature in Celsius
        "power_on_hours": 12847,            # Total runtime hours
        "power_cycles": 156,                # Number of power-ons
        "reallocated_sectors": 0,           # Bad sectors remapped (health!)
        "pending_sectors": 0,               # Sectors waiting to be remapped
        "uncorrectable_sectors": 0,         # Unreadable sectors (critical!)
        "crc_errors": 0                     # Cable/connection errors
    },
    "sdb": { ... }
}
```

### `sensors`
Hardware sensor readings (list of sensors).

```python
[
    {
        "label": "CPU",
        "value": 45.0       # Temperature in Celsius
    },
    ...
]
```

## Notes

- Default TTL is 10 seconds (configurable per call)
- Returns `None` if endpoint fails or doesn't exist
- SMART data is automatically parsed into a usable structure
- All other endpoints return raw Glances API responses
