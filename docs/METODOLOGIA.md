# Metodologia e fórmulas

## Dados e ajuste

A demonstração gera seis ativos fictícios DEMO_A–DEMO_F com semente 42. Séries geométricas com ruído são uma escolha para testar análise temporal; não são calibração, previsão ou reconstrução de uma população financeira real. Abertura, máxima e mínima são inventadas de forma coerente; volume é quantidade inteira simulada.

O calendário contém dias de segunda a sexta de 2024, sem remover feriados. Os 252 usados na anualização constituem uma convenção fixa, não a contagem de sessões desse gerador.

DEMO_A tem fator bruto 2 antes do evento e 1 depois; adjusted_close acompanha o processo latente em toda a janela. A série ajustada, portanto, não sofre a perda mecânica de 50% observada no preço bruto quando ocorre o split. Ela ainda pode variar por causa do ruído diário. Dividendos não são simulados ou incluídos no retorno.

## Medidas por ativo

Com P(t) como adjusted_close:

- Diário: r(t) = P(t)/P(t−1)−1. O primeiro retorno é ausente.
- Retorno de preço no intervalo: P(final)/P(inicial)−1. Equivale ao produto de (1+r) menos um nos retornos válidos, não à soma dos retornos.
- Mensal: último P observado no mês / último P do mês anterior consecutivo −1. Sem mês anterior consecutivo, valor ausente. Primeiro mês não tem retorno mensal calculável.
- Média bruta MoM: média(close) do mês / média(close) do mês anterior consecutivo −1. Não equivale ao retorno mensal e pode ser afetada mecanicamente por splits.
- Base 100: 100×P(t)/P(inicial).
- Drawdown: P(t)/max(P(0..t))−1. O resumo publica o menor valor, com referência ao início da janela observada, sem alegar máximo histórico fora dela.
- Volatilidade: desvio-padrão amostral (ddof=1) dos retornos, multiplicado por raiz de 252. Móvel: 20 retornos completos. No resumo: todos os retornos válidos do intervalo, com mínimo de dois. Janelas insuficientes permanecem ausentes.
- Momentum: P(t)/P(t−21)−1, com defasagem de 21 observações do calendário declarado, sem interpretação automática de sinal de negociação.
- Volume: soma de ações brutas por intervalo. Não é dinheiro, spread, profundidade ou prova suficiente de liquidez. Comparabilidade pode mudar em eventos de split.

As séries são ordenadas antes do cálculo; agrupamentos e janelas nunca atravessam ativos. Preços de ativos distintos não são somados para produzir desempenho. Percentuais são frações nos arquivos e multiplicados por 100 somente para apresentação.

## SQL e precisão

O SQLite usa dimensões de ativo/data e fato diária com chave composta. `vw_mensal` calcula contagem, média de close, volume e último adjusted_close observado. `vw_mensal_retorno` usa LAG por ativo e exige índice de mês consecutivo antes de calcular as duas variações.

Cada carga valida o Dataset antes da transação. Falhas de inserção fazem rollback, preservando o snapshot anterior nos testes de carga. O pipeline monta um arquivo SQLite novo por geração e reconcilia as chaves e seis colunas mensais com Pandas, usando tolerância numérica de 1e−10 e igualdade de valores ausentes.

Preços e indicadores analíticos são ponto flutuante; não se trata de livro contábil, cálculo tributário ou liquidação financeira. Volume é inteiro. SQL/Python usam aritmética independente para conferir as agregações e os retornos mensais; isso não valida dados reais ou qualquer medida DAX.

## Referências técnicas

- [Pandas pct_change: variação fracionária](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.pct_change.html)
- [NumPy std e ddof](https://numpy.org/doc/stable/reference/generated/numpy.std.html)
- [SQLite: foreign keys](https://www.sqlite.org/foreignkeys.html)
- [SQLite: tabelas STRICT](https://www.sqlite.org/stricttables.html)

O painel histórico descrevia objetivos de BI e investimento. Esta reconstrução comprova processamento, cálculos e apresentação sobre dados fictícios, sem inferir resultado comercial, retorno total ou adequação a decisões de investimento.
