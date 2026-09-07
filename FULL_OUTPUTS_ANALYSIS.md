# POPIN v4 — análise dos outputs completos

Data: 2026-08-16  
Base: 45.492 discursos elegíveis (`dtype != INVALID`)  
Modelos: Qwen local e DeepSeek V4 Flash 0731  
Prompt do DeepSeek: `v4`  
Provedor: Decart

## 1. Resultado principal

Os dois modelos ordenam os discursos de forma bastante semelhante, mas não
produzem scores na mesma escala:

| Medida | Qwen | DeepSeek | Diferença DeepSeek − Qwen |
|---|---:|---:|---:|
| N | 45.492 | 45.492 | — |
| Média | 33,40 | 11,13 | −22,27 |
| Desvio-padrão | 20,81 | 13,08 | −7,73 |
| Pearson | — | — | 0,851 |
| Spearman | — | — | 0,887 |
| MAE entre modelos | — | — | 22,29 |

O DeepSeek gera uma distribuição mais conservadora e comprimida:

| Faixa | Qwen | DeepSeek |
|---|---:|---:|
| Score = 0 | 3,8% | 21,0% |
| Score < 5 | 7,7% | 46,2% |
| Score ≥ 20 | 68,3% | 20,3% |
| Score ≥ 40 | 38,3% | 5,1% |
| Score ≥ 60 | 12,4% | 0,2% |

### Interpretação

O DeepSeek não está produzindo resultados aleatórios: a correlação ordinal
global é alta (`Spearman = 0,887`). Porém, o score não deve ser interpretado
como diretamente intercambiável com o Qwen. O modelo parece exigir uma
calibração de escala se o paper comparar níveis absolutos.

## 2. Diferenças por tipo de texto

| Tipo | N | Média Qwen | Média DeepSeek | Diferença | Spearman |
|---|---:|---:|---:|---:|---:|
| SPEECH | 34.821 | 37,36 | 12,74 | −24,62 | 0,880 |
| INTERVIEW | 2.653 | 30,85 | 9,22 | −21,63 | 0,853 |
| PRESS_RELEASE | 6.675 | 16,02 | 4,18 | −11,84 | 0,784 |
| COMMUNIQUE | 859 | 20,29 | 6,55 | −13,74 | 0,838 |
| DECREE | 322 | 26,33 | 10,20 | −16,13 | 0,915 |
| LETTER | 162 | 24,07 | 8,54 | −15,53 | 0,891 |

O padrão é consistente: o DeepSeek reduz o nível médio em todos os tipos, mas
mantém associação alta com o Qwen. A diferença é maior em `SPEECH`, justamente
o tipo mais importante para a análise substantiva.

## 3. Validação com o GPD — base completa

Usando os mesmos 64 líder–mandato do teste bloqueado, agregando os discursos
`SPEECH` no intervalo temporal do mandato e reescalando o GPD para 0–100:

| Modelo | N termos | Spearman | Pearson | MAE | RMSE | Viés POPIN − GPD |
|---|---:|---:|---:|---:|---:|---:|
| Qwen | 64 | 0,409 | 0,665 | 22,68 | 25,76 | +16,09 |
| DeepSeek | 64 | **0,501** | **0,751** | **15,00** | **22,30** | −9,37 |

Restrição aos 40 mandatos com pelo menos 20 discursos POPIN:

| Modelo | N termos | Spearman | Pearson | MAE | RMSE | Viés POPIN − GPD |
|---|---:|---:|---:|---:|---:|---:|
| Qwen | 40 | 0,644 | 0,837 | 19,50 | **22,06** | +11,61 |
| DeepSeek | 40 | 0,642 | 0,826 | **16,41** | 24,84 | −12,95 |

### Interpretação do GPD

No conjunto completo de termos, o DeepSeek apresenta a melhor associação e o
menor erro absoluto. Entre os mandatos com maior volume textual, os dois
modelos têm Spearman praticamente idêntico; o DeepSeek mantém vantagem em MAE,
mas o Qwen tem RMSE ligeiramente menor.

Isso sugere que:

1. o DeepSeek é melhor calibrado em média contra o GPD;
2. a vantagem do modelo diminui quando a média POPIN é estimada com muitos
   discursos;
3. o tamanho da amostra por mandato é tão importante quanto a escolha do modelo.

## 4. Validação com LALLPI — SPEECH por país–ano

O teste usa `POP_R` como indicador principal e `POP` como indicador secundário.
O LALLPI foi reescalado para 0–100.

### `POP_R` — retórica populista

| Modelo | N país–ano | Spearman | Pearson | MAE | Viés POPIN − LALLPI |
|---|---:|---:|---:|---:|---:|
| Qwen | 339 | 0,491 | 0,519 | 24,88 | −13,59 |
| DeepSeek | 339 | **0,563** | **0,591** | 38,45 | −37,75 |

Com pelo menos 20 discursos por país–ano:

| Modelo | N país–ano | Spearman | Pearson |
|---|---:|---:|---:|
| Qwen | 176 | 0,716 | 0,745 |
| DeepSeek | 176 | **0,746** | **0,755** |

### `POP` — índice composto

| Modelo | N país–ano | Spearman | Pearson | MAE | Viés POPIN − LALLPI |
|---|---:|---:|---:|---:|---:|
| Qwen | 319 | 0,491 | 0,635 | 17,73 | +15,26 |
| DeepSeek | 319 | **0,562** | **0,688** | **11,85** | −8,86 |

Com pelo menos 20 discursos por país–ano:

| Modelo | N país–ano | Spearman | Pearson |
|---|---:|---:|---:|
| Qwen | 168 | 0,752 | 0,902 |
| DeepSeek | 168 | **0,777** | **0,907** |

### Interpretação do LALLPI

O DeepSeek melhora a ordenação dos países e anos em relação ao Qwen tanto para
`POP_R` quanto para `POP`, especialmente quando há pelo menos 20 discursos por
célula. Entretanto, o viés negativo em `POP_R` é grande porque o DeepSeek opera
em uma escala muito mais baixa.

Consequentemente, para o LALLPI:

- DeepSeek é melhor para ordenar unidades país–ano;
- Qwen tem níveis médios mais próximos de `POP_R`;
- a comparação de níveis absolutos exige calibração;
- `POP_R` continua sendo uma validação externa imperfeita, pois é um indicador
  de partido governante, não uma codificação discurso a discurso.

## 5. Conclusão substantiva

Os outputs completos dão suporte à seguinte conclusão:

> O DeepSeek V4 com o prompt v4 produz uma medida altamente correlacionada com
> a medida Qwen, apresenta melhor validade convergente com o GPD no conjunto
> completo de líder–mandato e ordena melhor as unidades país–ano do LALLPI.
> Contudo, seus scores são sistematicamente mais baixos e mais concentrados,
> portanto não podem ser combinados diretamente com os scores Qwen sem
> calibração.

## 6. Recomendação para o paper

Minha recomendação é:

1. usar o **DeepSeek v4 como especificação principal**;
2. usar o Qwen como teste de robustez;
3. apresentar as correlações e os rankings como resultado principal;
4. reportar médias, erros-padrão e níveis absolutos separadamente por modelo;
5. fazer calibração linear usando apenas o conjunto de desenvolvimento do GPD,
   nunca usando o teste bloqueado;
6. calcular os erros-padrão por país–ano ponderando pelo número de discursos.

Não se deve afirmar que o DeepSeek é simplesmente “mais populista” ou “menos
populista” que o Qwen. A diferença principal é de escala e calibração, enquanto
as ordenações são bastante próximas.
