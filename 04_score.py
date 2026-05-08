"""
POPIN v4 — Step 4: Scoring de populismo via LLM

Pontua cada discurso nas 5 dimensões do POPIN (0.00–100.00):
  - PeopleCentrism         : referências ao "povo" como ator central
  - AntiElitism            : antagonismo a elites políticas/econômicas/midiáticas
  - MoralDichotomy         : divisão moral entre povo puro e elite corrupta
  - PopularSovereignty     : apelos à soberania e vontade popular
  - ExclusionaryRhetoric   : exclusão de grupos do "povo verdadeiro"
  - FinalScore             : média simples das 5 dimensões

Textos longos são divididos em chunks. Os scores finais são a média
ponderada pelo tamanho de cada chunk.

Discursos com dtype=INVALID são ignorados.
Discursos já pontuados (na tabela scores) são ignorados.

Uso:
    python 04_score.py
    python 04_score.py --limit 50          # teste com N discursos
    python 04_score.py --concurrency 16    # paralelismo (padrão: 16)
    python 04_score.py --iso3 BRA          # apenas um país
"""

import argparse
import asyncio
import json
import os
import re
import uuid

import duckdb
from dotenv import load_dotenv
from openai import AsyncOpenAI
from tqdm.asyncio import tqdm

load_dotenv()
DB_PATH        = os.getenv("DB_PATH", "./popin.duckdb")
VLLM_BASE_URL  = os.getenv("VLLM_BASE_URL", "http://localhost:8080/v1")
VLLM_API_KEY   = os.getenv("VLLM_API_KEY", "vx")
VLLM_MODEL     = os.getenv("VLLM_MODEL", "Qwen/Qwen3-30B-A3B-Instruct-2507")

CHUNK_WORDS      = 800   # reduzido: sistema+chunk deve caber em 4096 tokens
CHECKPOINT_EVERY = 100
DIMENSIONS       = ["people_centrism", "anti_elitism", "moral_dichotomy",
                    "popular_sovereignty", "exclusionary_rhetoric", "crisis_rhetoric"]


# ── Prompt ────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are a political science research assistant specialized in comparative populism across world regions.
Analyze the political speech excerpt using the 5-dimensional framework below.
Output ONLY valid minified JSON — no spaces, no newlines, no extra fields.

CONCEPTUAL FRAMEWORK (for scoring only; do NOT include in output):
- People-Centrism: the "people" — however locally defined — are portrayed as unified, virtuous, and the supreme political actor. (Mudde, 2004)
- Anti-Elitism: "elites" — political, economic, media, judicial, foreign, or technocratic — are portrayed as corrupt, self-serving, and opposed to the people. (Weyland, 2017)
- MoralDichotomy: an explicit moral divide is drawn between a good/pure people and evil/corrupt elites or outsiders. (Mudde & Kaltwasser, 2017)
- PopularSovereigntyClaim: the leader claims to directly embody, represent, or act on the will of the people, overriding or bypassing institutions. (Pappas, 2019)
- ExclusionaryRhetoric: "the people" is defined by explicitly excluding out-groups — by class, ethnicity, religion, nationality, ideology, or other identity markers. (Moffitt, 2016)
- CrisisRhetoric: performative invocation of crisis, emergency, breakdown, or existential threat as a mobilizing tool — the situation demands urgent action, normal rules no longer apply, and only the leader/the people can save society. (Moffitt, 2016)

REGIONAL SCOPE — academically grounded regional variants (score language-agnostically in any language):

LATIN AMERICA (Weyland 2001; de la Torre 2010; Laclau 2005; Mudde & Kaltwasser 2012):
- "The people" (pueblo) = the virtuous poor and working masses; defined by CLASS and MORAL standing, not ethnicity.
- Elites = domestic oligarchy + foreign capital; portrayed as anti-national and corrupt.
- Populism as POLITICAL STRATEGY (Weyland): direct, unmediated charismatic bond between leader and unorganized followers, bypassing institutions.
- Laclau: "empty signifiers" (pueblo, patria, justicia) chain disparate demands into anti-elite bloc. The people's content is discursively constructed, not fixed.
- Typically INCLUSIONARY (Mudde & Kaltwasser): expands "the people" downward to the marginalized; ExclusionaryRhetoric tends to be lower unless specific out-groups are targeted.

EUROPE (Mudde 2007; Brubaker 2017; Pappas 2019; Mudde & Kaltwasser 2012):
- Thin ideology combining populism + NATIVISM + authoritarianism (Mudde): the native ethnic/cultural nation vs. cosmopolitan elites and foreign others.
- Elites = EU bureaucrats, globalists, liberal media, "cosmopolitan" political class accused of betraying native citizens.
- Typically EXCLUSIONARY: defines "the people" by ethnic/cultural/civilizational boundaries.
- Western Europe (Brubaker 2017): CIVILIZATIONIST framing — threat is Islam as a civilization, not merely migrants; invokes secularism, gender equality, and Christian heritage as markers of European identity.
- Eastern Europe (Pappas 2019): democratic illiberalism — accepts elections while dismantling checks and balances; socially conservative and religious.

AFRICA (Mamdani 1996; Resnick 2014; Moffitt 2016):
- Colonial bifurcation (Mamdani): colonialism created citizen/subject divide; post-colonial populism frames the rural/subaltern as the authentic people against Westernized elites who inherited the colonial state.
- Elites = Westernized urban professionals, post-colonial bureaucrats, IMF/World Bank conditionality enforcers; framed as neo-colonial collaborators.
- Ethnic institutionalization (Mamdani): colonialism politicized ethnicity; this can fracture simple people/elite binaries into ethnic clientelism — watch for ethnic in-group definitions of "the people."
- Resnick (2014): urban poverty and informality drive African populism; slum dwellers and informal workers are key constituencies.

ASIA / MIDDLE EAST (Hadiz 2016; Yilmaz 2021, 2023; Mietzner & Fossati):
- Islamic populism (Hadiz 2016): NOT reducible to religion — it is CLASS GRIEVANCE expressed in Islamic idiom. Muslim subaltern communities mobilize against secular-Westernized elites who monopolized post-colonial advantages.
- "The people" = the Muslim umma (community of believers); marginalized Muslim majorities against secular-military or Westernized minorities.
- Elites = secular establishment, military technocracy, Western-backed NGOs, ethnic-Chinese business elites (Southeast Asia); framed as both class enemies and civilizational threats.
- Civilizational populism (Yilmaz 2023): AKP/Erdoğan variant — Ottoman-Islamic civilization vs. Western civilization; exclusion of secular "apostates," religious minorities, LGBTQ+ individuals as incompatible with Islamic civilization.
- ExclusionaryRhetoric often HIGH: religious and civilizational boundary-drawing is constitutive of "the people."

NORTH AMERICA / OCEANIA (Norris & Inglehart 2019; Moffitt 2016; Canovan 1999; Taggart 2000):
- Cultural backlash (Norris & Inglehart 2019): status anxiety of culturally traditional cohorts displaced by the post-material Silent Revolution — values, not primarily economics, drive support.
- "The people" = the "silent majority," the "heartland" (Taggart 2000) — an idealized pre-political community of ordinary, hard-working, culturally traditional citizens; often implicitly coded as white/Anglo/Christian without explicit racial language.
- Elites = coastal elites, liberal media, university-educated professionals, "deep state" bureaucrats, globalist corporations.
- Exclusion operates via CULTURAL and VALUE-BASED language: multiculturalism, "political correctness," progressive ideology as threats — explicit ethnic language is often avoided.
- Moffitt (2016): populism as POLITICAL STYLE — "bad manners," norm-violating transgressive communication, and permanent invocation of crisis are constitutive, not merely rhetorical.

CHUNK SAFETY:
- Treat each input as a self-contained excerpt. Score ONLY what is present in THIS chunk.
- Do not assume prior context or infer cues not present in the text.

CUE INTERPRETATION — what counts and what does NOT:
- Count only EXPLICIT, NORMATIVE claims. Merely naming "the people" or "the nation" without moral/political force does NOT qualify as People-Centrism.
- Weight: direct normative assertions > metaphors > implications. Repeated, prominent, varied cues score higher than isolated or passing references.
- Anti-Elitism requires MORALIZED framing (elites as corrupt, evil, or anti-people). Criticizing policy performance, inefficiency, or technical failure alone does NOT qualify.
- PopularSovereigntyClaim: institutional deference ("we respect the constitution", "checks and balances") LOWERS the score unless simultaneously overridden by claims to embody the people's will above institutions.
- ExclusionaryRhetoric requires explicit boundary-drawing that NARROWS who belongs to "the people" — e.g., "true citizens", "real workers", "internal enemies", nativist or religious in-group definitions. General references to crime, corruption, or incompetence without group exclusion do NOT qualify.
- CrisisRhetoric: score HIGH when the text frames the situation as a critical emergency demanding immediate action ("the country is collapsing", "now or never", "existential threat"), invokes breakdown of order or civilization, or positions the leader as the only savior. Score LOW when crisis language is merely descriptive or policy-analytical without urgency/mobilization. Mere criticism of government problems without existential framing does NOT qualify.
- Tone, aggressiveness, or emotional intensity alone do NOT raise scores if the required conceptual cues are absent.

CONTINUOUS SCORING RULES:
- Range: [0.00, 100.00] with 0.01 resolution. Always format with exactly two decimals (e.g. 63.27, 41.58).
- Avoid round numbers: prefer non-.00 / non-.50 values unless the text truly warrants exact thresholds.
- Soft floor: if ANY qualifying cue for an axis is present, assign at least 1.00–9.99 (non-round, e.g. 3.14, 7.83). Use 0.00 ONLY when the axis is completely absent.
- Calibration: weak/incidental ≈ 1–24 | moderate ≈ 25–60 | strong ≈ 61–84 | extreme ≈ 85–100
- Cross-axis independence: score each axis on its own evidence. Correlated movement across axes is allowed but NOT automatically forced.
- Length normalization: score by intensity and salience of cues, NOT by token count. Do not inflate scores for longer excerpts.
- Sanity: if ANY qualifying populist cue exists in the text, at least one axis MUST be > 0.00.

OUTPUT SCHEMA (strict minified JSON):
{"people_centrism":0.00,"anti_elitism":0.00,"moral_dichotomy":0.00,"popular_sovereignty":0.00,"exclusionary_rhetoric":0.00,"crisis_rhetoric":0.00}

FEW-SHOT EXAMPLE (format and calibration anchor — do NOT copy these scores):
{"people_centrism":62.73,"anti_elitism":71.28,"moral_dichotomy":58.41,"popular_sovereignty":44.36,"exclusionary_rhetoric":15.92,"crisis_rhetoric":48.61}

Output ONLY the final JSON. Begin when the speech text is provided."""

def build_user_prompt(chunk: str) -> str:
    return f"Score this political passage:\n\n{chunk}"


# ── Chunking ──────────────────────────────────────────────────────────────────

def split_chunks(text: str, max_words: int = CHUNK_WORDS) -> list[str]:
    """Divide o texto em chunks de ~max_words palavras.

    Respeita parágrafos (\\n\\n) mas também quebra parágrafos longos
    para garantir que nenhum chunk exceda max_words.
    """
    def words_to_chunks(word_list: list[str]) -> list[str]:
        return [" ".join(word_list[i:i + max_words])
                for i in range(0, len(word_list), max_words)]

    paragraphs = [p.strip() for p in re.split(r"\n{1,}", text) if p.strip()]
    chunks, current, current_words = [], [], 0

    for para in paragraphs:
        para_words = para.split()

        # Parágrafo maior que o limite: quebra direto por palavras
        if len(para_words) > max_words:
            if current:
                chunks.append(" ".join(current))
                current, current_words = [], 0
            chunks.extend(words_to_chunks(para_words))
            continue

        if current_words + len(para_words) > max_words and current:
            chunks.append(" ".join(current))
            current, current_words = [], 0

        current.extend(para_words)
        current_words += len(para_words)

    if current:
        chunks.append(" ".join(current))

    return chunks or [text]


# ── LLM call ──────────────────────────────────────────────────────────────────

async def score_chunk(client: AsyncOpenAI, semaphore: asyncio.Semaphore,
                      chunk: str, retries: int = 3) -> tuple[dict | None, str | None]:
    """Retorna (scores, erro). scores=None indica falha."""
    async with semaphore:
        for attempt in range(retries):
            try:
                resp = await client.chat.completions.create(
                    model=VLLM_MODEL,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user",   "content": build_user_prompt(chunk)},
                    ],
                    temperature=0.1,
                    max_tokens=80,
                    extra_body={"chat_template_kwargs": {"enable_thinking": False}},
                )
                raw = resp.choices[0].message.content.strip()

                if raw.startswith("```"):
                    raw = raw.split("```")[1]
                    if raw.startswith("json"):
                        raw = raw[4:]
                    raw = raw.strip()

                data = json.loads(raw)

                scores = {}
                for dim in DIMENSIONS:
                    val = data.get(dim)
                    if val is None:
                        scores[dim] = 0.0
                    else:
                        scores[dim] = round(max(0.0, min(100.0, float(val))), 2)
                return scores, None

            except json.JSONDecodeError as exc:
                error = f"JSON inválido (tentativa {attempt+1}): {raw[:120]!r}"
                if attempt < retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    return None, error
            except Exception as exc:
                error = f"{type(exc).__name__} (tentativa {attempt+1}): {exc}"
                if attempt < retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    return None, error


async def score_discourse(client: AsyncOpenAI, semaphore: asyncio.Semaphore,
                          doc_id: str, text: str) -> tuple[str, dict | None, str | None]:
    """Pontua um discurso completo com média ponderada dos chunks.
    Retorna (doc_id, scores, erro_ou_None)."""
    chunks = split_chunks(text)
    tasks  = [score_chunk(client, semaphore, chunk) for chunk in chunks]
    results = await asyncio.gather(*tasks)

    valid  = []
    errors = []
    for chunk, (s, err) in zip(chunks, results):
        if s is not None:
            valid.append((len(chunk.split()), s))
        else:
            errors.append(err)

    if not valid:
        return doc_id, None, " | ".join(errors)

    total_words = sum(w for w, _ in valid)

    avg = {}
    for dim in DIMENSIONS:
        avg[dim] = round(sum(w * s[dim] for w, s in valid) / total_words, 2)

    avg["final_score"] = round(sum(avg[d] for d in DIMENSIONS) / len(DIMENSIONS), 2)
    avg["n_chunks"]    = len(chunks)
    return doc_id, avg, None


# ── Schema migration ───────────────────────────────────────────────────────────

SCORES_DDL = """
    CREATE TABLE scores (
        discourse_id          VARCHAR REFERENCES discourses(id),
        model_id              VARCHAR NOT NULL,
        people_centrism       FLOAT,
        anti_elitism          FLOAT,
        moral_dichotomy       FLOAT,
        popular_sovereignty   FLOAT,
        exclusionary_rhetoric FLOAT,
        crisis_rhetoric       FLOAT,
        final_score           FLOAT,
        n_chunks              INTEGER,
        raw_json              VARCHAR,
        scored_at             TIMESTAMP DEFAULT now(),
        PRIMARY KEY (discourse_id, model_id)
    )
"""

CORRECT_COLS = ["discourse_id", "model_id", "people_centrism", "anti_elitism",
                "moral_dichotomy", "popular_sovereignty", "exclusionary_rhetoric",
                "crisis_rhetoric", "final_score", "n_chunks", "raw_json", "scored_at"]

def ensure_schema(con):
    """Garante schema correto: colunas, ordem e PRIMARY KEY."""
    current_cols = [row[0] for row in con.execute("DESCRIBE scores").fetchall()]

    # Verifica se PRIMARY KEY existe
    has_pk = bool(con.execute("""
        SELECT constraint_name FROM information_schema.table_constraints
        WHERE table_name = 'scores' AND constraint_type = 'PRIMARY KEY'
    """).fetchone())

    needs_rebuild = (current_cols != CORRECT_COLS) or not has_pk

    if needs_rebuild:
        # Salva dados existentes (colunas em comum)
        common = [c for c in CORRECT_COLS if c in current_cols]
        cols   = ", ".join(common)
        con.execute(f"""
            CREATE TABLE scores_backup AS SELECT {cols} FROM scores;
            DROP TABLE scores;
            {SCORES_DDL};
            INSERT INTO scores ({cols}) SELECT {cols} FROM scores_backup;
            DROP TABLE scores_backup;
        """)
        print("Tabela scores recriada com schema correto (PK + ordem de colunas).")

    con.commit()


# ── Jobs ──────────────────────────────────────────────────────────────────────

def get_or_create_job(con, total_rows: int, iso3: str | None) -> str:
    job_id = str(uuid.uuid4())[:8]
    label  = f"score_{iso3}" if iso3 else "score"
    con.execute(
        "INSERT INTO jobs (job_id, job_type, total_rows, model_id) VALUES (?, ?, ?, ?)",
        [job_id, label, total_rows, VLLM_MODEL]
    )
    con.commit()
    return job_id

def checkpoint(con, job_id: str, processed: int):
    con.execute(
        "UPDATE jobs SET last_row = ?, updated_at = now() WHERE job_id = ?",
        [processed, job_id]
    )
    con.commit()

def finish_job(con, job_id: str):
    con.execute(
        "UPDATE jobs SET status = 'done', updated_at = now() WHERE job_id = ?",
        [job_id]
    )
    con.commit()


# ── Main ──────────────────────────────────────────────────────────────────────

async def score(limit: int | None, concurrency: int, iso3: str | None, rescore: bool):
    con = duckdb.connect(DB_PATH)
    ensure_schema(con)

    if rescore:
        if iso3:
            deleted = con.execute(
                "DELETE FROM scores WHERE model_id = ? AND discourse_id IN "
                "(SELECT id FROM discourses WHERE iso3 = ?)",
                [VLLM_MODEL, iso3.upper()]
            ).rowcount
        else:
            deleted = con.execute(
                "DELETE FROM scores WHERE model_id = ?", [VLLM_MODEL]
            ).rowcount
        con.commit()
        scope = f"país {iso3.upper()}" if iso3 else "todos os países"
        print(f"Rescore: {deleted:,} scores removidos ({scope}, modelo: {VLLM_MODEL})\n")

    where  = "d.dtype IS NOT NULL AND d.dtype != 'INVALID' AND s.discourse_id IS NULL"
    params = [VLLM_MODEL]
    if iso3:
        where += " AND d.iso3 = ?"
        params.append(iso3.upper())

    query = f"""
        SELECT d.id, d.discourse
        FROM discourses d
        LEFT JOIN scores s ON s.discourse_id = d.id AND s.model_id = ?
        WHERE {where}
        ORDER BY d.id
    """
    if limit:
        query += f" LIMIT {limit}"

    rows  = con.execute(query, params).fetchall()
    total = len(rows)
    print(f"Discursos a pontuar: {total:,} | concorrência: {concurrency} | modelo: {VLLM_MODEL}\n")

    if total == 0:
        print("Nada a fazer.")
        con.close()
        return

    job_id    = get_or_create_job(con, total, iso3)
    con.close()   # libera o lock — DBeaver pode conectar entre batches

    client    = AsyncOpenAI(base_url=VLLM_BASE_URL, api_key=VLLM_API_KEY,
                           timeout=60.0)
    semaphore = asyncio.Semaphore(concurrency)
    stats     = {"ok": 0, "failed": 0}
    processed = 0

    pbar = tqdm(total=total, desc="Pontuando")

    for batch_start in range(0, len(rows), CHECKPOINT_EVERY):
        batch   = rows[batch_start : batch_start + CHECKPOINT_EVERY]
        tasks   = [score_discourse(client, semaphore, doc_id, discourse)
                   for doc_id, discourse in batch]
        results = await asyncio.gather(*tasks)

        # Abre conexão só para gravar o batch — fecha logo após
        con = duckdb.connect(DB_PATH)
        for doc_id, sd, err in results:
            if sd is None:
                stats["failed"] += 1
                tqdm.write(f"  FALHA [{doc_id}]: {err}")
                continue

            con.execute("""
                INSERT INTO scores
                    (discourse_id, model_id, people_centrism, anti_elitism,
                     moral_dichotomy, popular_sovereignty, exclusionary_rhetoric,
                     crisis_rhetoric, final_score, n_chunks, raw_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (discourse_id, model_id) DO UPDATE SET
                    people_centrism       = excluded.people_centrism,
                    anti_elitism          = excluded.anti_elitism,
                    moral_dichotomy       = excluded.moral_dichotomy,
                    popular_sovereignty   = excluded.popular_sovereignty,
                    exclusionary_rhetoric = excluded.exclusionary_rhetoric,
                    crisis_rhetoric       = excluded.crisis_rhetoric,
                    final_score           = excluded.final_score,
                    n_chunks              = excluded.n_chunks,
                    raw_json              = excluded.raw_json,
                    scored_at             = now()
            """, [
                doc_id, VLLM_MODEL,
                sd["people_centrism"],
                sd["anti_elitism"],
                sd["moral_dichotomy"],
                sd["popular_sovereignty"],
                sd["exclusionary_rhetoric"],
                sd["crisis_rhetoric"],
                sd["final_score"],
                sd["n_chunks"],
                json.dumps(sd),
            ])
            stats["ok"] += 1

        processed += len(batch)
        checkpoint(con, job_id, processed)
        con.close()   # libera lock — DBeaver pode conectar agora

        # Progresso em arquivo de texto (não requer DuckDB)
        with open("scoring_progress.txt", "w") as f:
            f.write(f"pontuados : {stats['ok']:,} / {total:,}\n")
            f.write(f"falhas    : {stats['failed']:,}\n")
            f.write(f"progresso : {processed/total*100:.1f}%\n")
            f.write(f"job_id    : {job_id}\n")

        pbar.update(len(batch))

    # Marca job como concluído
    con = duckdb.connect(DB_PATH)
    finish_job(con, job_id)
    con.close()

    print(f"\nConcluído — job: {job_id}")
    print(f"  pontuados:  {stats['ok']:,}")
    print(f"  falhas:     {stats['failed']:,}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit",       type=int,            default=None,  help="Pontua apenas N discursos")
    parser.add_argument("--concurrency", type=int,            default=16,    help="Requisições simultâneas (padrão: 16)")
    parser.add_argument("--iso3",        type=str,            default=None,  help="Filtra por país (ex: BRA)")
    parser.add_argument("--rescore",     action="store_true",                help="Apaga scores existentes e reponta tudo")
    args = parser.parse_args()
    asyncio.run(score(limit=args.limit, concurrency=args.concurrency, iso3=args.iso3, rescore=args.rescore))
