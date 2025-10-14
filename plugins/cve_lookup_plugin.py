# CVE lookup plugin (enhanced): fuzzy match and optional OSV lookup
import sqlite3, re, difflib, json
from pathlib import Path
DB_PATH = Path('cve_index.db')
def lookup_local(product, version, conn):
    cur=conn.cursor(); product_l=(product or '').lower()
    rows=[]
    cur.execute("SELECT product, version_pattern, cve, description, url FROM cve_index WHERE product = ?", (product_l,))
    for r in cur.fetchall():
        vp=r[1]
        if not vp or (version and re.search(vp, version)): rows.append(r[2:])
    if rows: return rows
    # fuzzy fallback
    cur.execute("SELECT product, version_pattern, cve, description, url FROM cve_index")
    choices=[r[0] for r in cur.fetchall()]
    # can't easily map back, so do a simple LIKE
    cur.execute("SELECT product, version_pattern, cve, description, url FROM cve_index WHERE product LIKE ?", ('%'+product_l+'%',))
    for r in cur.fetchall():
        rows.append(r[2:])
    return rows
def query_osv(product, version):
    try:
        import requests
    except Exception:
        return []
    url='https://api.osv.dev/v1/query'
    payload={'version': version, 'package': {'name': product, 'ecosystem': 'OSS-Fuzz'}}
    try:
        r=requests.post(url,json=payload,timeout=6)
        if r.status_code==200:
            data=r.json().get('vulns',[])
            out=[]
            for v in data:
                vid=v.get('id'); desc=v.get('summary') or v.get('details','')
                out.append((vid, desc, ''))
            return out
    except Exception:
        return []
def run(target, outputs, parsed):
    print('[plugin][cve] running for', target)
    if not parsed:
        print('[plugin][cve] no parsed results'); return
    if not DB_PATH.exists():
        print('[plugin][cve] local DB not found; try tools/build_cve_db.py to populate cve_index.db')
        # still try OSV for each service
    found=[]
    conn=None
    if DB_PATH.exists():
        conn=sqlite3.connect(str(DB_PATH))
    for h in parsed:
        addr=h.get('addr')
        for p in h.get('open_ports',[]):
            port, proto, svc, ver = p
            svc_n = (svc or '').lower()
            matches=[]
            if conn:
                matches=lookup_local(svc_n, ver, conn)
            if not matches:
                matches = query_osv(svc_n, ver) if ver else []
            for m in matches:
                if isinstance(m, tuple) and len(m)>=2:
                    cve=m[0]; desc=m[1]; url=(m[2] if len(m)>2 else '')
                    line=f"{addr} {port}/{proto} {svc} {ver} -> {cve}: {desc} {url}"
                    print('[plugin][cve]', line); found.append(line)
    if conn: conn.close()
    if found:
        rpt = outputs.get('xml') + '.cve_report.txt'
        try:
            with open(rpt,'w',encoding='utf-8') as fh: fh.write('\n'.join(found))
            print('[plugin][cve] report written', rpt)
        except Exception as e:
            print('[plugin][cve] failed write', e)
