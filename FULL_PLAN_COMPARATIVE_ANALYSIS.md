# POPIN v4 — análise integrada do plano de validação

Data: 2026-08-15  
Modelos: Qwen v4 local, Qwen neutro via OpenRouter, DeepSeek V4 Flash 0731 e DeepSeek neutro.  
Amostra comparativa: 900 discursos congelados.

## 1. Desenho efetivamente estimado

| Cenário | Fonte | Prompt | N |
|---|---|---|---:|
| Qwen v4 | DuckDB, execução local | v4 | 900 |
| Qwen neutro | OpenRouter, checkpoint Qwen3-30B-A3B-Instruct-2507 | neutro | 900 |
| DeepSeek v4 | OpenRouter | v4 | 900 |
| DeepSeek neutro | OpenRouter | neutro | 900 |

Todos os quatro arquivos têm 900 discursos válidos. A comparação Qwen v4–Qwen neutro contém uma diferença de runtime, pois o primeiro é local e o segundo foi executado no OpenRouter. A comparação entre os dois prompts do DeepSeek é o teste mais limpo de sensibilidade ao prompt.

## 2. GPD — comparação entre modelos e prompts

Validação no nível de líder–mandato, usando os 64 termos do teste bloqueado e 499 discursos da amostra. O `totalaverage` do GPD foi reescalado de 0–2 para 0–100. A correlação de Spearman usa postos médios para empates.

| Cenário | N termos | Spearman | Pearson | MAE | RMSE | Viés POPIN − GPD |
|---|---:|---:|---:|---:|---:|---:|
| Qwen v4 local | 64 | 0,399 | 0,528 | 24,09 | 27,33 | +15,16 |
| Qwen neutro | 64 | 0,401 | 0,556 | 19,33 | 23,26 | +6,12 |
| DeepSeek v4 | 64 | **0,543** | **0,684** | **15,48** | 23,78 | −9,53 |
| DeepSeek neutro | 64 | 0,527 | 0,669 | 16,30 | 25,76 | −12,55 |

Robustez restringindo a termos com pelo menos 5 discursos na amostra (45 termos):

| Cenário | Spearman | Pearson | MAE |
|---|---:|---:|---:|
| Qwen v4 local | 0,548 | 0,619 | 22,67 |
| Qwen neutro | 0,559 | 0,636 | 18,89 |
| DeepSeek v4 | **0,614** | **0,704** | 17,73 |
| DeepSeek neutro | 0,604 | 0,688 | 18,95 |

## 3. Sensibilidade ao prompt

| Modelo | Pearson entre prompts | Spearman entre prompts | MAE | Viés do neutro − v4 |
|---|---:|---:|---:|---:|
| DeepSeek | 0,966 | **0,940** | 3,52 | −3,22 |
| Qwen* | 0,954 | **0,965** | 8,60 | −8,21 |

\* A comparação Qwen inclui a diferença entre execução local e OpenRouter. No DeepSeek, o prompt neutro reduz o nível dos scores, mas preserva fortemente a ordenação dos discursos.

## 4. LALLPI — comparação exploratória entre modelos e prompts

O teste principal usa `POP_R`, a retórica populista do partido governante, reescalada para 0–100. `POP` é reportado como critério secundário, pois inclui política econômica e institucional. Na amostra de 900 discursos, há 299 células país–ano comuns; `POP_R` está disponível em 263 e `POP` em 248.

### 4.1 `POP_R` — retórica populista

| Cenário | N país–ano | Spearman | Pearson | MAE | Viés POPIN − LALLPI |
|---|---:|---:|---:|---:|---:|
| Qwen v4 local | 263 | 0,331 | 0,361 | 26,01 | −13,62 |
| Qwen neutro | 263 | 0,277 | 0,343 | 29,41 | −22,48 |
| DeepSeek v4 | 263 | **0,365** | **0,433** | 37,85 | −36,85 |
| DeepSeek neutro | 263 | 0,348 | 0,408 | 40,54 | −39,87 |

### 4.2 `POP` — índice composto de populismo ativo

| Cenário | N país–ano | Spearman | Pearson | MAE | Viés POPIN − LALLPI |
|---|---:|---:|---:|---:|---:|
| Qwen v4 local | 248 | 0,387 | 0,459 | 20,54 | +15,28 |
| Qwen neutro | 248 | 0,329 | 0,454 | 16,29 | +6,37 |
| DeepSeek v4 | 248 | **0,408** | **0,511** | **12,90** | −8,28 |
| DeepSeek neutro | 248 | 0,400 | 0,489 | 13,85 | −11,19 |

Esses resultados do LALLPI são exploratórios para a comparação entre modelos: apenas 33 células país–ano têm pelo menos 5 discursos na amostra, e nenhuma tem pelo menos 20. Por isso, não devem substituir a validação maior do Qwen feita sobre toda a base.

## 5. Validação maior disponível sem novas chamadas de API

Usando o Qwen v4 em toda a base POPIN e agregando apenas `SPEECH` por país–ano:

| Amostra | Indicador | N | Spearman | Pearson | MAE |
|---|---|---:|---:|---:|---:|
| Todos os anos-país disponíveis | `POP_R` | 339 | 0,491 | 0,519 | 24,88 |
| Pelo menos 20 discursos | `POP_R` | 176 | **0,716** | **0,745** | 26,03 |
| Todos os anos-país disponíveis | `POP` | 319 | 0,491 | 0,635 | 17,73 |
| Pelo menos 20 discursos | `POP` | 168 | **0,752** | **0,902** | 13,96 |

Para o GPD, a validação do Qwen em toda a base, nos 64 termos do teste bloqueado, produziu Spearman 0,410 e Pearson 0,669; restringindo a termos com pelo menos 20 discursos, Spearman sobe para 0,647 e Pearson para 0,846.

## 6. Síntese do plano

1. **Melhor desempenho na comparação controlada:** DeepSeek v4, por apresentar a maior associação com o GPD e o menor MAE.
2. **Robustez ao prompt:** DeepSeek v4 e neutro mantêm alta concordância ordinal (Spearman 0,940), embora o neutro produza scores menores.
3. **Validação maior do indicador:** o Qwen v4 na base inteira apresenta associação moderada a forte com o LALLPI quando há pelo menos 20 discursos por país–ano.
4. **Interpretação substantiva:** o POPIN parece ordenar adequadamente unidades mais e menos populistas, mas os níveis absolutos não são diretamente comparáveis entre modelos ou bases.
5. **Decisão recomendada:** usar o DeepSeek v4 como especificação alternativa mais forte na análise de sensibilidade; manter o Qwen v4 como instrumento principal da base completa, por razões de custo, tempo e cobertura.

## 7. Limitações que devem entrar no paper

- GPD e LALLPI operam em níveis diferentes: líder–mandato versus país–ano.
- LALLPI não é uma validação discurso a discurso.
- `POP_R` é mais próximo do construto do POPIN que `POP`; o índice `POP` inclui políticas.
- A comparação Qwen v4–Qwen neutro mistura efeito de prompt e runtime.
- A comparação LALLPI entre os modelos usa a amostra de 900 e tem poucas células país–ano com muitos discursos.
- Os resultados devem ser apresentados como validade convergente e robustez, não como prova de verdade observada.
