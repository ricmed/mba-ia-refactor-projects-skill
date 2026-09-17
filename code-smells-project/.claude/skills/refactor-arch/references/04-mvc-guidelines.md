# Guidelines de Arquitetura Alvo — MVC Agnóstico de Tecnologia (Fase 3)

O objetivo da Fase 3 é reorganizar o projeto para o padrão **MVC adaptado a uma API HTTP**
(sem view de HTML — "View" aqui é a camada de apresentação/serialização + roteamento).
As regras abaixo valem para qualquer linguagem; os exemplos usam Python/Flask e
Node.js/Express porque são as stacks-alvo deste desafio, mas o mapeamento de
responsabilidades é o que importa, não o nome exato das pastas.

## Estrutura de diretórios alvo

```
src/                        (ou raiz do projeto, se o ecossistema não usa src/)
├── config/
│   └── settings.(py|js)    # toda configuração e leitura de variáveis de ambiente
├── models/
│   └── <entidade>_model.(py|js)   # 1 arquivo por entidade/domínio
├── views/  (ou routes/)
│   └── <entidade>_routes.(py|js)  # definição de rotas HTTP, delega ao controller
├── controllers/
│   └── <entidade>_controller.(py|js) # orquestra request -> model -> response
├── middlewares/
│   └── error_handler.(py|js)      # tratamento de erro centralizado
└── app.(py|js)              # composition root: cria app, registra tudo, sobe o servidor
```

Adapte nomes de pasta à convenção idiomática do framework (ex.: em Flask é comum
`routes/` em vez de `views/` já que não há HTML; mantenha o nome se o projeto já o usa,
desde que a responsabilidade abaixo seja respeitada).

## Responsabilidade de cada camada

### Model
- Representa uma entidade de domínio e o acesso a dados dela (ORM class, ou funções de
  acesso a dados quando não há ORM).
- Contém **regras de validação e cálculo que pertencem ao dado em si** (ex.: `is_overdue()`,
  `validate_priority()`, hashing de senha do próprio usuário).
- **Nunca** conhece HTTP (não recebe `request`, não monta `response`, não sabe o que é uma rota).
- Toda query deve usar parâmetros vinculados (bind params) — nunca concatenação de string.
- Um Model por entidade/domínio (produto, usuário, pedido — não um arquivo `models.py` com
  todas as entidades e todas as queries do sistema).

### View / Routes
- Define **apenas** o mapeamento `método HTTP + path -> função do controller`.
- Não contém lógica de negócio, não acessa o banco diretamente.
- Pode fazer parsing/validação de formato de entrada (tipo do JSON, presença de campos) antes
  de repassar ao controller — mas não validação de regra de negócio.
- Idealmente uma "view/routes" por domínio (produto, usuário, pedido), registrada no
  composition root via blueprint/router.

### Controller
- Recebe a requisição já roteada, extrai os dados necessários, chama o(s) Model(s) e/ou
  Service(s) necessários, e traduz o resultado em uma resposta HTTP (status code + corpo).
- **Orquestra, não decide regra de negócio complexa** — se a regra é grande o suficiente para
  ter testes próprios (ex.: cálculo de checkout com pagamento), extraia para uma camada de
  serviço (`services/`) chamada pelo controller, para manter o controller fino.
- Trata exceções esperadas do domínio (ex.: "não encontrado") e as converte em códigos HTTP
  apropriados; erros inesperados sobem para o middleware de erro central.

### Config
- Toda credencial, URL de banco, chave de API, porta, feature flag vem de variáveis de
  ambiente (`os.environ` / `process.env`), com um único módulo `config/settings` que as lê
  e expõe como objeto/constantes tipadas. Nunca literal hardcoded no meio do código de
  negócio.
- Um arquivo `.env.example` deve documentar as variáveis esperadas (sem valores reais).

### Middleware / Error handling
- Um único ponto centralizado captura exceções não tratadas pelos controllers e retorna um
  formato de erro **consistente** (`{"erro": "..."}` ou `{"error": "..."}`) com o status code
  correto — em vez de cada controller decidir seu próprio formato ad-hoc.
- Logging estruturado (não `print`/`console.log` cru) deve acontecer aqui e nos pontos de
  falha, nunca dados sensíveis (senha, token, cartão) em log.

### Composition root (`app.py` / `app.js`)
- Cria a instância do framework, injeta config, registra middlewares, registra as
  views/rotas de cada domínio, e sobe o servidor.
- Não deve conter nenhuma regra de negócio nem rota inline de domínio (rotas genéricas como
  `/health` podem ficar aqui por serem infraestrutura, não domínio).

## Regras adicionais de qualidade aplicadas durante a Fase 3

- Eliminar toda concatenação de SQL — usar sempre bind params/ORM.
- Eliminar estado global mutável — se cache/conexão precisa ser compartilhado, encapsular em
  uma classe/módulo com ciclo de vida claro (ex.: singleton de conexão gerenciado pelo
  framework, não uma variável solta).
- Resolver N+1 com JOIN, eager loading do ORM, ou uma única query em lote.
- Substituir hashing de senha inseguro por uma função de hash de senha moderna da própria
  stack (ver `02-antipattern-catalog.md`).
- Nunca serializar campos sensíveis (senha/hash) nas respostas dos Models.
- Atualizar/possivelmente remover qualquer API deprecated identificada na Fase 2, adotando o
  substituto recomendado no catálogo.

## Quando o projeto já tem alguma separação (ex.: task-manager-api)

Não recrie do zero. Diagnostique **onde a responsabilidade de cada camada está sendo violada**
e mova apenas o que precisa mover:
- Lógica de negócio duplicada dentro das rotas → extrair para o Model ou um Service, e fazer
  as rotas chamarem esse único ponto.
- Serialização manual repetida em cada rota → usar o `to_dict()`/serializer já existente no
  Model em vez de reconstruir o dicionário à mão em cada endpoint.
- Config espalhada → centralizar em `config/`.
- Se as pastas já existem mas com nomes adequados (`models/`, `routes/`, `services/`,
  `utils/`), mantenha os nomes e apenas adicione o que falta (ex.: `config/`,
  `middlewares/error_handler`) e corrija o conteúdo de cada arquivo.
