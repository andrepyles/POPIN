# POPIN: observatório de dados

Rework autorizado em 2026-09-07. Modo Operate. Manter nome, dataset, cinco áreas de investigação e tema claro. Substituir a composição de sidebar, cartões e serifas por navegação horizontal, superfície clara neutra e instrumentos de comparação amplos.

## Direção

Leitura: dashboard de pesquisa para pesquisadores e jornalistas. DESIGN_VARIANCE 3; MOTION_INTENSITY 2; VISUAL_DENSITY 6. Native HTML/CSS/JS, sem migração de framework. IBM Plex Sans em controles e títulos; numerais tabulares. Escala contínua azul de 0 a 100; cores categóricas exclusivamente para séries comparadas. Estados ativos em teal.

Referências de estrutura consideradas: anuário estatístico, atlas de pesquisa, observatório público de dados, relatório de instituto, laboratório de análise, catálogo de séries, tabela de indicadores. A direção escolhida é observatório público de dados (terceira candidata, seed 03dffad5). Formas decorativas de arcade, neon ou tecido não ajudam a leitura quantitativa; a precisão dos números, a densidade útil e a reorganização estrutural em mobile são os critérios absorvidos.

## Plano e responsabilidades

- [x] Interface: substituir static/index.html e static/css/style.css; manter IDs da API de interface; filtros agrupados e cabeçalho horizontal, corpus compacto, mapa e tabela lado a lado, perfil lateral e metodologia recolhível.
- [x] Interações: static/js/app.js; localização, escala, corridas de requisições, carregamento/erro/vazio, resize de gráficos, intervalos reais p25-p75, teclado do perfil. Agente Mendel e integração principal.
- [x] Revisão independente: auditoria inicial Locke; revisão final de código Pasteur. Achado sobre quartis do score final em tooltips de outras dimensões corrigido e confirmado pelo revisor.
- [x] Verificação: syntax, endpoints, render desktop/mobile, filtros combinados, gráfico em seção oculta, perfil, idioma. 12 testes automatizados de estado passam. Detector em modo regex reduzido: sem achados, mas sem cálculo de contraste/seletores; não constitui aprovação visual automática.
- [x] Registro do sistema visual em DESIGN.md e .impeccable/design.json pelo agente Beauvoir; entrega local. Nenhuma publicação remota neste passo.

## Critérios

Todas as cinco seções funcionais; 45.492 observações da base web conferidas ao vivo. Valores não alterados. Quartis não são erros padrão nem intervalos de confiança. Não introduzir limiares populista/não-populista. Ausências não viram zeros. No mobile, controles acessíveis e nenhuma rolagem horizontal global; tabela pode ter rolagem local. Backup em .impeccable/backups/pre-rework-20260907.tar.gz.

## Evidências de entrega — 2026-09-08

- API /api/stats: 45.492 textos, 19 países, 105 líderes, 2000–2025; média 19,77. Banco e backend sem alterações neste rework.
- Navegador: cinco seções renderizadas; busca Bolsonaro com Brasil + tipo Discurso retornou n=381 e média 25,2. Perfil abre/fecha, Escape restaura foco, busca vazia informa ausência, PT/EN atualiza rótulos.
- Desktop 1477px: conteúdo1462px; mobile390px: conteúdo375px, sem overflow horizontal global. Histograma de intervalos horizontal com altura677px; legenda abaixo do título (687,6px vs652px na captura).
- Revisão independente foi de código/testes; inspeção visual desktop/mobile feita pelo agente principal. Capturas exibidas diretamente no navegador da ferramenta, não persistidas como arquivos locais.
- Testes: node --check static/js/app.js; node --test tests/dashboard-state.test.cjs (12/12); git diff --check -- static tests.
- Preview local: http://127.0.0.1:8765/?v=30. Ambiente Python em /home/andre/.cache/popin-web-venv, fora do mount, para evitar arquivos de ambiente virtual no OneDrive. Código e documentação permanecem no OneDrive.
- Sem commit, push ou publicação remota neste passo.

## Extensão solicitada — Sobre e curvas (2026-09-08)

- Nova seção Sobre no menu, substituindo o disclosure do rodapé. Modo Read integrado ao visual atual, com PT/EN, seis dimensões, fórmula, limitações, citação, dissertação e CSVs das validações.
- Conteúdo baseado na auditoria de 06/09/2026; distingue a dissertação v3 da extensão v4. GPD: 94 líder–mandatos SPEECH; sensibilidade ao prompt: 900 pares Luna full; LALLPI: país–ano POP_R.
- Séries temporais geral, por país e de perfil usam spline com smoothing 0.5. Marcadores, valores e lacunas preservados; intervalos e radar continuam retos. Interpolação visual explicitada no texto.
- node --check e 14/14 testes passaram; git diff --check sem problemas. PDF servido com HTTP 200, application/pdf, 1.012.131 bytes e SHA-256 idêntico ao original.
- Sobre inspecionado no navegador em desktop e mobile 390px; conteúdo 375px sem overflow global. Alternância PT/EN e ocultação dos filtros irrelevantes conferidas. Preview v31. Banco e backend não alterados.
