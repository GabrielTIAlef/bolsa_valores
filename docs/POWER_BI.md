# Guia de consumo no Power BI

O painel original foi mostrado numa captura dos materiais do portfólio, mas não há PBIX, DAX ou Power Query recuperados no histórico do repositório. Este guia descreve uma possível importação dos artefatos novos; não é validação em Power BI Desktop.

1. Execute a demonstração e consulte outputs/demo/latest.json para selecionar uma geração confirmada.
2. Importe ativos.csv e cotacoes_indicadores.csv; mantenha symbol como texto, date como data e preços/indicadores como decimais usando ponto no parsing. Volume é número inteiro.
3. Relacione ativos[symbol] de um para muitos com cotações[symbol]. Use uma dimensão de datas para filtros, com relações de um para muitos. A agregação mensal deve preservar ativo e mês.
4. Para desempenho, filtre um ativo ou compare curvas base 100 em uma janela comum. Não some preços, retornos ou índices entre empresas.
5. Não some return_daily para apresentar retorno acumulado; utilize composição de fatores ou a razão de preços da mesma janela. Não agregue volatilidade/momentum como somas.
6. Retorno mensal e média bruta MoM são medidas distintas; mensal.csv já as separa. Preserve os vazios do primeiro mês e confira as flags de períodos parciais. Se um filtro muda a janela, recompute o indicador com a definição desejada; as colunas pré-calculadas mantêm a referência da geração, não mudam semanticamente por filtrar um visual.
7. Use volume como quantidade de ações. Não chame de valor financeiro ou liquidez completa. Não apresente o calendário fictício como sessões NASDAQ.

As sugestões de páginas são: evolução normalizada, matriz de retornos mensais, volume e medidas de risco descritivas. narrativa.txt é um resumo Python da janela inteira, não Smart Narrative e não responde automaticamente a filtros Power BI.

Nenhuma medida DAX foi executada nesta etapa; não se publicam fórmulas como homologadas sem execução no respectivo motor. Os gráficos PNG são as visualizações verificadas na versão pública.
