# POPIN v4 — protocolo de validação externa com o GPD

Status: desenho operacional; nenhum resultado de modelo foi executado nesta etapa.

## 1. Fonte e papel do GPD

Usar a versão mais recente disponibilizada no registro oficial, atualmente o
arquivo `GPD_v2.1_20251120.csv` e seu arquivo wide correspondente, identificados
pelo DOI `10.7910/DVN/LFTQEZ`. Preservar os arquivos originais, o pacote de
discursos e o codebook no pacote de replicação. O GPD é o critério externo humano: ele não será tratado como uma
verdade absoluta nem como uma dimensão equivalente às seis dimensões do POPIN.

O desfecho humano principal é `totalaverage`, o escore holístico de populismo do
GPD na escala 0–2. O codebook define esse campo como a média aritmética das
notas de todos os discursos e codificadores dentro do líder–mandato. Para
comparação com o POPIN, reescalar o escore para 0–100 apenas na etapa analítica:

`gpd_0_100 = 50 * gpd_score_0_2`

Não converter o GPD em binário no resultado principal. A classificação em quatro
faixas (não populista, algo populista, populista, muito populista) será apenas uma
checagem secundária.

## 2. Unidade de validação

O teste primário será feito no nível líder–mandato, porque essa é a unidade de
análise do GPD. O POPIN será agregado para o mesmo líder–mandato, mantendo também
o número de discursos e o erro-padrão da média. Não substituir `totalaverage`
por uma média simples dos quatro textos se o número de codificadores variar;
essa seria uma especificação de sensibilidade separada.

Se os textos originais do GPD estiverem disponíveis, será feita uma análise
secundária no nível do discurso com correspondência textual, usando
`averagerubric` como desfecho de fala. Sem correspondência textual verificável,
não se deve chamar a comparação de validação discurso a discurso; nesse caso,
ela será reportada explicitamente como validação de convergência no nível
líder–mandato.

## 3. Chaves de ligação

Construir uma tabela de correspondência auditável, sem apagar candidatos:

1. `gpd_country` → ISO3, usando uma tabela explícita de aliases.
2. `gpd_leader` → nome normalizado, preservando também o nome original.
3. `gpd_yearbegin`, `gpd_yearend` → janela do mandato.
4. `gpd_speech_type`, `gpd_date`, `gpd_title` → campos auxiliares quando existirem.
5. `text_hash_normalized` → chave de maior qualidade quando o texto do GPD puder
   ser obtido.

Hierarquia de match:

- **A**: hash do texto normalizado idêntico;
- **B**: país + líder + data/título compatível;
- **C**: país + líder + janela do mandato, somente para a agregação
  líder–mandato;
- **D**: nome parecido sem confirmação temporal, nunca usado automaticamente.

Matches C e D devem ser revisados por regra e permanecer marcados na base. Um
match ambíguo não entra no teste principal.

## 4. Amostra operacional para comparação de modelos

Alvo: aproximadamente 900 discursos válidos do POPIN, sem `INVALID`, definidos
antes de consultar os resultados dos modelos alternativos.

- incluir todos os matches GPD de alta qualidade disponíveis até o limite da
  amostra;
- completar a amostra por estratos de país, ano, tipo de discurso e faixa do
  POPIN v4 baseline;
- manter vários discursos por líder–mandato quando isso for necessário para
  estimar o agregado, mas impedir que um único líder domine a amostra;
- registrar a semente, os estratos, os critérios de inclusão e a lista final de
  `discourse_id`.

Particionar por líder–mandato, nunca por discurso individual:

- **desenvolvimento (30%)**: calibrar decisões operacionais e detectar problemas
  de ligação;
- **teste bloqueado (70%)**: escolher o modelo e o prompt pelo desempenho neste
  conjunto somente após congelar o protocolo.

Se houver poucos matches GPD, não preencher artificialmente com casos não
validados. Reportar o número efetivo de unidades humanas e manter a amostra
complementar como teste de estabilidade do POPIN, não como validação humana.

## 5. Métricas para escolher modelo e prompt

Escolher uma especificação única antes de olhar o resultado do corpus completo.
No teste bloqueado, reportar:

- correlação de Spearman como métrica principal de ordenação;
- correlação de Pearson como métrica de associação linear;
- MAE e RMSE após reescala do GPD para 0–100;
- viés médio `POPIN - GPD`;
- correlação e erro por região e por número de discursos do líder–mandato;
- intervalo de confiança por bootstrap de líder–mandato.

Regra de decisão: primeiro maior Spearman no teste bloqueado; em empate próximo,
menor MAE; depois, menor sensibilidade entre os dois prompts. O desempenho no
conjunto de desenvolvimento não escolhe o vencedor, servindo apenas para
diagnóstico.

## 6. Escopo das execuções

Para cada discurso da amostra, manter a mesma base textual, o mesmo chunking v4
(até 800 palavras, contíguo, sem overlap) e a mesma agregação. Variar apenas:

- modelo: Qwen baseline e DeepSeek V4 Flash 0731;
- Luna fica fora da execução operacional por causa do limite temporário de
  requisições da conta OpenRouter, que torna a rodada completa impraticável;
- prompt: prompt v4 congelado e uma variante pré-registrada;
- temperatura: 0, salvo se a API do modelo exigir configuração equivalente
  documentada.

Salvar uma linha por execução com `run_id`, modelo, prompt hash, parâmetros,
timestamp, custo, latência, número de chunks, falhas JSON e versão do código.

## 7. Critério de parada desta etapa

Esta etapa termina quando:

1. o arquivo GPD v2.1, o codebook e, quando possível, os textos dos discursos
   estiverem disponíveis localmente;
2. a tabela de aliases e a tabela de matches forem geradas;
3. o tamanho efetivo da amostra e a quantidade de matches A/B/C forem conhecidos;
4. a lista de `discourse_id` e a partição por líder–mandato estiverem congeladas.

Só então executar as chamadas aos dois modelos.

## Fontes

- GPD v2 e metadados: https://research.ceu.edu/en/datasets/global-populism-database/
- Nota metodológica e codebook descrito pelos autores:
  https://populism.byu.edu/0000017d-bf5d-d270-a1fd-ff5fcf750001/global-populism-database-paper-pdf
- DOI do dataset: https://doi.org/10.7910/DVN/LFTQEZ
