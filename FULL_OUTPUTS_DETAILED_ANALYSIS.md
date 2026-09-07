# POPIN v4 — análise descritiva completa dos outputs

Data: 2026-08-16  
Base: 45.492 discursos elegíveis; 34.821 `SPEECH`  
Modelos: Qwen3-30B-A3B-Instruct-2507 e DeepSeek V4 Flash 0731  
Prompt: v4; provedor DeepSeek: Decart

## 1. Escopo e regra de leitura

As classificações substantivas abaixo usam `SPEECH`, que é a unidade mais
comparável para medir retórica de líderes. Os rankings exigem pelo menos 20
discursos por país ou líder. O erro-padrão (SE) é o desvio-padrão dos discursos
dividido pela raiz do número de discursos; ele mede a incerteza da média
amostral, não a incerteza total do modelo.

Qwen e DeepSeek são apresentados lado a lado, mas não devem ser tratados como
se estivessem na mesma escala substantiva.

## 2. Resultado geral

Na base completa elegível, os dois modelos produzem ordenações semelhantes,
mas níveis muito diferentes:

| Medida | Qwen | DeepSeek | Diferença DeepSeek − Qwen |
|---|---:|---:|---:|
| Discursos | 45.492 | 45.492 | — |
| Média | 33,40 | 11,13 | −22,27 |
| Desvio-padrão | 20,81 | 13,08 | −7,73 |
| Pearson | — | — | 0,851 |
| Spearman | — | — | 0,887 |
| MAE entre modelos | — | — | 22,29 |

Na população `SPEECH`:

| Medida | Qwen | DeepSeek |
|---|---:|---:|
| N | 34.821 | 34.821 |
| Média | 37,36 | 12,74 |
| Mediana | 37,05 | 7,70 |
| Desvio-padrão | 19,60 | 13,48 |
| Score igual a zero | 0,7% | 14,7% |
| Score maior ou igual a 20 | 77,1% | 23,5% |
| Score maior ou igual a 40 | 44,7% | 6,1% |
| Score maior ou igual a 60 | 14,7% | 0,2% |
| Correlação Spearman entre discursos | — | 0,880 |

O DeepSeek é mais conservador e concentra os resultados próximos de zero. A
correlação ordinal alta indica que ele não está produzindo resultados
aleatórios; indica, porém, que os níveis absolutos precisam de calibração.

## 2.1 Tabela comparativa: POPIN versus GPD e LALLPI

Todas as referências foram reescaladas para 0–100. `Bias` é POPIN menos a
referência; MAE e RMSE são erros absolutos e quadráticos na mesma escala. As
médias são calculadas na mesma amostra usada em cada validação.

| Referência e amostra | N | Média referência | Média Qwen | Média DeepSeek | Bias Qwen | Bias DeepSeek | Spearman Qwen / DeepSeek | Pearson Qwen / DeepSeek | MAE Qwen / DeepSeek | RMSE Qwen / DeepSeek |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| GPD; líder–mandato, teste bloqueado | 64 | 22,17 | 38,26 | 12,81 | +16,09 | −9,37 | 0,409 / **0,501** | 0,665 / **0,751** | 22,68 / **15,00** | 25,76 / **22,30** |
| GPD; somente N ≥ 20 discursos | 40 | 25,52 | 37,13 | 12,56 | +11,61 | −12,95 | 0,644 / 0,642 | **0,837** / 0,826 | 19,50 / **16,41** | **22,06** / 24,84 |
| LALLPI `POP_R`; todos os país–ano | 339 | 50,61 | 37,01 | 12,85 | −13,59 | −37,75 | 0,491 / **0,563** | 0,519 / **0,591** | **24,88** / 38,45 | **28,94** / 45,35 |
| LALLPI `POP_R`; somente N ≥ 20 | 176 | 54,37 | 36,46 | 12,56 | −17,90 | −41,81 | 0,716 / **0,746** | 0,745 / **0,755** | **26,03** / 42,04 | **29,68** / 48,99 |
| LALLPI `POP`; todos os país–ano | 319 | 20,99 | 36,25 | 12,13 | +15,26 | −8,86 | 0,491 / **0,562** | 0,635 / **0,688** | 17,73 / **11,85** | 21,42 / **16,75** |
| LALLPI `POP`; somente N ≥ 20 | 168 | 24,65 | 35,81 | 11,99 | +11,16 | −12,66 | 0,752 / **0,777** | 0,902 / **0,907** | 13,96 / **13,78** | 16,35 / **19,39** |

### Leitura da tabela comparativa

- **GPD:** DeepSeek vence no teste completo em todas as métricas principais.
  No subconjunto com N ≥ 20, há empate prático em Spearman; Qwen tem Pearson e
  RMSE ligeiramente melhores, enquanto DeepSeek mantém menor MAE.
- **LALLPI `POP_R`:** DeepSeek ordena melhor, mas seu nível fica muito abaixo
  do indicador de referência. Por isso, Qwen tem MAE e RMSE menores nesse caso.
- **LALLPI `POP`:** DeepSeek vence em correlação e erro absoluto/quadrático no
  conjunto completo. O `POP` é um teste secundário, pois inclui dimensões de
  política econômica e institucional além da retórica.
- **Escala:** Qwen tende a superestimar GPD e `POP`; DeepSeek tende a
  subestimar GPD e LALLPI, sobretudo `POP_R`. Isso é um problema de calibração,
  não evidência de que um modelo esteja simplesmente detectando mais ou menos
  populismo.

## 3. Ranking de países

### 3.1 Ranking principal — DeepSeek

| Rank | País | N | Média | Mediana | SE | IC95% da média | Qwen | SE Qwen |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | Venezuela | 3.526 | 30,72 | 31,45 | 0,26 | 30,22–31,23 | 62,87 | 0,25 |
| 2 | Cuba | 519 | 26,70 | 27,00 | 0,67 | 25,39–28,00 | 51,78 | 0,78 |
| 3 | Equador | 1.625 | 23,95 | 23,30 | 0,39 | 23,18–24,72 | 50,77 | 0,43 |
| 4 | Nicarágua | 800 | 16,17 | 10,94 | 0,52 | 15,15–17,18 | 41,22 | 0,72 |
| 5 | Argentina | 5.512 | 14,88 | 12,21 | 0,17 | 14,56–15,21 | 39,22 | 0,25 |
| 6 | Bolívia | 252 | 14,37 | 9,12 | 0,89 | 12,63–16,11 | 43,46 | 1,14 |
| 7 | Costa Rica | 25 | 11,85 | 9,54 | 1,88 | 8,15–15,54 | 37,09 | 3,00 |
| 8 | Honduras | 803 | 11,78 | 9,23 | 0,36 | 11,07–12,49 | 39,88 | 0,55 |
| 9 | Peru | 1.098 | 11,11 | 7,22 | 0,35 | 10,43–11,79 | 37,08 | 0,55 |
| 10 | Brasil | 4.283 | 10,90 | 7,86 | 0,16 | 10,59–11,22 | 34,37 | 0,27 |
| 11 | Guatemala | 299 | 10,05 | 4,15 | 0,79 | 8,50–11,60 | 32,19 | 1,13 |
| 12 | Panamá | 690 | 9,99 | 5,78 | 0,45 | 9,11–10,86 | 34,81 | 0,70 |
| 13 | Paraguai | 368 | 9,55 | 6,39 | 0,53 | 8,52–10,59 | 31,24 | 0,91 |
| 14 | México | 2.725 | 8,53 | 4,96 | 0,17 | 8,20–8,87 | 29,04 | 0,28 |
| 15 | Colômbia | 4.990 | 7,53 | 4,98 | 0,12 | 7,29–7,77 | 33,80 | 0,22 |
| 16 | El Salvador | 2.225 | 6,85 | 3,40 | 0,20 | 6,47–7,24 | 28,76 | 0,36 |
| 17 | Chile | 2.329 | 5,47 | 3,76 | 0,11 | 5,25–5,69 | 26,06 | 0,28 |
| 18 | República Dominicana | 1.054 | 5,33 | 3,06 | 0,19 | 4,95–5,70 | 29,30 | 0,50 |
| 19 | Uruguai | 1.698 | 4,42 | 2,06 | 0,15 | 4,13–4,71 | 23,86 | 0,33 |

### 3.2 Leitura do ranking

- O topo é muito nítido: Venezuela, Cuba e Equador ocupam as três primeiras
  posições nos dois modelos.
- Venezuela é um outlier substantivo: média DeepSeek de 30,72 e média Qwen de
  62,87, muito acima do restante da amostra.
- O grupo seguinte é Nicarágua, Argentina e Bolívia. A posição exata troca
  entre modelos, mas o agrupamento é estável.
- O bloco inferior é formado por Chile, República Dominicana e Uruguai, com
  scores DeepSeek abaixo de 6.
- A correlação entre as médias nacionais é Pearson = 0,972 e Spearman = 0,958.
  Portanto, a escolha do modelo altera pouco a hierarquia entre países, embora
  altere bastante a escala dos scores.
- A Costa Rica deve ser tratada com cautela: N = 25 e SE = 1,88; seu intervalo
  de confiança é muito mais amplo que o dos demais países.

## 4. Líderes com pelo menos 20 discursos

### Top 15 pelo DeepSeek

| Rank | Líder | País | N | Média DeepSeek | SE | Média Qwen |
|---:|---|---|---:|---:|---:|---:|
| 1 | Nicolás Maduro Moros | Venezuela | 2.351 | 32,42 | 0,33 | 63,75 |
| 2 | Rafael Vicente Correa Delgado | Equador | 611 | 32,11 | 0,56 | 58,24 |
| 3 | Miguel Díaz-Canel Bermúdez | Cuba | 188 | 31,46 | 1,03 | 54,60 |
| 4 | Daniel Noboa | Equador | 434 | 27,38 | 0,71 | 56,00 |
| 5 | Hugo Rafael Chávez Frías | Venezuela | 1.175 | 27,32 | 0,40 | 61,10 |
| 6 | Fidel Castro Ruz | Cuba | 244 | 24,89 | 0,99 | 52,29 |
| 7 | Raúl Castro Ruz | Cuba | 87 | 21,49 | 1,48 | 44,27 |
| 8 | Néstor Carlos Kirchner Ostoic | Argentina | 676 | 21,14 | 0,60 | 46,59 |
| 9 | Javier Gerardo Milei | Argentina | 301 | 21,08 | 0,75 | 48,94 |
| 10 | Iris Xiomara Castro Sarmiento | Honduras | 81 | 20,34 | 1,90 | 42,60 |
| 11 | Jair Messias Bolsonaro | Brasil | 381 | 20,02 | 0,77 | 42,94 |
| 12 | José Daniel Ortega Saavedra | Nicarágua | 507 | 19,40 | 0,70 | 47,15 |
| 13 | Juan Evo Morales Ayma | Bolívia | 161 | 16,77 | 1,19 | 45,41 |
| 14 | Fernando Armindo Lugo Méndez | Paraguai | 80 | 15,59 | 1,31 | 40,48 |
| 15 | Gustavo Francisco Petro Urrego | Colômbia | 553 | 14,99 | 0,64 | 42,22 |

Os cinco primeiros líderes também concentram o topo nacional. Isso é
substantivamente coerente, mas exige cuidado inferencial: a hierarquia dos
países é parcialmente uma hierarquia de líderes muito representados na base.

## 5. País–ano

As maiores médias país–ano, exigindo N ≥ 20, são:

| País–ano | N | Média DeepSeek | SE | Média Qwen |
|---|---:|---:|---:|---:|
| Equador 2007 | 45 | 39,13 | 2,10 | 64,76 |
| Venezuela 2015 | 213 | 37,10 | 0,92 | 68,44 |
| Cuba 2024 | 30 | 35,01 | 3,26 | 57,78 |
| Venezuela 2017 | 306 | 34,68 | 0,85 | 67,03 |
| Venezuela 2019 | 303 | 34,16 | 0,93 | 65,54 |
| Cuba 2019 | 23 | 34,10 | 3,02 | 57,19 |
| Equador 2015 | 128 | 33,23 | 1,31 | 58,52 |
| Venezuela 2016 | 201 | 33,03 | 1,12 | 63,47 |

As menores médias país–ano incluem México 2016 (1,98), Uruguai 2025 (2,10),
México 2015 (2,26), México 2017 (2,27) e Chile 2012 (2,28). Esses resultados
devem ser apresentados como médias condicionais ao corpus observado; não
constituem uma série temporal balanceada.

## 6. Dimensões do índice

As médias são calculadas nos 34.821 discursos `SPEECH`.

| Dimensão | Qwen média | Qwen mediana | Qwen DP | DeepSeek média | DeepSeek mediana | DeepSeek DP |
|---|---:|---:|---:|---:|---:|---:|
| Centrismo do povo | 51,20 | 54,34 | 25,77 | 22,27 | 16,99 | 18,72 |
| Antielitismo | 36,60 | 30,70 | 25,48 | 14,83 | 7,20 | 18,88 |
| Dicotomia moral | 44,49 | 44,66 | 24,25 | 13,15 | 6,43 | 16,48 |
| Soberania popular | 36,20 | 34,82 | 20,92 | 9,55 | 3,69 | 13,42 |
| Retórica excludente | 12,72 | 11,94 | 10,17 | 3,80 | 0,00 | 6,70 |
| Retórica de crise | 42,98 | 41,58 | 22,43 | 12,87 | 8,72 | 14,48 |

O padrão é importante para a interpretação: a compressão do DeepSeek não é
uniforme apenas no score final. Ela é particularmente forte em exclusão,
soberania popular e dicotomia moral. No DeepSeek, 55,0% dos discursos recebem
zero em retórica excludente; no Qwen, 3,5%.

## 7. Distribuição e extremos

### Distribuição dos scores em `SPEECH`

| Faixa | Qwen | DeepSeek |
|---|---:|---:|
| 0–<10 | 7,7% | 56,4% |
| 10–<20 | 15,2% | 20,1% |
| 20–<30 | 15,2% | 10,5% |
| 30–<40 | 17,1% | 6,9% |
| 40–<50 | 17,1% | 4,2% |
| 50–<60 | 12,9% | 1,6% |
| 60–<70 | 9,2% | 0,2% |
| 70–<80 | 4,7% | 0,02% |
| 80–<90 | 0,8% | 0% |

### Maiores scores individuais

No DeepSeek, os dez maiores casos são majoritariamente discursos de Nicolás
Maduro entre 2013 e 2019, com scores entre 68,57 e 72,12. O maior caso é um
discurso de Maduro na Venezuela em 2015: DeepSeek = 72,12 e Qwen = 87,17.

O maior score Qwen é um discurso de José Daniel Ortega na Nicarágua em 2018:
Qwen = 88,77 e DeepSeek = 57,40. O segundo é um discurso de Nicolás Maduro em
2016: Qwen = 88,60 e DeepSeek = 64,45.

Esses casos extremos são úteis para inspeção qualitativa, mas não devem ser
usados como evidência isolada. A conclusão mais robusta vem das médias por
país, país–ano e líder, sempre acompanhadas de N e SE.

## 8. Tipos de texto

| Tipo | N | Média Qwen | SE Qwen | Média DeepSeek | SE DeepSeek |
|---|---:|---:|---:|---:|---:|
| SPEECH | 34.821 | 37,36 | 0,11 | 12,74 | 0,07 |
| INTERVIEW | 2.653 | 30,85 | 0,40 | 9,22 | 0,24 |
| PRESS_RELEASE | 6.675 | 16,02 | 0,20 | 4,18 | 0,10 |
| COMMUNIQUE | 859 | 20,29 | 0,70 | 6,55 | 0,40 |
| DECREE | 322 | 26,33 | 1,30 | 10,20 | 0,64 |
| LETTER | 162 | 24,07 | 1,71 | 8,54 | 0,93 |

O tipo textual é um forte determinante descritivo: discursos têm níveis muito
maiores que comunicados e press releases nos dois modelos. Isso recomenda
manter `SPEECH` como especificação substantiva e tratar os demais tipos como
robustez ou análise separada.

## 8.1 Comparação por líder: POPIN, GPD e LALLPI

Esta tabela resolve a dúvida sobre a média baixa por líder. O ranking está
ordenado pelo DeepSeek e exige pelo menos 20 discursos `SPEECH` por líder.
`LALLPI POP_R` é a média dos anos país–ano em que há discursos daquele líder;
é um proxy contextual, não uma codificação direta do líder.

| Líder | N discursos | Qwen | SE Qwen | DeepSeek | SE DS | GPD | Termos GPD | LALLPI POP_R | Anos LALLPI |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Nicolás Maduro | 2.351 | 63,75 | 0,33 | **32,42** | 0,33 | 80,00 | 2 | 98,60 | 9 |
| Rafael Correa | 611 | 58,24 | 0,59 | **32,11** | 0,56 | 62,50 | 1 | 95,42 | 10 |
| Miguel Díaz-Canel | 188 | 54,60 | 1,22 | **31,46** | 1,03 | 41,87 | 1 | 79,10 | 2 |
| Daniel Noboa | 434 | 56,00 | 0,70 | **27,38** | 0,71 | — | — | — | — |
| Hugo Chávez | 1.175 | 61,10 | 0,37 | **27,32** | 0,40 | 88,89 | 3 | 99,07 | 17 |
| Fidel Castro | 244 | 52,29 | 1,13 | **24,89** | 0,99 | — | — | 79,31 | 9 |
| Raúl Castro | 87 | 44,27 | 1,91 | **21,49** | 1,48 | — | — | 79,13 | 11 |
| Néstor Kirchner | 676 | 46,59 | 0,85 | **21,14** | 0,60 | — | — | 79,25 | 4 |
| Javier Milei | 301 | 48,94 | 0,91 | **21,08** | 0,75 | — | — | — | — |
| Xiomara Castro | 81 | 42,60 | 2,32 | **20,34** | 1,90 | — | — | — | — |
| Jair Bolsonaro | 381 | 42,94 | 1,04 | **20,02** | 0,77 | — | — | — | — |
| Daniel Ortega | 507 | 47,15 | 0,88 | **19,40** | 0,70 | 52,50 | 2 | 68,83 | 14 |
| Evo Morales | 161 | 45,41 | 1,45 | **16,77** | 1,19 | 66,04 | 3 | 90,51 | 14 |
| Fernando Lugo | 80 | 40,48 | 1,87 | **15,59** | 1,31 | — | — | — | 4 |
| Gustavo Petro | 553 | 42,22 | 0,79 | **14,99** | 0,64 | — | — | — | — |

### O que a comparação por líder mostra

- A média DeepSeek não é baixa porque os líderes do topo estejam ausentes: os
  líderes mais associados ao populismo aparecem no topo, mas em uma escala
  comprimida. Maduro, por exemplo, tem DeepSeek = 32,42, Qwen = 63,75 e GPD =
  80,00.
- O Qwen fica mais próximo do GPD em nível para Maduro e Correa, mas ainda
  tende a superestimar alguns casos. O DeepSeek preserva melhor a ordenação,
  mas subestima o nível em vários líderes.
- Chávez aparece como primeiro no GPD, enquanto Maduro aparece como primeiro no
  DeepSeek. Isso não invalida o resultado: o GPD cobre apenas três termos para
  Chávez e dois para Maduro, enquanto o POPIN usa 1.175 e 2.351 discursos,
  respectivamente.
- Os três líderes no topo do DeepSeek — Maduro, Correa e Díaz-Canel — também
  estão entre os líderes com LALLPI `POP_R` mais alto. Isso sustenta a validade
  convergente, mas não permite dizer que o LALLPI mediu diretamente a fala de
  cada líder.
- Entre os 104 líderes da base, há correspondência GPD para 55 e cobertura
  LALLPI contextual para 76. Portanto, a tabela completa por líder deve manter
  valores ausentes onde não há correspondência, sem imputação.

## 9. Validade externa

### GPD

Nos 64 termos líder–mandato bloqueados para teste, agregando todos os
discursos `SPEECH` da janela do mandato:

| Modelo | Spearman | Pearson | MAE | RMSE | Viés POPIN − GPD |
|---|---:|---:|---:|---:|---:|
| Qwen | 0,409 | 0,665 | 22,68 | 25,76 | +16,09 |
| DeepSeek | **0,501** | **0,751** | **15,00** | 22,30 | −9,37 |

Entre os 40 termos com pelo menos 20 discursos, Spearman é praticamente igual
(Qwen 0,644; DeepSeek 0,642), o Qwen tem RMSE ligeiramente menor (22,06 contra
24,84), e o DeepSeek mantém menor MAE (16,41 contra 19,50).

### LALLPI

No nível país–ano, o DeepSeek ordena melhor as unidades do que o Qwen:

| Indicador | Modelo | N país–ano | Spearman | Pearson | MAE | Viés |
|---|---|---:|---:|---:|---:|---:|
| POP_R | Qwen | 339 | 0,491 | 0,519 | 24,88 | −13,59 |
| POP_R | DeepSeek | 339 | **0,563** | **0,591** | 38,45 | −37,75 |
| POP | Qwen | 319 | 0,491 | 0,635 | 17,73 | +15,26 |
| POP | DeepSeek | 319 | **0,562** | **0,688** | **11,85** | −8,86 |

Com pelo menos 20 discursos por célula, a vantagem ordinal do DeepSeek aumenta:
para `POP_R`, Spearman = 0,746 contra 0,716; para `POP`, Spearman = 0,777
contra 0,752.

O GPD e o LALLPI não são equivalentes. O GPD é uma validação mais próxima da
construção de populismo em líderes e mandatos; o LALLPI é um indicador externo
agregado de partidos e retórica nacional. Eles devem ser reportados como
testes de validade convergente complementares.

## 10. Diagnóstico final

1. **Ranking nacional:** muito robusto. Venezuela, Cuba e Equador estão no
   topo nos dois modelos; Chile, República Dominicana e Uruguai estão no fundo.
2. **Escala:** não robusta entre modelos. O DeepSeek produz scores menores e
   mais concentrados; não se deve fazer média entre Qwen e DeepSeek.
3. **Ordenação:** robusta. A associação entre modelos é alta, inclusive no
   nível país–ano.
4. **Validade:** DeepSeek tem melhor validade convergente no conjunto completo
   do GPD e melhor ordenação no LALLPI; Qwen não deve ser descartado, pois é uma
   especificação de robustez e apresenta menor RMSE em parte do teste GPD.
5. **Amostragem:** países e líderes com poucos discursos têm SE maior. Costa
   Rica é o caso mais evidente; rankings com N baixo não devem receber a mesma
   interpretação que Venezuela, Argentina, Brasil ou Colômbia.
6. **Composição da base:** o volume de discursos por líder e por país é
   desigual. As tabelas devem sempre mostrar N, média, mediana e SE; quando a
   inferência for temporal, deve-se evitar tratar a série como painel balanceado.

## 11. Recomendação para a versão publicável

Usar o DeepSeek v4 como especificação principal para os resultados substantivos
e o Qwen como teste de robustez. Publicar os rankings nacionais com média,
mediana, N, DP/SE e intervalo de confiança. Para qualquer comparação de nível
absoluto entre modelos, calibrar a escala usando somente o conjunto de
desenvolvimento do GPD; o conjunto de teste bloqueado deve permanecer intocado.
O argumento central deve ser sobre ordenação e validade convergente, não sobre a
diferença bruta de nível entre as duas LLMs.

## 12. Calibração preliminar da escala

É possível transformar os scores para uma escala aproximada do GPD sem alterar
os scores brutos. O procedimento correto é estimar a transformação apenas nos
30 termos de desenvolvimento e avaliar nos 64 termos `test_locked`.

Calibração linear preliminar, com truncamento para 0–100:

```text
DeepSeek_calibrado = max(0, min(100, 1,7405 × DeepSeek_bruto − 3,4563))
Qwen_calibrado     = max(0, min(100, 1,3030 × Qwen_bruto − 27,9154))
```

No teste bloqueado, sem recalibrar usando o teste:

| Modelo | Versão | Viés | MAE | RMSE | Spearman |
|---|---|---:|---:|---:|---:|
| Qwen | bruto | +16,09 | 22,68 | 25,76 | 0,409 |
| Qwen | calibrado | −0,14 | 15,77 | 19,46 | 0,407 |
| DeepSeek | bruto | −9,37 | 15,00 | 22,30 | 0,501 |
| DeepSeek | calibrado | −3,34 | 13,49 | 17,98 | 0,501 |

O ajuste melhora principalmente a comparabilidade dos níveis: o score médio do
DeepSeek no teste passa de 12,81 para aproximadamente 18,83, enquanto a média
GPD é 22,17. A correlação ordinal permanece praticamente igual porque uma
transformação linear monotônica não muda a ordenação.

Esses coeficientes ainda devem ser tratados como preliminares, pois foram
estimados em apenas 30 termos de desenvolvimento. Antes da publicação, a
calibração deve ser congelada, acompanhada de bootstrap ou validação cruzada no
desenvolvimento, e aplicada uma única vez ao teste bloqueado. O LALLPI não deve
ser usado para calibrar a escala, pois não é uma codificação humana direta do
líder ou do discurso.
