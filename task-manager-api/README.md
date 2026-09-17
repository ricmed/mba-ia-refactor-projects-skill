# task-manager-api

API de Task Manager em Python/Flask usada como entrada do desafio `refactor-arch`. Diferente
dos outros projetos, este já possuía alguma separação de camadas (`models/`, `routes/`,
`services/`, `utils/`) — a skill refinou essa organização em vez de recriá-la do zero.

> Refatorado pela skill [`refactor-arch`](.claude/skills/refactor-arch/SKILL.md) (cópia
> idêntica da usada em `code-smells-project`).
> Relatório de auditoria original: [`reports/audit-project-3.md`](../reports/audit-project-3.md).

## Estrutura

```
app.py                          # composition root
config/
└── settings.py                 # configuração via variáveis de ambiente (.env)
controllers/                    # NOVO — lógica de orquestração movida das rotas
├── task_controller.py
├── user_controller.py
├── report_controller.py
└── category_controller.py
routes/                         # agora só mapeamento rota -> controller
├── task_routes.py
├── user_routes.py
├── report_routes.py
└── category_routes.py          # NOVO — separado de report_routes.py
models/                         # mantido (já existia e já era adequado)
├── task.py
├── user.py
└── category.py
services/
└── notification_service.py     # credenciais SMTP agora vêm de config/settings.py
utils/
└── helpers.py                  # constantes e validações — agora efetivamente usadas pelas rotas
middlewares/                    # NOVO
├── error_handler.py            # tratamento de erro centralizado
└── auth.py                     # decorator de JWT pronto para adoção incremental (ver abaixo)
```

## Como rodar

```bash
pip install -r requirements.txt
cp .env.example .env   # opcional — valores padrão já funcionam localmente
python seed.py
python app.py
```

A aplicação sobe em `http://localhost:5000`.

## Principais mudanças em relação à versão original

- Lógica de orquestração movida de `routes/*.py` para `controllers/*.py` — rotas agora só
  mapeiam método+path para a função do controller.
- Hashing de senha trocado de `hashlib.md5` (quebrado) para `werkzeug.security.generate_password_hash`.
- `User.to_dict()` não retorna mais o hash da senha em nenhum endpoint.
- `SECRET_KEY` e credenciais SMTP saíram do código para `config/settings.py` + `.env`.
- Cálculo de "task atrasada", antes reimplementado em 5 lugares diferentes, agora usa
  `Task.is_overdue()` (chamado a partir de `to_dict()`), com uma única fonte de verdade.
- N+1 do relatório de produtividade (`/reports/summary`) e da listagem de tasks (`/tasks`)
  resolvido com agregação SQL (`GROUP BY`) e `joinedload`, respectivamente.
- `Model.query.get(id)` (API legacy do SQLAlchemy) substituído por `db.session.get(Model, id)`
  em todas as rotas.
- Login agora emite um JWT real e assinado (`PyJWT`), com expiração — antes era a string fixa
  `"fake-jwt-token-" + id`. Um decorator `middlewares/auth.py` (`require_auth`) já está pronto
  para proteger rotas, mas **não foi aplicado a nenhum endpoint nesta refatoração** para não
  quebrar o contrato de API existente (nenhuma rota exigia token antes); é um follow-up
  recomendado e documentado, não uma correção silenciosamente incompleta.
- Dependências não usadas (`marshmallow`, `requests`) removidas; `python-dotenv` (já declarada)
  passou a ser efetivamente usada em `config/settings.py`.
- Suporte a paginação opcional (`?page=&per_page=`) em `/tasks` e `/users`.
- Imports não utilizados removidos (`utils/helpers.py`, `routes/*.py`, `app.py`).

Detalhes completos dos problemas encontrados: [`reports/audit-project-3.md`](../reports/audit-project-3.md).
