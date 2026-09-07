# POPIN v4 — amostra congelada para sensibilidade

Data de congelamento: 2026-08-15  
Seed determinística: `popin_v4_sensitivity_20260815`  
Arquivo: `data/gpd_v2_1_20251120/sensitivity_test_sample.csv`

## Composição

- 900 discursos `SPEECH` válidos, todos já pontuados pelo Qwen baseline.
- 414 selecionados como âncoras de líder–mandato GPD.
- 68 selecionados como âncoras textuais GPD; 77 IDs POPIN distintos possuem
  correspondência textual aceita na revisão.
- 418 selecionados no complemento estratificado por país e faixa de score POPIN.
- 19 países representados; Costa Rica permanece com 25 casos por ser o limite
  disponível no corpus válido.

## Partição GPD

A partição foi feita por líder–mandato, nunca por discurso:

- desenvolvimento: 30 líder–mandato;
- teste bloqueado: 64 líder–mandato;
- sem vínculo a líder–mandato GPD: 154 discursos, usados apenas para testar
  estabilidade operacional.

O arquivo contém 746 discursos vinculados a um líder–mandato GPD. A seleção de
modelo e prompt deverá usar apenas o teste bloqueado; desenvolvimento serve para
diagnóstico. Os discursos sem vínculo humano não entram na métrica de validação.

## Regra de uso

Não alterar a lista depois de observar resultados dos modelos alternativos. Cada
execução deve usar exatamente os mesmos 900 `discourse_id`, o chunking v4 e a
agregação v4. Se houver falha de API, registrar a falha e repetir o mesmo ID; não
substituir casos silenciosamente.
