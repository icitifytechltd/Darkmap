# Darkmap — Dark‑Map v2 (Ultimate Edition)
---
Darkmap v2
---

**Dark‑Map v2** is an enhanced **Nmap** wrapper and automation framework that brings together fast presets, a Textual TUI, dynamic welcome/splash, plugin hooks, CVE lookup utilities, and flexible report export (CSV/HTML). It is designed for penetration testers, network engineers, and security researchers who need a single, extensible tool to orchestrate and parse nmap scans.

> ⚠️ **Important:** Only scan systems you own or have **explicit permission** to test. Misuse of network scanning tools can be illegal.

---

## Contact

* **Support / Questions / Report issues:** `info@icitifytech.com`
* **Project & contributions:** [https://github.com/icitifytechltd/Darkmap](https://github.com/icitifytechltd/Darkmap)

---

## What this tool provides

* Simple, human-friendly CLI wrapper around `nmap` with presets (quick, full, stealth, vuln, ping).
* Parallel scanning support (concurrency) for running many targets quickly.
* Automatic output files per-scan: `.nmap`, `.gnmap`, `.xml` and optional `.csv` / `.html` reports.
* Parsing of nmap XML to present a concise summary of open ports and services.
* Optional `python-nmap` parsing when available for richer data structures.
* Plugin architecture: drop Python plugins into `plugins/` that expose a `run(target, outputs, parsed)` function.
* A Textual TUI (`dark-map-tui.py`) for interactive scanning and simple workflows.
* Packaging support: build a `.deb`, host an APT repo (GitHub Pages), or install via `pipx` / virtualenv.

---

## Quick highlights — new in v2

* Built packaging workflow and `postinst` script practices so the global `darkmap` command works reliably.
* Optional APT hosting recipe (GitHub Pages) with `dists/` & `pool/` layout and GPG-signed `Release` file.
* `--examples` flag: prints ready-made sample commands to run common scans.
* Better defaults and config file `config/settings.json` for output, welcome, and concurrency.

---

## Installation (recommended options)

Choose one method depending on how you want to manage the tool:

### Option A — **pipx** (recommended, isolated & simple)

`pipx` installs apps globally but in isolated venvs:

```bash
sudo apt update
sudo apt install -y pipx
sudo pipx ensurepath
# install directly from GitHub
pipx install git+https://github.com/icitifytechltd/Darkmap.git
# Verify
darkmap -h
```

This is the safest for Kali / Debian because it avoids modifying system Python packages.

---

### Option B — **Local virtualenv** (developer / editable)

```bash
sudo apt update
sudo apt install -y nmap python3 python3-venv python3-pip
cd ~/Downloads
git clone https://github.com/icitifytechltd/Darkmap.git
cd Darkmap
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# Optional editable install to get console script
pip install -e .
# Run
darkmap -h
```

Use this when developing plugins or editing source.

---

### Option C — **Local .deb** (system-wide)

Build a Debian package and install it locally for a system-wide command:

1. Make sure `package-build/` contains the correct layout:

```
package-build/
├── DEBIAN/control
├── DEBIAN/postinst     # executable
└── usr/local/lib/darkmap/   # application files
    └── darkmap.py
```

2. Build and install:

```bash
dpkg-deb --build package-build
mv package-build.deb darkmap_<version>_all.deb
sudo dpkg -i darkmap_<version>_all.deb
sudo apt -f install
```

If postinst fails, remove broken symlinks and re-run (see Troubleshooting).

---

### Option D — **APT repo (global install for many users)**

Host the `.deb` on GitHub Pages or any HTTPS server using the APT layout and optionally sign the `Release` with GPG.

**Minimal structure** to publish on GitHub Pages (gh-pages branch):

```
<repo>/
├─ dists/stable/main/binary-all/Packages.gz
├─ pool/main/<pkgname>/<pkgfile>.deb
└─ dists/stable/Release
```

On client machines add the repository (signed) and install:

```bash
# download maintainer public key first (if signed)
sudo wget -O /usr/share/keyrings/darkmap-archive-keyring.gpg https://<your-gh-pages>/public-key.gpg
echo "deb [signed-by=/usr/share/keyrings/darkmap-archive-keyring.gpg] https://<your-gh-pages>/ stable main" | sudo tee /etc/apt/sources.list.d/darkmap.list
sudo apt update
sudo apt install darkmap
```

For quick testing without signatures use `deb [trusted=yes]` (not recommended for production).

---

## Basic usage & flags

Run `darkmap -h` to display full help. Key flags and what they do:

```
-t, --targets <targets...>        # One or more targets (IP, hostname, CIDR)
-f, --targets-file <file>         # File with one target per line
--preset <quick|full|stealth|vuln|ping>
--nmap-args "..."                 # Raw nmap args
--nse-cats <cats>                 # NSE categories (e.g., vuln)
--nse-scripts "script1,script2"  # Specific NSE scripts
--concurrency <n>                 # Parallel scans
--out-prefix <prefix>             # Output filename prefix
--timeout <seconds>               # Per-scan timeout
--no-parse                        # Skip XML parsing step
--csv-report                      # Write CSV per-target
--html-report                     # Generate consolidated HTML
--use-python-nmap                 # Use python-nmap to parse XML
--examples                        # Show examples
-h, --help                        # Show help
```

---

## Examples (copy/paste)

```bash
# Quick scan
darkmap -t 192.168.1.10 --preset quick --csv-report

# Full all-port scan (slow, requires sudo for raw sockets)
sudo darkmap -t 192.168.1.10 --preset full --html-report

# Stealth SYN scan (requires sudo)
sudo darkmap -t 192.168.1.10 --preset stealth

# Vulnerability category NSE scripts
sudo darkmap -t 192.168.1.10 --nse-cats vuln --csv-report

# Multiple targets from file
darkmap -f targets.txt --preset quick --concurrency 8 --csv-report
```

---

## Output files & where to find them

Default output directory is configurable via `config/settings.json`. Typical outputs per target:

* `*.nmap` — human-readable nmap output
* `*.gnmap` — grepable nmap output
* `*.xml` — nmap XML (used for parsing)
* `*.csv` — CSV report (if `--csv-report`)
* `*.html` — HTML report (if `--html-report`)

Example view commands:

```bash
less scans/darkmap_192.168.1.10_*.nmap
xmllint --format scans/darkmap_192.168.1.10_*.xml | less
column -s, -t < scans/darkmap_192.168.1.10_*.csv | less -#2 -N -S
xdg-open scans/darkmap_*.html
```

---

## Plugins

* Place plugin Python files in `plugins/`.
* Each plugin must implement: `def run(target, outputs, parsed):`.
* Plugins will be loaded automatically when `darkmap` runs. See `plugins/example_plugin.py` for a template.

---

## Configuration

Edit `config/settings.json` to change defaults such as `default_output_dir`, `default_preset`, `welcome` behavior, `concurrency`, and plugin paths.

---

## Packaging & maintainer notes

* Keep the launcher at `/usr/local/bin/darkmap` as a small shim script that runs `python3 /usr/local/lib/darkmap/darkmap.py "$@"`.
* Ensure `postinst` and other maintainer scripts are executable (`chmod 755`) and robust (check for existence of target files, remove stale symlinks).
* Build `.deb` with `dpkg-deb --build package-build` and generate APT metadata with `dpkg-scanpackages` or `apt-ftparchive`.

---

## Troubleshooting

### Common install errors

* **Dangling symlink / postinst chmod errors**: Remove old symlink and reinstall:

```bash
sudo rm -f /usr/local/bin/darkmap
sudo dpkg --remove --force-remove-reinstreq darkmap || true
sudo dpkg -i darkmap_<version>_all.deb
sudo apt -f install
```

```

* **Large pushes to GitHub time out**: increase git buffer: `git config --global http.postBuffer 524288000` or use SSH/Git LFS.

---

## Security & legal

* Always scan only systems you have permission to test. Follow local laws and organizational policies.
* Sign APT `Release` files and publish the public key; do not use `trusted=yes` in production.

---

## License

Add your chosen license file in `LICENSE` (MIT).

---

## Support

If you have questions, request features, or report bugs, email: **[info@icitifytech.com](mailto:info@icitifytech.com)**

---

*End of README*
