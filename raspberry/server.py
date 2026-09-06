#!/usr/bin/env python3
import json, os, sqlite3, mimetypes
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

ROOT=Path(__file__).resolve().parent
DB=Path(os.getenv('MI_DB', ROOT/'mi_inspire.db'))
HOST=os.getenv('MI_HOST','0.0.0.0'); PORT=int(os.getenv('MI_PORT','8080'))

SEEDS=[
('VISIONE','Trasformiamo sistemi complessi in progresso concreto.','Innovazione e competenza al servizio di chi guarda al futuro.','all','industry'),
('PERSONE','Oltre 600 professionisti. Un’unica direzione: crescere insieme.','Ogni competenza rafforza il valore dell’intera squadra.','all','people'),
('SICUREZZA','Il lavoro migliore è quello che ci riporta a casa, ogni giorno.','La sicurezza è una responsabilità condivisa.','cantieri','mission'),
('INNOVAZIONE','L’esperienza ci dà solide radici. La ricerca ci porta più lontano.','Curiosità, metodo e tecnologia trasformano le idee in soluzioni.','uffici','vision'),
('QUALITÀ','L’eccellenza è il modo in cui affrontiamo ogni dettaglio.','Precisione e affidabilità costruiscono fiducia.','produzione','industry'),
('SQUADRA','Dalla progettazione alla manutenzione, il risultato parla di tutti noi.','Competenze diverse, responsabilità comune.','all','people')]

def db():
    c=sqlite3.connect(DB,timeout=10); c.row_factory=sqlite3.Row; return c

def init_db():
    with db() as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY AUTOINCREMENT,category TEXT NOT NULL,title TEXT NOT NULL,subtitle TEXT DEFAULT '',target TEXT DEFAULT 'all',image TEXT DEFAULT 'industry',status TEXT DEFAULT 'pending',start_at TEXT,end_at TEXT,created_at TEXT NOT NULL,updated_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS screens(id TEXT PRIMARY KEY,name TEXT NOT NULL,department TEXT DEFAULT 'all',last_seen TEXT,current_message INTEGER);
        CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT NOT NULL);
        ''')
        if c.execute('SELECT COUNT(*) FROM messages').fetchone()[0]==0:
            now=utcnow()
            c.executemany('INSERT INTO messages(category,title,subtitle,target,image,status,created_at,updated_at) VALUES(?,?,?,?,?,"approved",?,?)',[(*x,now,now) for x in SEEDS])
        defaults={'duration':'15','reviewer':'Responsabile comunicazione interna','company':'Meridionale Impianti','updated_at':utcnow()}
        for k,v in defaults.items(): c.execute('INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)',(k,v))

def utcnow(): return datetime.now(timezone.utc).isoformat(timespec='seconds')
def rows(rs): return [dict(x) for x in rs]

class Handler(SimpleHTTPRequestHandler):
    def log_message(self,fmt,*args): print('[MI]',fmt%args)
    def send_json(self,data,status=200):
        raw=json.dumps(data,ensure_ascii=False).encode(); self.send_response(status); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Cache-Control','no-store'); self.send_header('Content-Length',len(raw)); self.end_headers(); self.wfile.write(raw)
    def body(self):
        try:return json.loads(self.rfile.read(int(self.headers.get('Content-Length','0'))) or b'{}')
        except:return None
    def do_GET(self):
        u=urlparse(self.path)
        if u.path=='/api/health': return self.send_json({'ok':True,'time':utcnow()})
        if u.path=='/api/messages':
            with db() as c: return self.send_json(rows(c.execute('SELECT * FROM messages ORDER BY id DESC')))
        if u.path=='/api/screens':
            with db() as c:return self.send_json(rows(c.execute('SELECT * FROM screens ORDER BY name')))
        if u.path=='/api/settings':
            with db() as c:return self.send_json({x['key']:x['value'] for x in c.execute('SELECT * FROM settings')})
        if u.path=='/api/state':
            q=parse_qs(u.query); department=q.get('department',['all'])[0]; screen=q.get('screen',['tv-hall'])[0]; now=utcnow()
            with db() as c:
                c.execute('INSERT INTO screens(id,name,department,last_seen) VALUES(?,?,?,?) ON CONFLICT(id) DO UPDATE SET department=excluded.department,last_seen=excluded.last_seen',(screen,screen.replace('-',' ').title(),department,now))
                msgs=rows(c.execute('SELECT * FROM messages WHERE status="approved" AND (target="all" OR target=?) AND (start_at IS NULL OR start_at="" OR start_at<=?) AND (end_at IS NULL OR end_at="" OR end_at>=?) ORDER BY id',(department,now,now)))
                settings={x['key']:x['value'] for x in c.execute('SELECT * FROM settings')}
            return self.send_json({'messages':msgs,'settings':settings,'server_time':now})
        if u.path in ('/','/admin'): return self.serve('index.html')
        if u.path=='/player': return self.serve('player.html')
        return self.serve(u.path.lstrip('/'))
    def do_POST(self):
        u=urlparse(self.path); data=self.body()
        if data is None:return self.send_json({'error':'JSON non valido'},400)
        now=utcnow()
        if u.path=='/api/messages':
            title=str(data.get('title','')).strip(); category=str(data.get('category','CRESCITA')).strip().upper()
            if not title:return self.send_json({'error':'Il messaggio è obbligatorio'},400)
            with db() as c:
                cur=c.execute('INSERT INTO messages(category,title,subtitle,target,image,status,start_at,end_at,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?)',(category,title,str(data.get('subtitle','')),str(data.get('target','all')),str(data.get('image','people')),'pending',data.get('start_at') or None,data.get('end_at') or None,now,now))
                item=dict(c.execute('SELECT * FROM messages WHERE id=?',(cur.lastrowid,)).fetchone())
            return self.send_json(item,201)
        if u.path.startswith('/api/messages/'):
            try: mid=int(u.path.split('/')[3]); action=u.path.split('/')[4]
            except:return self.send_json({'error':'Percorso non valido'},404)
            status={'approve':'approved','reject':'rejected','archive':'archived'}.get(action)
            if not status:return self.send_json({'error':'Azione non valida'},400)
            with db() as c:
                c.execute('UPDATE messages SET status=?,updated_at=? WHERE id=?',(status,now,mid)); item=c.execute('SELECT * FROM messages WHERE id=?',(mid,)).fetchone()
            return self.send_json(dict(item) if item else {'error':'Messaggio non trovato'},200 if item else 404)
        if u.path=='/api/settings':
            allowed=('duration','reviewer','company')
            with db() as c:
                for k in allowed:
                    if k in data:c.execute('INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',(k,str(data[k])))
                c.execute('INSERT INTO settings(key,value) VALUES("updated_at",?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',(now,))
            return self.send_json({'ok':True})
        return self.send_json({'error':'Endpoint non trovato'},404)
    def serve(self,name):
        p=(ROOT/'static'/name).resolve()
        if not str(p).startswith(str((ROOT/'static').resolve())) or not p.is_file():return self.send_error(404)
        raw=p.read_bytes(); self.send_response(200); self.send_header('Content-Type',mimetypes.guess_type(p.name)[0] or 'application/octet-stream'); self.send_header('Content-Length',len(raw)); self.end_headers(); self.wfile.write(raw)

if __name__=='__main__':
    init_db(); print(f'MI Inspire attivo: http://{HOST}:{PORT}'); ThreadingHTTPServer((HOST,PORT),Handler).serve_forever()
