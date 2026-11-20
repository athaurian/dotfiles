# Battery charge limit

Thresholds apply only where the kernel exposes writable charge attributes. Other
hosts are skipped, as described below. The configuration uses two values and two
attributes.

| Setting            | Value | Requires                         |
| :----------------- | :---- | :------------------------------- |
| Start threshold    | 75%   | `charge_control_start_threshold` |
| Stop threshold     | 80%   | `charge_control_end_threshold`   |
| Attribute location | —     | `/sys/class/power_supply/`       |
| Installed by       | —     | `chezmoi apply`                  |

The threshold is firmware state rather than a configuration file. It disappears
after an unclean shutdown, and the controller emits `change` events while the
system runs. Two installers restore it:

| Mechanism                          | Trigger                   | Action                                      |
| :--------------------------------- | :------------------------ | :------------------------------------------ |
| `systemd` boot service             | Every boot                | Runs `/usr/local/lib/charge-threshold`      |
| [`udev`](../glossary.md#udev) rule | `add` and `change` events | Runs the same script on power-supply events |

## Hardware behavior and skipped hosts

Drivers and firmware do not always support the full configuration. The table
below records the resulting behavior.

| Situation                                  | Result                                                      |
| :----------------------------------------- | :---------------------------------------------------------- |
| The driver rounds a written value          | The kernel uses the nearest supported threshold             |
| Only `charge_control_end_threshold` exists | The battery gets the `80%` stop limit without a start limit |

The service log records the values the kernel reports. The verification block
below shows the inspection command.

The installer evaluates the host before prompting for privilege elevation and
exits early in the following cases:

| Host condition                                                                                             | Skip reason                                                                      |
| :--------------------------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------- |
| A desktop, or a host with no `Battery` supply exposing `charge_control_end_threshold` (such as `optiplex`) | No threshold is available to write                                               |
| A virtual machine or container (`systemd-detect-virt`)                                                     | No physical battery is present to protect                                        |
| `tlp` is installed                                                                                         | TLP writes the same [`sysfs`](../glossary.md#sysfs) attributes on its own events |

## Changing the limit

Edit the start (`75`) and end (`80`) thresholds in
`data/charge-threshold/charge-threshold` inside the `chezmoi` source tree, then
apply:

```bash
chezmoi apply
```

## Verification

The commands below use `BAT0` as the battery name. Substitute the name reported
by the system if it differs.

```bash
cat /sys/class/power_supply/BAT0/charge_control_start_threshold
cat /sys/class/power_supply/BAT0/charge_control_end_threshold
journalctl -b -u charge-threshold.service
```

## Removal

`chezmoi` does not track or purge root-owned files outside `$HOME`. The
installed artifacts must therefore be removed explicitly:

```bash
sudo systemctl disable --now charge-threshold.service
sudo rm /etc/systemd/system/charge-threshold.service
sudo rm /etc/udev/rules.d/99-charge-threshold.rules
sudo rm /usr/local/lib/charge-threshold
sudo udevadm control --reload
```
