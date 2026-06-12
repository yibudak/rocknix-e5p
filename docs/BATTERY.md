# Battery and Power

The E5 Plus uses the RK817 PMIC charger / fuel gauge path exposed by the
mainline `rk817_charger` driver. The battery is modeled through a
`simple-battery` node referenced by the RK817 charger node with
`monitored-battery`.

## Current Kernel Model

The current DTS uses calibration data converted from the stock Android device
tree:

| Field | Stock value | Mainline property |
|---|---:|---|
| Design capacity | 4605 mAh | `charge-full-design-microamp-hours = <4605000>` |
| Design qmax | 5500 mAh | Reference only; not represented by `simple-battery` |
| Battery resistance | 67 mOhm | `factory-internal-resistance-micro-ohms = <67000>` |
| Charge current max | 2000 mA | `constant-charge-current-max-microamp = <2000000>` |
| Charge voltage max | 4300 mV | `constant-charge-voltage-max-microvolt = <4300000>` |
| Charge finish current | 300 mA | `charge-term-current-microamp = <300000>` |
| Power-off threshold | 3350 mV | Reference only; vendor RK817 behavior |
| OCV zero point | 3500 mV | `voltage-min-design-microvolt = <3500000>` |

Some retail listings describe the device battery as 5000 mAh or 6000 mAh.
Those values are not used in the kernel because the stock firmware calibration
is more specific to the actual board. The stock values suggest a 4605 mAh
design capacity with a 5500 mAh qmax calibration reference.

## Stock OCV Table

The stock vendor tree stores the OCV points from 0% to 100%:

```text
3500, 3529, 3562, 3592, 3615, 3632, 3650, 3672, 3701, 3741,
3793, 3840, 3872, 3894, 3933, 3980, 4014, 4027, 4059, 4111, 4187 mV
```

The mainline `simple-battery` binding expects descending
`<microvolt capacity-percent>` pairs, so the DTS contains the same table in
reverse order.

## Runtime Checks

On a booted ROCKNIX system:

```sh
cat /sys/class/power_supply/battery/charge_full_design
cat /sys/class/power_supply/battery/charge_full
cat /sys/class/power_supply/battery/capacity
cat /sys/class/power_supply/battery/status
cat /sys/class/power_supply/battery/voltage_avg
cat /sys/class/power_supply/charger/online
cat /sys/class/power_supply/charger/type
```

Expected `charge_full_design` after this DTS update is `4605000`.

If long charge/discharge testing proves that the actual pack capacity is closer
to 5000 mAh or 6000 mAh, update the design capacity together with the OCV
calibration rather than changing the capacity number alone.
