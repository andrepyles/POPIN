# Qwen baseline — validação GPD v2.1

Data: 2026-08-15  
Modelo: `Qwen/Qwen3-30B-A3B-Instruct-2507`  
Unidade: líder–mandato GPD no teste bloqueado  
Fonte POPIN: média dos discursos `SPEECH` pontuados no intervalo do mandato

## Resultado preliminar

| Amostra | n de mandatos | Spearman | Pearson | MAE | RMSE | Viés POPIN − GPD |
|---|---:|---:|---:|---:|---:|---:|
| Todos os mandatos do teste | 64 | 0.410 | 0.669 | 23.09 | 25.99 | +15.63 |
| Apenas mandatos com ≥20 discursos POPIN | 40 | 0.647 | 0.846 | 20.15 | 22.49 | +10.89 |

Bootstrap de Spearman por líder–mandato, 4.000 reamostragens:

- todos: IC 95% `[0.148, 0.621]`;
- `n ≥ 20`: IC 95% `[0.382, 0.817]`.

## Interpretação operacional

Este é apenas o ponto de partida para comparar modelos. O GPD mede uma amostra
quota de discursos, enquanto o POPIN baseline acima usa todos os discursos
`SPEECH` disponíveis no intervalo do mandato. O resultado não deve ser chamado
de acurácia discurso–a–discurso. O erro-padrão do POPIN e o número de discursos
por mandato serão mantidos nas tabelas de validação.

DeepSeek e Luna serão comparados com exatamente os mesmos 64 mandatos, a mesma
partição e as mesmas métricas. A especificação vencedora será escolhida pelo
Spearman no teste bloqueado, com MAE como desempate.
