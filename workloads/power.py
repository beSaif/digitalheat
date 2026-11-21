"""Whole-system power meter for Apple-silicon Macs, read from the battery gauge.

No sudo needed (unlike `powermetrics`). The battery controller exposes, in
`ioreg -rn AppleSmartBattery` -> PowerTelemetryData:

    AccumulatedSystemLoad       running sum of 1-per-second system-power samples, mW
    SystemLoadAccumulatorCount  number of samples in that sum

The gauge publishes new values roughly every 45-60 s (`UpdateTime`). The average
power between two published snapshots a and b is

    (b.acc - a.acc) / (b.count - a.count)   [mW]

which covers exactly (b.count - a.count) seconds of samples. To measure a load,
take both snapshots at publish events that lie fully inside the load period.

It measures the WHOLE machine (CPU, memory, display, everything else), and only
while running on battery: with the charger connected, the system is powered
from the adapter and these counters do not describe the load.
"""

import re
import subprocess
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class Snapshot:
    wall_time: float      # time.time() when read
    update_time: int      # gauge publish time (UNIX s)
    acc_mw: int           # AccumulatedSystemLoad
    count: int            # SystemLoadAccumulatorCount
    on_battery: bool


def _ioreg():
    return subprocess.run(
        ["ioreg", "-rn", "AppleSmartBattery"], capture_output=True, text=True, check=True
    ).stdout


def _int(text, key):
    m = re.search(r'"%s"\s*=\s*(\d+)' % key, text)
    if not m:
        raise RuntimeError(f"battery gauge field {key!r} not found; is this an Apple-silicon laptop?")
    return int(m.group(1))


def read():
    out = _ioreg()
    return Snapshot(
        wall_time=time.time(),
        update_time=_int(out, "UpdateTime"),
        acc_mw=_int(out, "AccumulatedSystemLoad"),
        count=_int(out, "SystemLoadAccumulatorCount"),
        on_battery='"ExternalConnected" = No' in out,
    )


def wait_for_publish(after=None, timeout_s=240, poll_s=0.5):
    """Block until the gauge publishes a snapshot newer than `after` (or the current one)."""
    ref = (after or read()).update_time
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        s = read()
        if s.update_time != ref and s.count > 0:
            return s
        time.sleep(poll_s)
    raise TimeoutError("battery gauge did not publish a new value in time")


def _signed_delta(a, b):
    """b - a for 64-bit counters, read as a signed number (handles wrap-around)."""
    d = (b - a) % 2**64
    return d - 2**64 if d >= 2**63 else d


def average_w(a, b):
    """Average whole-system power (W) and covered seconds between two snapshots.

    The sign convention differs between machines: on an M1 / macOS 26.3 the
    system-load samples are positive while on battery, on an M4 / macOS 26.6
    they are negative (SystemLoad = -BatteryPower; see docs/workloads.md,
    "Apple M4 battery-gauge diagnostic"). The magnitude is the power drawn in
    both cases, so we use it.
    """
    n = b.count - a.count
    if n <= 0:
        raise ValueError("snapshots cover no samples; take them at two different publish events")
    return abs(_signed_delta(a.acc_mw, b.acc_mw)) / n / 1000.0, n
