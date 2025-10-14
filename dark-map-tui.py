#!/usr/bin/env python3
"""Dark-Map TUI (enhanced) — requires textual
"""
from textual.app import App
from textual.widgets import Header, Footer, Input, Button, Static, Select, TextLog
from textual.containers import Horizontal, Vertical
import asyncio, shlex, os, subprocess
from pathlib import Path
DARKMAP_SCRIPT = Path.cwd() / 'dark-map.py'
PRESETS=[('quick','quick'),('full','full'),('stealth','stealth'),('vuln','vuln'),('ping','ping')]
class DarkMapTUI(App):
    CSS='''
    Screen {align:center middle}
    #controls {width:80%;padding:1 2;border:round $accent}
    TextLog{height:20;width:80%}
    '''
    async def on_mount(self):
        await self.view.dock(Header(show_clock=True),edge='top')
        await self.view.dock(Footer(),edge='bottom')
        from textual.widgets import Button, Input, Select, TextLog, Static
        from textual.containers import Vertical, Horizontal
        self.log=TextLog()
        self.targets=Input(placeholder='targets (comma separated)')
        self.preset=Select(PRESETS, prompt='preset')
        self.concurrency=Input(value='4')
        self.run_btn=Button('Run')
        self.stop_btn=Button('Stop',disabled=True)
        controls=Vertical(Static('Dark-Map TUI'),self.targets,Horizontal(self.preset,self.concurrency,self.run_btn,self.stop_btn),self.log)
        await self.view.dock(controls)
        self.proc=None
    async def handle_button_pressed(self,event):
        id=event.button.label
        if id=='Run': await self.start_scan()
        elif id=='Stop': await self.stop_scan()
    async def start_scan(self):
        t=self.targets.value.strip()
        if not t: self.log.write('[!] enter targets'); return
        preset=self.preset.value or 'quick'; concurrency=self.concurrency.value or '4'
        targets=[x.strip() for x in t.replace(',', ' ').split()]
        cmd=[str(DARKMAP_SCRIPT), '-t', *targets, '--preset', preset, '--concurrency', concurrency, '--out-prefix', 'tui_scan']
        self.log.write('[+] '+ ' '.join(shlex.quote(c) for c in cmd))
        self.run_btn.disabled=True; self.stop_btn.disabled=False
        self.proc=await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
        async def stream():
            assert self.proc
            while True:
                line=await self.proc.stdout.readline()
                if not line: break
                self.log.write(line.decode('utf-8',errors='ignore').rstrip())
            rc=await self.proc.wait(); self.log.write('[+] exited '+str(rc))
            self.run_btn.disabled=False; self.stop_btn.disabled=True
        asyncio.create_task(stream())
    async def stop_scan(self):
        if self.proc:
            try: self.proc.terminate(); self.log.write('[!] terminated')
            except Exception as e: self.log.write('[!] stop failed '+str(e))
if __name__=='__main__': DarkMapTUI.run()
