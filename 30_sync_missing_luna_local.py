#!/usr/bin/env python3
"""Sincroniza a única linha Luna ausente no DuckDB local a partir da VPS."""

import json
import subprocess
from pathlib import Path

import duckdb


DB = Path("/run/media/andre/5E12373112370E11/OneDrive/04 - Faculdade/02 - Mestrado/03 - Dissertação/02 - Código/popin/popin.duckdb")
DISCOURSE_ID = "f4e8a8b087e1b114"
MODEL = "gpt-5.6-luna"
SSH = ["ssh", "-i", "/home/andre/.ssh/id_rsa-windows", "-o", "IdentitiesOnly=yes", "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/tmp/codex_popin_known_hosts", "root@193.203.174.63", "python3", "-"]
REMOTE_SCRIPT = r'''
import duckdb, json
c=duckdb.connect('/root/popin-run/popin.duckdb', read_only=True)
r=c.execute("select discourse_id,people_centrism,anti_elitism,moral_dichotomy,popular_sovereignty,exclusionary_rhetoric,crisis_rhetoric,final_score,n_chunks,raw_json,prompt_id,provider,run_id from scores where model_id='gpt-5.6-luna' and discourse_id='f4e8a8b087e1b114'").fetchone()
print(json.dumps(r, ensure_ascii=False))
'''


def main() -> None:
    con = duckdb.connect(str(DB))
    existing = con.execute("select count(*) from scores where discourse_id=? and model_id=?", [DISCOURSE_ID, MODEL]).fetchone()[0]
    if existing:
        print("already_present")
        con.close()
        return
    proc = subprocess.run(SSH, input=REMOTE_SCRIPT.encode(), stdout=subprocess.PIPE, check=True)
    row = json.loads(proc.stdout.decode().strip())
    con.execute("""
        insert into scores (discourse_id,model_id,people_centrism,anti_elitism,moral_dichotomy,popular_sovereignty,exclusionary_rhetoric,crisis_rhetoric,final_score,n_chunks,raw_json,prompt_id,provider,run_id)
        values (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        on conflict (discourse_id,model_id) do nothing
    """, [row[0], MODEL, *row[1:10], row[10], row[11], row[12]])
    con.commit()
    print(con.execute("select count(*) from scores where discourse_id=? and model_id=?", [DISCOURSE_ID, MODEL]).fetchone()[0])
    con.close()


if __name__ == "__main__":
    main()
