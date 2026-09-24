"""Generate a read-only SQLite snapshot for a project review."""
import argparse
from datetime import datetime
from html import escape
from pathlib import Path
import sqlite3
import webbrowser

TABLES = {
    'cameras': 'Video sources and the active camera',
    'traffic_analytics': 'Periodic overall traffic measurements',
    'lane_analytics': 'Periodic lane or estimated traffic-band measurements',
    'signal_decisions': 'Saved rule-based signal decisions',
    'vehicle_events': 'Vehicle-event table; it may be empty because event persistence is not wired into the current frame loop',
    'users': 'Local application accounts (password hashes omitted)',
}


def build(database,output):
    sections=[]
    summaries=[]
    with sqlite3.connect(database.resolve().as_uri()+'?mode=ro',uri=True,timeout=10) as connection:
        connection.execute('PRAGMA query_only=ON')
        connection.execute('BEGIN')
        for table,description in TABLES.items():
            schema=connection.execute(f'PRAGMA table_info("{table}")').fetchall()
            if not schema:
                continue
            columns=[r[1] for r in schema if r[1]!='password_hash']
            selected=','.join('"'+c.replace('"','""')+'"' for c in columns)
            count=connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
            rows=connection.execute(f'SELECT {selected} FROM "{table}" ORDER BY id DESC LIMIT 20').fetchall()
            summaries.append(f'<a href="#{table}"><b>{escape(table)}</b><strong>{count:,}</strong><span>rows</span></a>')
            headings=''.join(f'<th>{escape(c)}</th>' for c in columns)
            cells=''.join('<tr>'+''.join(f'<td>{escape(str(v)) if v is not None else "NULL"}</td>' for v in row)+'</tr>' for row in rows)
            if not cells:
                cells=f'<tr><td colspan="{len(columns)}">No records yet.</td></tr>'
            structure=', '.join(f'{r[1]} ({r[2]})' for r in schema if r[1]!='password_hash')
            sections.append(f'<section id="{table}"><h2>{table}</h2><p>{escape(description)}. Showing latest {len(rows)} of {count:,} rows.</p><details><summary>Column definitions</summary><p>{escape(structure)}</p></details><div class="scroll"><table><thead><tr>{headings}</tr></thead><tbody>{cells}</tbody></table></div></section>')
    stamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    html='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Traffic database review</title><style>body{font:15px system-ui;background:#f2f6fa;color:#192a3b;margin:32px}h1{font-size:32px}p{line-height:1.6}.cards{display:flex;gap:12px;flex-wrap:wrap}.cards a{display:grid;gap:8px;background:white;padding:20px;border-radius:10px;color:#183f58;text-decoration:none;min-width:150px}.cards strong{font-size:30px}section{background:white;margin-top:24px;padding:22px;border-radius:10px}.scroll{overflow-x:auto}table{border-collapse:collapse;width:100%;margin-top:15px;font-size:13px}th,td{text-align:left;border-bottom:1px solid #d8e1e8;padding:10px;white-space:nowrap}th{background:#e5f0f6}details{color:#465b6a}code{background:#e5edf3;padding:2px 5px}</style><h1>AI Smart Traffic — database</h1>'''
    html+=f'<p><b>Read-only snapshot:</b> {stamp}<br><b>Database:</b> {escape(str(database.resolve()))}<br>SQLite local development database. Run <code>Show-Database.cmd</code> again for a fresh snapshot. Traffic timestamps are stored in UTC.</p>'
    html+='<p>History includes earlier sample-video runs and different ROI settings; it is not a clean accuracy-evaluation dataset. Lane rows may represent estimated traffic bands. No database records are changed by this viewer.</p>'
    html+='<div class="cards">'+''.join(summaries)+'</div>'+''.join(sections)+'</html>'
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(html,encoding='utf-8')
    return output


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',default='logs/database-review.html')
    parser.add_argument('--no-open',action='store_true')
    args=parser.parse_args()
    result=build(Path('traffic_local.db'),Path(args.output))
    print(f'Read-only database snapshot: {result.resolve()}')
    if not args.no_open:
        webbrowser.open(result.resolve().as_uri())
