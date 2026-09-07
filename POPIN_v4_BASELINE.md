# POPIN v4 — baseline operacional

Manifesto de congelamento do estado de trabalho antes dos testes de modelos,
prompts e validação externa.

## Registro

- Data: 2026-08-15T17:26:11-03:00
- Repositório: `main`
- HEAD: `aa3f189a53c84c454e50fdacdbf047a2679266fe`
- Estado: worktree não limpo; alterações preexistentes foram preservadas
- Banco principal: `popin.duckdb`
- Corpus: 48.256 documentos coletados; 45.492 documentos válidos pontuados
- Palavras nos documentos válidos: 115.415.751
- Modelo atualmente registrado nos scores: `Qwen/Qwen3-30B-A3B-Instruct-2507`

Este arquivo registra o estado exato do baseline. Nenhum `reset`, `checkout` ou
commit foi realizado para não sobrescrever alterações anteriores do projeto.

## Decisões v4 registradas

- seis dimensões: `people_centrism`, `anti_elitism`, `moral_dichotomy`,
  `popular_sovereignty`, `exclusionary_rhetoric` e `crisis_rhetoric`;
- chunks contíguos de até 800 palavras, sem overlap;
- temperatura de pontuação igual a `0.0`;
- saída estruturada com seis scores numéricos;
- score final como média aritmética das seis dimensões;
- agregação dos chunks ponderada pelo número de palavras;
- documentos classificados como `INVALID` excluídos da pontuação.

## Arquivos e hashes SHA-256

| Arquivo | SHA-256 |
|---|---|
| `03_classify.py` | `f073004651412062329d13d85d260c23ece994fab8755b38f7eb7c40517cd288` |
| `04_score.py` | `64287a11964803a88c80122e86c0e94454c45a3a6efb7d461115bc34e3927934` |
| `README.md` | `ed963125ad927fd627e8a2a631710f476a4a56d769cc2147f650d3d161e3234a` |
| `06_robustness_checks.py` | `174b1dc042c16fb2cf348c6f5b8259b762ed475aeae52e10765b6265d4268d2e` |
| `07_pca_analysis.py` | `09677d50ec4e4a005d946a775e81f886758fb871577c16e214cc5abd487304db` |
| `06_website/main.py` | `57df9682a8c86586d598e8a7fc6c04dfe7b5d11807786dfc24215435f674799d` |
| `06_website/static/index.html` | `37275640e6878ed5376697e10b86e3d830582fcdb1db10036b113bd7283fdf80` |
| `06_website/static/popin-apresentacao.html` | `f753934ebc00a08d9a1e3071e9e1d3174f8254d2f4d7821748d57c01786bdd14` |
| `06_website/static/css/style.css` | `1d869b3c16b2a93a1ae7181bd326ecfd602ae197fac634ca13ba0544a964ea7e` |
| `06_website/static/js/app.js` | `81dac659d4a7ad75c6ff82ec376f4afe4404471461dc1bf98d84cf132f38e352` |
| `popin.duckdb` | `34bfa1fa430f27516f0b2e88975cb05ec14b8c70ea03f7693852fccf0a2fe607` |
| `Populism by numbers - POPIN v4.docx` | `ab3f59eac266b61a174f4a60cf54447626f52d0914711fa5bc29769347c719cd` |
| `Populism by numbers - POPIN v4.pdf` | `ab3c0ec7917c9f1d2dbc520b537b3dde8f5bd2ffeda76398a6f082b3617111ce` |
| `insumos paper.xlsx` | `6503da992da1a463e711cf095a64d5303e535339654ba56bc5fcf167c8d722b3` |

Os três últimos arquivos estão em:

`/run/media/andre/5E12373112370E11/OneDrive/04 - Faculdade/02 - Mestrado/06 - Paper/`

## Alterações já existentes no worktree

`.gitignore`, `04_score.py`, `06_robustness_checks.py`, `06_website/.gitignore`,
`06_website/main.py`, `06_website/render.yaml`, `06_website/requirements.txt`,
`06_website/run.bat`, `06_website/static/css/style.css`,
`06_website/static/js/app.js`, `07_pca_analysis.py` e `README.md` já estavam
alterados durante o início desta etapa. Esses arquivos não foram restaurados.
