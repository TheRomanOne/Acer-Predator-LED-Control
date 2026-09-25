# LED Studio

Custom RGB lighting control for the **Acer Predator Helios 16 AI (PH16-73)** on Windows and
Ubuntu, with a web UI for designing your own patterns.

It replaces Predator Sense's lighting tab. Every lighting zone on this laptop is a standard
**HID LampArray** device (the same protocol Windows Dynamic Lighting uses), so the app talks to
the hardware directly over HID: no kernel module, no WMI, and the same code path on both OSes.

| Zone (firmware name) | Kind | Lamps |
| --- | --- | --- |
| Keyboard (Sunrex `05af:667a`) | per-key keyboard | 103 |
| InfiniteRing (Darfon `0d62:a20a`) | chassis light ring | 33 |
| Pmma Logo (Darfon `0d62:a01a`) | lid logo | 14 |
| Cover Logo (Darfon `0d62:a01a`) | lid strip | 16 |

## Layout

```
backend/    Python 3.13 · FastAPI · hidapi      — device access, pattern engine, REST + WebSocket API
frontend/   Node 24 · React 19 · TypeScript      — pattern editor and live preview (talks to the API only)
```

## Running

One-shot launchers install everything on first run, start both servers and open the browser:

- Windows: double-click `run_app.cmd` (or run `run_app.ps1` from PowerShell)
- Ubuntu: `./run_app.sh`

Ctrl+C in that window stops both servers. To run the pieces by hand instead:

Start the backend (it opens the LampArray devices and serves on `127.0.0.1:8765`):

```bash
cd backend
python -m venv .venv
.venv/Scripts/pip install -e ".[dev]"      # Linux: .venv/bin/pip
.venv/Scripts/python -m led_studio.main     # Linux: .venv/bin/python
```

Start the frontend dev server (proxies `/api` to the backend) and open http://localhost:5173:

```bash
cd frontend
npm install
npm run dev
```

Command-line helpers, useful for checking which physical LEDs belong to which zone:

```bash
python -m led_studio.cli list        # enumerate zones
python -m led_studio.cli identify    # light each zone in a different colour
python -m led_studio.cli release     # hand control back to the firmware
```

Configuration is read from `LED_STUDIO_*` environment variables (`DATA_DIR`, `HOST`, `PORT`,
`FPS`). The API has no authentication, so it only binds to loopback addresses and rejects
requests whose `Host`/`Origin` is not this machine (blocks cross-site requests from web pages). Saved patterns live in `%LOCALAPPDATA%\led-studio` on Windows and
`~/.local/share/led-studio` on Linux, and the last applied pattern is restored on startup.

### Ubuntu notes

hidapi talks to `/dev/hidraw*`, which is root-only by default. Grant your user access with a udev
rule:

```bash
sudo tee /etc/udev/rules.d/70-led-studio.rules <<'EOF'
KERNEL=="hidraw*", ATTRS{idVendor}=="05af", ATTRS{idProduct}=="667a", TAG+="uaccess"
KERNEL=="hidraw*", ATTRS{idVendor}=="0d62", TAG+="uaccess"
EOF
sudo udevadm control --reload-rules && sudo udevadm trigger
```

The Windows `Predator Sense` / Dynamic Lighting services are not needed; on Windows the app
coexists with them because it takes the LampArrays out of autonomous mode while a pattern plays
and gives them back on **Stop**.

## How patterns work

A pattern is a stack of **layers**. Each layer runs one effect over the zones it targets and is
alpha-blended over the layers below it:

- `solid`, `gradient`, `wave`, `rainbow`, `breathing`, `ripple`, `keyframes` — parametric effects
  computed from each lamp's real position, so a wave flows continuously from the light ring
  across the keyboard.
- `paint` — explicit per-lamp colours; click keys in the editor to paint them.

The preview panel shows one zone at a time: pick it from the zone tabs, which also show each
zone's live colours, frame counter and error state. A paint layer follows the zone it was
painted on, and painting a different zone moves the layer there.

The backend renders frames at 30 fps, sends only the lamps that changed, and streams the same
frames to the browser for the live preview.

## Development

```bash
cd backend && .venv/Scripts/python -m pytest && .venv/Scripts/python -m ruff check . && .venv/Scripts/python -m mypy
cd frontend && npm test && npm run typecheck && npm run lint
```

Hardware access is isolated in `backend/led_studio/hid/transport.py`; everything above it is
tested against an in-memory LampArray emulator (`backend/tests/fakes.py`).
