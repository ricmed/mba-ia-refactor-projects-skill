# Template do Relatório de Auditoria (Fase 2)

A Fase 2 SEMPRE produz um relatório neste formato exato — tanto impresso no terminal quanto
salvo em arquivo Markdown quando solicitado. Não pule seções. Não invente findings: cada um
precisa ter arquivo e linha(s) reais, confirmados por leitura do código.

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome do diretório do projeto>
Stack:   <linguagem> + <framework>
Files:   <N> analyzed | ~<M> lines of code

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

## Findings

### [<SEVERIDADE>] <Nome do anti-pattern>
File: <arquivo>:<linha ou intervalo de linhas>
Description: <o que foi encontrado, objetivamente, citando o trecho ofensivo>
Impact: <consequência concreta — segurança, manutenibilidade, performance>
Recommendation: <ação de correção, referenciando o padrão do playbook de refatoração>

... (repetir bloco "### [<SEVERIDADE>] ..." para cada finding, dos mais para os menos
     severos: todos os CRITICAL primeiro, depois HIGH, depois MEDIUM, depois LOW)

================================
Total: <N> findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

## Regras de preenchimento

1. **Ordenação obrigatória**: CRITICAL → HIGH → MEDIUM → LOW. Dentro da mesma severidade,
   ordene pela ordem em que o anti-pattern aparece no catálogo (`02-antipattern-catalog.md`).
2. **Localização exata**: `arquivo.ext:linha` para um único ponto, ou `arquivo.ext:linha_inicio-linha_fim`
   para um bloco/classe/função inteira (ex.: um God Class que ocupa o arquivo inteiro).
3. **Sem duplicar o mesmo finding em domínios diferentes**: se o mesmo anti-pattern (ex.: SQL
   Injection) aparece em várias funções do mesmo arquivo, agrupe em um único finding citando
   todas as linhas relevantes, a menos que a severidade real varie ponto a ponto.
4. **Mínimo de findings**: o relatório deve ter pelo menos 5 findings, incluindo no mínimo 1
   CRITICAL ou HIGH. Se a varredura contra o catálogo completo (`02-antipattern-catalog.md`)
   render menos que isso, releia o código mais devagar antes de concluir a Fase 2 — não
   avance com um relatório incompleto.
5. **Contagem de linhas do projeto** (`~M lines of code`): some as linhas dos arquivos de
   código-fonte analisados (exclua dependências/lockfiles/venv/node_modules).
6. **Após imprimir o relatório**, pare e peça confirmação explícita do usuário com a pergunta
   `Proceed with refactoring (Phase 3)? [y/n]`. **Nunca** edite ou crie arquivos de código antes
   de receber uma resposta afirmativa clara. Se a resposta for negativa, encerre a skill sem
   tocar em nenhum arquivo do projeto.
7. **Persistência do relatório**: quando o usuário/skill-runner pedir para salvar o relatório
   (ex.: em `reports/audit-project-N.md` na raiz do repositório multi-projeto), grave o
   conteúdo completo do bloco acima em Markdown, sem truncar findings.
