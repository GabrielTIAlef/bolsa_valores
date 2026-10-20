# Contrato de ativos, sessões e cotações

A API utiliza `Dataset(assets, quotes, metadata)`. A CLI fornece somente `generate()`: não lê contas, provedores ou arquivos privados automaticamente. Até 20 ativos, 2000 sessões declaradas e 20000 cotações. Mesmo calendário e moeda USD para todos os ativos; IPOs, suspensões e múltiplos calendários não são representados por imputação.

## Tabelas

`assets`: exatamente symbol, name, currency, nesta ordem. symbol deve começar com letra maiúscula e conter até 16 letras maiúsculas, números ou sublinhado. É único. name contém até 64 letras ASCII, números, espaço, hífen ou sublinhado e começa com letra/número; não deve conter pessoas ou informações privadas. currency é USD.

`quotes`: exatamente symbol, date, open, high, low, close, adjusted_close, volume, nesta ordem. Chave única symbol/date. Data como texto ISO YYYY-MM-DD, entre 1900 e 2100, sem horário ou conversão silenciosa. A implementação ordena por ativo/data antes dos cálculos.

Preços devem ser números reais finitos, maiores que zero e até um bilhão. `low <= open/close <= high`, e low <= high. adjusted_close não precisa estar entre low e high: ele é uma série retroativamente ajustada por split. Volume é inteiro entre zero e um trilhão por observação; a soma aceita no lote é limitada para representação segura. Booleanos, complexos, strings numéricas, NaN e infinitos são rejeitados pela API.

## Metadados

Obrigatórios: synthetic (bool), currency (USD), adjustment_basis (split_only), calendar, coverage_start, coverage_end e sessions. Datas seguem o mesmo formato e domínio. sessions é lista ordenada e única, com 2–2000 datas dentro da cobertura. Exige-se exatamente uma observação de cada ativo em cada sessão declarada.

Campos opcionais permitidos: seed (inteiro de 0 a 2^32−1), origin (descrição de 1–300 caracteres) e split_demo (symbol/date/ratio). Campos adicionais são rejeitados para reduzir publicação acidental de configurações ou credenciais. Não inclua informações privadas em descrições aceitas: o contrato não certifica anonimização.

Calendário `synthetic_weekdays`: permitido somente com synthetic=true; as sessões precisam coincidir com todos os dias de segunda a sexta entre os limites. Não é calendário oficial de bolsa e não desconta feriados.

Calendário `declared_sessions`: aceita a lista explicitamente fornecida. A consistência interna é verificada, mas o sistema não consulta uma bolsa para certificar feriados ou completude dessa lista. Dados reais não podem ser marcados com calendário fictício. A origem sintética é declaração, não inferência automática.

Evento split_demo precisa referenciar ativo/data presentes e razão numérica positiva. É um metadado demonstrativo, não motor de validação de eventos corporativos reais. Não se recalcula ou inventa adjusted_close: a série fornecida deve obedecer à política split_only. Dividendos e retorno total não são suportados.

## Ausência e limites

Nenhuma linha é eliminada para esconder inconsistência. Não há forward fill, substituição de retorno ausente por zero, ou continuidade entre ativos. Primeiro retorno, janelas insuficientes e retorno mensal sem mês anterior consecutivo permanecem ausentes.

Completude mensal declarada exige cobertura desde o início até o fim civil do mês. Essa flag depende da declaração de sessões e intervalo: não certifica um calendário externo. Um retorno entre últimos preços observados pode ser calculado em mês parcial, mas as flags distinguem esse caso de dois meses totalmente cobertos.
