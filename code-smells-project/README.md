# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`.

> Refatorado para o padrão MVC pela skill [`refactor-arch`](.claude/skills/refactor-arch/SKILL.md).
> Relatório de auditoria original: [`reports/audit-project-1.md`](../reports/audit-project-1.md).

## Estrutura

```
src/
├── app.py                  # composition root
├── config/
│   ├── settings.py         # configuração via variáveis de ambiente
│   └── database.py         # conexão SQLite + schema + seed
├── models/
│   ├── produto_model.py
│   ├── usuario_model.py
│   └── pedido_model.py
├── views/                  # definição de rotas (mapeamento HTTP -> controller)
│   ├── general_routes.py
│   ├── produto_routes.py
│   ├── usuario_routes.py
│   └── pedido_routes.py
├── controllers/
│   ├── produto_controller.py
│   ├── usuario_controller.py
│   └── pedido_controller.py
└── middlewares/
    └── error_handler.py    # tratamento de erro centralizado
```

## Como rodar

```bash
pip install -r requirements.txt
cp .env.example .env   # opcional — valores padrão já funcionam localmente
python src/app.py
```

A aplicação sobe em `http://localhost:5000`. O banco SQLite (`loja.db`) é criado
automaticamente no primeiro boot, já com produtos e usuários de exemplo (senhas
armazenadas com hash, nunca em texto puro).

## Principais mudanças em relação à versão original

- Removida toda concatenação de SQL (SQL Injection) — todas as queries usam bind params.
- Removidos os endpoints `/admin/reset-db` e `/admin/query` (execução arbitrária de SQL sem autenticação).
- Senhas passam a ser hasheadas com `werkzeug.security.generate_password_hash`.
- Endpoints de usuário e `/health` não retornam mais senha/hash nem `SECRET_KEY`/`debug`.
- `SECRET_KEY`, porta, host e path do banco vêm de variáveis de ambiente (`config/settings.py`).
- N+1 de pedidos/itens resolvido com `JOIN` único.
- Suporte a paginação opcional (`?limit=&offset=`) nas listagens.
- Logging estruturado (`logging`) no lugar de `print()`.

Detalhes completos dos problemas encontrados: [`reports/audit-project-1.md`](../reports/audit-project-1.md).
