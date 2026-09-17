# Refactor Arch — Auditoria e Refatoração Arquitetural Automatizada com Skills

Este repositório é a entrega do desafio **"Criação de Skills — Refatoração Arquitetural
Automatizada"**. Contém a skill [`refactor-arch`](code-smells-project/.claude/skills/refactor-arch/SKILL.md)
(criada com **Claude Code**, no formato `SKILL.md` + arquivos de referência em Markdown) e o
resultado de sua execução, em 3 fases, sobre os 3 projetos legados fornecidos:

| # | Projeto | Stack | Organização original |
|---|---|---|---|
| 1 | [`code-smells-project/`](code-smells-project/) | Python + Flask | Monolito de 4 arquivos, sem camadas |
| 2 | [`ecommerce-api-legacy/`](ecommerce-api-legacy/) | Node.js + Express | God Class (`AppManager`) |
| 3 | [`task-manager-api/`](task-manager-api/) | Python + Flask | Camadas parciais (`models/`, `routes/`, `services/`, `utils/`) |

Relatórios de auditoria (saída da Fase 2, gerados pela skill antes de qualquer alteração):
[`reports/audit-project-1.md`](reports/audit-project-1.md) ·
[`reports/audit-project-2.md`](reports/audit-project-2.md) ·
[`reports/audit-project-3.md`](reports/audit-project-3.md).

---

## A) Análise Manual

Leitura de código feita antes de escrever a skill, para entender os problemas que ela
precisaria detectar. Os achados abaixo foram depois confirmados (e expandidos) pela
execução formal da Fase 2 da skill nos relatórios em `reports/`.

### Projeto 1 — `code-smells-project` (Python/Flask, E-commerce)

| Severidade | Problema | Onde | Por que é relevante |
|---|---|---|---|
| CRITICAL | SQL Injection generalizado | `models.py` (praticamente toda função, ex. `login_usuario` linha 109-111) | Toda query é concatenação de string com entrada do usuário — permite bypass de login (`' OR '1'='1`) e leitura/escrita arbitrária no banco. |
| CRITICAL | Endpoint `/admin/query` executa qualquer SQL enviado no corpo da requisição, sem autenticação | `app.py:59-78` | Equivale a um shell SQL público — comprometimento total do banco por qualquer cliente HTTP. |
| CRITICAL | `SECRET_KEY` hardcoded e devolvida em `/health` junto com `debug: True` | `app.py:7`; `controllers.py:264-292` | Segredo da aplicação vaza tanto pelo código-fonte quanto por uma resposta HTTP pública. |
| HIGH | Senhas armazenadas e comparadas em texto puro | `models.py:105-131` | Qualquer vazamento de banco expõe a senha real do usuário (reaproveitada em outros sistemas, tipicamente). |
| MEDIUM | Query N+1 ao montar pedidos com itens | `models.py:171-233` | Uma query por pedido + uma por item — não escala com o volume de dados. |
| MEDIUM | CORS liberado para qualquer origem, sem paginação nas listagens | `app.py:9`; `controllers.py:5-12` | Superfície desnecessariamente ampla; payload de resposta cresce sem limite. |
| LOW | `print()` como logging e listas de categoria/percentuais de desconto hardcoded | `controllers.py` (múltiplas linhas); `models.py:256-262` | Sem observabilidade estruturada; qualquer mudança de regra exige caçar o literal no código. |

### Projeto 2 — `ecommerce-api-legacy` (Node.js/Express, LMS com checkout)

| Severidade | Problema | Onde | Por que é relevante |
|---|---|---|---|
| CRITICAL | Credenciais e chave de gateway de pagamento (`pk_live_...`) hardcoded | `src/utils.js:1-6` | Chave com aparência de produção versionada no Git. |
| CRITICAL | `AppManager` é uma God Class: schema, seed, rotas e regra de pagamento no mesmo arquivo | `src/AppManager.js:1-141` | Impossível testar isoladamente; qualquer mudança arrisca efeito colateral em tudo. |
| CRITICAL | "Hash" de senha artesanal e reversível (`badCrypto`) | `src/utils.js:17-23` | Não é criptografia real — senha pode ser recuperada trivialmente. |
| HIGH | Checkout com 5+ níveis de callbacks aninhados, sem transação | `src/AppManager.js:28-78` | Falha no meio da cadeia deixa dados parcialmente gravados; impossível testar unitariamente. |
| MEDIUM | Relatório financeiro com N+1 severo (query por curso × matrícula × aluno) | `src/AppManager.js:80-129` | Contadores manuais (`coursesPending`/`enrPending`) além de lento, são propensos a bugs de sincronização. |
| MEDIUM | Respostas inconsistentes (`res.send("texto")` vs `res.json(...)`) | `src/AppManager.js` (várias linhas) | Clientes da API não conseguem tratar erros de forma previsível. |
| LOW | `DELETE /api/users/:id` deixa matrículas/pagamentos órfãos de propósito (a própria mensagem admite) | `src/AppManager.js:131-137` | Viola integridade referencial dos dados. |

### Projeto 3 — `task-manager-api` (Python/Flask, Task Manager, parcialmente organizado)

| Severidade | Problema | Onde | Por que é relevante |
|---|---|---|---|
| CRITICAL | Hashing de senha com MD5 sem salt, e o hash é retornado pela API | `models/user.py:16-32`; usado em `routes/user_routes.py` | MD5 é quebrado para senha; expor o hash na resposta piora ainda mais, permitindo ataque offline direto. |
| CRITICAL | `SECRET_KEY` e credenciais SMTP hardcoded | `app.py:13`; `services/notification_service.py:9-10` | Mesma classe de risco do Projeto 1: segredos versionados no Git. |
| HIGH | Regra de "task atrasada" reimplementada manualmente em 5 lugares, embora já exista `Task.is_overdue()` | `models/task.py:50-60` + 4 rotas | Qualquer ajuste de regra exige lembrar de replicar em todos os pontos — alto risco de divergência. |
| HIGH | Login gera token fake (`"fake-jwt-token-" + id`) e nenhuma rota verifica autenticação | `routes/user_routes.py:185-211` | Falsa sensação de segurança; API inteira está de fato aberta. |
| MEDIUM | Query N+1 no relatório de produtividade por usuário | `routes/report_routes.py:53-68` | 1 query de tasks por usuário em vez de agregação SQL. |
| MEDIUM | Dependências declaradas e nunca usadas (`marshmallow`, `python-dotenv`) | `requirements.txt` | Sugere validação/config via env que na prática nunca foi implementada — configuração continua hardcoded. |
| LOW | `except:` genérico e imports não utilizados | `routes/task_routes.py:62`; `app.py:7` | Esconde a causa real de erros; ruído de leitura. |

---

## B) Construção da Skill

### Decisões de design

A skill vive em `.claude/skills/refactor-arch/` e segue o formato de *progressive disclosure*
recomendado pela documentação de Skills do Claude Code: um `SKILL.md` enxuto que **orquestra**
as 3 fases e decide **quando** carregar cada arquivo de referência, em vez de um único arquivo
gigante carregado de uma vez.

```
.claude/skills/refactor-arch/
├── SKILL.md                              # orquestra Fase 1 → 2 → 3, com frontmatter (name/description)
└── references/
    ├── 01-project-analysis.md            # heurísticas de detecção (Fase 1)
    ├── 02-antipattern-catalog.md         # 12 anti-patterns + tabela de APIs deprecated (Fase 2)
    ├── 03-report-template.md             # formato exato do relatório de auditoria (Fase 2)
    ├── 04-mvc-guidelines.md               # regras da arquitetura alvo (Fase 3)
    └── 05-refactoring-playbook.md         # 10 padrões de transformação com antes/depois (Fase 3)
```

- **`SKILL.md`** é o "prompt": diz o que fazer em cada fase, quando parar para pedir
  confirmação, e qual referência ler em cada momento — mas não contém o conhecimento de
  domínio em si (isso fica nas referências), para que o `SKILL.md` continue pequeno e legível.
- **Cada referência cobre exatamente uma das 5 áreas de conhecimento exigidas** pelo desafio
  (análise de projeto, catálogo de anti-patterns, template de relatório, guidelines de MVC,
  playbook de refatoração) — nenhuma mistura de responsabilidades entre arquivos.
- **Sinais de detecção são acionáveis, não vagos**: cada anti-pattern do catálogo tem uma
  seção "Sinal de detecção" com o padrão de código literal a procurar (ex. "query SQL
  montada por concatenação/f-string com entrada do usuário", não "código inseguro").

### Anti-patterns incluídos no catálogo (12 no total, mínimo exigido: 8)

Hardcoded Credentials, SQL Injection, Endpoint de execução arbitrária, God Class/Module,
Lógica de negócio em Controller/Rota, Estado Global Mutável, Criptografia quebrada de senha,
Exposição de dados sensíveis na resposta, Query N+1, Falta de validação/paginação, Duplicação
de lógica/`except` genérico, Nomenclatura/magic numbers — cobrindo as 4 severidades exigidas
(CRITICAL → LOW) e mapeados 1:1 para os problemas reais encontrados nos 3 projetos-alvo. A
seção de **APIs deprecated** é uma tabela separada dentro do catálogo (MD5 para senha, `debug=True`
em produção, `@app.before_first_request`, driver `sqlite3` por callback, `body-parser`
standalone, `new Buffer()`, `Query.get()` do SQLAlchemy, `datetime.utcnow()`), verificada em
toda execução da Fase 2 mesmo quando o resultado é "nenhuma encontrada".

### Como a skill garante ser agnóstica de tecnologia

- **Nenhuma heurística assume uma stack fixa**: a Fase 1 detecta linguagem/framework por
  manifesto de dependências (`requirements.txt`, `package.json`, etc.) em vez de assumir
  Python de antemão.
- **O catálogo de anti-patterns é descrito por padrão estrutural, não por sintaxe de uma
  linguagem específica** (ex. "montagem de query por concatenação" se aplica igualmente a
  Python, JS, PHP, Java), com exemplos em mais de uma linguagem quando ajuda a generalizar.
- **O playbook traz exemplos em Python/Flask e Node.js/Express lado a lado** para o mesmo
  padrão de transformação, deixando explícito que a receita é a mesma independentemente da
  sintaxe.
- **Prova empírica**: a mesma pasta `refactor-arch/` foi **copiada sem nenhuma alteração**
  para `ecommerce-api-legacy/` (Node.js) e `task-manager-api/` (Flask com camadas parciais) e
  produziu relatórios de qualidade equivalente nos 3 projetos (ver seção C).

### Desafios encontrados e como foram resolvidos

- **Risco de relatório genérico demais**: a primeira versão do catálogo descrevia os
  anti-patterns em termos abstratos demais para gerar findings com arquivo:linha exatos.
  Resolvido reescrevendo cada "Sinal de detecção" como um padrão de código literal
  (concatenação de string em `cursor.execute`, `except:` vazio, etc.), o que tornou a
  varredura determinística.
- **Projeto 3 já tinha camadas — recriar do zero seria destrutivo**: a Fase 3 originalmente
  assumia sempre criar `src/{models,views,controllers}` do zero. Adicionada explicitamente a
  seção "Quando o projeto já tem alguma separação" nas guidelines de MVC, instruindo a mover
  apenas o que viola a responsabilidade da camada (lógica de negócio das rotas → novo
  `controllers/`) e manter os nomes de pasta já corretos (`models/`, `services/`, `utils/`).
- **Risco de a Fase 3 quebrar o contrato de API ao "corrigir demais"**: por exemplo, aplicar
  autenticação obrigatória a todas as rotas do Projeto 3 (para resolver o finding HIGH de
  "autenticação falsa") quebraria todos os endpoints hoje abertos. Resolvido com uma regra
  explícita no `SKILL.md` ("preserve o comportamento externo, exceto quando a própria correção
  do finding é uma melhoria de segurança esperada") e uma decisão documentada de emitir um JWT
  real no login mas **não** aplicar o middleware de autorização a rotas existentes nesta
  rodada — deixado como follow-up explícito em vez de uma correção parcial disfarçada de
  completa.
- **Callback hell do Node (Projeto 2) dificultava extrair regra de negócio**: resolvido
  encapsulando o driver `sqlite3` em uma classe `Database` com métodos que retornam Promise,
  o que permitiu reescrever o checkout como uma função `async/await` linear antes de movê-la
  para `services/checkoutService.js`.

---

## C) Resultados

### Findings por severidade (Fase 2, antes de qualquer alteração)

| Projeto | CRITICAL | HIGH | MEDIUM | LOW | Total |
|---|---|---|---|---|---|
| 1 — code-smells-project | 5 | 2 | 2 | 2 | **11** |
| 2 — ecommerce-api-legacy | 3 | 3 | 3 | 2 | **11** |
| 3 — task-manager-api | 2 | 2 | 4 | 3 | **11** |

Relatórios completos: [`reports/audit-project-1.md`](reports/audit-project-1.md) ·
[`reports/audit-project-2.md`](reports/audit-project-2.md) ·
[`reports/audit-project-3.md`](reports/audit-project-3.md).

### Antes / Depois da estrutura

**Projeto 1** — de 4 arquivos soltos na raiz para MVC completo:
```
Antes                       Depois
app.py                      src/app.py                 (composition root)
controllers.py              src/config/{settings,database}.py
models.py                   src/models/{produto,usuario,pedido}_model.py
database.py                 src/views/{general,produto,usuario,pedido}_routes.py
                             src/controllers/{produto,usuario,pedido}_controller.py
                             src/middlewares/error_handler.py
```

**Projeto 2** — de uma God Class para MVC + services:
```
Antes                       Depois
src/app.js                  src/app.js                  (composition root)
src/AppManager.js           src/config/{settings,database,cache}.js
src/utils.js                src/models/{user,course,enrollment,payment,auditLog,report}Model.js
                             src/views/{checkout,admin,user}Routes.js
                             src/controllers/{checkout,admin,user}Controller.js
                             src/services/checkoutService.js
                             src/middlewares/errorHandler.js
```

**Projeto 3** — camadas mantidas, controllers extraídos das rotas:
```
Antes                        Depois
app.py                       app.py                      (composition root, agora usa config/)
database.py                  config/settings.py           NOVO
models/{task,user,category}  models/{task,user,category}  (mantidos, hashing corrigido)
routes/{task,user,report}    routes/{task,user,report,category}_routes.py (agora só mapeamento)
services/notification_...    controllers/{task,user,report,category}_controller.py  NOVO
utils/helpers.py             services/notification_service.py (config via env)
                              utils/helpers.py (constantes agora usadas)
                              middlewares/{error_handler,auth}.py  NOVO
```

### Checklist de Validação

Preenchido para os 3 projetos após a execução completa da skill:

**Projeto 1 — code-smells-project**
```
### Fase 1 — Análise
- [x] Linguagem detectada corretamente (Python 3)
- [x] Framework detectado corretamente (Flask 3.1.1)
- [x] Domínio da aplicação descrito corretamente (E-commerce: produtos/usuários/pedidos)
- [x] Número de arquivos analisados condiz com a realidade (4)

### Fase 2 — Auditoria
- [x] Relatório segue o template definido nos arquivos de referência
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [x] Mínimo de 5 findings identificados (11)
- [x] Detecção de APIs deprecated incluída (debug=True em produção)
- [x] Skill pausa e pede confirmação antes da Fase 3

### Fase 3 — Refatoração
- [x] Estrutura de diretórios segue padrão MVC
- [x] Configuração extraída para módulo de config (sem hardcoded)
- [x] Models criados para abstrair dados
- [x] Views/Routes separadas para roteamento
- [x] Controllers concentram o fluxo da aplicação
- [x] Error handling centralizado
- [x] Entry point claro (src/app.py)
- [x] Aplicação inicia sem erros
- [x] Endpoints originais respondem corretamente
```

**Projeto 2 — ecommerce-api-legacy**
```
### Fase 1 — Análise
- [x] Linguagem detectada corretamente (Node.js/JavaScript)
- [x] Framework detectado corretamente (Express 4.18.2)
- [x] Domínio da aplicação descrito corretamente (LMS com checkout)
- [x] Número de arquivos analisados condiz com a realidade (3)

### Fase 2 — Auditoria
- [x] Relatório segue o template definido nos arquivos de referência
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [x] Mínimo de 5 findings identificados (11)
- [x] Detecção de APIs deprecated incluída (driver sqlite3 baseado em callback)
- [x] Skill pausa e pede confirmação antes da Fase 3

### Fase 3 — Refatoração
- [x] Estrutura de diretórios segue padrão MVC (+ services/)
- [x] Configuração extraída para módulo de config (sem hardcoded)
- [x] Models criados para abstrair dados
- [x] Views/Routes separadas para roteamento
- [x] Controllers concentram o fluxo da aplicação
- [x] Error handling centralizado
- [x] Entry point claro (src/app.js)
- [x] Aplicação inicia sem erros
- [x] Endpoints originais respondem corretamente
```

**Projeto 3 — task-manager-api**
```
### Fase 1 — Análise
- [x] Linguagem detectada corretamente (Python 3)
- [x] Framework detectado corretamente (Flask 3.0.0 + Flask-SQLAlchemy)
- [x] Domínio da aplicação descrito corretamente (Task Manager)
- [x] Número de arquivos analisados condiz com a realidade (15)

### Fase 2 — Auditoria
- [x] Relatório segue o template definido nos arquivos de referência
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [x] Mínimo de 5 findings identificados (11)
- [x] Detecção de APIs deprecated incluída (MD5 para senha, Model.query.get())
- [x] Skill pausa e pede confirmação antes da Fase 3

### Fase 3 — Refatoração
- [x] Estrutura de diretórios segue padrão MVC (models/routes/services/utils mantidos + controllers/config/middlewares novos)
- [x] Configuração extraída para módulo de config (sem hardcoded)
- [x] Models mantidos e corrigidos (hashing, sem duplicação de regra)
- [x] Views/Routes separadas para roteamento (lógica movida para controllers/)
- [x] Controllers concentram o fluxo da aplicação
- [x] Error handling centralizado
- [x] Entry point claro (app.py)
- [x] Aplicação inicia sem erros
- [x] Endpoints originais respondem corretamente
```

### Logs de validação (Fase 3, após a refatoração)

**Projeto 1** (`python src/app.py` + chamadas HTTP reais):
```
2026-09-17 19:12:46 INFO SERVIDOR INICIADO — Rodando em http://0.0.0.0:5051
GET  /                     -> 200 {"mensagem":"Bem-vindo à API da Loja", ...}
GET  /health               -> 200 {"status":"ok","counts":{"produtos":10,"usuarios":3,"pedidos":0}}
GET  /produtos/1            -> 200 {"dados":{...},"sucesso":true}
POST /login (correto)      -> 200 {"dados":{...},"sucesso":true,"mensagem":"Login OK"}
POST /pedidos               -> 201 {"dados":{"pedido_id":1,"total":5999.99},"sucesso":true}
GET  /relatorios/vendas     -> 200 {"dados":{"faturamento_bruto":5999.99,...}}
POST /admin/query (removido) -> 404  (endpoint de execução arbitrária eliminado)
```

**Projeto 2** (`node src/app.js` + chamadas HTTP reais):
```
LMS API rodando na porta 3051...
POST /api/checkout (cartão válido)   -> 200 {"msg":"Sucesso","enrollment_id":2}
POST /api/checkout (cartão inválido) -> 400 {"error":"Pagamento recusado"}
GET  /api/admin/financial-report     -> 200 [{"course":"Clean Architecture","revenue":997,...}]
DELETE /api/users/1                  -> 200 {"message":"Usuário e todos os registros associados ... removidos."}
GET  /api/admin/financial-report (pós-delete) -> revenue do curso do usuário deletado zera corretamente (sem órfãos)
```

**Projeto 3** (`python app.py` + chamadas HTTP reais):
```
* Serving Flask app 'app' — Debug mode: off
GET  /tasks           -> 200 [...] (campo "overdue" calculado uma única vez, via Task.is_overdue())
GET  /users           -> 200 [...] (sem campo "password" em nenhum registro)
POST /login (correto) -> 200 {"token": "eyJhbGciOiJIUzI1NiIs..."}  (JWT real, assinado)
GET  /reports/summary -> 200 {"overview": {...}, "user_productivity": [...]}
GET  /reports/user/1  -> 200 {"statistics": {...}}
```

### Observações sobre o comportamento em stacks diferentes

- A mesma skill, **copiada sem nenhuma edição**, produziu relatórios no formato correto e com
  volume de findings equivalente (11 em cada um dos 3 projetos) em Python/Flask e em
  Node.js/Express — confirmando que o catálogo e o playbook realmente generalizam.
- No projeto Node (God Class + callbacks), a maior dificuldade foi **extrair regra de negócio
  de um estilo assíncrono baseado em callback**; a skill resolveu isso promovendo o acesso a
  dados para uma API baseada em Promise antes de separar controller/service — uma adaptação
  específica da stack que não é necessária em Python (já síncrono por padrão nesses projetos).
- No projeto Flask com camadas parciais (Projeto 3), a skill corretamente **evitou recriar a
  estrutura do zero** e, em vez disso, identificou a violação real (lógica nas rotas em vez de
  nos controllers, duplicação de regra de negócio) — mostrando que o comportamento da Fase 3 se
  adapta ao ponto de partida em vez de aplicar um template rígido.
- Em todos os 3 projetos a Fase 2 parou e pediu confirmação explícita antes de qualquer
  escrita em disco (fluxo de aprovação manual, ver histórico desta sessão/PR).

---

## D) Como Executar

### Pré-requisitos

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview) instalado e
  autenticado (`claude` disponível no PATH).
- Python 3.10+ e `pip` (Projetos 1 e 3).
- Node.js 18+ e `npm` (Projeto 2).

### Executar a skill em cada projeto

```bash
# Projeto 1 — Python/Flask
cd code-smells-project
claude "/refactor-arch"

# Projeto 2 — Node.js/Express (skill já copiada para ecommerce-api-legacy/.claude/skills/)
cd ../ecommerce-api-legacy
claude "/refactor-arch"

# Projeto 3 — Python/Flask com camadas parciais (skill já copiada para task-manager-api/.claude/skills/)
cd ../task-manager-api
claude "/refactor-arch"
```

Em cada execução: a Fase 1 imprime o resumo de stack/arquitetura, a Fase 2 imprime o relatório
de auditoria e **pausa pedindo confirmação** (`Proceed with refactoring (Phase 3)? [y/n]`) antes
de tocar em qualquer arquivo, e a Fase 3 só roda após uma resposta afirmativa.

### Como validar que a refatoração funcionou

```bash
# Projeto 1
cd code-smells-project
pip install -r requirements.txt
python src/app.py &
curl http://localhost:5000/health
curl http://localhost:5000/produtos

# Projeto 2
cd ecommerce-api-legacy
npm install
npm start &
curl -X POST http://localhost:3000/api/checkout -H "Content-Type: application/json" \
  -d '{"usr":"Teste","eml":"teste@teste.com","pwd":"123456","c_id":1,"card":"4111111111111111"}'

# Projeto 3
cd task-manager-api
pip install -r requirements.txt
python seed.py
python app.py &
curl http://localhost:5000/tasks
curl http://localhost:5000/reports/summary
```

Se os servidores subirem sem traceback e os `curl` acima retornarem `200`/`201` com JSON
coerente, a refatoração está validada — exatamente o processo usado para preencher os
checklists e logs da seção C.
