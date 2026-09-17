# Playbook de Refatoração (Fase 3)

Cada padrão abaixo mapeia diretamente para um item do catálogo de anti-patterns
(`02-antipattern-catalog.md`). Contém exemplo de "antes" e "depois" em Python/Flask e/ou
Node.js/Express — generalize a mesma transformação para outras stacks quando necessário.
São 10 padrões (mínimo exigido: 8).

---

## RP1 — Extrair config hardcoded para módulo de configuração
Resolve: AP1 (Hardcoded Credentials).

**Antes (Flask):**
```python
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
app.config["DEBUG"] = True
```

**Depois:**
```python
# config/settings.py
import os

class Settings:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
    DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    DATABASE_PATH = os.environ.get("DATABASE_PATH", "loja.db")

# app.py
from config.settings import Settings
app.config.from_object(Settings)
```
Adicionar `.env.example` documentando `SECRET_KEY`, `FLASK_DEBUG`, `DATABASE_PATH`.

---

## RP2 — Parametrizar queries SQL (eliminar SQL Injection)
Resolve: AP2 (SQL Injection).

**Antes:**
```python
cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))
```

**Depois:**
```python
cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))
```

**Antes (Node/sqlite3 — já correto neste caso, mas ilustrando o erro comum):**
```js
db.run(`INSERT INTO users (name) VALUES ('${name}')`);
```

**Depois:**
```js
db.run("INSERT INTO users (name) VALUES (?)", [name]);
```

---

## RP3 — Remover endpoint de execução arbitrária
Resolve: AP3.

**Antes:**
```python
@app.route("/admin/query", methods=["POST"])
def executar_query():
    query = request.get_json().get("sql", "")
    cursor.execute(query)   # executa qualquer SQL enviado pelo cliente
```

**Depois:** remover o endpoint por completo. Se um caso de uso administrativo real motivou
sua existência (ex.: relatório ad-hoc), substituir por endpoints específicos, com
autenticação/autorização de admin e sem SQL livre vindo do cliente.

---

## RP4 — Quebrar God Class/Module em Models por domínio
Resolve: AP4.

**Antes:** `models.py` com `get_todos_produtos`, `criar_usuario`, `login_usuario`,
`criar_pedido`, `relatorio_vendas` — tudo no mesmo arquivo.

**Depois:**
```
models/
├── produto_model.py     # get_all, get_by_id, create, update, delete, search
├── usuario_model.py     # get_all, get_by_id, create, authenticate
└── pedido_model.py      # create, get_by_user, get_all, update_status, sales_report
```
Cada função continua fazendo apenas acesso a dados da sua entidade; a lógica de orquestração
entre entidades (ex.: `criar_pedido` decrementando estoque de `produtos`) permanece no Model
de Pedido, que pode chamar o Model de Produto — mas nunca o Controller acessando SQL direto.

---

## RP5 — Mover lógica de negócio do Controller/Rota para Model/Service
Resolve: AP5.

**Antes (Node, checkout dentro do handler de rota):**
```js
app.post('/api/checkout', (req, res) => {
    // 50 linhas misturando validação, pagamento, matrícula, log de auditoria...
});
```

**Depois:**
```js
// controllers/checkout_controller.js
async function checkout(req, res) {
    const result = await checkoutService.process(req.body);
    if (result.error) return res.status(result.status).json({ error: result.error });
    res.status(200).json(result.data);
}

// services/checkout_service.js
async function process({ usr, eml, pwd, c_id, card }) {
    const course = await courseModel.getActive(c_id);
    if (!course) return { error: 'Curso não encontrado', status: 404 };
    const user = await userModel.findOrCreate(usr, eml, pwd);
    const payment = await paymentService.charge(card, course.price);
    if (!payment.approved) return { error: 'Pagamento recusado', status: 400 };
    const enrollment = await enrollmentModel.create(user.id, c_id);
    await auditLogModel.record(`Checkout curso ${c_id} por ${user.id}`);
    return { data: { msg: 'Sucesso', enrollment_id: enrollment.id } };
}
```
O controller fica fino (orquestra request → service → response); a regra de negócio vive em
`services/`, testável isoladamente sem precisar de um servidor HTTP rodando.

---

## RP6 — Encapsular estado global mutável
Resolve: AP6.

**Antes:**
```js
let globalCache = {};
function logAndCache(key, data) { globalCache[key] = data; }
```

**Depois:**
```js
// config/cache.js
class Cache {
    #store = new Map();
    set(key, value) { this.#store.set(key, value); }
    get(key) { return this.#store.get(key); }
}
module.exports = new Cache(); // instância única, gerenciada por este módulo, com API clara
```
Se o objetivo era cache real (com expiração), preferir uma dependência dedicada (ex.: LRU
cache) em vez de objeto simples que cresce indefinidamente.

---

## RP7 — Substituir hashing de senha inseguro
Resolve: AP7.

**Antes (Python, MD5 sem salt):**
```python
self.password = hashlib.md5(pwd.encode()).hexdigest()
```

**Depois:**
```python
from werkzeug.security import generate_password_hash, check_password_hash

self.password = generate_password_hash(pwd)   # salga e usa scrypt/pbkdf2 internamente
...
def check_password(self, pwd):
    return check_password_hash(self.password, pwd)
```

**Antes (Node, "badCrypto" artesanal):**
```js
function badCrypto(pwd) {
    let hash = "";
    for (let i = 0; i < 10000; i++) hash += Buffer.from(pwd).toString('base64').substring(0, 2);
    return hash.substring(0, 10);
}
```

**Depois:**
```js
const bcrypt = require('bcrypt');
const hash = await bcrypt.hash(pwd, 10);
const ok = await bcrypt.compare(pwd, hash);
```

---

## RP8 — Remover campos sensíveis da serialização
Resolve: AP8.

**Antes:**
```python
def to_dict(self):
    return {"id": self.id, "name": self.name, "email": self.email, "password": self.password}
```

**Depois:**
```python
def to_dict(self):
    return {"id": self.id, "name": self.name, "email": self.email}
    # password/hash nunca sai da camada de Model
```
Aplicar o mesmo princípio ao `health_check`: nunca retornar `debug`, `secret_key` ou paths
internos de banco em endpoints públicos de diagnóstico.

---

## RP9 — Eliminar N+1 com JOIN / query em lote
Resolve: AP9.

**Antes:**
```python
for row in pedidos:
    cursor2.execute("SELECT * FROM itens_pedido WHERE pedido_id = " + str(row["id"]))
```

**Depois (SQL puro, uma única query com JOIN):**
```python
cursor.execute("""
    SELECT p.id AS pedido_id, p.status, p.total, ip.produto_id, ip.quantidade, ip.preco_unitario
    FROM pedidos p
    LEFT JOIN itens_pedido ip ON ip.pedido_id = p.id
""")
# agrupar as linhas em memória por pedido_id em vez de 1 query por pedido
```

**Depois (ORM, eager loading):**
```python
tasks = Task.query.options(db.joinedload(Task.user), db.joinedload(Task.category)).all()
```

---

## RP10 — Padronizar respostas de erro e centralizar tratamento de exceções
Resolve: AP10, AP11.

**Antes:** cada rota decide seu próprio formato (`res.send("texto")`, `jsonify({"erro": ...})`,
`jsonify({"error": ...})` misturados) e usa `except:`/`catch(e){}` genérico.

**Depois (Flask):**
```python
# middlewares/error_handler.py
from flask import jsonify

def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"erro": "Recurso não encontrado"}), 404

    @app.errorhandler(Exception)
    def handle_unexpected(e):
        app.logger.exception("Erro não tratado")
        return jsonify({"erro": "Erro interno do servidor"}), 500
```
```python
# app.py
from middlewares.error_handler import register_error_handlers
register_error_handlers(app)
```

**Depois (Express):**
```js
// middlewares/errorHandler.js
module.exports = (err, req, res, next) => {
    console.error(err);
    res.status(err.status || 500).json({ error: err.message || 'Erro interno' });
};

// app.js
app.use(routes);
app.use(errorHandler); // registrado por último
```
Todo controller passa a lançar/propagar erro para este handler único, em vez de decidir o
formato da resposta de erro individualmente.
