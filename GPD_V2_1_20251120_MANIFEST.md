# GPD v2.1 — manifest local

Download realizado em 2026-08-15 a partir do registro oficial do Harvard
Dataverse, DOI `10.7910/DVN/LFTQEZ`. O pacote foi preservado sem alterações em
`data/gpd_v2_1_20251120/`.

## Conteúdo verificado

- `GPD_v2.1_20251120.csv`: 5.552 linhas de codificação; 1.305 IDs de discurso
  não vazios; 269 líderes; 77 países; 361 líder–mandato.
- `GPD_v2.1_20251120_Wide.csv`: 361 linhas de líder–mandato.
- `GPD Codebook_v2.1.pdf`: codebook da versão baixada.
- `speeches_20251120/`: 1.310 arquivos de texto disponibilizados no pacote.
- `Rubrics_20251120.zip`: rubricas disponibilizadas no pacote.
- `gpd_speech_inventory.csv`: inventário deduplicado dos 1.305 IDs de discurso,
  com status de ligação ao texto, contagem de palavras e hash SHA-256.
- `gpd_popin_matches.csv`: primeira passagem de correspondência textual exata.
- `gpd_popin_match_review.csv`: candidatos por similaridade textual, com score,
  margem e decisão conservadora.
- `gpd_popin_leader_term_matches.csv`: correspondência no nível líder–mandato,
  com média POPIN, desvio-padrão, erro-padrão e número de discursos.
- `sensitivity_test_sample.csv`: amostra congelada de 900 discursos para os
  testes de modelo e prompt.

O arquivo longo contém observações por codificador. A unidade de discurso deve
ser deduplicada por `merging_variable`; a unidade líder–mandato deve ser
deduplicada por `country + leader + term`. O campo `totalaverage` é o desfecho
humano holístico de referência. Antes do match, devem ser tratados os 15 IDs
vazios ou inconsistentes e os 19 nomes de arquivo que não coincidem literalmente
com a tabela, mantendo cada decisão no log de correspondência.

O inventário inicial encontrou 1.291 correspondências por nome exato, 8 por
normalização de acentos/espaços e 6 IDs sem texto correspondente. Esses seis
casos ficam fora da validação discurso–texto, mas continuam elegíveis para a
validação líder–mandato via `totalaverage`.

No cruzamento textual, 2 casos foram exatos e 76 foram classificados como
candidatos de alta similaridade com margem clara; 6 ficaram em revisão e 1.215
não foram aceitos automaticamente. No cruzamento líder–mandato, 94 dos 361
mandatos GPD tiveram um único líder POPIN compatível e pelo menos um discurso
no intervalo temporal; 260 não têm líder POPIN correspondente e 7 não têm
discursos POPIN no intervalo.

## SHA-256

```text
cd90b8e5e70b680b34fbbb9c87d26f99564f7a6e827f8dc1e46106fd78a49d3a  GPD_v2.1_20251120.csv
0a956b95deb6e0d4da1bcfb237e6a2cf1be72c8bf1a945b99391dcf6f8813295  GPD_v2.1_20251120_Wide.csv
7f96a54c2866630f98d4d0f636d3c51cf406294a0ca96cc08b3a73ea69a2e429  GPD Codebook_v2.1.pdf
6bdeb00559e2bcfaa4505db26f66370fea9aa3cbf7160bc39259c361cac0a662  speeches_20251120.zip
1cae12a1b8271694a48c4267efe3eb1b7bc045f69a6877861f7c666168d19dba  Rubrics_20251120.zip
```

O próximo passo é gerar o inventário de matches com o corpus POPIN; nenhuma
chamada a modelo é necessária para isso.
