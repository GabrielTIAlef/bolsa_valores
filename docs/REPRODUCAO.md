# Reprodução e publicação

Use Python 3.12 em ambiente virtual, instale requirements-lock.txt e execute pip check, scripts/run_tests.py, scripts/run_demo.py e scripts/validate_notebook.py. SQLite 3.37+ é necessário para tabelas STRICT. A instalação precisa dos pacotes; o processamento não acessa rede, APIs ou provedores de mercado.

Os scripts usam seu próprio caminho para localizar os módulos e podem ser chamados por caminho absoluto fora da raiz. O notebook deve ser aberto na raiz ou em notebooks/, ou executado pelo validador fornecido. Esse validador cria um kernel temporário do Python ativo, executa todas as células, encerra o kernel e só então registra sucesso. Não instala kernels globais ou salva saídas no notebook versionado.

`python scripts/run_demo.py --output outputs/outra_execucao` escolhe outro destino. A CLI sempre usa o gerador fictício, com seed=42. Para exploração de parâmetros, use o notebook e a API Python, mantendo os limites do contrato.

Cada execução prepara CSVs, SQLite, JSON, narrativa e gráficos numa pasta de staging. A base é fechada antes do cálculo de hashes. A pasta de geração é renomeada e latest.json é substituído no mesmo filesystem somente quando todas as etapas terminam. Se qualquer etapa anterior falha, o ponteiro confirmado anteriormente permanece válido.

Consumidores devem ler latest.json, localizar directory e conferir hashes. Não combinar dados de gerações diferentes. Uma falha ao confirmar pode deixar uma geração órfã, sem torná-la confirmada. O esquema não oferece transação distribuída, recuperação universal após falta de energia ou ordenação entre produtores concorrentes: vence o último replace. Evite escritores concorrentes quando a ordem for relevante.

Instalação fixada e semente permitem reproduzir os valores no ambiente validado. UUIDs dos manifestos, PNGs, binário SQLite e arredondamentos entre plataformas não são prometidos como bytes idênticos. Os testes e as tolerâncias tratam os valores analíticos, não uma identidade binária universal.

Não publique dados próprios em examples/ ou docs/evidence/. Essas pastas são reservadas a arquivos fictícios conferidos. Arquivos SQLite e outputs/ ficam ignorados; a demonstração pode ser reconstruída pelos comandos sem versionar bancos binários.
