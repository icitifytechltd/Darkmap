#!/usr/bin/env python3
import csv, sqlite3, argparse
from pathlib import Path
DB = Path('cve_index.db')
CREATE = '''CREATE TABLE IF NOT EXISTS cve_index (id INTEGER PRIMARY KEY AUTOINCREMENT, product TEXT, version_pattern TEXT, cve TEXT, description TEXT, url TEXT);'''
def from_csv(path):
    conn=sqlite3.connect(str(DB)); cur=conn.cursor(); cur.execute(CREATE)
    with open(path,newline='',encoding='utf-8') as fh:
        r=csv.DictReader(fh); cnt=0
        for row in r:
            prod=row.get('product','').strip().lower(); vp=row.get('version_pattern','').strip(); cve=row.get('cve','').strip(); desc=row.get('description','').strip(); url=row.get('url','').strip()
            if not prod or not cve: continue
            cur.execute('INSERT INTO cve_index (product, version_pattern, cve, description, url) VALUES (?,?,?,?,?)',(prod,vp,cve,desc,url)); cnt+=1
    conn.commit(); conn.close(); print('inserted',cnt)
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--from-csv'); args=p.parse_args()
    if args.from_csv: from_csv(args.from_csv)
    else: print('use --from-csv file.csv')
