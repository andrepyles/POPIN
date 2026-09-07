# POPIN v4 — análise final de modelos, dimensões e especificações

Data: 2026-08-23  
Base: 45.492 discursos válidos; análises substantivas principais restritas a `dtype=SPEECH`.

## 1. Decisão executiva

Especificação recomendada para o paper:

**DeepSeek V4 Flash 0731 + prompt v4 + chunked de 800 palavras, sem sobreposição, score final como média das seis dimensões.**

Essa escolha prioriza validade convergente ordinal, estabilidade ao prompt e cobertura integral. O Luna full deve permanecer como análise de robustez importante, porque produz a escala mais próxima do GPD em nível absoluto e na distribuição por líder–mandato. Ele não deve ser escolhido como especificação principal antes de uma sensibilidade ao prompt própria.

O índice de seis dimensões deve ser mantido como resultado principal. A exclusão de dimensões observada depois dos resultados seria uma decisão pós-hoc. Variantes com quatro dimensões serão reportadas como robustez exploratória.

## 2. Cenários efetivamente disponíveis

| Cenário | Cobertura | Tipo | Observação |
|---|---:|---|---|
| Qwen v4 | 45.492 | chunked 800 | execução integral |
| DeepSeek v4 | 45.492 | chunked 800 | execução integral |
| DeepSeek v4 neutral | 900 | chunked 800 | sensibilidade pareada ao prompt |
| Qwen v4 neutral | 900 | chunked 800 | sensibilidade; baseline Qwen vem da execução integral |
| Luna full | 45.492 | não chunked | união de partes complementares |
| Luna chunked | 45.492 | chunked 800 | união de partes complementares |
| GLM 4.7 Flash | 1.000 | chunked 800 | somente piloto; não elegível para especificação final |

As duas versões do Luna cobrem os mesmos 45.492 discursos quando as partes são unidas. A comparação full versus chunked na base completa tem 45.492 pares: Spearman = 0,942, MAE = 7,261 e o chunked produz score menor em 69,2% dos discursos. O antigo pareamento de 19 casos era apenas um piloto não coincidente e não deve ser usado.

## 3. Diagnóstico das dimensões

Os números abaixo são para discursos `SPEECH` da base integral. `zero` é a proporção exata de score zero; `rho-final` é correlação com a média das seis dimensões e não constitui evidência independente, pois o score final contém a própria dimensão.

| Modelo | Dimensão | Média | DP | Zero | P95 |
|---|---|---:|---:|---:|---:|
| Qwen | people | 51,20 | 25,77 | 0,7% | 87,38 |
| Qwen | anti | 36,60 | 25,48 | 1,7% | 83,59 |
| Qwen | moral | 44,49 | 24,25 | 1,8% | 82,27 |
| Qwen | sovereignty | 36,20 | 20,92 | 1,9% | 73,53 |
| Qwen | exclusion | 12,72 | 10,17 | 3,5% | 31,91 |
| Qwen | crisis | 42,98 | 22,43 | 1,8% | 81,57 |
| DeepSeek | people | 22,27 | 18,72 | 14,7% | 58,42 |
| DeepSeek | anti | 14,83 | 18,88 | 36,7% | 57,20 |
| DeepSeek | moral | 13,15 | 16,48 | 34,9% | 48,98 |
| DeepSeek | sovereignty | 9,55 | 13,42 | 37,0% | 39,76 |
| DeepSeek | exclusion | 3,80 | 6,70 | 55,0% | 16,64 |
| DeepSeek | crisis | 12,87 | 14,48 | 26,8% | 43,60 |
| Luna full | people | 36,74 | 27,02 | 5,2% | 82,47 |
| Luna full | anti | 20,44 | 28,39 | 37,6% | 86,27 |
| Luna full | moral | 19,88 | 27,82 | 33,1% | 84,62 |
| Luna full | sovereignty | 24,19 | 23,72 | 6,0% | 76,83 |
| Luna full | exclusion | 7,42 | 14,34 | 42,1% | 38,91 |
| Luna full | crisis | 25,79 | 25,58 | 13,7% | 79,26 |
| Luna chunked | people | 28,32 | 21,53 | 5,2% | 72,84 |
| Luna chunked | anti | 12,45 | 18,54 | 35,5% | 55,66 |
| Luna chunked | moral | 12,46 | 18,45 | 30,9% | 55,90 |
| Luna chunked | sovereignty | 16,52 | 16,47 | 6,4% | 54,16 |
| Luna chunked | exclusion | 3,87 | 7,68 | 41,3% | 18,73 |
| Luna chunked | crisis | 17,18 | 17,77 | 13,6% | 56,09 |

Diagnóstico: todas as dimensões variam, mas não são igualmente informativas. `exclusion` é rara e dependente de contexto; `crisis` também é contextual. `anti` e `moral` são altamente redundantes: correlação = 0,946 no DeepSeek e 0,976 no Luna full. Isso recomenda tratá-las como dimensões distintas teoricamente, mas discutir a redundância empiricamente.

## 4. Validade convergente com GPD

Unidade: 94 líder–mandato com correspondência POPIN revisada e pelo menos um discurso `SPEECH` na janela do mandato. O GPD foi reescalado de 0–2 para 0–100.

| Modelo | Pearson | Spearman | MAE | RMSE | Viés POPIN−GPD |
|---|---:|---:|---:|---:|---:|
| Qwen v4 | 0,678 | 0,480 | 22,234 | 24,903 | +16,285 |
| DeepSeek v4 | 0,752 | **0,579** | 13,693 | 20,854 | −8,413 |
| Luna full | **0,755** | 0,482 | 13,385 | **16,750** | **+0,405** |
| Luna chunked | **0,766** | 0,563 | **13,464** | 19,429 | −6,041 |

Interpretação: Luna full é superior em nível absoluto, RMSE e viés. DeepSeek é superior em ordenação; Luna chunked fica próximo. Os intervalos bootstrap de Spearman são amplos: DeepSeek v4 [0,415; 0,711], Luna full [0,286; 0,638] e Luna chunked [0,388; 0,695]. Portanto, não se deve declarar uma diferença definitiva entre DeepSeek e Luna chunked apenas por Spearman.

### Desempenho por dimensão contra GPD

Spearman por dimensão, na mesma unidade líder–mandato:

| Dimensão | Qwen | DeepSeek | Luna full | Luna chunked |
|---|---:|---:|---:|---:|
| people | 0,400 | 0,538 | 0,429 | 0,520 |
| anti | 0,545 | 0,610 | 0,573 | **0,639** |
| moral | 0,456 | 0,602 | 0,581 | **0,631** |
| sovereignty | 0,470 | 0,595 | 0,454 | 0,539 |
| exclusion | 0,495 | 0,512 | 0,507 | 0,537 |
| crisis | 0,431 | 0,467 | 0,348 | 0,350 |

`crisis` é a dimensão menos associada ao GPD em todos os modelos; `anti` e `moral` são as mais consistentes nos modelos Luna e DeepSeek.

## 5. Validade convergente com LALLPI

O teste principal usa `POP_R`, por ser o componente retórico do LALLPI. `POP` é apresentado como teste secundário, pois inclui componentes institucionais e econômicos.

| Modelo | POP_R Spearman | POP_R MAE | POP Spearman | POP MAE |
|---|---:|---:|---:|---:|
| Qwen v4 | 0,491 | 24,879 | 0,491 | 17,733 |
| DeepSeek v4 | **0,563** | 38,452 | **0,562** | 11,846 |
| Luna full | 0,516 | 30,857 | 0,488 | **10,397** |
| Luna chunked | 0,520 | 36,308 | 0,509 | 11,260 |

O LALLPI confirma o padrão: DeepSeek ordena melhor a retórica populista, enquanto Luna full fica mais próximo em nível do índice composto `POP`. As escalas não são intercambiáveis; a correlação ordinal é o resultado mais defensável.

## 6. Sensibilidade ao prompt

| Modelo | Spearman v4/neutral | MAE | Diferença média neutral−v4 | Diferença >5 |
|---|---:|---:|---:|---:|
| DeepSeek | **0,940** | **3,525** | −3,221 | 26,7% |
| Qwen | 0,965 | 8,603 | −8,208 | 67,1% |
| Luna | não executado | — | — | — |

O Qwen não permite uma leitura pura porque o baseline v4 foi executado em runtime diferente. O DeepSeek é a única configuração com estabilidade de prompt demonstrada de forma limpa. O Luna ainda precisa de `v4 neutral` nos mesmos 900 discursos para ser considerado plenamente validado.

## 7. Variantes teóricas do índice

As variantes abaixo são análises exploratórias; não substituem o v4 predefinido.

| Modelo | Índice | GPD Spearman | LALLPI POP_R Spearman |
|---|---|---:|---:|
| DeepSeek | all6 | 0,579 | 0,563 |
| DeepSeek | core3 | 0,600 | **0,588** |
| DeepSeek | core3 + moral | **0,608** | 0,586 |
| Luna full | all6 | 0,482 | 0,516 |
| Luna full | core3 | 0,485 | 0,529 |
| Luna full | core3 + moral | **0,507** | **0,542** |
| Luna chunked | all6 | 0,563 | 0,520 |
| Luna chunked | core3 | 0,585 | 0,540 |
| Luna chunked | core3 + moral | **0,599** | **0,548** |

Esses resultados sugerem que `exclusion` e `crisis` reduzem a validade convergente, mas retirar dimensões após observar GPD/LALLPI produziria overfitting. A decisão academicamente correta é manter o índice v4 de seis dimensões como principal e apresentar essas variantes como robustez.

## 8. Distribuição por líder–mandato

Distância L1 entre a distribuição do modelo e a distribuição GPD, nas 94 unidades:

| Modelo | Distância L1 | Média do score |
|---|---:|---:|
| **Luna full** | **2,636** | **21,429** |
| Luna chunked | 3,182 | 14,984 |
| DeepSeek v4 | 3,455 | 12,612 |
| Qwen v4 | 6,364 | 37,309 |

Esse é o principal argumento a favor do Luna full: ele reproduz melhor a escala e a cauda do GPD. Porém, a distribuição marginal não informa se os líderes corretos estão sendo ordenados corretamente; por isso, deve ser reportada junto com Spearman, MAE e RMSE.

## 9. Decisão final

### Especificação principal recomendada

- Modelo: **DeepSeek V4 Flash 0731**.
- Prompt: **v4**.
- Chunker: **800 palavras, sem sobreposição**.
- Score: média aritmética das seis dimensões.
- Unidade substantiva: médias por líder, líder–mandato e país–ano, sempre acompanhadas de `n` e erro-padrão.

### Justificativa

DeepSeek é a única alternativa que simultaneamente apresenta validade ordinal forte, melhor desempenho no `POP_R` do LALLPI e estabilidade limpa ao prompt. A compressão de escala deve ser tratada como limitação de calibração do modelo, não corrigida post-hoc no resultado principal.

### Como tratar o Luna full

O Luna full deve ser mantido como robustez principal e discutido explicitamente: ele tem melhor escala, menor RMSE contra GPD, viés praticamente nulo e menor distância distributiva. Entretanto, sua Spearman com GPD é menor e ainda não há teste de sensibilidade ao prompt. Se a prioridade substantiva do paper for a comparabilidade da escala absoluta sem calibração, Luna full é uma alternativa plausível; não é, porém, a escolha mais segura para a especificação principal com os testes hoje disponíveis.

### O que não fazer

- Não remover `exclusion` ou `crisis` do score principal com base apenas nesses resultados exploratórios.
- Não tratar GPD ou LALLPI como padrão-ouro perfeito.
- Não comparar médias brutas entre modelos como se estivessem na mesma escala.
- Não chamar a validade de definitiva: a evidência é de validade convergente moderada, com dependência da unidade de agregação.

### Último teste antes de congelar a publicação

Executar Luna `v4 neutral` nos mesmos 900 discursos e repetir a tabela de sensibilidade ao prompt. Se o Luna full permanecer estável, a decisão entre DeepSeek e Luna poderá ser apresentada como uma escolha explícita entre **validade ordinal/robustez** e **calibração/legibilidade de escala**, em vez de uma escolha arbitrária de modelo.
