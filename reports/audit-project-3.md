```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python 3
Framework:     Flask 3.0.0 (flask-sqlalchemy 3.1.1, flask-cors 4.0.0)
Dependencies:  marshmallow 3.20.1 (declarada mas não usada), requests 2.31.0, python-dotenv 1.0.0 (declarada mas não usada)
Domain:        Task Manager (tasks, users, categories — prioridade, prazo, tags, notificações por e-mail)
Architecture:  Camadas parcialmente separadas (models/, routes/, services/, utils/ já existem), mas rotas fazem serialização manual e lógica de negócio duplicada em vez de reusar os Models
Source files:  15 files analyzed (app.py, database.py, seed.py, models/{__init__,task,user,category}.py, routes/{__init__,task_routes,user_routes,report_routes}.py, services/{__init__,notification_service}.py, utils/{__init__,helpers}.py)
DB tables:     tasks, users, categories
================================
```

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask (com Flask-SQLAlchemy)
Files:   15 analyzed | ~1156 lines of code

## Summary
CRITICAL: 2 | HIGH: 2 | MEDIUM: 4 | LOW: 3

## Findings

### [CRITICAL] Hardcoded Credentials
File: app.py:13; services/notification_service.py:9-10
Description: `app.config['SECRET_KEY'] = 'super-secret-key-123'`; `NotificationService` embute usuário e senha de SMTP (`taskmanager@gmail.com` / `senha123`) diretamente no código.
Impact: Credenciais de e-mail e chave de assinatura da aplicação versionadas no Git.
Recommendation: Mover para `config/settings.py` lido de variáveis de ambiente (RP1).

### [CRITICAL] Hashing de Senha Quebrado (MD5) e Exposição do Hash na API
File: models/user.py:16-25, 27-32; routes/user_routes.py:33, 85-86, 129
Description: `set_password`/`check_password` usam `hashlib.md5` sem salt (API deprecated para uso de senha — ver tabela de APIs deprecated); `User.to_dict()` retorna o campo `password` (o hash) e é usado diretamente pelas rotas de detalhe/criação/atualização de usuário, expondo o hash a qualquer chamador.
Impact: MD5 é quebrado para senha (colisão e força-bruta triviais); o hash exposto na API piora ainda mais o risco, permitindo ataque offline direto.
Recommendation: Trocar para `werkzeug.security.generate_password_hash`/`check_password_hash` (RP7) e remover `password` da serialização pública (RP8).

### [HIGH] Duplicação de Lógica de Negócio (cálculo de "atrasado")
File: models/task.py:50-60 (`is_overdue`, já existe!); routes/task_routes.py:30-39, 71-80; routes/user_routes.py:171-180; routes/report_routes.py:34-43
Description: A regra "task atrasada" (`due_date < agora` E `status not in (done, cancelled)`) já está implementada como método do Model (`Task.is_overdue`), mas é **reimplementada manualmente** com o mesmo `if` aninhado em mais 4 lugares diferentes nas rotas, em vez de chamar o método existente.
Impact: Qualquer ajuste na regra (ex.: novo status terminal) exige lembrar de replicar em 5 lugares; alto risco de divergência silenciosa.
Recommendation: Substituir toda reimplementação por chamadas a `task.is_overdue()`.

### [HIGH] Autenticação Falsa / Nenhuma Rota Protegida
File: routes/user_routes.py:185-211
Description: `/login` gera um token fake (`'fake-jwt-token-' + str(user.id)`, linha 210) sem assinatura nem expiração real; nenhuma rota do sistema (tasks, categories, reports) verifica esse ou qualquer outro token — todos os endpoints estão completamente abertos.
Impact: Falsa sensação de segurança; qualquer cliente pode ler/alterar/excluir tasks e usuários de qualquer pessoa sem se autenticar.
Recommendation: Implementar JWT real (`PyJWT`/`flask-jwt-extended`) e um middleware/decorator de autenticação aplicado às rotas sensíveis.

### [MEDIUM] Query N+1
File: routes/task_routes.py:41-57 (busca `User`/`Category` por task, dentro do loop de `get_tasks`); routes/report_routes.py:53-68 (`summary_report` busca tasks de cada usuário em loop)
Description: Em vez de `JOIN`/eager loading, cada task dispara até 2 queries adicionais, e o relatório de produtividade dispara 1 query de tasks por usuário.
Impact: Tempo de resposta cresce linearmente com o número de tasks/usuários.
Recommendation: Usar `db.session.query(Task).options(db.joinedload(Task.user), db.joinedload(Task.category))` (RP9).

### [MEDIUM] API Deprecated: `Model.query.get(id)`
File: routes/task_routes.py:42, 51, 67, 117, 122, 157, 188, 195; routes/user_routes.py:29, 94, 136, 155; routes/report_routes.py:105, 159, 192, 213
Description: O projeto usa `SomeModel.query.get(id)` (API "legacy query" do SQLAlchemy) em mais de 15 pontos — no SQLAlchemy 2.0 (que o Flask-SQLAlchemy 3.1.1 usa internamente) esse padrão está marcado como legado, mantido apenas por compatibilidade.
Impact: Acoplamento a uma API destinada à remoção futura; inconsistente com o estilo 2.0 recomendado pelo próprio SQLAlchemy.
Recommendation: Substituir por `db.session.get(SomeModel, id)`.

### [MEDIUM] Falta de Paginação
File: routes/task_routes.py:11-63 (`get_tasks`); routes/user_routes.py:10-25 (`get_users`)
Description: Ambos os endpoints de listagem retornam **todos** os registros da tabela sem `limit`/`offset`/`page`.
Impact: Payload cresce sem limite conforme a base de dados cresce; não escala para produção.
Recommendation: Adicionar paginação via query params (RP10).

### [MEDIUM] Dependências Declaradas e Não Usadas Mascarando Ausência de Validação/Config
File: requirements.txt:4 (`marshmallow`), requirements.txt:6 (`python-dotenv`)
Description: `marshmallow` está no `requirements.txt` mas nenhuma rota usa schema de validação (todas validam campo a campo manualmente); `python-dotenv` está declarado mas nenhum arquivo chama `load_dotenv()` nem lê `os.environ` — a configuração (linhas 11-13 de `app.py`) continua 100% hardcoded.
Impact: Sugere uma tentativa de introduzir boas práticas que nunca foi concluída; desenvolvedores podem assumir, erroneamente, que a validação/config via env já existe.
Recommendation: Ou remover as dependências não usadas, ou efetivamente adotá-las (schemas Marshmallow nas rotas, `load_dotenv()` + `os.environ` em `config/settings.py`).

### [LOW] Bare `except` Genérico
File: routes/task_routes.py:62; routes/user_routes.py:130, 149
Description: Blocos `except:` sem especificar o tipo de exceção, escondendo a causa real do erro (inclusive erros de programação, não só de banco).
Impact: Debugging em produção fica muito mais difícil; pode mascarar bugs sérios como `KeyError`/`AttributeError`.
Recommendation: Capturar exceções específicas (ex.: `except SQLAlchemyError as e`) e logar `str(e)`.

### [LOW] Imports Não Utilizados
File: app.py:7 (`os, sys, json`); routes/task_routes.py:7 (`json, os, sys, time`); routes/report_routes.py:8 (`json`)
Description: Módulos importados e nunca referenciados no corpo do arquivo.
Impact: Ruído de leitura; pode indicar código morto ou refatoração incompleta.
Recommendation: Remover os imports não utilizados.

### [LOW] Constantes Definidas mas Não Reaproveitadas
File: utils/helpers.py:110-116 (`VALID_STATUSES`, `MIN_TITLE_LENGTH`, `MAX_TITLE_LENGTH`, `DEFAULT_PRIORITY`, `DEFAULT_COLOR`); routes/task_routes.py (literais `'pending'`, `3`, `200`, `4` repetidos); routes/user_routes.py (mesma lista de status/roles repetida)
Description: O módulo `utils/helpers.py` já centraliza as constantes corretas, mas as rotas continuam usando os literais soltos em vez de importar essas constantes.
Impact: Se um valor mudar (ex.: título máximo passar de 200 para 300), é preciso lembrar de atualizar em todos os pontos manualmente.
Recommendation: Importar e usar as constantes de `utils/helpers.py` em vez de duplicar os literais.

================================
Total: 11 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```
