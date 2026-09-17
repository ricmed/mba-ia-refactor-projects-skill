```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      JavaScript (Node.js)
Framework:     Express 4.18.2
Dependencies:  sqlite3 ^5.1.6
Domain:        LMS — plataforma de cursos com fluxo de checkout (users, courses, enrollments, payments, audit_logs)
Architecture:  Monolito com God Class — AppManager concentra schema, seed, roteamento HTTP e regra de negócio de pagamento na mesma classe; utils.js mistura config e estado global mutável
Source files:  3 files analyzed (src/app.js, src/AppManager.js, src/utils.js)
DB tables:     users, courses, enrollments, payments, audit_logs
================================
```

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   Node.js + Express
Files:   3 analyzed | ~183 lines of code

## Summary
CRITICAL: 3 | HIGH: 3 | MEDIUM: 3 | LOW: 2

## Findings

### [CRITICAL] Hardcoded Credentials
File: src/utils.js:1-6
Description: `config` embute em código-fonte `dbPass: "senha_super_secreta_prod_123"`, `paymentGatewayKey: "pk_live_1234567890abcdef"` (chave de gateway de pagamento com aparência de chave **live**) e `smtpUser`.
Impact: Credenciais de produção e uma chave de pagamento real-like versionadas no Git; comprometimento imediato caso o repositório vaze.
Recommendation: Mover para variáveis de ambiente via módulo `config/settings.js` (RP1).

### [CRITICAL] God Class
File: src/AppManager.js:1-141
Description: A classe `AppManager` cria o schema do banco, popula dados de seed, define TODAS as rotas HTTP e executa a regra de negócio de checkout/pagamento e o relatório financeiro — tudo na mesma classe.
Impact: Impossível testar checkout ou relatório isoladamente; qualquer mudança de schema, rota ou regra de pagamento arrisca efeito colateral nas demais responsabilidades.
Recommendation: Separar em `models/` (acesso a dados por entidade), `views/routes` (mapeamento de rotas), `controllers/` (orquestração) e `services/` (regra de checkout) — RP4/RP5.

### [CRITICAL] Criptografia Quebrada para Senha
File: src/utils.js:17-23 (função `badCrypto`), usada em src/AppManager.js:68
Description: `badCrypto` não é uma função de hash criptográfico — apenas repete a codificação Base64 da senha 10.000 vezes e trunca o resultado; é determinística, reversível e sem salt.
Impact: Senhas de usuário podem ser recuperadas trivialmente a partir do "hash" armazenado; nenhuma proteção real contra vazamento de banco.
Recommendation: Substituir por `bcrypt`/`argon2` (RP7).

### [HIGH] Lógica de Negócio e Callback Hell na Rota de Checkout
File: src/AppManager.js:28-78
Description: O handler de `/api/checkout` aninha 5+ níveis de callbacks do driver SQLite, misturando validação de entrada, criação de usuário, "autorização" de pagamento fake (`cc.startsWith("4")`), matrícula e log de auditoria em uma única função — sem transação, então uma falha no meio da cadeia deixa dados parcialmente gravados (ex.: usuário criado sem matrícula).
Impact: Código impossível de testar unitariamente; risco real de inconsistência de dados em caso de erro parcial.
Recommendation: Extrair para `services/checkout_service.js` com funções compostas e uso de transação (RP5).

### [HIGH] Exclusão de Usuário Deixa Dados Órfãos Deliberadamente
File: src/AppManager.js:131-137
Description: `DELETE /api/users/:id` apaga o usuário mas mantém `enrollments` e `payments` associados, e a própria mensagem de resposta admite isso: "Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco."
Impact: Viola integridade referencial; relatórios financeiros e de matrícula passam a referenciar usuários inexistentes.
Recommendation: Excluir (ou anonimizar) os registros dependentes na mesma transação, ou usar exclusão lógica (soft delete) com `ON DELETE CASCADE`/verificação explícita.

### [HIGH] Estado Global Mutável
File: src/utils.js:9-10
Description: `globalCache = {}` e `totalRevenue = 0` são variáveis de módulo mutáveis, atualizadas por `logAndCache` a cada requisição, compartilhadas entre todas as requisições concorrentes.
Impact: Condição de corrida entre requisições simultâneas; `globalCache` cresce indefinidamente (vazamento de memória) sem nenhuma política de expiração.
Recommendation: Encapsular em uma classe `Cache` com API própria e ciclo de vida controlado (RP6).

### [MEDIUM] Query N+1 / Callbacks Aninhados no Relatório Financeiro
File: src/AppManager.js:80-129
Description: `/api/admin/financial-report` itera cursos, e para cada curso itera matrículas, e para cada matrícula faz mais 2 queries (usuário + pagamento) — tudo com callbacks aninhados e contadores manuais (`coursesPending`, `enrPending`) para saber quando finalizar a resposta.
Impact: Uma query por matrícula × 2 (N+1 severo); lógica de sincronização manual e propensa a bugs de contagem (ex.: corrida se `enrPending` chegar a 0 antes de todas as respostas).
Recommendation: Substituir por uma única query com `JOIN` entre `courses`, `enrollments`, `users` e `payments` (RP9).

### [MEDIUM] API Deprecated: driver `sqlite3` baseado em callback
File: src/AppManager.js (todas as chamadas `this.db.run/get/all(...)`), src/app.js:1
Description: O pacote `sqlite3` usado exclusivamente com API de callback é o padrão legado da biblioteca; não há uso de `async/await`, o que força o callback-hell relatado acima.
Impact: Reforça o acoplamento a callbacks aninhados; dificulta introduzir tratamento de erro consistente e transações.
Recommendation: Migrar para `better-sqlite3` (síncrono) ou envolver o driver atual em uma camada `promisify`/usar um ORM leve (Sequelize/Prisma) com `async/await`.

### [MEDIUM] Contrato de API Inconsistente e Sem Validação de Entrada
File: src/AppManager.js:35, 38, 41, 48, 51, 55, 60, 84, 133-136
Description: Respostas ora usam `res.status(400).send("Bad Request")` (texto puro), ora `res.json({...})`; não há nenhuma validação de schema/tipo dos campos recebidos em `/api/checkout` (aceita qualquer JSON).
Impact: Clientes da API não conseguem tratar erros de forma uniforme; payloads malformados podem chegar às camadas internas sem serem rejeitados cedo.
Recommendation: Padronizar todas as respostas em JSON e adicionar validação de entrada no controller/rota (RP10).

### [LOW] Nomenclatura de Variáveis Pouco Descritiva
File: src/AppManager.js:29-33
Description: Parâmetros extraídos do corpo da requisição recebem nomes de 1-2 letras sem significado: `u`, `e`, `p`, `cid`, `cc`.
Impact: Aumenta o esforço cognitivo para entender o fluxo de checkout; propenso a troca acidental de variáveis parecidas.
Recommendation: Renomear para `nomeUsuario`, `email`, `senha`, `cursoId`, `numeroCartao` (ou equivalente em inglês, conforme convenção do projeto).

### [LOW] Log de Dados Sensíveis no Console
File: src/AppManager.js:45
Description: `console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`)` grava o número completo do cartão e a chave do gateway de pagamento em texto puro no log da aplicação.
Impact: Qualquer pessoa com acesso aos logs (inclusive de infraestrutura terceirizada) vê dados de cartão e credencial de pagamento.
Recommendation: Nunca logar PAN de cartão nem segredos; se necessário depurar, mascarar (`**** **** **** 4444`).

================================
Total: 11 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```
