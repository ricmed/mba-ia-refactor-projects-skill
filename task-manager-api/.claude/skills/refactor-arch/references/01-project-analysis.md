# Heurísticas de Análise de Projeto (Fase 1)

Objetivo desta fase: em menos de 1 minuto de leitura, produzir um resumo confiável de
**linguagem, framework, dependências, domínio, arquitetura atual e superfície de dados**,
sem executar código do projeto (apenas leitura estática de arquivos).

Esta skill é **agnóstica de tecnologia**. Não assuma Python/Flask. Use os sinais abaixo
para detectar a stack real e adapte o vocabulário do relatório a ela.

## 1. Detecção de linguagem e gerenciador de pacotes

Procure, na raiz do projeto (e um nível abaixo), pelos arquivos-manifesto:

| Arquivo encontrado | Linguagem | Gerenciador |
|---|---|---|
| `requirements.txt`, `Pipfile`, `pyproject.toml` | Python | pip / poetry |
| `package.json` | JavaScript/TypeScript (Node.js) | npm / yarn / pnpm |
| `go.mod` | Go | go modules |
| `pom.xml`, `build.gradle` | Java/Kotlin | Maven / Gradle |
| `Gemfile` | Ruby | Bundler |
| `composer.json` | PHP | Composer |
| `Cargo.toml` | Rust | Cargo |

Se houver `tsconfig.json` junto de `package.json`, marque a linguagem como TypeScript.

## 2. Detecção de framework

Leia o manifesto de dependências identificado acima e cruze com esta tabela (lista não
exaustiva — generalize pelo nome do pacote quando não houver correspondência exata):

| Dependência | Framework | Categoria |
|---|---|---|
| `flask` | Flask | Web (Python, micro) |
| `django` | Django | Web (Python, full-stack) |
| `fastapi` | FastAPI | Web (Python, async) |
| `express` | Express | Web (Node.js, micro) |
| `@nestjs/core` | NestJS | Web (Node.js, opinionated/MVC) |
| `koa` | Koa | Web (Node.js, micro) |
| `spring-boot-starter*` | Spring Boot | Web (Java) |
| `rails` | Ruby on Rails | Web (Ruby, full-stack) |

Também registre a **versão** declarada (ex.: `flask==3.1.1`, `"express": "^4.18.2"`) — ela é
necessária para a checagem de APIs deprecated (ver `02-antipattern-catalog.md`).

Se nenhum framework for encontrado mas houver um servidor HTTP manual (ex.: `http.createServer`
em Node puro, `http.server` em Python), classifique como "framework: nenhum (HTTP nativo)".

## 3. Banco de dados

Procure por:
- Import/require de drivers: `sqlite3`, `psycopg2`, `pymysql`, `mysql2`, `pg`, `mongoose`, `pymongo`.
- ORMs: `flask_sqlalchemy`/`SQLAlchemy`, `sequelize`, `prisma`, `typeorm`, `django.db.models`.
- Strings de conexão ou `CREATE TABLE` embutidas no código (comum em projetos legados).

Para mapear as tabelas/entidades sem executar o banco:
- Procure literalmente por `CREATE TABLE` (SQL cru) e extraia os nomes.
- Ou procure classes que herdam de uma base de ORM (`db.Model`, `Model`, `Base`) e use o
  nome da classe/`__tablename__`.

Reporte também se a conexão é **global mutável** (variável de módulo reaberta a cada
request) — isso já é um sinal antecipado de anti-pattern (ver catálogo, "Estado Global Mutável").

## 4. Domínio da aplicação

Não pergunte ao usuário — infira o domínio de negócio a partir de nomes de rotas, tabelas e
campos (em qualquer idioma). Exemplos de heurística:
- Tabelas/rotas como `produtos`, `pedidos`, `itens_pedido`, `usuarios` → **E-commerce**.
- `courses`, `enrollments`, `payments`, `checkout` → **LMS / plataforma de cursos com cobrança**.
- `tasks`, `categories`, `users`, `priority`, `due_date` → **Gestão de tarefas (Task Manager)**.

Descreva o domínio em uma linha objetiva, citando as entidades principais em português ou no
idioma original do código.

## 5. Mapeamento da arquitetura atual

Classifique o projeto em um dos três perfis abaixo — isso determina o quão agressiva a
Fase 3 precisa ser:

1. **Monolito de arquivo único ou poucos arquivos "flat"** — tudo (rotas + SQL + regra de
   negócio + config) misturado em 1-5 arquivos na raiz, sem pastas por camada.
   Sinal: `app.py`/`app.js`, `models.py`, `controllers.py` soltos na raiz, sem `src/`.
2. **Camadas parcialmente separadas** — já existem pastas como `models/`, `routes/`,
   `services/`, `utils/`, mas os arquivos dentro delas ainda violam a responsabilidade da
   camada (ex.: rota fazendo cálculo de negócio, model fazendo I/O externo).
3. **MVC bem aplicado** — camadas separadas E cada arquivo respeita sua responsabilidade
   (raro nos projetos-alvo deste desafio; serve como critério de "objetivo final").

Para cada arquivo fonte relevante, contabilize linhas (`wc -l` ou equivalente) e liste no
resumo o número de arquivos analisados — o valor deve bater com a contagem real de arquivos
de código-fonte (exclua `node_modules`, `venv`, `__pycache__`, artefatos de build e arquivos
de dependência travada como `package-lock.json`).

## 6. Saída da Fase 1

Imprima um bloco assim (adapte os campos ao que foi detectado; não invente dados):

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <linguagem> <versão se aplicável>
Framework:     <framework> <versão>
Dependencies:  <lista curta das libs relevantes>
Domain:        <descrição de 1 linha do domínio>
Architecture:  <um dos 3 perfis da seção 5, com 1 frase de justificativa>
Source files:  <N> files analyzed (<lista de nomes/pastas>)
DB tables:     <tabelas/entidades detectadas>
================================
```

Não avance para a Fase 2 sem antes mostrar este bloco ao usuário.
