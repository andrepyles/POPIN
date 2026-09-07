# POPIN v4 — piloto da etapa 2 com 10 discursos

Data: 2026-08-16  
Objetivo: comparar modelo e prompt antes de uma nova execução integral.  
Escopo: somente scoring; não houve nova classificação de tipo textual.

## Desenho

Foram selecionados 10 discursos comuns aos outputs já existentes, estratificados
por cinco faixas do score baseline. Cada caso foi comparado em:

- Qwen com prompt v4;
- Qwen com prompt neutral;
- DeepSeek com prompt v4;
- DeepSeek com prompt neutral.

O piloto reutiliza outputs da etapa 2 já calculados para a amostra congelada de
900 discursos. Não foram adicionados exemplos ao prompt nem feita nova
classificação dos discursos.

## Scores finais por discurso

| Líder | País–ano | Baseline | Qwen v4 | Qwen neutral | DeepSeek v4 | DeepSeek neutral |
|---|---|---:|---:|---:|---:|---:|
| Óscar Berger | GTM–2007 | 9,04 | 9,04 | 8,86 | 1,62 | 0,00 |
| Iván Duque | COL–2019 | 13,69 | 13,69 | 11,39 | 6,18 | 3,12 |
| Laurentino Cortizo | PAN–2022 | 26,43 | 26,43 | 19,87 | 2,06 | 3,06 |
| Daniel Ortega | NIC–2016 | 33,01 | 33,01 | 17,63 | 6,85 | 5,17 |
| Andrés Manuel López Obrador | MEX–2021 | 46,47 | 46,47 | 40,03 | 23,79 | 21,23 |
| Lula da Silva | BRA–2004 | 51,75 | 51,75 | 39,37 | 16,49 | 10,20 |
| Rafael Correa | ECU–2015 | 64,55 | 64,55 | 69,40 | 38,37 | 37,83 |
| Fidel Castro | CUB–2000 | 70,46 | 70,46 | 73,05 | 52,07 | 45,23 |
| Fidel Castro | CUB–2007 | 80,80 | 80,80 | 83,36 | 40,95 | 33,51 |
| Jair Bolsonaro | BRA–2019 | 82,66 | 82,66 | 81,78 | 58,19 | 44,23 |

## Distribuição no piloto

| Configuração | Média | Mediana | DP | Mínimo | Máximo |
|---|---:|---:|---:|---:|---:|
| Qwen v4 | 47,89 | 49,11 | 26,78 | 9,04 | 82,66 |
| Qwen neutral | 44,47 | 39,70 | 29,96 | 8,86 | 83,36 |
| DeepSeek v4 | 24,66 | 20,14 | 21,34 | 1,62 | 58,19 |
| DeepSeek neutral | 20,36 | 15,71 | 18,29 | 0,00 | 45,23 |

## Sensibilidade ao prompt

| Modelo | Diferença média neutral − v4 | Pearson | Spearman | MAE entre prompts |
|---|---:|---:|---:|---:|
| Qwen | −3,41 | 0,979 | 0,964 | 5,41 |
| DeepSeek | −4,30 | 0,987 | 0,976 | 4,50 |

O prompt neutral reduz os níveis médios dos dois modelos, mas preserva quase
completamente a ordenação. Não há evidência, neste piloto, de que a remoção do
escopo regional seja uma solução para a escala comprimida.

## Médias dimensionais

| Configuração | Povo | Antielite | Moral | Soberania | Exclusão | Crise |
|---|---:|---:|---:|---:|---:|---:|
| Qwen v4 | 59,53 | 51,51 | 54,19 | 44,93 | 24,24 | 52,91 |
| Qwen neutral | 51,64 | 45,35 | 49,62 | 41,42 | 28,13 | 50,68 |
| DeepSeek v4 | 34,07 | 31,52 | 29,21 | 16,67 | 13,48 | 22,99 |
| DeepSeek neutral | 25,65 | 28,58 | 25,24 | 12,16 | 11,57 | 18,94 |

O padrão de compressão do DeepSeek aparece em quase todos os eixos, sobretudo
em soberania popular e crise. Portanto, o problema não está apenas na média
final: é uma diferença de uso da escala em cada dimensão.

## Decisão operacional

1. Não alterar o constructo nem remover eixos.
2. Não inserir exemplos few-shot novos no prompt.
3. Não mudar a classificação textual.
4. O próximo teste deve comparar uma versão v4 com âncoras textuais mínimas de
   escala, sem exemplos de discursos, contra o v4 atual.
5. A versão escolhida deve ser definida por validade no desenvolvimento, não por
   produzir números visualmente maiores.
6. Depois disso, executar a base integral com o mesmo prompt para Qwen e
   DeepSeek, preservando os outputs atuais como baseline.

## Luna

Os arquivos disponíveis do Luna têm apenas 20 linhas por prompt, com somente 7
resultados válidos em cada configuração e 13–14 erros. Portanto, não há 10
casos válidos comparáveis para incluí-lo neste piloto. Ele não deve orientar a
decisão metodológica até que a execução seja operacionalmente estável.

## Teste de ajuste de escala no piloto

Foram testadas duas transformações sobre os scores já calculados:

1. **Calibração GPD:** transformação linear estimada exclusivamente nos 30
   termos de desenvolvimento:

   ```text
   Qwen = 1,3030 × score − 27,9154
   DeepSeek = 1,7405 × score − 3,4563
   ```

   Os valores são limitados ao intervalo 0–100.

2. **Percentil empírico:** posição relativa do score dentro dos 900 discursos.
   Essa transformação melhora a leitura visual, mas não representa uma escala
   substantiva comparável entre bases.

### Médias no piloto

| Configuração | Média bruta | Média calibrada GPD | Média percentil |
|---|---:|---:|---:|
| Qwen v4 | 47,89 | 37,10 | 61,30 |
| Qwen neutral | 44,47 | 33,68 | 64,67 |
| DeepSeek v4 | 24,66 | 39,52 | 64,97 |
| DeepSeek neutral | 20,36 | 32,32 | 65,81 |

### Exemplos substantivos — DeepSeek v4

| Líder–ano | Bruto | Calibrado GPD | Percentil |
|---|---:|---:|---:|
| Óscar Berger–2007 | 1,62 | 0,00 | 17,58 |
| López Obrador–2021 | 23,79 | 37,95 | 76,64 |
| Correa–2015 | 38,37 | 63,33 | 88,43 |
| Fidel Castro–2000 | 52,07 | 87,17 | 96,89 |
| Bolsonaro–2019 | 58,19 | 97,82 | 99,11 |

### Comparação nos 8 casos do piloto com referência GPD

| Configuração | Viés bruto | Viés calibrado | MAE bruto | MAE calibrado |
|---|---:|---:|---:|---:|
| Qwen v4 | +12,67 | +0,44 | 20,26 | 20,01 |
| Qwen neutral | +7,76 | −4,68 | 19,59 | 20,82 |
| DeepSeek v4 | −9,09 | +1,75 | 20,33 | 21,47 |
| DeepSeek neutral | −12,68 | −4,15 | 18,26 | **17,22** |

O piloto é pequeno demais para escolher definitivamente entre prompts, mas já
permite três conclusões:

- a calibração GPD resolve o problema de subescala e torna scores como 38 ou 52
  mais legíveis, sem inventar uma nova dimensão;
- o percentil é adequado para o site como indicador relativo, mas não deve ser o
  score principal do paper;
- não há justificativa para multiplicar o DeepSeek por um fator arbitrário.

## Decisão provisória

Para a próxima rodada, manter os seis eixos e o prompt v4 sem novos exemplos.
Executar a base integral preservando o score bruto e gerar uma coluna separada
`score_gpd_calibrated`, estimada apenas no desenvolvimento. No site, exibir
também o percentil como medida de posição relativa. A decisão final deve ser
confirmada com a nova execução integral e o teste bloqueado do GPD.

## Piloto novo: v4 com âncoras e sem few-shot

Foi executado um novo piloto real, com os mesmos 10 discursos, Qwen e
DeepSeek, comparando o prompt v4 atual com uma variante que mantém os seis
eixos, inclui apenas âncoras textuais de escala, remove completamente o
exemplo few-shot e não usa calibração posterior.

A primeira saída marcada como `anchored` foi descartada porque ainda continha o
few-shot original. Os resultados abaixo são somente da execução corrigida.

### Distribuição dos scores

| Configuração | Média | Mediana | DP | Mínimo | Máximo |
|---|---:|---:|---:|---:|---:|
| Qwen v4 | 46,79 | 46,27 | 27,50 | 9,13 | 82,20 |
| Qwen v4 sem few-shot | 53,83 | 55,78 | 26,69 | 8,91 | 87,14 |
| DeepSeek v4 | 25,12 | 19,46 | 21,71 | 1,40 | 56,84 |
| DeepSeek v4 sem few-shot | 19,66 | 13,75 | 20,47 | 0,00 | 48,33 |

### Sensibilidade à nova instrução

| Modelo | Diferença sem few-shot − v4 | MAE entre prompts | Pearson | Spearman |
|---|---:|---:|---:|---:|
| Qwen | +7,04 | 7,65 | 0,974 | 0,988 |
| DeepSeek | −5,46 | 5,46 | 0,977 | 0,926 |

### Comparação com o GPD nos 8 casos disponíveis

| Modelo/prompt | Viés | MAE | RMSE | Spearman |
|---|---:|---:|---:|---:|
| Qwen v4 | +11,20 | 20,63 | 26,56 | 0,635 |
| Qwen sem few-shot | +19,29 | 20,79 | 29,11 | 0,635 |
| DeepSeek v4 | −8,85 | 19,02 | 24,06 | 0,647 |
| DeepSeek sem few-shot | −14,68 | 20,82 | 26,13 | **0,687** |

### Decisão do piloto

A remoção do few-shot não é uma solução geral para a escala comprimida. Ela
produz efeitos opostos nos modelos: aumenta os scores do Qwen e reduz os do
DeepSeek. O DeepSeek mantém a melhor escala relativa ao GPD em nível de erro
geral no prompt v4, enquanto a variante sem few-shot melhora apenas a
correlação ordinal neste piloto muito pequeno.

Portanto, não devemos escolher o prompt pela média mais alta. A especificação
mais segura neste momento é manter o prompt v4 atual, preservar os seis eixos e
usar o GPD/LALLPI apenas para validação. O piloto não justifica uma nova
execução integral com o prompt sem few-shot.
