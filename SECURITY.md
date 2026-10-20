# Segurança e procedência

Ativos e cotações publicados são fictícios, criados pelo gerador local. Não são preços NASDAQ, dados anonimizados ou retornos reais de empresas. Não é necessário autenticar em corretoras, bancos, Power BI ou sistemas corporativos.

A CLI só executa a demonstração. A API Python valida tabelas e metadados explicitamente fornecidos, mas não certifica origem, licença, anonimização ou veracidade da política de ajuste declarada. Não inclua nomes pessoais, caminhos internos, credenciais ou descrições privadas em campos aceitos. Metadados não previstos e colunas adicionais são rejeitados.

Entradas privadas devem permanecer fora de examples/ e docs/evidence/. Dados e saídas locais estão ignorados por padrão, assim como bancos SQLite e arquivos PBIX. Antes de publicar, confira as diferenças e os arquivos novos. Símbolos e nomes possuem formato restrito para reduzir risco de fórmula em CSV; as demais colunas de cotações são datas ISO e números.

A auditoria direcionada dos dois commits anteriores encontrou apenas README e não encontrou os padrões de credenciais examinados. Isso não garante ausência universal de segredos. Não houve reescrita histórica ou tentativa de validar credenciais.

As capturas de navegador das Fontes não foram republicadas: servem como referência visual histórica, sem restaurar links de sistemas, sessões ou artefatos confidenciais. Nenhum dado empresarial é necessário para reproduzir o projeto.
