# Entradas fictícias

ativos.csv, cotacoes.csv e metadata.json são produzidos por `bolsa.synthetic.generate(seed=42)`. Todos os registros são inventados e não representam empresas, cotações ou pregões reais. A demonstração gera as entradas novamente; não depende desses arquivos para executar.

Há seis ativos, um calendário de segunda a sexta em 2024 e um split fictício 2:1 em DEMO_A. O ajuste é somente por split; não inclui dividendos. USD é a unidade monetária de apresentação fictícia. Os dias do calendário podem coincidir com feriados reais: não se trata de calendário NASDAQ.

As tabelas e os metadados seguem docs/CONTRATO_DADOS.md. A API Dataset aceita sua leitura por Pandas com symbol/date textuais; não há integração com fontes reais nesta versão.
