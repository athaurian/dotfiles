# Battery charge limit

On laptops whose power-supply driver exposes `charge_control_end_threshold` in
`/sys/class/power_supply/`, `chezmoi apply` configures the battery to start
charging below **75%** and stop at **80%**.

The limit disappears when the controller loses power during an unclean shutdown,
and the battery reports `change` events while the system runs. The installer
sets up both a `systemd` boot service and a `udev` rule (`add` and `change`
events) that run `/usr/local/lib/charge-threshold`.

## Hardware behavior and skipped hosts

- **Rounding and missing start thresholds:** Drivers round a written threshold
  to the nearest supported level, and a controller can expose only
  `charge_control_end_threshold`. A battery without
  `charge_control_start_threshold` receives the `80%` stop limit alone, and the
  service log (`journalctl -b -u charge-threshold.service`) records the values
  the kernel reports.
- **When installation is skipped:** The installer checks the host before
  prompting for privilege elevation and exits early on:
  - Desktops or hosts with no `Battery` supply exposing
    `charge_control_end_threshold` (such as `optiplex`)
  - Virtual machines and containers (`systemd-detect-virt`)
  - Systems with `tlp` installed, since TLP writes the same `sysfs` attributes
    on its own events

## Changing the limit

Edit the start (`75`) and end (`80`) thresholds in
`data/charge-threshold/charge-threshold` inside the `chezmoi` source tree, then
apply:

```bash
chezmoi apply
```

## Verification

```bash
cat /sys/class/power_supply/BAT0/charge_control_start_threshold
cat /sys/class/power_supply/BAT0/charge_control_end_threshold
journalctl -b -u charge-threshold.service
```

## Removal

Because `chezmoi` does not track or purge root-owned files outside `$HOME`,
remove them manually:

```bash
sudo systemctl disable --now charge-threshold.service
sudo rm /etc/systemd/system/charge-threshold.service
sudo rm /etc/udev/rules.d/99-charge-threshold.rules
sudo rm /usr/local/lib/charge-threshold
sudo udevadm control --reload
```
