# POPIN v4 — análise comparativa preliminar

Data: 2026-08-15  
Amostra: 900 discursos da amostra congelada; 64 termos-líder no teste bloqueado do GPD (499 discursos da amostra).

## 1. Cenários comparados

| Cenário | Execução | N | Falhas |
|---|---|---:|---:|
| Qwen v4 | Qwen local, resultado baseline do DuckDB | 900 | 0 |
| Qwen neutro | `qwen/qwen3-30b-a3b-instruct-2507` via OpenRouter | 900 | 0 |
| DeepSeek v4 | `deepseek/deepseek-v4-flash-0731` via OpenRouter | 900 | 0 |
| DeepSeek neutro | `deepseek/deepseek-v4-flash-0731` via OpenRouter | 900 | 0 |

O prompt v4 é o prompt congelado do `04_score.py`. O prompt neutro remove apenas o bloco de calibração regional. A comparação Qwen v4–Qwen neutro deve ser interpretada com cautela, pois o primeiro foi executado localmente e o segundo via OpenRouter. A comparação entre DeepSeek v4 e DeepSeek neutro é mais limpa.

## 2. Distribuição dos scores na amostra

| Cenário | Média | DP | Mediana | Mínimo | Máximo | Score ≥50 |
|---|---:|---:|---:|---:|---:|---:|
| Qwen v4 local | 38,09 | 21,43 | 37,20 | 0,00 | 87,11 | 31,0% |
| Qwen neutro | 29,88 | 22,16 | 24,07 | 0,00 | 89,44 | 19,8% |
| DeepSeek v4 | 14,52 | 15,62 | 8,04 | 0,00 | 70,22 | 4,1% |
| DeepSeek neutro | 11,30 | 13,98 | 5,17 | 0,00 | 64,02 | 2,2% |

Há uma diferença clara de calibração entre os modelos: o Qwen produz scores mais altos, enquanto o DeepSeek é mais conservador.

## 3. Concordância com o Qwen v4 baseline

| Cenário | Pearson | Spearman | MAE | Viés em relação ao Qwen |
|---|---:|---:|---:|---:|
| Qwen neutro | 0,954 | 0,965 | 8,60 | −8,21 |
| DeepSeek v4 | 0,875 | 0,901 | 23,57 | −23,57 |
| DeepSeek neutro | 0,837 | 0,883 | 26,79 | −26,79 |

O DeepSeek preserva bastante a ordenação relativa dos discursos, mas opera em uma escala substancialmente mais baixa que o Qwen.

## 4. Sensibilidade ao prompt

| Modelo | Pearson entre prompts | Spearman entre prompts | MAE | Viés do neutro − v4 | Diferença absoluta >5 pontos |
|---|---:|---:|---:|---:|---:|
| DeepSeek | 0,966 | 0,935 | 3,52 | −3,22 | 26,7% |
| Qwen* | 0,954 | 0,965 | 8,60 | −8,21 | 67,1% |

\* Para o Qwen, essa diferença também contém o efeito do runtime local versus OpenRouter; portanto, não é uma estimativa pura da sensibilidade ao prompt.

O DeepSeek apresenta boa estabilidade ordinal: o prompt neutro reduz os scores, mas altera pouco a ordenação geral.

## 5. Validação convergente com o GPD

Agregação por termo-líder usando os 499 discursos da amostra que pertencem aos 64 termos do teste bloqueado. O alvo GPD foi reescalado de 0–2 para 0–100.

| Cenário | Spearman | Pearson | MAE | RMSE | Viés POPIN − GPD |
|---|---:|---:|---:|---:|---:|
| Qwen v4 local | 0,407 | 0,528 | 24,09 | 27,33 | +15,16 |
| Qwen neutro | 0,408 | 0,556 | 19,33 | 23,26 | +6,12 |
| DeepSeek v4 | **0,550** | **0,684** | **15,48** | 23,78 | −9,53 |
| DeepSeek neutro | 0,535 | 0,669 | 16,30 | 25,76 | −12,55 |

Intervalos bootstrap de 95% para Spearman:

- Qwen v4 local: [0,140; 0,598]
- Qwen neutro: [0,140; 0,603]
- DeepSeek v4: [0,321; 0,702]
- DeepSeek neutro: [0,306; 0,695]

## 6. Leitura substantiva

1. **Resultado provisório:** o DeepSeek v4 apresenta o melhor desempenho convergente com o GPD nesta comparação: maior Spearman e Pearson e menor MAE entre os quatro cenários.
2. O DeepSeek subestima o nível absoluto do GPD em aproximadamente 9,5 pontos, enquanto o Qwen v4 superestima em aproximadamente 15,2 pontos.
3. O prompt neutro melhora a calibração do Qwen, reduzindo o viés e o MAE, mas essa conclusão é parcialmente confundida pela diferença de runtime.
4. No DeepSeek, a mudança de prompt é relativamente pequena: MAE de 3,52 pontos e Spearman de 0,935 entre as duas versões.
5. Os resultados de GPD desta tabela não devem ser comparados diretamente ao baseline anterior calculado sobre todos os discursos do banco. Aqui usamos somente os 900 discursos congelados e a agregação amostral nos 64 termos bloqueados.

## 7. Conclusão para decisão

O resultado atual favorece **DeepSeek v4** como instrumento alternativo para o POPIN, sujeito a uma análise de subgrupos, testes de sensibilidade por número de discursos por termo e checagem de outliers. A evidência ainda deve ser descrita como **validade convergente moderada**, não como validação definitiva contra uma verdade observada.
