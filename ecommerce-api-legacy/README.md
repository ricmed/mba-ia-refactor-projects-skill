# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express usada como entrada do desafio `refactor-arch`.

> Refatorado para o padrão MVC pela skill [`refactor-arch`](.claude/skills/refactor-arch/SKILL.md)
> (copiada de `code-smells-project/.claude/skills/refactor-arch`, sem nenhuma alteração —
> prova de que a skill é agnóstica de tecnologia).
> Relatório de auditoria original: [`reports/audit-project-2.md`](../reports/audit-project-2.md).

## Estrutura

```
src/
├── app.js                     # composition root
├── config/
│   ├── settings.js            # configuração via variáveis de ambiente
│   ├── database.js            # wrapper Promise sobre o driver sqlite3 + schema + seed
│   └── cache.js                # cache encapsulado (substitui o globalCache mutável)
├── models/
│   ├── userModel.js
│   ├── courseModel.js
│   ├── enrollmentModel.js
│   ├── paymentModel.js
│   ├── auditLogModel.js
│   └── reportModel.js          # relatório financeiro com JOIN único (sem N+1)
├── views/                      # mapeamento de rotas -> controller
│   ├── checkoutRoutes.js
│   ├── adminRoutes.js
│   └── userRoutes.js
├── controllers/
│   ├── checkoutController.js
│   ├── adminController.js
│   └── userController.js
├── services/
│   └── checkoutService.js      # regra de negócio de checkout, com transação
└── middlewares/
    └── errorHandler.js         # tratamento de erro centralizado
```

## Como rodar

```bash
npm install
cp .env.example .env   # opcional — valores padrão já funcionam localmente
npm start
```

A aplicação sobe em `http://localhost:3000`. O banco SQLite continua em memória e é
populado com o mesmo seed original no boot. Exemplos de requisições em `api.http`.

## Principais mudanças em relação à versão original

- `AppManager.js` (God Class) foi eliminado — schema/seed vive em `config/database.js`,
  rotas em `views/`, orquestração em `controllers/`, regra de negócio em `services/`.
- Checkout deixou de ser uma pirâmide de 5+ callbacks aninhados: agora é uma função
  `async/await` testável isoladamente, executada dentro de uma transação (`BEGIN`/`COMMIT`/`ROLLBACK`).
- `badCrypto` (hash artesanal reversível) substituído por `bcryptjs`.
- Credenciais e chave de gateway de pagamento saíram do código-fonte (`config/settings.js` + `.env`).
- `DELETE /api/users/:id` agora remove matrículas e pagamentos associados em vez de
  deixá-los órfãos no banco.
- Relatório financeiro (`/api/admin/financial-report`) resolvido com uma única query JOIN
  em vez de N+1 callbacks aninhados.
- `globalCache`/`totalRevenue` (estado global mutável) substituídos por uma instância de
  `Cache` encapsulada.
- Respostas padronizadas em JSON (antes misturava `res.send("texto")` e `res.json(...)`).

Detalhes completos dos problemas encontrados: [`reports/audit-project-2.md`](../reports/audit-project-2.md).
