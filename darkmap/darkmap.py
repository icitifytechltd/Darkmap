#!/usr/bin/env python3
"""
Dark-Map v2 — Advanced Nmap Automation Framework
Author: ICITIFY TECH
Created: 2025
License: Open Source
"""
import argparse
import subprocess
import sys
import os
import datetime
import json
import platform
import getpass
import shutil
import time
import random
import csv
import importlib.util
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import xml.etree.ElementTree as ET

# Optional modules
try:
    from jinja2 import Template
except ImportError:
    Template = None
try:
    import nmap as _pynmap
except ImportError:
    _pynmap = None

# === GLOBAL PATHS & DEFAULTS ===
BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / 'config' / 'settings.json'
OUTPUT_DIR_DEFAULT = BASE_DIR / 'scans'
NMAP_BIN = shutil.which('nmap') or 'nmap'
VERSION = "2.5.0"
AUTHOR = "ICITIFY TECH"

PRESETS = {
    'quick': '-sV -T4 --min-rate 1000',
    'full': '-p- -sV -O -A -T4',
    'stealth': '-sS -sV -A -T3 --reason',
    'vuln': '-sV --script vuln -T4',
    'ping': '-sn -T4'
}

# === CONFIG LOADER ===


def load_config():
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as fh:
                return json.load(fh)
        except Exception:
            return {}
    return {}


CONFIG = load_config()
OUTPUT_DIR = Path(CONFIG.get('default_output_dir', str(OUTPUT_DIR_DEFAULT)))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# === WELCOME BANNER ===
BANNER = [
    r"""  ____             _    __  __                         """,
    r""" |  _ \  __ _  ___| | _|  \/  | __ _ _ __   __ _  ___ """,
    r""" | | | |/ _` |/ __| |/ / |\/| |/ _` | '_ \ / _` |/ _ \ """,
    r""" | |_| | (_| | (__|   <| |  | | (_| | | | | (_| |  __/ """,
    r""" |____/ \__,_|\___|_|\_\_|  |_|\__,_|_| |_|\__, |\___| """,
    r"""                                          |___/         """
]

TIPS = [
    'DESIGNED AND POWERED BY ICITIFY TECH',
    'Tip: Only scan networks you own or have permission to test.',
    'Tip: Use "--preset full" for a full deep scan with OS detection.',
    'Tip: Combine "--nse-scripts" for custom NSE vulnerability scans.',
    'Tip: Try "--csv-report" or "--html-report" for rich output formats.'
]


def banner_animation():
    print('\n' + '=' * 70)
    for r in BANNER:
        print('\033[96m' + r + '\033[0m')
        time.sleep(0.04)
    print('=' * 70 + '\n')
    user = getpass.getuser()
    plat = platform.platform()
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"User: {user} | System: {plat} | Time: {now}")
    print(f"Dark-Map v{VERSION} by {AUTHOR}")
    print(f"\033[93m{random.choice(TIPS)}\033[0m\n")

# === NMAP UTILS ===


def ensure_nmap():
    try:
        subprocess.run([NMAP_BIN, '--version'],
                       capture_output=True, check=True)
    except Exception as e:
        print('[!] nmap missing or not executable:', e)
        sys.exit(1)


def make_output_paths(prefix: str, target: str):
    safe = target.replace('/', '_').replace(':', '_')
    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    base = OUTPUT_DIR / f"{prefix}_{safe}_{ts}"
    return {
        'normal': str(base) + '.nmap',
        'grep': str(base) + '.gnmap',
        'xml': str(base) + '.xml',
        'csv': str(base) + '.csv',
        'html': str(base) + '.html'
    }


def run_nmap_scan(target: str, args_list, out_prefix, timeout=None):
    out = make_output_paths(out_prefix, target)
    cmd = [NMAP_BIN, *args_list, '-oN', out['normal'],
           '-oG', out['grep'], '-oX', out['xml'], target]
    print('[+] Running:', ' '.join(cmd))
    try:
        r = subprocess.run(cmd, capture_output=True,
                           text=True, timeout=timeout)
        if r.returncode != 0:
            print('[!] nmap returned', r.returncode)
    except subprocess.TimeoutExpired:
        print('[!] timeout for', target)
    return out

# === PARSERS ===


def parse_nmap_xml_basic(xml_path):
    results = []
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        for host in root.findall('host'):
            addr = None
            for a in host.findall('address'):
                if a.get('addrtype') in ('ipv4', 'ipv6'):
                    addr = a.get('addr')
                    break
            ports = []
            pe = host.find('ports')
            if pe is not None:
                for p in pe.findall('port'):
                    s = p.find('state')
                    if s is None:
                        continue
                    if s.get('state') == 'open':
                        port = p.get('portid')
                        proto = p.get('protocol')
                        svc = p.find('service')
                        svcname = svc.get('name') if svc is not None else ''
                        ver = svc.get('version') if svc is not None else ''
                        ports.append((port, proto, svcname, ver))
            results.append({'addr': addr, 'open_ports': ports})
    except Exception as e:
        print('[!] xml parse fail', e)
    return results


def parse_nmap_with_python_nmap(xml_path):
    if not _pynmap:
        return None
    scanner = _pynmap.PortScanner()
    try:
        scanner.analyse_nmap_xml_scan(open(xml_path).read())
        parsed = []
        for host in scanner.all_hosts():
            open_ports = []
            for proto in scanner[host].all_protocols():
                for port in scanner[host][proto].keys():
                    if scanner[host][proto][port]['state'] == 'open':
                        svc = scanner[host][proto][port].get('name', '')
                        version = scanner[host][proto][port].get('version', '')
                        open_ports.append((str(port), proto, svc, version))
            parsed.append({'addr': host, 'open_ports': open_ports})
        return parsed
    except Exception as e:
        print('[!] python-nmap parse fail', e)
        return None

# === PLUGINS ===


def load_plugins():
    pdir = BASE_DIR / 'plugins'
    plugins = []
    if not pdir.exists():
        return plugins
    for p in pdir.glob('*.py'):
        try:
            spec = importlib.util.spec_from_file_location(p.stem, p)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            if hasattr(mod, 'run'):
                plugins.append(mod)
                print('[+] Loaded plugin:', p.name)
        except Exception as e:
            print('[!] plugin load error:', p.name, e)
    return plugins


# === REPORT HELPERS ===
HTML_TEMPLATE = """<html><head><meta charset='utf-8'><title>Dark-Map Report</title></head>
<body><h1>Dark-Map Scan Report</h1><p>Generated: {{generated}}</p>
{% for s in scans %}
<h2>{{s.target}}</h2>
{% if s.parsed %}
<table border=1 cellpadding=4><tr><th>addr</th><th>port</th><th>proto</th><th>service</th><th>ver</th></tr>
{% for h in s.parsed %}{% for p in h.open_ports %}
<tr><td>{{h.addr}}</td><td>{{p[0]}}</td><td>{{p[1]}}</td><td>{{p[2]}}</td><td>{{p[3]}}</td></tr>
{% endfor %}{% endfor %}
</table>{% else %}<p>No parsed results</p>{% endif %}
{% endfor %}
</body></html>"""


def write_csv(path, parsed):
    try:
        with open(path, 'w', newline='', encoding='utf-8') as fh:
            w = csv.writer(fh)
            w.writerow(['addr', 'port', 'proto', 'service', 'version'])
            for h in parsed:
                for p in h.get('open_ports', []):
                    w.writerow([h.get('addr'), p[0], p[1], p[2], p[3]])
    except Exception as e:
        print('[!] csv write', e)


def write_html(path, scans):
    if Template is None:
        print('[!] jinja2 not installed: skip html')
        return
    try:
        tpl = Template(HTML_TEMPLATE)
        out = tpl.render(
            generated=datetime.datetime.now().isoformat(), scans=scans)
        open(path, 'w', encoding='utf-8').write(out)
    except Exception as e:
        print('[!] html write', e)

# === MAIN ===


def main():
    parser = argparse.ArgumentParser(
        prog="Dark-Map",
        description="Dark-Map — All-in-One Nmap Automation Framework",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("-t", "--targets", nargs="+",
                        help="Specify targets (IP, host, or CIDR).")
    parser.add_argument("-f", "--targets-file",
                        help="File with one target per line.")
    parser.add_argument("--preset", choices=list(PRESETS.keys()), default="quick",
                        help="Scan mode preset:\n  quick, full, stealth, vuln, ping")
    parser.add_argument(
        "--nmap-args", help="Custom nmap args (overrides preset).")
    parser.add_argument("--concurrency", type=int, default=4,
                        help="Concurrent threads (default: 4)")
    parser.add_argument("--timeout", type=int,
                        help="Timeout in seconds per scan.")
    parser.add_argument("--out-prefix", default="darkmap",
                        help="Output file prefix.")
    parser.add_argument("--no-parse", action="store_true",
                        help="Skip result parsing.")
    parser.add_argument("--csv-report", action="store_true",
                        help="Generate CSV output.")
    parser.add_argument("--html-report", action="store_true",
                        help="Generate HTML report.")
    parser.add_argument("--use-python-nmap",
                        action="store_true", help="Use python-nmap parser.")
    parser.add_argument(
        "--nse-cats", help="Nmap script categories (comma-separated).")
    parser.add_argument(
        "--nse-scripts", help="Specific NSE scripts (comma-separated).")
    parser.add_argument("--version", action="store_true",
                        help="Show version and exit.")
    parser.add_argument("--about", action="store_true",
                        help="Show author and tool information.")
    parser.add_argument("--examples", action="store_true",
                        help="Show example commands and exit.")

    args = parser.parse_args()

    # metadata flags
    if args.version:
        print(f"Dark-Map v{VERSION}")
        sys.exit(0)
    if args.about:
        print(
            f"Dark-Map v{VERSION} — by {AUTHOR}\nA unified Nmap automation framework for ethical cybersecurity scanning.")
        sys.exit(0)

    # examples flag: print a curated list of ready-to-run commands and exit
    if args.examples:
        examples = [
            "# Quick single-host scan (version detection):",
            "python3 dark-map.py -t 192.168.1.10 --preset quick",
            "",
            "# Full all-ports scan for multiple targets from a file (8 parallel scans):",
            "python3 dark-map.py -f targets.txt --preset full --concurrency 8 --csv-report --html-report",
            "",
            "# SYN stealth scan + NSE vuln scripts on a host:",
            "python3 dark-map.py -t 10.0.0.5 --preset stealth --nse-cats vuln --csv-report",
            "",
            "# Run a custom nmap command (overrides preset):",
            "python3 dark-map.py -t example.com --nmap-args \"-sS -p1-65535 -T4\" --out-prefix customscan",
            "",
            "# Use python-nmap for richer parsing (requires 'python-nmap' package):",
            "python3 dark-map.py -t 10.0.0.5 --use-python-nmap --csv-report",
            "",
            "# Run the Textual TUI (interactive):",
            "python3 dark-map-tui.py",
            "",
            "# Start the web dashboard locally (dev):",
            "python3 web/app.py  # then open http://127.0.0.1:5000",
            "",
            "# Start web frontend as a systemd service (example):",
            "sudo systemctl start darkmap-web.service",
            "",
            "# Run example CVE DB import (create cve_index.db from CSV):",
            "python3 tools/build_cve_db.py --from-csv tools/sample_cves.csv",
            "",
            "# Helpful: save console log of a run to a file:",
            "python3 dark-map.py -t 10.0.0.5 --csv-report | tee ~/darkmap_last_run.log",
            "",
            "# Show this help again:",
            "python3 dark-map.py --help",
        ]
        print("\n=== Dark-Map Example Commands ===\n")
        print("\n".join(examples))
        print("\nAll example commands assume you are in the project root and have installed requirements.")
        sys.exit(0)

    # Normal execution flow
    banner_animation()
    ensure_nmap()

    if args.targets_file:
        targets = [x.strip() for x in open(args.targets_file).read(
        ).splitlines() if x.strip() and not x.startswith('#')]
    elif args.targets:
        targets = args.targets
    else:
        print("[!] No targets specified. Use -t or -f.")
        sys.exit(1)

    arglist = args.nmap_args.split() if args.nmap_args else PRESETS.get(
        args.preset, '').split()
    if args.nse_cats:
        arglist += ['--script', args.nse_cats.replace(' ', '')]
    if args.nse_scripts:
        arglist += ['--script', args.nse_scripts.replace(' ', '')]

    plugins = load_plugins()
    results = []

    with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        futures = {ex.submit(run_nmap_scan, t, arglist,
                             args.out_prefix, args.timeout): t for t in targets}
        for fut in as_completed(futures):
            target = futures[fut]
            out = fut.result()
            parsed = None
            if not args.no_parse:
                if args.use_python_nmap and _pynmap:
                    parsed = parse_nmap_with_python_nmap(
                        out['xml']) or parse_nmap_xml_basic(out['xml'])
                else:
                    parsed = parse_nmap_xml_basic(out['xml'])
            results.append(
                {'target': target, 'outputs': out, 'parsed': parsed})
            if args.csv_report and parsed:
                write_csv(out['csv'], parsed)
            for p in plugins:
                try:
                    p.run(target, out, parsed)
                except Exception as e:
                    print('[!] Plugin error:', p.__name__, e)

    # === Summary ===
    print('\n==== Summary ====')
    for r in results:
        print('\nTarget:', r['target'])
        parsed = r['parsed']
        if not parsed:
            print(' - no parsed results')
            continue
        for h in parsed:
            addr = h.get('addr') or r['target']
            if not h.get('open_ports'):
                print(' -', addr, ': no open ports')
                continue
            print(' -', addr, ':', len(h.get('open_ports')), 'open ports')
            for p in h.get('open_ports'):
                print('   ', p[0] + '/' + p[1], p[2], p[3])

    if args.html_report:
        write_html(str(
            OUTPUT_DIR / f"{args.out_prefix}_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.html"), results)

    print('\n[✔] Saved all outputs to', OUTPUT_DIR.resolve())
    print('Scan complete — stay ethical!')


def launch():
    """Entry point for external launchers or modules."""
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] Scan aborted by user.")
        sys.exit(0)
    except Exception as e:
        print("[!] Fatal error:", e)
        sys.exit(1)


if __name__ == "__main__":
    launch()
