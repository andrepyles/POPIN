# POPIN v4 — análise do índice de quatro dimensões

## Especificação testada

O índice foi recalculado como a média de:

- `people_centrism`
- `anti_elitism`
- `popular_sovereignty`
- `crisis_rhetoric`

Foram removidas `moral_dichotomy` e `exclusionary_rhetoric`. A comparação usa os mesmos scores já existentes e não exige nova execução de LLM.

## Comparação com o índice de seis dimensões

| Modelo | GPD Spearman 4D | GPD Spearman 6D | GPD MAE 4D | GPD MAE 6D | LALLPI POP_R Spearman 4D | LALLPI POP_R Spearman 6D |
|---|---:|---:|---:|---:|---:|---:|
| Qwen v4 | 0,472 | 0,480 | 25,005 | 22,234 | 0,481 | 0,491 |
| DeepSeek v4 | 0,580 | 0,579 | **13,425** | 13,693 | 0,559 | **0,563** |
| Luna full | 0,465 | **0,482** | 14,854 | **13,385** | 0,501 | **0,516** |
| Luna chunked | 0,538 | **0,563** | 13,575 | **13,464** | 0,509 | **0,520** |

Unidade GPD: 94 líder–mandato. Unidade LALLPI: 339 país–ano com `POP_R` disponível.

## Distribuição por líder–mandato

Distância L1 em relação ao GPD; menor é melhor:

| Modelo | 4D | 6D |
|---|---:|---:|
| Qwen v4 | 6,273 | 6,364 |
| DeepSeek v4 | **3,182** | 3,455 |
| Luna full | 3,818 | **2,636** |
| Luna chunked | 3,182 | 3,182 |

O índice 4D aumenta as médias por eliminar duas dimensões de baixa escala. As médias passam de 12,61 para 14,92 no DeepSeek, de 21,43 para 26,32 no Luna full e de 14,98 para 18,74 no Luna chunked. Isso melhora a aparência da escala, mas não constitui validação.

## Sensibilidade ao prompt

Na amostra pareada de 900 discursos:

| Modelo | Spearman 4D v4/neutral | MAE 4D | Delta médio neutral−v4 |
|---|---:|---:|---:|
| DeepSeek | 0,941 | 4,071 | −3,722 |
| Qwen | 0,964 | 9,603 | −9,351 |

Não há ainda teste de prompt Luna.

## Conclusão

O índice 4D não melhora de forma consistente a validade. Ele melhora ligeiramente o DeepSeek, mas piora GPD, LALLPI e distribuição do Luna full, que é justamente o modelo com melhor calibração absoluta. Além disso, as quatro dimensões restantes continuam correlacionadas: `people`–`sovereignty` = 0,851 no DeepSeek e 0,902 no Luna full.

Portanto, a versão 4D deve ser tratada como análise de sensibilidade, não como substituição automática do v4 de seis dimensões. A recomendação principal permanece manter as seis dimensões no índice v4, reportando o 4D no apêndice ou como robustez.
