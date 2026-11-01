# Desenho: completar POPIN v4.1.0 e teste comparativo de Cuba

## Intenção

Completar a release GitHub `v4.1.0` com um pacote que permita a um pesquisador externo reconstruir e auditar a análise POPIN v4. Em paralelo, entregar um script local para comparar modelos de decisão nos 519 discursos `SPEECH` de Cuba, usando o prompt-base POPIN v4 e cada texto integral.

## O que já existe

- O conceito e instrumento de medida continuam sendo POPIN v4; v4.1.0 é a revisão do pacote de código e dados, não uma nova versão do índice.
- A release v4.0 já publicou um DuckDB completo. A release v4.1.0 existe no GitHub, mas ainda não tem assets.
- O DuckDB raiz `popin.duckdb` (cerca de 1,52 GB) contém textos integrais, scores e metadados de execução. `06_website/popin_web.duckdb` (cerca de 5,6 MB) serve ao painel e não é banco analítico completo.
- O export atual contém 45.492 documentos: 44.592 linhas do lote GPT-5.6 v4 completo e 900 linhas provenientes de uma execução marcada como piloto. A documentação precisa distinguir a composição real e definir uma tabela primária sem ambiguidade de proveniência.
- A instrução e o prompt v4 estão em `04_score.py`. O código de produção existente usa Qwen e segmentação em blocos; o artigo e a especificação atual descrevem GPT-5.6, texto integral e seis dimensões. O pacote deve declarar esses fluxos separadamente.
- Cuba tem 519 discursos `SPEECH` (1.673.546 palavras; maior: 189.214). O texto de 384.239 palavras mencionado na conversa é um `INTERVIEW`, fora da amostra solicitada.

## Abordagens consideradas

1. **Completar a v4.1.0 (escolhida):** manter POPIN v4 como instrumento, corrigir manifesto e instruções, publicar código e exports necessários no repositório e anexar um DuckDB analítico completo à release v4.1.0. Preserva continuidade com v4.0 e deixa explícito o que cada versão de código/modelo reproduz.
2. **Criar uma release de dados separada:** reduziria mudanças na release existente, mas dividiria código e dados de reprodução entre versões e tornaria mais difícil para um observador descobrir o pacote correto.
3. **Preparar só localmente:** permitiria inspeção antes de publicar, mas não atende à decisão do usuário de completar v4.1.0.

## Escopo do pacote v4.1.0

- Corrigir README, mapa de código, dicionário, guia de reprodução e manifesto para identificar um banco analítico como fonte de referência e separar o DuckDB do painel.
- Fornecer no repositório os scripts de análise, o prompt e seus metadados, exports portáteis, manifestos de fontes, instruções de ambiente/execução e hashes. Usar assets da release para arquivos grandes; não colocar DuckDB gigante no histórico Git.
- Anexar um DuckDB que permita acessar os textos integrais necessários, resultados, identificadores e histórico/metadados suficientes para refazer as tabelas centrais e verificar proveniência. Não anexar credenciais, caches temporários nem logs transitórios. Preservar as condições de redistribuição das fontes originais e registrar, para material não redistribuível, URLs, versões e checksums necessários para reconstrução.
- Preservar o snapshot congelado atual de 45.492 documentos como referência, identificando no banco, no export e no manifesto quais 44.592 vieram do lote completo e quais 900 vieram do piloto. O protocolo v4 será verificado nos dois grupos antes da publicação; se diferir, o grupo de piloto fica separado e as estatísticas primárias são regeneradas com a amostra que corresponda ao manuscrito.
- Manter v4.0 documentada como snapshot Qwen/chunked e declarar v4.1.0 como revisão do pacote que acompanha a especificação GPT-5.6/full-text do manuscrito. Não sugerir equivalência metodológica entre esses resultados.

## Script comparativo para Cuba

- Ler os 519 textos `SPEECH` de Cuba do DuckDB em modo somente leitura, sem substituir ou atualizar dados existentes.
- Reproduzir a formulação, dimensões e instruções de mensuração do prompt v4 de `04_score.py`; salvar a versão/hash do prompt aplicado.
- Enviar cada discurso inteiro, uma unidade por chamada, aos modelos configurados pelo usuário via OpenRouter. Cada resposta avaliará as seis dimensões v4 em JSON, com categorias ordinais de 0 a 9; normalizar cada categoria por `100/9`. Assim haverá uma chamada por discurso/modelo, sem dividir o texto nem fazer seis chamadas separadas. A execução não será iniciada durante a preparação do código.
- Tratar os valores normalizados como aproximação comparativa, não como escore contínuo idêntico ao POPIN v4; guardar também as categorias ordinais originais.
- Guardar resposta bruta, scores por dimensão, modelo/id, prompt, status, erro, tempo/uso de tokens e contagem de palavras em saída separada, com retomada segura. Registrar discursos não aceitos por limite de contexto; não truncar silenciosamente.
- Comparar somente casos pareados com o baseline POPIN, reportando cobertura por modelo e as diferenças nas seis dimensões e score final.

## Fora do escopo

- Rodar chamadas pagas aos modelos, escolher ou configurar credenciais do usuário.
- Alterar os textos, scores congelados ou banco ativo durante o teste comparativo.
- Reclassificar os resultados exploratórios v4.0 como equivalentes ao pipeline principal v4.1.0.

## Decisões de implementação deixadas ao executor

- Estrutura exata do DuckDB público e dos assets, desde que os identificadores, textos publicados, scores, proveniência e análises centrais possam ser reconstruídos e auditados. Manter a cobertura textual já disponibilizada na release v4.0; documentar fontes e restrições existentes.
- Extração do prompt e detalhes do JSON; a transformação ordinal para escala comparável é 0–9 multiplicado por `100/9`, mantendo o valor ordinal original.
- Atualização do asset e metadados da release GitHub v4.1.0 após revisão de hashes e conteúdo.

## Critérios de aceite

1. Um observador consegue baixar a release v4.1.0, conferir hashes, abrir o DuckDB em modo leitura e reconstruir as tabelas centrais a partir de código/documentação do repositório.
2. A documentação identifica corretamente a tabela de análise, o conjunto de textos, modelo, prompt, segmentação, cobertura e limitações de redistribuição.
3. O script de Cuba prepara uma execução integral e retomável para exatamente os 519 discursos escolhidos, sem executar chamadas externas automaticamente.
4. A comparação distingue respostas ordinais normalizadas de scores POPIN contínuos e informa cobertura pareada.
