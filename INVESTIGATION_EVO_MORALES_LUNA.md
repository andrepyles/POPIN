# Investigação da discrepância do Luna full para Evo Morales

## Resultado principal

A discrepância do terceiro mandato de Evo Morales não é explicada por uma falha de processamento do Luna full. Depois de consolidar o run principal com o piloto não chunked, os 77 discursos `SPEECH` de 2015–2019 estão presentes.

| Unidade | GPD | Luna full consolidado |
|---|---:|---:|
| Evo I | 75,00 | 52,57 |
| Evo II | 50,00 | 28,75 |
| Evo III | 73,12 | 17,00 |

## Evidências sobre a composição do corpus

O GPD não usa uma amostra representativa dos 77 discursos do terceiro mandato. Ele usa quatro discursos selecionados por categoria:

| Categoria GPD | Palavras | GPD reescalado |
|---|---:|---:|
| Campaign | 3.127 | 47,50 |
| Famous | 10.506 | 72,50 |
| International | 4.030 | 87,50 |
| Ribbon cutting | 8.054 | 85,00 |

Os quatro textos têm média de aproximadamente 6.429 palavras. Nos 77 discursos do POPIN, a média é 1.239 palavras e a mediana é apenas 186 palavras.

| Faixa de tamanho | N | Luna full | Qwen | DeepSeek |
|---|---:|---:|---:|---:|
| <100 palavras | 23 | 4,23 | 29,06 | 5,21 |
| 100–499 | 25 | 10,56 | 40,36 | 11,29 |
| 500–999 | 6 | 35,92 | 56,87 | 33,53 |
| 1.000–2.999 | 12 | 28,72 | 46,29 | 17,34 |
| 3.000+ | 11 | 35,24 | 39,53 | 17,54 |

Nos quatro discursos mais longos do POPIN, a média do Luna é 54,98, muito acima da média de 17,00 da base completa. Isso é consistente com um efeito forte de seleção dos textos do GPD.

## Padrão temporal

O terceiro mandato contém muitos textos curtos e cerimoniais:

| Ano | N | Palavras médias | Luna full |
|---:|---:|---:|---:|
| 2015 | 42 | 1.774 | 21,46 |
| 2016 | 20 | 616 | 13,98 |
| 2017 | 4 | 1.836 | 24,70 |
| 2018 | 10 | 116 | 2,83 |
| 2019 | 1 | 96 | 0,71 |

O ano de 2018, embora tenha poucos discursos, puxa a média para baixo: dez textos, média de 115 palavras e score Luna de 2,83.

## Comparação entre modelos

Nos mesmos 77 discursos, a correlação Qwen–Luna é 0,719, mas o Qwen fica em média 22,08 pontos acima do Luna. DeepSeek e Luna têm correlação 0,863 e diferença média de apenas −3,95 pontos. Isso indica que o Qwen é o outlier de escala; Luna e DeepSeek concordam mais sobre quais textos são altos ou baixos.

A leitura dos extremos confirma o padrão. Textos curtos sobre esporte, felicitações, inaugurações e cerimônias recebem scores muito baixos no Luna. Discursos internacionais, longos e com oposição entre povo, elites, soberania e imperialismo recebem scores altos, entre 60 e 73.

## Diagnóstico

O GPD está medindo a intensidade populista de quatro discursos substantivamente selecionados; o POPIN está estimando a média de toda a produção discursiva. As duas quantidades não são equivalentes.

O resultado do Luna para Evo III é, portanto, melhor interpretado como **baixa intensidade média no corpus completo**, não como ausência de retórica populista. O GPD mostra que Evo produziu discursos altamente populistas em textos selecionados, enquanto o POPIN mostra que essa intensidade não aparece uniformemente em todos os seus discursos.

Para o paper, a validação principal deve comparar os discursos do GPD individualmente — ou uma amostra POPIN estratificada por tipo e tamanho —, e não comparar diretamente a média nacional ou a média de todo o mandato com o GPD.
