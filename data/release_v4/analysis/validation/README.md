# POPIN v4.1.0 — validação e robustez

Este diretório reúne as tabelas finais usadas para documentar a validade
externa, a sensibilidade ao prompt, a sensibilidade ao chunking e a
integridade do pacote. Os arquivos podem ser recriados a partir do DuckDB de
release e dos insumos versionados em
`data/release_v4/analysis/source_inputs/`.

## Escopos

- `model_gpd_speech.csv`: métricas de Pearson, Spearman, MAE, RMSE e viés nos
  mesmos 94 pares líder–mandato `SPEECH`; inclui `min_docs = 1`, `5` e `20`.
- `gpd_term_points_speech.csv`: pontos pareados usados para calcular a tabela
  GPD, no escopo `SPEECH`.
- `prompt_sensitivity.csv`: comparação pareada de 900 IDs entre prompts; o
  arquivo mantém as métricas originais da auditoria.
- `lallpi_country_year.csv`: associação com o componente POP_R do LALLPI em
  nível país–ano, com os cortes de suporte definidos na auditoria.
- `gpd_word_cutoffs_speech.csv`: sensibilidade da comparação GPD a cortes de
  comprimento; a tabela já foi produzida no recorte SPEECH.
- `model_pairs_full_corpus.csv`: concordância entre configurações no corpus
  integral pontuado; não é validação externa.
- `coverage_all_models.csv`, `score_integrity_all_models.csv`,
  `prompt_inventory.csv`, `gpd_text_match_diagnostics.csv` e
  `luna_raw_integrity.csv`: cobertura, integridade e rastreabilidade.

## Interpretação

O GPD é uma referência codificada por humanos, mas a comparação principal é
no nível líder–mandato: cada média POPIN resume os textos disponíveis do
mesmo líder dentro dos limites anuais do crosswalk. Isso não equivale a
comparar necessariamente os mesmos documentos. O reescalonamento 0–2 para
0–100 é apenas uma convenção de apresentação.

O LALLPI tem unidade e construto próprios e é usado como evidência
complementar de associação. A sensibilidade ao prompt é pareada e preserva a
ordenação melhor do que o nível; ambas as informações devem ser reportadas.

Os scripts que reconstroem os arquivos são:

```bash
python tools/reproduce_validation_audit.py
python 51_generate_validation_tables.py
```

`tools/reproduce_validation_audit.py` recria os diagnósticos intermediários em
`analysis/source_audit/`. `51_generate_validation_tables.py` gera este
diretório final. `validation_metadata.json` registra filtros, fontes,
contagens e hashes dos arquivos gerados.
