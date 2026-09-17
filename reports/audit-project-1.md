```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python 3
Framework:     Flask 3.1.1
Dependencies:  flask-cors 5.0.1
Domain:        E-commerce API (produtos, pedidos, usuários, itens_pedido)
Architecture:  Monolito de arquivo único — tudo em 4 arquivos na raiz, sem pastas de camada (models/, routes/, controllers/ inexistentes)
Source files:  4 files analyzed (app.py, controllers.py, models.py, database.py)
DB tables:     produtos, usuarios, pedidos, itens_pedido
================================
```

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask
Files:   4 analyzed | ~784 lines of code

## Summary
CRITICAL: 5 | HIGH: 2 | MEDIUM: 2 | LOW: 2

## Findings

### [CRITICAL] Hardcoded Credentials
File: app.py:7
Description: `app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"` — segredo da aplicação embutido diretamente no código-fonte.
Impact: Chave versionada no Git; qualquer pessoa com acesso ao repositório pode forjar sessões/tokens assinados com essa chave.
Recommendation: Mover para variável de ambiente via módulo `config/settings.py` (RP1 do playbook).

### [CRITICAL] SQL Injection
File: models.py:28, 48-50, 58-61, 92, 109-111, 127-129, 140, 148-151, 155-166, 174, 188, 192, 220, 224, 279-280, 291-297
Description: Praticamente todas as queries do arquivo são montadas por concatenação de string com dados de entrada não sanitizados (ex.: `"SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"` em `login_usuario`, linha 109-111).
Impact: Permite bypass de autenticação (`' OR '1'='1`), leitura/alteração/exclusão arbitrária de dados via qualquer campo de entrada (id, nome, categoria, termo de busca, status).
Recommendation: Substituir toda concatenação por bind params (`?`) — ver RP2 do playbook.

### [CRITICAL] Endpoint de Execução SQL Arbitrária
File: app.py:47-78
Description: `/admin/reset-db` apaga todas as tabelas sem autenticação; `/admin/query` executa **qualquer string SQL enviada no corpo da requisição** (`cursor.execute(query)`, linha 69), sem allowlist nem autenticação.
Impact: Qualquer cliente HTTP não autenticado tem acesso irrestrito de leitura/escrita/exclusão em todo o banco de dados — equivalente a um shell SQL público.
Recommendation: Remover ambos os endpoints; se necessário um caso de uso administrativo real, criar endpoints específicos com autenticação/autorização de admin (RP3).

### [CRITICAL] Senhas Armazenadas em Texto Puro
File: models.py:105-131, database.py:75-83
Description: `criar_usuario` e o seed de `database.py` gravam a senha exatamente como recebida (`'123456'`, `'admin123'`); `login_usuario` (linha 109-111) compara a senha em texto puro via SQL.
Impact: Qualquer vazamento de banco (inclusive via o próprio SQL Injection acima) expõe as senhas reais dos usuários, que tipicamente são reaproveitadas em outros sistemas.
Recommendation: Usar `werkzeug.security.generate_password_hash`/`check_password_hash` (RP7).

### [CRITICAL] Exposição de Dados Sensíveis na API
File: controllers.py:128-144, 264-292
Description: `listar_usuarios`/`buscar_usuario` retornam o campo `senha` de `models.py` diretamente na resposta JSON; `health_check` (linha 264-292) retorna `secret_key` e `debug: True` no corpo da resposta de um endpoint público, sem autenticação.
Impact: Vazamento direto de senha (mesmo texto puro) e da chave secreta da aplicação para qualquer chamador da API.
Recommendation: Remover campos sensíveis da serialização de usuário e do health-check (RP8).

### [HIGH] God Module (models.py e controllers.py)
File: models.py:1-315, controllers.py:1-293
Description: Um único arquivo `models.py` concentra todo o acesso a dados de 3 domínios (produtos, usuários, pedidos); `controllers.py` concentra toda a lógica de validação, orquestração e formatação dos mesmos 3 domínios.
Impact: Qualquer alteração em um domínio arrisca efeitos colaterais nos demais; impossível testar um domínio isoladamente; navegação e revisão de código ficam custosas.
Recommendation: Separar em `models/produto_model.py`, `models/usuario_model.py`, `models/pedido_model.py` e controllers equivalentes (RP4).

### [HIGH] Debug Mode Habilitado em Produção
File: app.py:8, 88
Description: `app.config["DEBUG"] = True` e `app.run(host="0.0.0.0", port=5000, debug=True)` — servidor de desenvolvimento com debugger interativo do Werkzeug exposto publicamente em `0.0.0.0`.
Impact: O debugger do Werkzeug permite execução remota de código quando acessível externamente; é uma configuração de desenvolvimento vazando para produção (API deprecated/perigosa para uso produtivo).
Recommendation: `DEBUG=False` por padrão, controlado por variável de ambiente, e servidor WSGI dedicado (gunicorn/uwsgi) atrás de proxy em produção.

### [MEDIUM] Query N+1
File: models.py:171-233
Description: `get_pedidos_usuario` e `get_todos_pedidos` disparam uma nova query de `itens_pedido` para cada pedido, e dentro desse loop, mais uma query de `produtos` para cada item — 3 níveis de queries aninhadas em loop.
Impact: Tempo de resposta cresce linearmente (ou pior) com o volume de pedidos/itens; não escala.
Recommendation: Substituir por uma única query com `JOIN` entre `pedidos`, `itens_pedido` e `produtos` (RP9).

### [MEDIUM] Falta de Paginação e CORS Irrestrito
File: app.py:9; controllers.py:5-12, 128-135, 229-236
Description: `CORS(app)` libera qualquer origem sem restrição; `listar_produtos`, `listar_usuarios` e `listar_todos_pedidos` sempre retornam a tabela inteira, sem `limit`/`offset`.
Impact: Superfície de CORS desnecessariamente ampla; payloads de resposta crescem sem limite conforme a base de dados cresce.
Recommendation: Restringir CORS às origens conhecidas e adicionar paginação nos endpoints de listagem (RP10).

### [LOW] Uso de `print()` como Logging e Magic Numbers/Strings
File: controllers.py:8, 11, 57, 61, 106, 161, 179, 182, 208-210, 248, 250; models.py:256-262; controllers.py:52
Description: Logging feito via `print()` cru em vez do módulo `logging`; percentuais de desconto (`0.1`, `0.05`, `0.02`) e limiares (`10000`, `5000`, `1000`) hardcoded em `relatorio_vendas`; lista de categorias válidas duplicada apenas em `controllers.py:52` sem fonte única de verdade.
Impact: Dificulta observabilidade em produção (sem níveis de log, sem estrutura); qualquer alteração de regra de desconto ou categoria exige caçar o literal no meio do código.
Recommendation: Adotar `logging` padrão e extrair constantes nomeadas (RP nomenclatura/constantes — seção de qualidade das guidelines).

================================
Total: 11 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```
