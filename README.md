# Dark-Map v2 — Ultimate Edition

Dark-Map v2 bundles an enhanced `nmap` wrapper, a Textual TUI, plugin hooks, CVE lookup utilities, and a dynamic welcome experience designed and powered by ICITIFY TECH.
All files are provided separately so you can copy, run, and extend them.

See `config/settings.json` for defaults.

## Quick install (Kali / Debian)
```bash
sudo apt update && sudo apt install -y nmap python3 python3-venv python3-pip
python3 -m venv darkmap-env
source darkmap-env/bin/activate
pip install -r requirements.txt
chmod +x dark-map.py dark-map-tui.py
mkdir -p scans plugins systemd tools config
```

## Run
- CLI: `./dark-map.py --help`
- TUI: `python3 dark-map-tui.py`

Only scan systems you own or have explicit permission to test.
