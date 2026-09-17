# Catálogo de Anti-Patterns (Fase 2)

Use este catálogo como checklist ao auditar o código. Para cada item: procure o **sinal de
detecção** literalmente no código (grep mental ou real), anote **arquivo:linha exatos**, e
classifique com a **severidade** indicada (a severidade pode subir um nível se o impacto no
projeto analisado for excepcionalmente grave — justifique quando isso acontecer).

Escala de severidade (definida pelo desafio):
- **CRITICAL** — falha grave de arquitetura/segurança: credenciais hardcoded, SQL Injection,
  God Class com DB+lógica+roteamento juntos, execução de código/SQL arbitrário.
- **HIGH** — forte violação de MVC/SOLID: lógica de negócio pesada em Controllers/rotas,
  acoplamento forte sem DI, estado global mutável.
- **MEDIUM** — padronização, duplicação, performance moderada: N+1, middleware mal usado,
  validação ausente.
- **LOW** — legibilidade, nomenclatura, magic numbers.

Este catálogo tem 12 anti-patterns (mínimo exigido: 8). Nem todo projeto terá todos — reporte
apenas os que encontrar evidência real, com localização exata.

---

### AP1 — Hardcoded Credentials / Secrets (CRITICAL)
**Sinal de detecção:** literais de string atribuídos a `SECRET_KEY`, `password`, `pass`,
`api_key`, `token`, `dbPass`, connection strings, chaves de gateway de pagamento (`pk_live_`,
`sk_live_`), credenciais SMTP — direto no código-fonte, fora de variáveis de ambiente.
**Por que importa:** vaza para o histórico do Git, para logs e para qualquer pessoa com acesso
ao repositório; é a causa nº1 de vazamento de credenciais em produção.
**Exemplo real:** `app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"`.

### AP2 — SQL Injection (CRITICAL)
**Sinal de detecção:** montagem de query por concatenação/f-string/template literal com
entrada do usuário (`"SELECT * FROM x WHERE id = " + str(id)`, `` `... ${id}` ``), em vez de
placeholders parametrizados (`?`, `%s`, bind params do ORM).
**Por que importa:** permite ler, alterar ou apagar qualquer dado do banco, inclusive
contornar autenticação (`' OR '1'='1`).
**Exemplo real:** `cursor.execute("SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'")`.

### AP3 — Endpoint de execução arbitrária (CRITICAL)
**Sinal de detecção:** rota que recebe uma string (SQL, comando de shell, código) do corpo da
requisição e executa diretamente (`cursor.execute(dados["sql"])`, `eval(...)`, `exec(...)`,
`child_process.exec(req.body.cmd)`), sem allowlist nem autenticação.
**Por que importa:** é RCE/exfiltração total — qualquer cliente HTTP vira um client SQL/shell
irrestrito do servidor.

### AP4 — God Class / God Module (CRITICAL quando mistura DB+lógica+rota; HIGH caso contrário)
**Sinal de detecção:** um único arquivo/classe concentra acesso a dados (queries), regra de
negócio de múltiplos domínios e, às vezes, o próprio roteamento HTTP — sem nenhuma fronteira
de responsabilidade. Difícil de testar isoladamente; qualquer mudança arrisca efeitos
colaterais em funcionalidades não relacionadas.
**Exemplo real:** `models.py` com CRUD de produtos, usuários e pedidos no mesmo arquivo;
`AppManager.js` com schema, seed, rotas e regra de pagamento na mesma classe.

### AP5 — Lógica de negócio em Controller/Rota (HIGH)
**Sinal de detecção:** handler de rota contendo cálculos de preço/desconto, validações de
regra de negócio (não apenas de formato), orquestração de múltiplos side-effects (enviar
e-mail + atualizar estoque + logar auditoria) diretamente no corpo da função de rota.
**Por que importa:** viola a responsabilidade do Controller (orquestrar, não decidir regra de
negócio); torna a regra impossível de reusar/testar fora do contexto HTTP.

### AP6 — Estado Global Mutável (HIGH)
**Sinal de detecção:** variável de módulo mutável (`let cache = {}`, `db_connection = None`
alterado por função, contador global) compartilhada entre requisições concorrentes, sem
encapsulamento nem injeção.
**Por que importa:** condição de corrida, vazamento de memória (cache que nunca expira),
impossível de isolar em testes (estado "vaza" entre casos de teste).

### AP7 — Criptografia quebrada / hashing inadequado de senha (CRITICAL)
**Sinal de detecção:** senha armazenada em texto puro; ou hash "artesanal" não criptográfico
(concatenar/repetir base64); ou uso de `MD5`/`SHA1` sem salt para senhas — todos são
**quebrados para esse uso** e permitem recuperação/força-bruta trivial da senha original.
**Exemplo real:** `hashlib.md5(pwd.encode()).hexdigest()` sem salt; função que faz
`Buffer.from(pwd).toString('base64')` em loop fingindo ser hash.
**Recomendação:** usar `werkzeug.security.generate_password_hash` (bcrypt/scrypt) em Python
ou `bcrypt`/`argon2` em Node — nunca reinventar hashing de senha.

### AP8 — Exposição de dados sensíveis na resposta da API (CRITICAL)
**Sinal de detecção:** serialização (`to_dict`, `JSON.stringify`) que inclui campos como
`password`, `senha`, `secret_key`, `debug` em endpoints públicos, inclusive de
health-check/diagnóstico.
**Por que importa:** vaza hash de senha (viabiliza ataque offline) e detalhes internos de
configuração para qualquer chamador não autenticado.

### AP9 — Query N+1 (MEDIUM)
**Sinal de detecção:** loop `for` sobre uma lista de registros que, a cada iteração, dispara
uma nova query para buscar dado relacionado (`for pedido in pedidos: cursor.execute(...)`),
em vez de um `JOIN` ou eager-loading/lote único.
**Por que importa:** degrada performance linearmente com o volume de dados; é um dos gargalos
mais comuns e mais fáceis de eliminar em APIs.

### AP10 — Falta de validação/paginação nas rotas & inconsistência de contrato (MEDIUM)
**Sinal de detecção:** endpoints de listagem sem paginação (`SELECT * FROM tabela` sempre
completo); ausência de schema/validação de tipo nos dados de entrada (aceita qualquer JSON);
respostas de erro/sucesso em formatos inconsistentes (`res.send("texto")` vs `res.json({...})`
no mesmo serviço); CORS liberado para qualquer origem (`Access-Control-Allow-Origin: *`) sem
necessidade.
**Por que importa:** quebra a previsibilidade do contrato da API para os clientes e cria risco
de payloads gigantes / dados malformados chegando às camadas internas.

### AP11 — Duplicação de lógica (DRY) / uso de bare `except`/`catch` genérico (LOW/MEDIUM)
**Sinal de detecção:** a mesma regra (ex.: cálculo de "atrasado") reimplementada em 3+ lugares
em vez de chamar um único método do Model; blocos `except:`/`catch (e) {}` vazios ou que só
fazem `print`, escondendo a causa real do erro.
**Por que importa:** qualquer correção precisa ser replicada manualmente em todos os lugares
duplicados (alto risco de divergência); erros engolidos dificultam debugging em produção.

### AP12 — Legibilidade: nomenclatura ruim, magic numbers, imports não usados (LOW)
**Sinal de detecção:** variáveis de 1-2 letras sem significado (`u`, `e`, `cc`, `p`) fora de
loops triviais; números/strings mágicos repetidos (`0.1`, `"pendente"`, `200`) que deveriam
ser constantes nomeadas; `import` de módulos nunca referenciados no arquivo; `print()` usado
como logging em vez do módulo de logging padrão da linguagem.
**Por que importa:** aumenta o custo cognitivo de leitura e o risco de digitar o literal errado
em algum dos pontos duplicados.

---

## Detecção de APIs Deprecated (obrigatório verificar sempre)

Além dos anti-patterns estruturais acima, verifique explicitamente o uso das APIs abaixo.
Reporte como um finding próprio, severidade **MEDIUM** (ou **HIGH** se a API deprecated for
também uma falha de segurança, como `hashlib.md5` para senha — nesse caso, funde-se com AP7).

| API / padrão deprecated encontrado | Motivo | Substituto moderno recomendado |
|---|---|---|
| `hashlib.md5` / `hashlib.sha1` para senha | Quebrado para uso criptográfico de senha | `werkzeug.security.generate_password_hash` (Flask) ou `bcrypt`/`argon2` |
| `app.run(debug=True)` em código de produção | Ativa o debugger Werkzeug, que permite execução remota de código se exposto | `debug=False` + variável de ambiente `FLASK_DEBUG`, servidor WSGI (gunicorn/uwsgi) atrás de proxy |
| Flask `@app.before_first_request` (removido no Flask 2.3+) | Removido oficialmente do Flask | Inicialização no factory `create_app()` / `with app.app_context(): ...` |
| `sqlite3` (Node) com API baseada em callback | Callback-hell, não é mais o pacote recomendado para uso novo | `better-sqlite3` (síncrono) ou `sqlite`+`sqlite3` com wrapper `async/await`, ou um ORM (Prisma/Sequelize/TypeORM) |
| `body-parser` standalone (`require('body-parser')`) | Funcionalidade incorporada ao Express desde a v4.16 | `express.json()` / `express.urlencoded()` nativos |
| `new Buffer(...)` (Node) | Deprecated e inseguro (não zera memória) desde Node 6 | `Buffer.from(...)` / `Buffer.alloc(...)` |
| `request` (biblioteca Python `requests` está OK, mas o pacote npm `request`) | Descontinuado pelos mantenedores | `axios`, `node-fetch`, `fetch` nativo (Node 18+) |
| SQLAlchemy `Model.query.get(id)` (deprecated no padrão 2.0) | API "legacy query" marcada para remoção | `db.session.get(Model, id)` |
| `datetime.utcnow()` (Python, deprecated desde 3.12) | Marcado deprecated a favor de datas timezone-aware | `datetime.now(datetime.UTC)` |

Ao encontrar qualquer uma dessas, cite a versão do framework/linguagem detectada na Fase 1
para confirmar que a API realmente está deprecated nessa versão antes de reportar.
