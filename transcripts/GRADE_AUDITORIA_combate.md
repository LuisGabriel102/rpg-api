# GRADE DE AUDITORIA — Sessao de combate ao vivo (aplicar sobre o .jsonl)

Ler `transcripts/combate_vivo_<ts>.jsonl` (1 linha/turno) + o `.summary`. Cada criterio
cita TURNO + trecho literal. O motor (cells/vitais/dado) e a verdade objetiva; a prosa e
o que se audita contra ele.

## A — A3: vazamento de numero de mecanica na PROSA
A prosa (`prosa_cronista`) contem numero de regra? ("X de dano", "pressao N", "HP", vida/
mana/vigor/fadiga em digito). Esses numeros devem viver SO no `<estado>` (`estado_ditado`),
nunca na prosa. Listar cada ocorrencia: turno + trecho. Esperado: ZERO digito de mecanica
na prosa (numeros por extenso, se houver).

## B — Tom (witcher-grey, consequencia real)
A prosa entrega consequencia fisica (sangue, dor, exaustao, peso) ou vira coreografia
heroica/limpa? Citar 2-3 trechos representativos. Sinal ruim: golpes "elegantes" sem custo,
heroismo, adjetivacao epica.

## C — Coerencia motor <-> narracao
Cruzar `cells`/`vitais`/`dado` com `prosa_cronista` turno a turno:
  - Houve dano no motor (vigor/hp caiu, ou hp do alvo caiu) -> a prosa narra o golpe/ferimento?
  - Ferida nas cells (`feridas` nao vazio) -> a prosa menciona a ferida/sangramento?
  - Alvo com hp 0 / `[X caiu]` em `resultado` -> a prosa fecha aquela luta (nao segue batendo)?
  - `via: magico/combo` -> a prosa mostra a fagulha/magia, nao so a lamina?
Listar divergencias (turno + o que o motor diz vs o que a prosa diz).

## D — Trava de linguagem (moldura espirita)
alma/fantasma/espirito/demonio usados como SER/entidade? Listar ocorrencias (turno + trecho).
Esperado: zero (a moldura do mundo nao e espirita).

## E — Respeito ao dado
A prosa declara o DESFECHO de uma acao testada ANTES do dado rolar? (ex.: narra o inimigo
caindo no mesmo turno em que so ARMOU o dado, antes do roll). Cruzar: turno onde `dado` e
null mas a prosa ja resolve o golpe -> suspeito. Listar turnos.

## F — Fecho (B1): a ultima imagem
O ultimo turno (rescaldo): a imagem final CONFORTA (alivio facil, promessa de que vai
ficar bem) ou deixa a CONSEQUENCIA de pe (custo, cansaco, o que se perdeu)? Citar a frase
final literal.
