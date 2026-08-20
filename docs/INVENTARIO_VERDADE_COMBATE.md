# INVENTÁRIO DA VERDADE — Combate no /jogar-c

Estado **real**, lido do código vivo (jun/2026), não da memória. Gerado em modo noturno
como FALLBACK da "faxina da pressão morta" (ver §6 — por que a faxina foi bloqueada).

Convenção: a ficha estilo C vive em `ficha_c.py` (extraída do mock `jogar_mock/`); o loop
do jogo vive em `jogo.py`. Tudo escopado a `/jogar-c` (flag `FICHA_C`, jogo.py:111). O
`/jogar` produção é intocado.

---

## 1. A cadeia de combate (Fatias 0–3) — o que cada uma liga

| Fatia | O que liga | Escrita no banco? |
|---|---|---|
| **0 — espelho vivo** | A ficha re-lê os 5 vitais do banco a cada turno → barras refletem sozinhas. | Não (leitura) |
| **1 — Tensão** | Sistema sabe quando há briga (flag `combate: 1` do Cronista → contador 1-10 em memória). Barra `.p-pressao` mostra Tensão em combate, escondida fora. | Não (memória) |
| **2 — dano em você** | A faixa do 2d10 custa um vital (Vigor amortece, HP é o ferimento real, transbordo). | **Sim** (UPDATE personagens + commit) |
| **3 — o inimigo** | Cronista declara `inimigo: nome \| tier`; a faixa fere o inimigo; condição volta qualitativa; ao cair, a luta encerra (Tensão some). | Não (memória) |

**O circuito de "vencer uma briga" está fechado:** uma faixa resolve os dois lados
(você sofre num desfecho ruim; o inimigo cede num bom), no mesmo roll.

---

## 2. Símbolos-chave (arquivo:linha real)

### jogo.py — regex/constantes (módulo)
- `_RE_ESTADO` — **jogo.py:505** (isola o bloco `<estado>…</estado>`)
- `_RE_PRESSAO` — **jogo.py:508** (parseia `pressao_emocional` — ver §6, débito)
- `_RE_COMBATE` — **jogo.py:511** (`combate: (1|sim|ativo)`)
- `_RE_INIMIGO` — **jogo.py:514** (`inimigo: nome | (comum|bravo|elite)`)
- `TIER_HP` — **jogo.py:515** (`{comum:6, bravo:12, elite:20}`)

### jogo.py — estado por sessão (dentro de `_pagina_jogar`)
- `tensao_atual = None` init — **jogo.py:2439** (Tensão 1-10, efêmera/memória)
- `inimigo = None` init — **jogo.py:2440** (`{nome, hp, hp_max}`, efêmero/memória)
- `pressao_atual = 0` init — **jogo.py:2435** (ver §6)

### jogo.py — Fatia 0 (espelho vivo)
- `async def _empurrar_vitais(sessao_id, *, com_estaticos=False)` — **def jogo.py:2481**
  - push dos 5 vitais via `fichaSetVitais` — **jogo.py:2524**
  - chamada no LOAD (`com_estaticos=True`) — dentro de `if com_ficha and FICHA_C:` **jogo.py:2590**
  - chamada no FIM DO TURNO — **jogo.py:2844** (guardada por `if com_ficha and FICHA_C:` L2843)

### jogo.py — Fatia 1 (Tensão)
- parse do flag (escopado ao `<estado>`) + contagem — **jogo.py:~2802-2806** (no `narrar`)
- push da barra de Tensão — **jogo.py:2835** (`fichaSetTensao(tensao_atual)`)
- esconder no load — **jogo.py:2597** (`fichaSetTensao(null)`)
- resets: recomeçar **jogo.py:2899/2905**, encerrar **jogo.py:2940/2946**
- nonlocals com `tensao_atual`: narrar **jogo.py:2691**, recomeçar **2890**, encerrar **2913**

### jogo.py — Fatia 2 (dano em você)
- `async def _aplicar_dano_combate(sessao_id, faixa)` — **def jogo.py:2546**
  - SELECT+UPDATE+commit atômico, depois `_empurrar_vitais` (re-push)
- disparo no `ao_rolar_dado` — **jogo.py:2999-3000** (gate `if tensao_atual is not None and FICHA_C`)

### jogo.py — Fatia 3 (inimigo)
- SPAWN no `narrar` — **jogo.py:2808-2814** (`if not _combate_on: inimigo=None` / `else` spawn se None)
- lado do inimigo no `ao_rolar_dado` — **jogo.py:3001-3017** (mesmo gate da Fatia 2, mesmo roll)
- limpa ao cair (`inimigo = None`) — **jogo.py:3012**
- resets: recomeçar **jogo.py:2900**, encerrar **jogo.py:2941**

### ficha_c.py — hooks da ficha (JS)
- `window.fichaSetTensao(n)` — **ficha_c.py:1109** (1-10 mostra/`null` esconde a `.p-pressao`)
- `window.fichaSetVitais(v)` — **ficha_c.py:1130** (5 barras: Vida/Vigor/Mana/Fadiga/Dissolução)
- `window.fichaSetAtributos`, `window.fichaSetIdentidade` — Fatias 0/1 (mods, vocação/nível)
- `window.fichaSetPressao` — **ficha_c.py:1098** (VESTIGIAL: existe, **não é mais chamado** por jogo.py)
- barra `.p-pressao` — BODY **ficha_c.py:602**; rótulo "Pressão emocional" **ficha_c.py:601** (lê Tensão; rótulo velho — ver §6)

---

## 3. As travas vivas (invariantes do código)

**Vitais (Fatias 0/2):**
- best-effort POR CAMPO: `is not None` (0 é válido — Fadiga/Dissolução nunca caem por truthy).
- clamp piso 0 ANTES do UPDATE (nunca grava negativo).
- atômico: SELECT + UPDATE + commit na mesma session; re-leitura (`_empurrar_vitais`) só após o commit.
- `falha` → transbordo: déficit que o Vigor não absorveu cai no HP.

**Tensão (Fatia 1):**
- flag parseado SÓ do bloco `<estado>` (`_m_est.group(1)`), nunca da prosa.
- conta em memória; cap 10; `combate` ausente → `None` (barra some).

**Inimigo (Fatia 3):**
- spawn SÓ se `inimigo is None` (re-declarar não reseta o HP de um ativo).
- `tier.lower()` no spawn (regex é case-insensitive).
- chaves literais de dano: `{"sucesso_critico":6, "sucesso":4, "sucesso_parcial":2}`.
- ordem dos branches: `hp<=0` (caiu) ANTES de `hp<=hp_max/2` (ferido).
- tag de condição anexada ao `resultado_pendente` SEMPRE (fora do guard de intenção) → "caiu" sempre chega ao Cronista e a luta fecha.
- 100% memória — zero escrita no banco por causa do inimigo.

**Regra dos dois lados (uma faixa):**
| faixa | inimigo | você |
|---|---|---|
| sucesso_critico | −6 | nada |
| sucesso | −4 | nada |
| sucesso_parcial | −2 | −2 Vigor |
| falha | nada | −4 Vigor (transbordo HP) |
| falha_critica | nada | −ceil(15% HP máx) |

**Condição do inimigo → Cronista (qualitativa, nunca número):**
hp>50% sem tag · 0<hp≤50% `[<nome> está ferido]` · hp≤0 `[<nome> caiu]` + derrotado.

---

## 4. Contrato com o Cronista (`cronista_prompt.py`, bloco `<canal_duplo>`)

O Cronista emite, no `<estado>` ao fim da resposta:
- `pressao_emocional: N` — SEMPRE (vestígio; nada consome o valor na barra — ver §6).
- `combate: 1` — só em briga física ativa; omitir quando a violência para (Fatia 1).
- `inimigo: nome | tier` — uma vez, ao entrar oponente (Fatia 3); tier por perigo; nunca número.

De volta, no `[ESTADO]` de entrada (montado por `_montar_estado_safe`, jogo.py:387):
`pressão_emocional: N` + `resultado_teste: <intenção> — <faixa> [<inimigo> ferido/caiu]`.

---

## 5. O que NÃO existe ainda (próximas fatias)

- **Turno-de-inimigo / iniciativa** — o inimigo não age; não há ordem de turnos.
- **Postura** (medidor estilo Sekiro que enche e quebra).
- **Custo de Ação** (Quick / Standard / Heavy).
- **Posição + Efeito** (Controlada/Arriscada/Desesperada × Limitado/Normal/Grande — estilo Blades).
- **Ferimento nomeado** (descritores) — só há as tags qualitativas ferido/caiu.
- **Vínculo do companheiro** (pool de tokens).
- **Distinção ataque × ação defensiva** — hoje QUALQUER faixa boa em combate fere o inimigo (até uma esquiva). Simplificação conhecida.
- **Mais de um inimigo** — um por vez (spawn só se None).
- **`combat.py` (D&D 5e, stored procs)** — NÃO usado pelo /jogar; é a rpg-api legada, paradigma diferente (d20). O combate vivo reusa o loop 2d10 do /jogar.
- **Barra de vida do inimigo** — de propósito: o inimigo é invisível como número; lê-se o estado dele na prosa (estética witcher-grey).

---

## 6. A Pressão Emocional — por que a faxina foi BLOQUEADA (acoplamento vivo)

A hipótese era que `pressao_atual` fosse puramente vestigial. **Não é.** O PASSO 0 divergiu:

- **H1 FALSO / H2 FALSO:** o valor parseado por `_RE_PRESSAO` (jogo.py:508/556) vira `pressao_atual` (jogo.py:2798) e é **consumido vivo** em dois lugares:
  1. **`_montar_estado_safe`** (jogo.py:2722 → linha `pressão_emocional: N` em jogo.py:399) — o `[ESTADO]` de entrada do Cronista, que o `cronista_prompt.py` documenta. Compartilhado pelas duas rotas.
  2. **`window.Jogar.setPressao(pressao_atual)`** — o HUD do **shell**.
- **H3 = ZONA DE RISCO CONFIRMADA:** `setPressao` está em **jogo.py:2832**, no bloco compartilhado do `narrar` — **fora** do guard `if com_ficha and FICHA_C` (que só começa em jogo.py:2843). Também em recomeçar (jogo.py:2904) e encerrar (jogo.py:2945). **Não é escopável ao /jogar-c**: remover toca o `/jogar` produção.

→ Remover `pressao_atual` / `_RE_PRESSAO` / `setPressao` mexeria no `/jogar` produção (sagrado) **e** no contrato de entrada do Cronista. Por isso a faxina foi abortada (modo noturno, sem ninguém pra decidir o acoplamento).

**H4 (isolado e seguro, mas NÃO aplicado — gate mandou fallback):** a barra `.p-pressao`
**já lê Tensão** (`fichaSetTensao`, ficha_c.py:1109); só o rótulo "Pressão emocional"
(ficha_c.py:601) está velho. Trocar o rótulo → "Tensão" é uma mudança limpa, isolada a
`ficha_c.py`, que NÃO toca o /jogar. **Débito pronto pra aplicar** numa janela acordada.

**Débitos cosméticos/mortos anotados (não tocados):**
- ficha_c.py:601 — rótulo "Pressão emocional" deveria ser "Tensão".
- ficha_c.py:1098 — `fichaSetPressao` é código morto (não chamado); pode sair.
- cronista_prompt.py — o Cronista ainda emite `pressao_emocional: N` (vestígio inofensivo).
- jogo.py — `pressao_atual` + `_RE_PRESSAO` só sobrevivem por causa do HUD do shell e do
  `[ESTADO]` de entrada; a remoção real exige decidir o destino do HUD do shell (com o Gabriel).
