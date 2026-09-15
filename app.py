#!/usr/bin/env python3
# Portable Notes Web: local-first notes app using only Python standard library.
from __future__ import annotations
import json, re, sqlite3, webbrowser, zipfile, io, os
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DB = DATA / "notes.db"
STATIC = ROOT / "static"
HOST, PORT = "127.0.0.1", 8765
DATA.mkdir(exist_ok=True)

def now(): return datetime.now(timezone.utc).isoformat()
def slug(text):
    value = re.sub(r"[^a-zA-Z0-9 _-]", "", text).strip().lower().replace(" ", "-")
    return value[:80] or "untitled"

def connect():
    db=sqlite3.connect(DB); db.row_factory=sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    return db

def init_db():
    with connect() as db:
        db.executescript('''
        CREATE TABLE IF NOT EXISTS notes(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          title TEXT NOT NULL DEFAULT 'Untitled',
          content TEXT NOT NULL DEFAULT '',
          folder TEXT NOT NULL DEFAULT 'Inbox',
          tags TEXT NOT NULL DEFAULT '[]',
          favorite INTEGER NOT NULL DEFAULT 0,
          pinned INTEGER NOT NULL DEFAULT 0,
          deleted INTEGER NOT NULL DEFAULT 0,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_notes_updated ON notes(updated_at DESC);
        CREATE INDEX IF NOT EXISTS idx_notes_deleted ON notes(deleted);
        ''')
        if not db.execute("SELECT 1 FROM notes LIMIT 1").fetchone():
            t=now(); db.execute("INSERT INTO notes(title,content,folder,tags,pinned,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",
              ("Welcome to Portable Notes", "# Welcome\n\nYour private, local-first knowledge base.\n\n## Try these\n- Create a note with **Ctrl+N**\n- Link notes using [[Another Note]]\n- Add #tags or use the tag field\n- Toggle preview with **Ctrl+Shift+P**\n- Autosave is enabled\n\n- [ ] First task", "Getting Started", '["welcome","guide"]', 1, t, t))

def row(note):
    d=dict(note); d['tags']=json.loads(d.get('tags') or '[]'); d['favorite']=bool(d['favorite']); d['pinned']=bool(d['pinned']); d['deleted']=bool(d['deleted']); return d

class Handler(SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args): print("[Portable Notes]", fmt%args)
    def send_json(self, obj, status=200):
        raw=json.dumps(obj, ensure_ascii=False).encode(); self.send_response(status)
        self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Content-Length',str(len(raw))); self.send_header('Cache-Control','no-store'); self.end_headers(); self.wfile.write(raw)
    def body(self):
        n=int(self.headers.get('Content-Length','0')); return json.loads(self.rfile.read(n) or b'{}')
    def do_GET(self):
        p=urlparse(self.path)
        if p.path=='/api/notes':
            q=parse_qs(p.query); search=q.get('q',[''])[0].strip().lower(); deleted=int(q.get('deleted',['0'])[0])
            sql="SELECT * FROM notes WHERE deleted=?"; params=[deleted]
            if search: sql += " AND (lower(title) LIKE ? OR lower(content) LIKE ? OR lower(tags) LIKE ? OR lower(folder) LIKE ?)"; params += ['%'+search+'%']*4
            sql += " ORDER BY pinned DESC, updated_at DESC"
            with connect() as db: notes=[row(x) for x in db.execute(sql,params)]
            return self.send_json(notes)
        if p.path.startswith('/api/notes/'):
            try: nid=int(p.path.rsplit('/',1)[1])
            except: return self.send_json({'error':'Invalid ID'},400)
            with connect() as db: n=db.execute('SELECT * FROM notes WHERE id=?',(nid,)).fetchone()
            return self.send_json(row(n) if n else {'error':'Not found'}, 200 if n else 404)
        if p.path=='/api/meta':
            with connect() as db:
                folders=[x[0] for x in db.execute("SELECT DISTINCT folder FROM notes WHERE deleted=0 ORDER BY folder")]
                tags=sorted({t for x in db.execute("SELECT tags FROM notes WHERE deleted=0") for t in json.loads(x[0] or '[]')})
            return self.send_json({'folders':folders,'tags':tags})
        if p.path=='/api/export':
            mem=io.BytesIO()
            with zipfile.ZipFile(mem,'w',zipfile.ZIP_DEFLATED) as z, connect() as db:
                for n in db.execute('SELECT * FROM notes WHERE deleted=0'):
                    d=row(n); front='---\nfolder: '+d['folder']+'\ntags: '+', '.join(d['tags'])+'\n---\n\n'
                    z.writestr(f"{slug(d['title'])}-{d['id']}.md", front+'# '+d['title']+'\n\n'+d['content'])
                z.writestr('portable-notes-backup.json', json.dumps([row(n) for n in db.execute('SELECT * FROM notes')],indent=2))
            raw=mem.getvalue(); self.send_response(200); self.send_header('Content-Type','application/zip'); self.send_header('Content-Disposition','attachment; filename="portable-notes-backup.zip"'); self.send_header('Content-Length',str(len(raw))); self.end_headers(); return self.wfile.write(raw)
        if p.path=='/': self.path='/static/index.html'
        return super().do_GET()
    def do_POST(self):
        if self.path=='/api/notes':
            b=self.body(); t=now()
            with connect() as db:
                cur=db.execute("INSERT INTO notes(title,content,folder,tags,created_at,updated_at) VALUES(?,?,?,?,?,?)",(b.get('title','Untitled').strip() or 'Untitled',b.get('content',''),b.get('folder','Inbox'),json.dumps(b.get('tags',[])),t,t)); nid=cur.lastrowid; n=db.execute('SELECT * FROM notes WHERE id=?',(nid,)).fetchone()
            return self.send_json(row(n),201)
        return self.send_json({'error':'Not found'},404)
    def do_PUT(self):
        if self.path.startswith('/api/notes/'):
            try: nid=int(self.path.rsplit('/',1)[1]); b=self.body()
            except: return self.send_json({'error':'Bad request'},400)
            allowed=['title','content','folder','favorite','pinned','deleted']; sets=[]; vals=[]
            for k in allowed:
                if k in b: sets.append(k+'=?'); vals.append(int(b[k]) if k in ('favorite','pinned','deleted') else b[k])
            if 'tags' in b: sets.append('tags=?'); vals.append(json.dumps(b['tags']))
            sets.append('updated_at=?'); vals.append(now()); vals.append(nid)
            with connect() as db:
                db.execute('UPDATE notes SET '+','.join(sets)+' WHERE id=?',vals); n=db.execute('SELECT * FROM notes WHERE id=?',(nid,)).fetchone()
            return self.send_json(row(n) if n else {'error':'Not found'},200 if n else 404)
        return self.send_json({'error':'Not found'},404)
    def do_DELETE(self):
        if self.path.startswith('/api/notes/'):
            try: nid=int(self.path.rsplit('/',1)[1])
            except: return self.send_json({'error':'Bad ID'},400)
            with connect() as db: db.execute('DELETE FROM notes WHERE id=?',(nid,))
            return self.send_json({'ok':True})
        return self.send_json({'error':'Not found'},404)

def main():
    init_db(); os.chdir(ROOT); server=ThreadingHTTPServer((HOST,PORT),Handler)
    url=f'http://{HOST}:{PORT}'; print(f'Portable Notes running at {url}\nPress Ctrl+C to stop.')
    try: webbrowser.open(url); server.serve_forever()
    except KeyboardInterrupt: print('\nStopped.')
    finally: server.server_close()
if __name__=='__main__': main()
