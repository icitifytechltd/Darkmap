# Example plugin: writes a simple summary next to XML output
def run(target, outputs, parsed):
    try:
        p = outputs.get('xml') + '.summary.txt'
        with open(p,'w',encoding='utf-8') as fh:
            fh.write(f'Scan summary for {target}\n')
            if not parsed: fh.write('No parsed results\n'); return
            for h in parsed:
                fh.write(f'Host: {h.get("addr")}\n')
                for pp in h.get('open_ports',[]): fh.write(f'  {pp[0]}/{pp[1]} {pp[2]} {pp[3]}\n')
        print('[plugin] example summary written:', p)
    except Exception as e:
        print('[plugin] example failed', e)
