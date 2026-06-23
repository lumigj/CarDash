# CarDash

CarDash is a custom Raspberry Pi car dashboard. It reads live OBD-II data from an ELM327 adapter, renders a PyQt dashboard, and switches to a backup camera when a reverse-gear circuit drives a Raspberry Pi GPIO input.

## Project Layout

- `scripts/obd_interface.py`: main dashboard app.
- `scripts/obd_logger.py`: standalone OBD-II CSV logger.
- `scripts/reverse_gpio.py`: reverse-gear GPIO monitor.
- `scripts/start_dashboard.sh`: Raspberry Pi startup wrapper that launches the dashboard.
- `dashboard/dashboard.py`: speed and RPM dashboard rendering.
- `dashboard/camera_view.py`: Picamera2 backup-camera view and mock camera view.
- `requirements-rpi.txt`: Python packages installed with pip on the Raspberry Pi.

## Raspberry Pi Setup

Find the Raspberry Pi IP from a computer on the same Wi-Fi or LAN. First try
the Raspberry Pi hostname:

```bash
ssh raspberrypi.local
```

If that does not resolve, find the current subnet:

```bash
iface=$(ip route show default | awk '{print $5; exit}')
subnet=$(ip -o -4 addr show dev "$iface" | awk '{print $4; exit}')
echo "$subnet"
```

Then list active devices on that subnet:

```bash
nmap -sn "$subnet"
```

If SSH is already enabled, this shorter scan prints only devices with SSH open:

```bash
nmap -p 22 --open "$subnet" | awk '/Nmap scan report/{print $NF}'
```

Look for a host named `raspberrypi`, a Raspberry Pi Foundation MAC address, or
a newly appeared IP after powering the Raspberry Pi on. Use that IP to connect:

```bash
ssh pi@192.168.1.42
```

Replace `pi` with the actual Raspberry Pi username. If no scan shows the
Raspberry Pi, confirm it is powered on and connected to the same network. You
can also check the router DHCP client list, or run `hostname -I` on the
Raspberry Pi itself. If the IP appears in `nmap -sn` but not in the SSH scan,
enable SSH on the Raspberry Pi with `sudo raspi-config`.

Install the project on the Raspberry Pi:

```bash
git clone https://github.com/lumigj/CarDash.git
cd CarDash
sudo apt install python3-pyqt5
python3 -m venv .venv --system-site-packages
source .venv/bin/activate
pip install -r requirements-rpi.txt
```

Enable desktop autologin:

```bash
sudo raspi-config
```

Choose:

```text
System Options -> Boot / Auto Login -> Desktop Autologin
```

Create an autostart entry:

```bash
mkdir -p ~/.config/autostart
nano ~/.config/autostart/car-dashboard.desktop
```

Use this desktop entry, adjusting paths if the repo lives somewhere else:

```ini
[Desktop Entry]
Type=Application
Name=Car Dashboard
Exec=/bin/bash -lc "/home/lumi/CarDash/scripts/start_dashboard.sh >> /home/lumi/car-dashboard.log 2>&1"
WorkingDirectory=/home/lumi/CarDash
Terminal=false
X-GNOME-Autostart-enabled=true
```

The startup wrapper launches the local checkout without updating it. To update
the Raspberry Pi, pull or reset the repo manually before rebooting.

## Clash Verge Rev TUN Notes

Clash Verge Rev is not part of the dashboard startup path. `scripts/start_dashboard.sh` only starts the dashboard app. Install and troubleshoot Clash Verge Rev as a separate Raspberry Pi desktop application.

On a Raspberry Pi OS `arm64` system, download only the ARM64 Debian package:

```bash
cd /tmp
wget -O Clash.Verge_2.5.1_arm64.deb https://github.com/clash-verge-rev/clash-verge-rev/releases/download/v2.5.1/Clash.Verge_2.5.1_arm64.deb
sudo dpkg -i ./Clash.Verge_2.5.1_arm64.deb
sudo apt -f install
```

Use `sudo apt -f install` without `-y` if you want to review the dependency plan first. During the observed setup, apt installed missing dependencies and did not upgrade existing packages:

```text
Upgrading: 0
Installing: 7
Removing: 0
```

If `apt install ./Clash.Verge_2.5.1_arm64.deb` reports `Unsupported file`, use `dpkg -i` as shown above. If `wget` saves `index.html`, the URL was incomplete. The release directory must include the leading `v` in `v2.5.1`, and the URL must end with the `.deb` file name.

TUN mode failed during setup with this log:

```text
Start TUN listening error: configure tun interface: operation not permitted
```

This means the Mihomo core did not have permission to create or configure the TUN interface. First confirm the kernel TUN device exists:

```bash
ls -l /dev/net/tun
```

Expected output includes:

```text
crw-rw-rw- 1 root root 10, 200 ... /dev/net/tun
```

If `/dev/net/tun` is missing:

```bash
sudo modprobe tun
sudo mkdir -p /dev/net
sudo mknod /dev/net/tun c 10 200
sudo chmod 666 /dev/net/tun
echo tun | sudo tee /etc/modules-load.d/tun.conf
```

In Clash Verge Rev, use these TUN settings:

```text
Tun Stack: GVisor
Device Name: Mihomo
Auto Route: on
Auto Redirect: off
Strict Route: off
Auto Detect Interface: on
DNS Hijack: any:53
MTU: 1500
```

Save the settings, turn TUN mode off and on again, then inspect the logs. A working TUN startup looks like:

```text
[TUN] Tun adapter listening at: Mihomo(...), mtu: 1500, auto route: true, auto redirect: false, ip stack: gVisor
```

If the log still says `operation not permitted`, authorize the Mihomo core. In newer Linux builds this may be under `Settings -> Clash Core` or a gear menu near the core setting. If the UI does not expose an authorize action, find the core and grant Linux capabilities manually:

```bash
find ~/.local/share ~/.config -type f \( -name 'verge-mihomo' -o -name 'mihomo' -o -name 'verge-mihomo-alpha' \) 2>/dev/null
sudo setcap cap_net_admin,cap_net_bind_service=+ep /path/to/verge-mihomo
getcap /path/to/verge-mihomo
pkill clash-verge
clash-verge
```

After TUN starts, verify traffic in `Connections` inside Clash Verge Rev or with:

```bash
curl -I https://www.google.com
```

Rollback steps:

```bash
sudo setcap -r /path/to/verge-mihomo
rm -f /tmp/Clash.Verge_2.5.1_arm64.deb /tmp/index.html
sudo apt remove clash-verge
sudo apt autoremove
```

If TUN was manually created and should not auto-load on boot anymore:

```bash
sudo rm -f /etc/modules-load.d/tun.conf
```

## Dashboard App

Run the live dashboard:

```bash
python scripts/obd_interface.py
```

If no OBD port is provided, the app tries these ports:

- `/dev/ttyUSB0`
- `/dev/ttyUSB1`

If neither port connects, the UI stays open, shows a retry countdown, and retries every 10 seconds. To use one fixed port:

```bash
python scripts/obd_interface.py --port /dev/ttyUSB0
```

The dashboard currently focuses on standard live OBD-II mode `01` values including speed, RPM, timing advance, throttle position, engine load, coolant temperature, intake pressure, intake temperature, fuel trim, and status when supported by the car.

## Mock Mode

Run the UI without OBD, camera, or GPIO hardware:

```bash
python scripts/obd_interface.py --mock
```

While the mocked UI is running, type one of these in the same terminal:

- `R` then Enter: reverse camera mode
- `N` then Enter: normal dashboard mode

Start directly in mocked reverse-camera mode:

```bash
python scripts/obd_interface.py --mock R
```

## Backup Camera

The dashboard watches Raspberry Pi BCM GPIO `17` for the reverse signal.

- `GPIO HIGH`: normal dashboard
- `GPIO LOW`: backup camera view

This is an active-low input. The camera view uses Picamera2 in live mode. Reverse detection is separate from OBD polling so the camera can switch quickly even if OBD queries are slow.
If Picamera2 cannot initialize a camera, the dashboard continues running and
the reverse-camera page shows a camera-unavailable message instead of exiting.

## Reverse Trigger Circuit

The reverse signal can come from either of these 12V sources:

- Backup light positive wire: 12V when reverse gear is selected.
- Backup camera reverse trigger wire: 12V when reverse gear is selected.

Do not connect a car 12V wire directly to a Raspberry Pi GPIO pin. Raspberry Pi GPIO is 3.3V only.

Use an optocoupler input circuit to isolate the car side from the Raspberry Pi side.

Recommended parts:

- PC817 or EL817 optocoupler
- 2.7k ohm or 3.3k ohm resistor for the 12V input side
- 10k ohm resistor for GPIO pull-up, optional if using the Raspberry Pi internal pull-up
- 1N4148 or 1N4007 diode for reverse-polarity protection, recommended
- Small inline fuse, 0.5A or 1A, recommended
- Wires, heat shrink, small perfboard or screw terminal module

You can also use a ready-made 12V optocoupler input module. If using a module, make sure the output side is powered by 3.3V, not 5V.

Car side:

```text
Reverse 12V signal
        |
      Fuse
        |
      2.7k / 3.3k resistor
        |
   PC817 LED anode
   PC817 LED cathode
        |
     Car ground
```

Optional reverse protection diode across the optocoupler LED:

```text
PC817 LED anode  ----|<|----  PC817 LED cathode
```

Raspberry Pi side:

```text
Raspberry Pi 3.3V
        |
      10k pull-up
        |
GPIO input pin -------- PC817 transistor collector
                        PC817 transistor emitter
                                |
                         Raspberry Pi GND
```

With this circuit:

- Not in reverse: GPIO reads HIGH
- In reverse: GPIO reads LOW

Example using BCM GPIO 17:

```python
import RPi.GPIO as GPIO

REVERSE_PIN = 17

GPIO.setmode(GPIO.BCM)
GPIO.setup(REVERSE_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

is_reverse = GPIO.input(REVERSE_PIN) == GPIO.LOW
```

Hardware notes:

- Car electrical systems are noisy. Avoid a simple resistor divider unless you also add protection.
- The optocoupler approach is preferred because it isolates the Raspberry Pi from voltage spikes and ground noise.
- If using a ready-made optocoupler module, confirm the output voltage with a multimeter before connecting to GPIO.
- Raspberry Pi GPIO pins are not 5V tolerant.
- Test the circuit with a multimeter before connecting it to the Raspberry Pi.

## OBD Logger

Run the standalone logger:

```bash
python scripts/obd_logger.py --port /dev/ttyUSB0
```

Default output:

- `logs/obd_log.csv`

Logging is controlled at the top of `scripts/obd_logger.py`:

```python
logging = True
```

- `True`: append CSV rows to `logs/obd_log.csv`
- `False`: print values in the terminal

Change the output file here:

```python
log_path = REPO_ROOT / "logs/obd_log.csv"
```

Set the sleep interval between polling loops:

```bash
python scripts/obd_logger.py --port /dev/ttyUSB0 --interval 1
```

The actual CSV row gap is roughly:

```text
time to query all supported OBD commands + interval sleep
```

On the sample `data.csv`, `--interval 1` produced about `3-4s` gaps because the car reported 18 supported commands and ELM327 queries them one by one.

The logger records all supported standard live OBD-II mode `01` commands reported by the car. This is not all possible car data. Manufacturer-specific CAN data needs custom PIDs or a different raw CAN approach.

## Service Workflow Note

Older workflow notes referenced a `svc.sh` helper:

```bash
sudo ./svc.sh install
sudo ./svc.sh start
sudo ./svc.sh status
```

That helper is not currently present in this repo. The supported startup path documented here is the Raspberry Pi desktop autostart file.

For an external Raspberry Pi GitHub Actions self-hosted runner installed as a systemd service, make the runner wait for networking and restart if Wi-Fi or DNS is still not ready.

Find the generated runner service name:

```bash
systemctl list-unit-files 'actions.runner*.service'
```

Edit the service override, replacing the placeholder with the real service name:

```bash
sudo systemctl edit actions.runner.<owner-repo>.<runner-name>.service
```

Add:

```ini
[Unit]
Wants=network-online.target
After=network-online.target

[Service]
Restart=always
RestartSec=30s
```

Reload systemd and restart the runner:

```bash
sudo systemctl daemon-reload
sudo systemctl restart actions.runner.<owner-repo>.<runner-name>.service
```

Enable the network wait service. On newer Raspberry Pi OS using NetworkManager:

```bash
sudo systemctl enable NetworkManager-wait-online.service
```

If the Pi uses `systemd-networkd` instead:

```bash
sudo systemctl enable systemd-networkd-wait-online.service
```

After reboot, inspect the service logs:

```bash
journalctl -u actions.runner.<owner-repo>.<runner-name>.service -b
```
