# POPIN v4 — validação externa com LALLPI

Data: 2026-08-15  
Fonte: LALLPI v2025.1, índice oficial disponibilizado pelos autores. A versão usada cobre 22 países e os anos 2000–2020.

## 1. O que está sendo comparado

O POPIN mede discurso. Por isso, o teste principal usa `POP_R`, o componente do LALLPI que mede a retórica populista do partido governante. O `POP` geral é reportado como teste secundário, pois combina retórica com políticas econômicas e institucionais.

O POPIN foi agregado por país–ano usando apenas discursos com `dtype=SPEECH` e scores do Qwen v4 já existentes no DuckDB. O LALLPI foi reescalado de `POP_R` (0–1) para 0–100.

## 2. Cobertura

- LALLPI: 524 observações país–ano.
- Sobreposição com POPIN SPEECH: 381 observações em 19 países.
- Variável `POP_R` disponível em 339 observações sobrepostas.
- Variável `POP` disponível em 319 observações sobrepostas.

## 3. Associação com o LALLPI — somente SPEECH

| Amostra | Indicador LALLPI | N | Pearson | Spearman | MAE | Viés POPIN − LALLPI |
|---|---|---:|---:|---:|---:|---:|
| Todos os anos-país disponíveis | `POP_R` | 339 | 0,519 | 0,491 | 24,88 | −13,59 |
| Todos os anos-país disponíveis | `POP` | 319 | 0,635 | 0,491 | 17,73 | +15,26 |
| Pelo menos 5 discursos | `POP_R` | 216 | 0,712 | 0,693 | 26,41 | −18,21 |
| Pelo menos 5 discursos | `POP` | 197 | 0,868 | 0,707 | 14,27 | +11,60 |
| Pelo menos 20 discursos | `POP_R` | 176 | 0,745 | 0,716 | 26,03 | −17,90 |
| Pelo menos 20 discursos | `POP` | 168 | 0,902 | 0,752 | 13,96 | +11,16 |

## 4. Robustez usando todos os tipos de discurso

Como checagem, também foi calculada a média por país–ano incluindo todos os tipos válidos de discurso, não apenas `SPEECH`.

| Amostra | Indicador | N | Pearson | Spearman | MAE | Viés POPIN − LALLPI |
|---|---|---:|---:|---:|---:|---:|
| Todos os anos-país disponíveis | `POP_R` | 349 | 0,451 | 0,403 | 25,84 | −15,03 |
| Todos os anos-país disponíveis | `POP` | 329 | 0,557 | 0,391 | 17,44 | +13,57 |
| Pelo menos 20 discursos | `POP_R` | 186 | 0,663 | 0,586 | 27,36 | −19,92 |
| Pelo menos 20 discursos | `POP` | 177 | 0,826 | 0,605 | 13,64 | +8,88 |

## 5. Interpretação

1. A associação do POPIN com `POP_R` é moderada no conjunto completo e fica forte quando há pelo menos 20 discursos por país–ano. Isso confirma que o tamanho da amostra textual é central para a estabilidade do indicador.
2. O `POP` composto apresenta associação mais alta que `POP_R`, especialmente nos anos-país com mais discursos. Isso é substantivamente plausível, mas não deve ser chamado de validação direta do discurso: o `POP` inclui dimensões de política econômica e institucional.
3. O POPIN fica, em média, abaixo do `POP_R` reescalado e acima do `POP` composto. Isso mostra que as escalas não são diretamente intercambiáveis; a correlação ordinal é mais informativa que a igualdade dos níveis absolutos.
4. O resultado apoia validade convergente moderada para o POPIN, sobretudo no recorte SPEECH com pelo menos 20 observações por país–ano.

## 6. Limitações

- LALLPI é um indicador de regime/país–ano, não uma codificação discurso a discurso.
- `POP_R` é retórica do partido governante, enquanto o POPIN agrega discursos do chefe do Executivo; as unidades não são idênticas.
- A cobertura comum é de 19 países, não dos 22 países do LALLPI.
- O teste usa o Qwen v4 já calculado para toda a base; não é uma comparação de modelos.
- Os resultados com `POP` são validade externa secundária, pois o índice combina retórica e política implementada.

## Fonte e dados locais

- Página do projeto: https://lallpi.netlify.app/
- Dataset v2025.1: https://lallpi.netlify.app/data/2025/output/index_2025.csv
- DOI informado pelos autores: https://doi.org/10.7910/DVN/KEJ9VF
- Crosswalk local: `data/lallpi_2025/lallpi_popin_country_year.csv`
