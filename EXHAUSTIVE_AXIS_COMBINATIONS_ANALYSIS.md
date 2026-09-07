# Teste exaustivo das combinações de eixos

## Desenho

Foram avaliadas as 63 combinações não vazias dos seis eixos do v4:

| Código | Eixo |
|---|---|
| P | people_centrism |
| A | anti_elitism |
| M | moral_dichotomy |
| S | popular_sovereignty |
| E | exclusionary_rhetoric |
| C | crisis_rhetoric |

O cálculo foi feito para Qwen, DeepSeek, Luna full e Luna chunked, usando a base não inválida e todos os tipos de texto disponíveis em cada execução. Para evitar que diferenças de cobertura determinassem o vencedor, a comparação conjunta usou o mesmo conjunto de 74 unidades líder–mandato ligadas ao GPD e 262 células país–ano comuns aos quatro cenários.

O ranking composto é a média dos postos em cinco critérios, com pesos iguais: Spearman com GPD, MAE contra GPD, viés absoluto contra GPD, Spearman com LALLPI POP_R e distância L1 da distribuição de scores frente ao GPD. GLM foi mantido apenas como piloto e não entrou no ranking final.

## Melhor combinação estatística

| Posição | Modelo | Eixos | Spearman GPD | MAE GPD | Viés absoluto | Spearman LALLPI POP_R | Distância L1 |
|---:|---|---|---:|---:|---:|---:|---:|
| 1 | Luna chunked | P+A | 0,6294 | 13,3953 | 4,3495 | 0,5906 | 0,3108 |
| 2 | DeepSeek | P+A | 0,6470 | 13,8923 | 6,1563 | 0,6259 | 0,3514 |
| 3 | Luna chunked | P+A+M | 0,6302 | 13,5608 | 6,7298 | 0,5985 | 0,3243 |
| 4 | Luna chunked | P+A+S | 0,6243 | 13,4969 | 5,6389 | 0,5773 | 0,2973 |
| 5 | Luna full | A+S | 0,5604 | 12,3803 | 4,2999 | 0,5906 | 0,2973 |

## Comparação mantendo os seis eixos do v4

Esta é a comparação relevante para a especificação principal do paper, porque não elimina dimensões previamente definidas no constructo.

| Modelo | Spearman GPD | MAE GPD | Viés | Spearman LALLPI POP_R | Distância L1 |
|---|---:|---:|---:|---:|---:|
| Qwen | 0,5447 | 19,5461 | +11,5209 | 0,5193 | 0,6622 |
| DeepSeek | 0,6304 | 15,3731 | −11,3155 | 0,6162 | 0,4054 |
| Luna full | 0,5313 | 13,0928 | −4,2804 | 0,5603 | 0,3378 |
| Luna chunked | 0,5913 | 14,6267 | −9,1571 | 0,5654 | 0,4189 |

## Interpretação

O vencedor puramente preditivo do grid é **Luna chunked com P+A**, mas essa conclusão é exploratória e pós-hoc: ela seleciona simultaneamente o modelo, o modo de processamento e os eixos após observar os resultados. Não deve ser apresentada como se os outros quatro eixos fossem empiricamente inválidos.

Para a versão publicável, a recomendação é:

1. manter os seis eixos do v4 como especificação substantiva;
2. usar **Luna full + v4** como especificação principal quando a prioridade é preservar o texto completo e minimizar erro/viés de escala;
3. reportar DeepSeek e Luna chunked como testes de robustez;
4. apresentar o grid de 63 combinações como análise exploratória/sensibilidade, não como a base para redefinir o constructo.

O teste também mostra que a escolha dos eixos tem efeito grande: a combinação que maximiza a concordância numérica não é necessariamente a mais defensável teoricamente. A cobertura comum foi menor que a base inteira porque a execução Luna full não contém todas as unidades líder–mandato do GPD; isso deve constar no relatório de limitações.
