# HANDOFF OPERACIONAL — TRILHA BESTIÁRIO (Alderyn)
### Para execução pelo Claude Code · gerado 2026-06-29 (pós-Bloco 4) · cobre o estado pós-Bloco 4 (Lotes 14–18 + Lote 19 + Blocos 1, 2, 3 e 4)

> **O que é isto.** Um runbook completo e auto-suficiente para canonizar criaturas do bestiário do *Sistema Nexus / Catedral do Alderyn*, convertendo stat blocks de D&D para o canon witcher-grey do mundo. Quem segue este documento consegue rodar um "Lote" (5 criaturas) do começo ao fim sem contexto extra. Tudo que muda (estado do banco, lista de exclusão, roster) está embutido e veio de query real em 28/06/2026, não de memória.
>
> **Regra-mãe:** banco vivo > docs > memória. Se este documento divergir do banco, o banco vence — re-leia o banco.

---

## 0. TL;DR (orientação em 30 segundos)

- **Tabela única:** `ref_criaturas`. **Banco:** Neon PostgreSQL 17.8, `projectId = delicate-heart-76798097`.
- **Estado:** **198 canonizadas**, **301 no pool de trabalho** (`status_conversao='classificada'`), **trava de linguagem = 0**.
- **Um Lote = 5 criaturas.** Cada uma vira um `UPDATE` numa linha que já existe (status `classificada` → `canonizada`).
- **Não se toca o stat block mecânico** (atributos, `dados_json`, `cr`, `idiomas`…). Escreve-se a **ficção em volta** dele.
- **Gate humano obrigatório:** Gabriel aprova a composição dos 5 ("bora") **antes** de qualquer escrita. Nada de canonizar sem o gate.
- **Sinal de sucesso do write:** `UPDATE` sem `RETURNING` devolve `[]`. Isso é **êxito**, não erro.
- **Três eixos sempre distintos entre os 5:** pilar, `behavior_archetype`, `tipo_perigo`.
- **Tom inegociável:** witcher-grey (moralmente ambíguo, magia tem custo, sem mal puro, sem high fantasy). **Trava de linguagem:** nada de *alma/fantasma/espírito/demônio* como ser, nem negado.

---

## 1. A MISSÃO E O QUE É UM "LOTE"

O bestiário tem ~2138 linhas importadas de D&D. Cada linha tem um stat block mecânico (CA, HP, atributos, ações em `dados_json`, etc.) e campos de ficção vazios. **Canonizar** = preencher os campos de ficção de uma criatura com lore witcher-grey do Alderyn, reescrevendo o monstro de D&D como uma criatura original do mundo, e marcar `status_conversao='canonizada'`.

Trabalha-se em **Lotes de 5 criaturas**. A graça do lote é **variedade máxima**: cada lote deve cobrir os 5 pilares, 5 arquétipos de comportamento e 5 tipos de perigo distintos, espalhando ainda continente, faixa de CR e (quando dá) tipo de criatura de D&D. Isso garante que o bestiário cresça equilibrado, não amontoado num canto.

Progresso atual: **93 de ~499 trabalháveis** (93 canonizadas + 406 classificadas). Os Lotes 1–18 já rodaram. **O próximo é o Lote 19.**

---

## 2. MODOS DE OPERAÇÃO E O GATE HUMANO (ler com atenção)

### 2.1. O gate humano é inegociável
A canonização é **irreversível por verbalização**: no projeto do Gabriel, o que é aprovado vira canon permanente. Portanto:

1. O Claude Code **compõe** os 5 (lê o pool, escolhe, confere variedade e colisão) e **apresenta** a composição ao Gabriel — tabela + conceito curto de cada um.
2. **Espera o Gabriel aprovar** (ele responde com palavra curta: "bora", "aprovado", "i"). Só o "bora" sobre a composição libera escrita.
3. **Só então grava.**

Nunca canonizar 5 criaturas direto sem mostrar a composição e receber o ok. Mesmo com acesso de escrita, o gate vem primeiro. Se o Gabriel pedir troca de alguma, troca-se antes de gravar.

### 2.2. Como a escrita chega ao banco (dois caminhos)
Dependendo de como o Claude Code estiver plugado:

- **Caminho A — escrita direta (MCP Neon / conexão psql):** se o Claude Code tem acesso de escrita confirmado ao Neon e o Gabriel autorizou rodar, ele mesmo executa os `UPDATE`s, um a um, e confirma cada `[]`.
- **Caminho B — gerar SQL pro Gabriel:** se não há acesso de escrita (ou o Gabriel prefere pgAdmin), o Claude Code **monta os 5 blocos `UPDATE` prontos pra colar**, delimitados e auto-contidos, e o Gabriel executa. O Claude Code então recebe a confirmação e roda as queries de verificação.

Em ambos os caminhos: **gate primeiro, escrita depois, verificação sempre.** Marque os blocos SQL pro Gabriel com 🟢 (rodar no pgAdmin) quando for o Caminho B.

---

## 3. BANCO: IDENTIDADE, SCHEMA, SINAIS

### 3.1. Identidade e sinais
- **projectId:** `delicate-heart-76798097`
- **Tabela:** `ref_criaturas` (~2138 linhas)
- **Sinal de sucesso de `UPDATE`/`run_sql` sem `RETURNING`:** retorna `[]`. **Isso é sucesso.** Não re-rodar achando que falhou.
- **Pool de trabalho:** `WHERE status_conversao='classificada'`.
- **Já feito:** `WHERE status_conversao='canonizada'`.

### 3.2. As 25 colunas de ficção (as ÚNICAS que se editam)
`nome`, `nome_ptbr`, `slug`, `origem`, `andar_primario`, `pilar_associado`, `continente` (array `_text`), `habitat`, `comportamento`, `organizacao`, `perigo`, `behavior_archetype`, `morale_modifier` (numeric), `morale_immune` (bool), `epigrafe`, `descricao`, `supersticao_popular`, `sinais_presenca`, `fraqueza_conhecida`, `fraqueza_real`, `descricao_sensorial`, `ecologia` (jsonb), `loot_table` (jsonb), `camada_narrativa` (jsonb), `status_conversao`.

### 3.3. O que NÃO se toca (stat block mecânico)
`ca`, `hp_medio`, `forca`, `destreza`, `constituicao`, `inteligencia`, `sabedoria`, `carisma`, `fortitude`, `reflexos`, `vontade`, `resistencias`, `imunidades`, `vulnerabilidades`, `sentidos`, `idiomas`, `velocidades`, `cr`, `tamanho`, `subtipo`, `dados_json`. A ficção se escreve **em volta** desses números. Se o `dados_json` não tem um efeito, a ficção **não inventa** esse efeito (ver §4.4).

### 3.4. Forma dos três campos JSONB
- **`ecologia`** = objeto com **6 chaves**:
  - `presa` (array, 2 itens)
  - `predador` (array, 1+ itens)
  - `competidor` (array, **2 itens — o 2º é o nome exato de uma criatura JÁ canonizada**; ver §5.9)
  - `simbionte` (array vazio: `jsonb_build_array()`)
  - `indicador` (string — "a presença dela diz que…")
  - `evitado_por` (array, 1 item)
- **`loot_table`** = array de **4 objetos**, cada um `{material, raridade, uso, risco}`. Raridades em ordem **decrescente**: `Raro` → `Notável` → `Distinto` → `Ordinário`. (Bestas mundanas, sem nada mágico, podem começar em `Notável` e pular `Raro`.) **O campo `uso` NUNCA contém a palavra "Espírito"** — usar o nome do pilar ou do andar (Clarão/Eco/Margem) em vez disso.
- **`camada_narrativa`** = objeto com **9 chaves**:
  - `som` (string)
  - `cheiro` (string)
  - `quer` (string — o que a criatura quer)
  - `tipo_perigo` (string — um de: Direto, Persistente, Condicional, Oculto, Ambiental)
  - `falas_exemplo` (array de **3 falas** SE a criatura fala; **`'null'::jsonb` se for muda** — ver §5.7)
  - `gatilhos_agressao` (array, 3)
  - `gatilhos_fuga` (array, 3)
  - `descoberta_fazendo` (string — o que ela está fazendo quando encontrada)
  - `desfechos_nao_combate` (array, 4 — saídas que não a luta)

---

## 4. A BÍBLIA DE CANON (tom, linguagem, prosa, reskin)

### 4.1. Witcher-grey, sempre
Moralmente ambíguo. Magia tem custo. **Sem mal puro, sem high fantasy, sem fofura.** Toda criatura tem lógica própria (caça, território, fome, dever frio), não "maldade" gratuita. Celestiais do **Clarão** são forças frias e indiferentes que julgam por régua, **não anjos bondosos**. Mesmo um guardião não é "bonzinho": é uma sentinela que não sofre aproximação.

### 4.2. Trava de linguagem (INEGOCIÁVEL)
Proibido usar **`alma(s)`, `fantasma(s)`, `espírito(s)`, `demônio(s)`** como ser sobrenatural — **mesmo negando** ("não há alma nenhuma" também viola). Proibido **inferno** como lugar.

| Em vez de… | Use… |
|---|---|
| alma / fantasma / espírito (ser) | eco, resto, sobra, vestígio, **Margem**, **Ressonância**, **Cicatriz** |
| demônio / coisa do inferno | o Corrompido, o Marginal, coisa da Margem |
| inferno (lugar) | a Margem, o fundo, a cova |

**Exceções permitidas:** `"Espírito"` **só** como valor de `pilar_associado` (nunca na prosa). `sombra` como sombra **literal** (a sombra projetada) é permitido. `anjo` é permitido **se** o texto deixa claro que o povo está errado (ex.: "alguns o chamam de anjo, mas não há bondade nele"). `morto`, `sagrado`, `céu` são permitidos.

**Auto-checagem:** a query de trava (§7.5) varre todo lote e pega violações inclusive em fichas antigas. Rodar **todo lote**, esperar `fichas_com_proibida = 0`.

### 4.3. Prosa das fichas
- **Sem bullets, sem listas, sem negrito** dentro dos campos de ficção. Só prosa corrida.
- Frases **curtas**, legíveis (registro McCarthy/Hemingway): palavra comum, frase enxuta, ritmo. É requisito de acessibilidade, não estilo.
- `descricao_sensorial` segue a ordem fixa: **som → cheiro → toque → visão**.
- Sem emojis. Sem apóstrofo dentro de `$DESC$` (escrever "da água", não "d'água") — apóstrofo quebra o dollar-quoting na prática do projeto.

### 4.4. Disciplina de reskin (fidelidade ao bloco)
Reescreve-se a **aparência, o nome e o significado** livremente, mas a **mecânica** vem do `dados_json`. **Não inventar efeitos que o bloco não tem.** Exemplos reais do que foi feito:
- "Hellfire Orb" → **fogo de cova / fogo amaldiçoado** (sem inferno). O nome da ação no `dados_json` fica intacto; a ficção descreve o efeito sem invocar inferno.
- Idioma "Abyssal" no bloco → fica mecânico e intocado; a ficção fala em "língua morta", nunca em demônios.
- Couatl (guardião bondoso) → **sentinela fria do Clarão** que não sofre aproximação.
- Hollyphant (elefantinho fofo dourado) → **caco pequeno, antigo e grave do Clarão**, com a aura anti-magia como o que importa; trompete "do bem/do mal" reskinado para só luz/dano.
- Green Slaad com "implante de ovo" **ausente** do bloco → a ficção **não** usou ovo; ficou no que o bloco tem (Shape-Shift = usa cara humana). Fidelidade.

### 4.5. Andares e como a origem mapeia — REGRA-ÂNCORA (inegociável)
O bestiário usa "andares": **Superfície, Eco, Margem, Clarão.** O `andar_primario` é **determinado pela origem** e vem **copiado da coluna `andar` do pool** — não é escolha de composição. Mapeamento:
- `Natural` → Superfície
- `Ressonante` → Superfície (criatura elemental/ressonante do mundo)
- `Marginal` → Margem (coisas da Margem; aberrações)
- `Cicatricial` → Eco (mortos) **ou** Clarão (luz-cicatriz/celestiais), conforme a criatura

**ÂNCORA (canon 2026-06-29):** o andar SEGUE a origem. Você COPIA o andar do pool; nunca o move, nunca o relabela. É proibido mudar o andar de um bicho para fugir de saturação — se o andar honesto está cheio, ou troca-se de criatura, ou aceita-se a saturação (que é preferência **soft**). Reskinar witcher-grey NÃO muda o andar: um celestial vira ser do Clarão de qualquer forma; um morto vira eco. Um bicho `Natural` reskinado como Espírito (ex.: o alce Cornamenta) continua `Natural`/Superfície.

**Loot segue a origem também:** criatura `Natural` (mundana) rende **corpo mundano**, teto **Notável** (Notável→Distinto→Ordinário→Ordinário), sem "Componente" mágico. Criatura sobrenatural (`Cicatricial`/`Marginal`/`Ressonante`) rende material especial, teto **Raro**. O pilar NÃO sobrescreve isto.

### 4.6. Os quatro continentes (sabor)
- **Vyrkhor** — frio, picos, ruínas geladas, passos de montanha.
- **Kethara** — calor, deserto, oásis, forjas, ruínas de areia.
- **Thornmarak** — cristais, alturas, o Clarão se aproxima ali; baixadas úmidas nas terras baixas.
- **Voranthar** — ruínas, o Eco da Primeira Travessia, exércitos caídos, esgotos de cidades mortas, a Margem fina.

### 4.7. Cânone de mundo que não pode ser contrariado
Demônios não existem. O mundo nunca é totalmente mapeado. Era atual: Vigília Quebrada, ano 312. 5 pilares: corpo, sombra, arcano, espírito, engenho. **Psionismo = Engenho** (canônico — domínio mental, telepatia e afins são Engenho, não Arcano).

---

## 5. ALGORITMO DE COMPOSIÇÃO (como escolher os 5)

### 5.1. Os três eixos DUROS (sempre 5 distintos)
1. **`pilar_associado`** — os 5: corpo, sombra, arcano, espírito, engenho. Um de cada por lote.
2. **`behavior_archetype`** — 5 distintos. Taxonomia em uso (§5.4).
3. **`tipo_perigo`** — os 5: Direto, Persistente, Condicional, Oculto, Ambiental. Um de cada (§5.5).

### 5.2. Eixos DESEJÁVEIS (otimizar, mas pode ceder por tema melhor)
- **5 tipos de criatura de D&D distintos** (besta, morto-vivo, gigante, aberração, elemental, celestial…). Bom ter, não obrigatório — já foi quebrado de propósito quando um tema fresco valia mais.
- **4 continentes** representados (o 5º dobra um).
- **Faixa de CR espalhada** dentro do lote (ou um lote "mid-tier" inteiro, como variação entre lotes).

### 5.3. Régua-1 (perigo por CR) — define o campo `perigo`
- **CR ≤ 5** → `Ameaça`
- **CR 6–15** → `Letal`
- **CR ≥ 16** → `Destruidor`

### 5.4. Taxonomia de `behavior_archetype` (valores em uso no banco)
`brute`, `predator`, `skirmisher`, `lurker`, `ambusher`, `controller`, `trapper`, `artillery`, `striker`, `defender`, `tactical`, `soldier`, `swarm`.

Distinções úteis (para não colidir dentro de um lote):
- **lurker** = se esconde, golpeia e some (móvel, furtivo).
- **ambusher** = espera emboscado/enterrado e agarra o que chega.
- **trapper** = faz armadilha/terreno; a presa vem até a armadilha.
- **brute** = massa, dano direto, aguenta porrada.
- **controller** = prende, domina, manipula o campo.
- **artillery** = dano à distância.
- **skirmisher** = bate e corre, mobilidade.

### 5.5. Definições de `tipo_perigo`
- **Direto** — o perigo é o ataque frontal; ela vem e bate/mata.
- **Persistente** — o perigo continua/piora (regeneração, doença que avança, ergue mais mortos, infecção que se espalha).
- **Condicional** — o perigo dispara numa condição (transgressão, ameaça ao que guarda, provocação).
- **Oculto** — o perigo está escondido/invisível até golpear (furtividade, breu, enterrado, invisível).
- **Ambiental** — o perigo é o espaço/terreno (zona de veneno, terremoto, chão que vira armadilha, área negada).

### 5.6. `origem`/`andar_primario`/`continente`
- `origem` e `andar_primario`: respeitar o mapeamento §4.5 e a natureza da criatura.
- `continente`: escolher pelo sabor (§4.6) e espalhar pelos 4. Sempre array: `ARRAY[$DESC$X$DESC$]::text[]`.

### 5.7. Voz (fala ou muda) — vem do bloco
Olhar `idiomas` no stat block:
- Tem língua / telepatia → **fala** → `falas_exemplo` = array de **3** (a 3ª costuma ser um "registro:" descrevendo COMO fala).
- `idiomas = "Nenhum"` (besta/mente nula) **ou** "entende mas não fala" → **muda** → `falas_exemplo` = `'null'::jsonb`.
- **Variar entre lotes:** alguns lotes com 0 mudos, outros com 1–2. Não deixar todo lote igual.

### 5.8. `morale_immune` e `morale_modifier`
- **`morale_immune = true`** (não foge por medo): forças mindless (besta sem mente, void), coisas presas a um dever/laço/maldição (sentinela, comandante amaldiçoado, servo amarrado), vereditos. Para essas, "fuga" nos `gatilhos_fuga` = "vai embora quando a condição se cumpre / quando o que a incomodava some", não medo.
- **`morale_immune = false`** + `morale_modifier`:
  - `+2` ousadia alta (regenera, quase não morre).
  - `+1` teimosa/dogmática no posto (defensor, predador territorial).
  - `0` luta padrão.
  - `-1` covarde, foge cedo (escravista que manda thralls na frente, bicho frágil).

### 5.9. Cross-ref ecológico (o 2º `competidor`)
O **2º item de `competidor`** deve ser o **nome exato de uma criatura já canonizada** (ver roster §8.3), de preferência do **mesmo continente** e nicho plausível. Isso costura a teia ecológica do bestiário. Variar a qual lote/criatura se liga. Conferir o nome exato no roster antes de escrever.

### 5.10. Colisão de primeira palavra (regra rígida)
**Zero colisão da primeira palavra do nome** (`split_part(nome,'-',1)`) com qualquer criatura já canonizada. Conferir via query (§7.2) **antes** de fechar nomes, testando variantes com e sem acento. Índice de primeiras-palavras tomadas em §8.4.

### 5.11. Estilo de nome
Padrão `Primeira-Segunda` (duas palavras, hífen), português, witcher-grey, concreto. Costuma nomear a criatura pelo traço-assinatura ou pela forma. Evitar repetir adjetivos batidos demais no mesmo lote (já saturados no banco: "-Vivo/a", "-Cego/a", "-Mudo/a", "-Faminto/a", "-Frio/a", "-Velho/a"). Conferir colisão sempre.

---

## 6. TEMPLATE DE FICHA (SQL preenchível) + EXEMPLO COMPLETO

### 6.1. Template em branco (preencher e rodar — UM por criatura)
```sql
UPDATE ref_criaturas SET
nome=$DESC$<Nome-Composto>$DESC$,
nome_ptbr=$DESC$<Nome-Composto>$DESC$,
slug=$DESC$<nome-composto-sem-acento>$DESC$,
origem=$DESC$<Natural|Ressonante|Marginal|Cicatricial>$DESC$,
andar_primario=$DESC$<Superfície|Eco|Margem|Clarão>$DESC$,
pilar_associado=$DESC$<Corpo|Sombra|Arcano|Espírito|Engenho>$DESC$,
continente=ARRAY[$DESC$<Continente>$DESC$]::text[],
habitat=$DESC$<onde vive, 1-2 frases>$DESC$,
comportamento=$DESC$<como age, 2-3 frases>$DESC$,
organizacao=$DESC$<sozinha / em grupo / etc.>$DESC$,
perigo=$DESC$<Ameaça|Letal|Destruidor>$DESC$,
behavior_archetype=$DESC$<archetype>$DESC$,
morale_modifier=<int>,
morale_immune=<true|false>,
epigrafe=$DESC$<uma fala curta de testemunha, sem aspas internas>$DESC$,
descricao=$DESC$<o corpo da ficha; prosa curta witcher-grey; o que é, o que faz, o custo>$DESC$,
supersticao_popular=$DESC$<o que o povo diz e o conselho prático; pode estar meio errado>$DESC$,
sinais_presenca=$DESC$<5 sinais concretos de que ela está perto>$DESC$,
fraqueza_conhecida=$DESC$<o que o povo ACHA que é a fraqueza; o método comum>$DESC$,
fraqueza_real=$DESC$<a fraqueza/verdade mais funda; o que de fato resolve>$DESC$,
descricao_sensorial=$DESC$<ordem fixa: som, depois cheiro, depois toque, depois visão>$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$<presa 1>$DESC$, $DESC$<presa 2>$DESC$),
'predador', jsonb_build_array($DESC$<predador/o que a encerra>$DESC$),
'competidor', jsonb_build_array($DESC$<competidor genérico>$DESC$, $DESC$<NOME DE CRIATURA JÁ CANONIZADA>$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presença dela diz que <o que a presença sinaliza>.$DESC$,
'evitado_por', jsonb_build_array($DESC$<quem sabe evitá-la>$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$<material raro>$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (<Pilar ou Andar> / <para quê>)$DESC$, 'risco', $DESC$<risco de manusear>$DESC$),
jsonb_build_object('material', $DESC$<material>$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$<uso>$DESC$, 'risco', $DESC$<risco>$DESC$),
jsonb_build_object('material', $DESC$<material>$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$<uso>$DESC$, 'risco', $DESC$<risco>$DESC$),
jsonb_build_object('material', $DESC$<material comum>$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (<para quê>)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$<som>$DESC$,
'cheiro', $DESC$<cheiro>$DESC$,
'quer', $DESC$<o que ela quer>$DESC$,
'tipo_perigo', $DESC$<Direto|Persistente|Condicional|Oculto|Ambiental>$DESC$,
'falas_exemplo', jsonb_build_array($DESC$<fala 1>$DESC$, $DESC$<fala 2>$DESC$, $DESC$(registro: <como ela fala>)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$<g1>$DESC$, $DESC$<g2>$DESC$, $DESC$<g3>$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$<f1>$DESC$, $DESC$<f2>$DESC$, $DESC$<f3>$DESC$),
'descoberta_fazendo', $DESC$<o que está fazendo quando encontrada>$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$<d1>$DESC$, $DESC$<d2>$DESC$, $DESC$<d3>$DESC$, $DESC$<d4>$DESC$)
),
status_conversao='canonizada'
WHERE id=<ID>;
```

**Variante MUDA:** trocar a linha de `falas_exemplo` por:
```sql
'falas_exemplo', 'null'::jsonb,
```

### 6.2. Exemplo COMPLETO e real (Grilhão-Frio — a primeira criatura psiônica, Lote 18)
Mostra: framing de Engenho via psionismo, falas (3), morale negativo (covarde), cross-ref para criatura canonizada (Marechal-Roto), uso de loot sem "Espírito".
```sql
UPDATE ref_criaturas SET
nome=$DESC$Grilhão-Frio$DESC$,
nome_ptbr=$DESC$Grilhão-Frio$DESC$,
slug=$DESC$grilhao-frio$DESC$,
origem=$DESC$Marginal$DESC$,
andar_primario=$DESC$Margem$DESC$,
pilar_associado=$DESC$Engenho$DESC$,
continente=ARRAY[$DESC$Voranthar$DESC$]::text[],
habitat=$DESC$Ruínas de Voranthar onde a Margem está fina. Caça vontade, não carne, do alto e do canto escuro.$DESC$,
comportamento=$DESC$Fraca de corpo, luta com a vontade: toma alguém por dentro e o faz obedecer um dia inteiro, mesmo contra os companheiros. Manda os dominados na frente e se esconde atrás. Foge cedo se cercada.$DESC$,
organizacao=$DESC$Solitária ou em poucos, cada uma com seus dominados.$DESC$,
perigo=$DESC$Ameaça$DESC$,
behavior_archetype=$DESC$controller$DESC$,
morale_modifier=-1,
morale_immune=false,
epigrafe=$DESC$Não foi a coisa que me machucou. Foi meu próprio irmão, com os olhos vazios, fazendo o que ela mandou pela minha cabeça.$DESC$,
descricao=$DESC$É pequeno, do tamanho de um cão magro, com cara de aranha e corpo de enguia, e fraco de força como poucos. Mas não luta com o corpo: luta com a vontade. Escolhe alguém perto e toma essa pessoa por dentro, e ela passa a obedecer, calada, de olhos vazios, por um dia inteiro, fazendo o que a coisa manda direto na cabeça, mesmo contra os próprios companheiros. A mordida dela tem veneno, e ela sobe parede como aranha, mas a arma de verdade é o escravo que ela faz de você. Manda os dominados na frente e se esconde atrás. Vive nas ruínas de Voranthar, onde a Margem está fina, e caça vontade, não carne.$DESC$,
supersticao_popular=$DESC$Nas ruínas de Voranthar, dizem que existe uma coisa pequena que faz de gente sua marionete, e que o perigo num grupo às vezes é o próprio companheiro de olhos vazios. Os que sabem desconfiam de quem fica calado de repente e obedece sem questionar, porque dizem que a coisa manda pela cabeça, a uma boa distância. Contam que matar a coisa solta os escravos, e que ferir o dominado às vezes o acorda, e que o certo é achar a aranha escondida atrás, não brigar com o amigo enfeitiçado.$DESC$,
sinais_presenca=$DESC$Alguém do grupo que fica calado de repente, de olhos vazios, e obedece a algo que ninguém ouve. Movimento de algo pequeno subindo parede onde não devia, no canto do olho. Teias ou ninhos sujos num canto alto de ruína. Pessoas sumidas de um assentamento sem briga, levadas dóceis. A sensação de uma ordem que não é sua passando pela cabeça de quem está perto.$DESC$,
fraqueza_conhecida=$DESC$A aranha, não o escravo. Quem ela domina vira arma dela, mas o dominado acorda se a coisa morre, se some para longe, ou às vezes quando ferido. Os que sabem não gastam a luta no companheiro de olhos vazios: procuram a coisa pequena escondida atrás, que manda tudo. Matar ou afastar a aranha solta quem ela prende. Brigar com o amigo enfeitiçado é fazer o jogo dela.$DESC$,
fraqueza_real=$DESC$Ela é covarde e fraca de corpo: foge cedo, manda os escravos morrerem por ela, e se esconde no alto ou atrás. Tirado o domínio, ela mesma quase não luta. O domínio quebra com a morte dela, com a distância, ou com dano no dominado, que ganha nova chance de acordar a cada ferida. Quem fura a linha dos escravos e vai na coisa pequena, ou tira o dominado do alcance dela, encerra o controle. Não a deixe escolher quem vira arma; ache-a e ela cai fácil, porque sozinha ela não é nada.$DESC$,
descricao_sensorial=$DESC$O som é um chiado baixo e o arranhar de patas em parede, e a ordem que chega na cabeça sem som. O cheiro é de bicho e de teia velha, azedo e seco. Ao toque, é pequena e leve, de pele fria e patas finas, fraca na mão que a segura. Aos olhos, é uma coisa de cara de aranha e corpo de enguia, pequena, que prefere o alto e o canto escuro, longe da briga que faz os outros travarem.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Gente que ela domina e usa de escravo e de arma$DESC$, $DESC$Viajantes e moradores levados dóceis das ruínas de Voranthar$DESC$),
'predador', jsonb_build_array($DESC$Sozinha é fraca e caçável; o perigo é o escravo que ela põe na frente$DESC$),
'competidor', jsonb_build_array($DESC$Outras coisas da Margem em Voranthar que disputam presa e território$DESC$, $DESC$Marechal-Roto$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presença dela diz que a Margem está fina naquele trecho de Voranthar, e que alguém ali pode estar obedecendo a uma vontade que não é a sua.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem desconfia do companheiro calado de olhos vazios e procura a coisa escondida atrás$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$A glândula com que ela toma a vontade alheia$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Engenho / domínio da mente, ordens à distância)$DESC$, 'risco', $DESC$Tenta dobrar a vontade de quem a manuseia sem preparo.$DESC$),
jsonb_build_object('material', $DESC$Veneno da mordida, recolhido das presas$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Engenho / venenos que entorpecem e amolecem a vontade)$DESC$, 'risco', $DESC$Amolece a guarda de quem o toca; dose errada apaga a vontade.$DESC$),
jsonb_build_object('material', $DESC$Carapaça leve de cara de aranha$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (foco leve, curiosidade)$DESC$, 'risco', $DESC$Nenhum além do desconforto de olhar.$DESC$),
jsonb_build_object('material', $DESC$Teia suja do ninho dela$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (fio grosso e pegajoso)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Chiado baixo e o arranhar de patas em parede, e a ordem que chega na cabeça sem som.$DESC$,
'cheiro', $DESC$Bicho e teia velha, azedo e seco.$DESC$,
'quer', $DESC$Tomar a vontade alheia e fazer de gente sua arma e seu escravo. Mandar de longe e do alto, sem se expor.$DESC$,
'tipo_perigo', $DESC$Direto$DESC$,
'falas_exemplo', jsonb_build_array($DESC$Esse aí já é meu. Olhe os olhos dele. Quer ser o próximo?$DESC$, $DESC$Eu não preciso te tocar. Só preciso que você me ouça por um instante.$DESC$, $DESC$(registro: fala mansa e fria, em comum e em línguas do fundo; promete e ameaça com a mesma calma de escravagista)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Alguém ao alcance fica isolado e vulnerável ao domínio dela$DESC$, $DESC$Alguém ameaça a coisa escondida atrás dos escravos$DESC$, $DESC$Um grupo entra no território dela com vontades para tomar$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Foge cedo quando os escravos caem e ela fica exposta$DESC$, $DESC$Sobe a parede e some no alto quando furam a linha e vão nela$DESC$, $DESC$Larga o domínio e corre quando a briga chega nela mesma, salvando a própria pele$DESC$),
'descoberta_fazendo', $DESC$Escondida no alto ou no canto escuro de uma ruína de Voranthar, mandando um ou mais dominados de olhos vazios fazerem o trabalho, longe da briga.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Procurar a coisa pequena escondida atrás, não brigar com o companheiro dominado.$DESC$, $DESC$Tirar o dominado do alcance dela, o que quebra o controle.$DESC$, $DESC$Ferir de leve o dominado para dar a ele nova chance de acordar, em vez de matá-lo.$DESC$, $DESC$Desconfiar de quem fica calado de olhos vazios e cortar o domínio achando a aranha.$DESC$)
),
status_conversao='canonizada'
WHERE id=543;
```

---

## 7. CAIXA DE QUERIES (prontas — trocar só os ids/listas)

### 7.1. Re-pull do pool (variedade aleatória, exclui já-vistos)
`rn <= 7` por origem; ajustar a lista `NOT IN` com a exclusão acumulada (§8.1).
```sql
WITH pool AS (
  SELECT id, nome, cr, tamanho, subtipo, origem, andar_primario, hp_medio, ca,
    (SELECT string_agg(a->>'nome', ' | ') FROM jsonb_array_elements(dados_json->'acoes') a) AS acoes,
    (SELECT string_agg(t->>'nome', ' | ') FROM jsonb_array_elements(dados_json->'tracos') t) AS tracos,
    row_number() OVER (PARTITION BY origem ORDER BY random()) AS rn
  FROM ref_criaturas
  WHERE status_conversao='classificada'
    AND hp_medio > 0
    AND jsonb_array_length(dados_json->'acoes') > 0
    AND id NOT IN (<EXCLUSAO_ACUMULADA>)
)
SELECT id, nome, cr, tamanho, subtipo, origem, andar_primario AS andar, hp_medio AS hp, ca, acoes, tracos
FROM pool WHERE rn <= 7 ORDER BY origem, cr;
```

### 7.2. Colisão de primeira palavra (deve dar `[]`)
```sql
SELECT id, nome, pilar_associado, split_part(nome,'-',1) AS primeira
FROM ref_criaturas
WHERE status_conversao='canonizada'
  AND split_part(nome,'-',1) ILIKE ANY(ARRAY['<PalavraA>','<VarianteSemAcento>','<PalavraB>','...'])
ORDER BY primeira;
```

### 7.3. Stat blocks completos dos 5 escolhidos
```sql
SELECT id, nome, cr, tamanho, subtipo, origem, andar_primario, hp_medio, ca,
  forca, destreza, constituicao, inteligencia, sabedoria, carisma,
  imunidades, resistencias, vulnerabilidades, sentidos, idiomas, velocidades, dados_json
FROM ref_criaturas
WHERE id IN (<id1>,<id2>,<id3>,<id4>,<id5>)
ORDER BY id;
```

### 7.4. Gate-2 (verificação pós-escrita; guarda contra null nas falas)
Esperado: 5 linhas, `n_loot=4`, `n_presa=2`, `n_comp=2`, `n_falas=3` (ou `null` se muda), `status=canonizada`.
```sql
SELECT id, nome, pilar_associado AS pilar, perigo, behavior_archetype AS arch,
  camada_narrativa->>'tipo_perigo' AS tp,
  array_length(continente,1) AS n_cont,
  jsonb_array_length(loot_table) AS n_loot,
  jsonb_array_length(ecologia->'presa') AS n_presa,
  jsonb_array_length(ecologia->'competidor') AS n_comp,
  CASE WHEN jsonb_typeof(camada_narrativa->'falas_exemplo')='array'
       THEN jsonb_array_length(camada_narrativa->'falas_exemplo') ELSE NULL END AS n_falas,
  morale_immune AS m_imune, morale_modifier AS m_mod, status_conversao AS status
FROM ref_criaturas WHERE id IN (<id1>,<id2>,<id3>,<id4>,<id5>) ORDER BY id;
```

### 7.5. Contagem + trava de linguagem (a regex EXCLUI `pilar_associado`)
Esperado após o Lote 19: `canonizada=98`, `classificada=401`, `fichas_com_proibida=0`.
```sql
SELECT
  (SELECT count(*) FROM ref_criaturas WHERE status_conversao='canonizada') AS canonizada,
  (SELECT count(*) FROM ref_criaturas WHERE status_conversao='classificada') AS classificada,
  (SELECT count(*) FROM ref_criaturas
     WHERE status_conversao='canonizada'
     AND concat_ws(' ',
        nome, nome_ptbr, descricao, supersticao_popular, sinais_presenca,
        fraqueza_conhecida, fraqueza_real, descricao_sensorial, habitat,
        comportamento, organizacao, epigrafe,
        ecologia::text, loot_table::text, camada_narrativa::text
     ) ~* '\m(almas?|fantasmas?|esp[íi]ritos?|dem[ôo]nios?)\M'
  ) AS fichas_com_proibida;
```

### 7.6. (Apoio) achar QUAL ficha violou a trava e com qual palavra
```sql
SELECT id, nome,
  (SELECT array_agg(DISTINCT lower(m[1])) FROM regexp_matches(
     concat_ws(' ', nome,nome_ptbr,descricao,supersticao_popular,sinais_presenca,
        fraqueza_conhecida,fraqueza_real,descricao_sensorial,habitat,comportamento,
        organizacao,epigrafe,ecologia::text,loot_table::text,camada_narrativa::text),
     '\m(almas?|fantasmas?|esp[íi]ritos?|dem[ôo]nios?)\M', 'gi') AS m) AS palavras
FROM ref_criaturas
WHERE status_conversao='canonizada'
  AND concat_ws(' ', nome,nome_ptbr,descricao,supersticao_popular,sinais_presenca,
        fraqueza_conhecida,fraqueza_real,descricao_sensorial,habitat,comportamento,
        organizacao,epigrafe,ecologia::text,loot_table::text,camada_narrativa::text)
   ~* '\m(almas?|fantasmas?|esp[íi]ritos?|dem[ôo]nios?)\M'
ORDER BY id;
```
Correção é cirúrgica via `replace()` no campo afetado, sem retocar o resto da ficha.

---

## 8. ESTADO (exclusão, candidatos, roster, índice de nomes)

### 8.1. Exclusão acumulada (colar inteiro no `NOT IN` do re-pull do Lote 19)
São os ids JÁ VISTOS e rejeitados (o filtro `status='classificada'` já tira os canonizados; esta lista evita re-puxar rejeitados). **[2026-06-29: no fluxo de 2 agentes o menu passou a ser o `pool_bestiario_refiltrado_pos-bloco4_2026-06-29.csv` (121 disponíveis). Esta lista vira histórico de 'já vistos'.]**
```
387,390,82,2406,495,2647,835,900,1115,2096,2117,539,567,905,1119,1144,101,940,971,1203,2399,861,602,1970,1897,1018,510,507,2170,1089,527,1844,70,708,2208,2113,2133,2092,2068,803,383,740,695,1922,672,1889,968,1141,2101,1979,1037,2094,492,1855,1046,2499,877,754,1033,646,651,2009,2177,1892,879,845,813,2129,409,1078,538,742,710,938,1895,925,1066,1110,480,2386,1153,889,1121,2195,2320,1137,1239,1072,69,2210,1007,2035,941,576,2111,897,796,785,1071,846,2010,2222,899,1204,615,2245,486,866,1186,684,1183,712,604,2224,1864,857,688,546,44,843,1212,728,963,997,1040,2061,1187,1138,2100,1009,2221,2119,610,2377,919,934,689,1139,875,784,739,653,1028,504,736,1796,2632,2128,543,1978,2378,2262,11,2095,2125,1038,2127,939,2536,1192,912,1166,522,1985,2292,1032,993,1022,1023,885,1936,776,1167,554,1199,2400,2033,1935,856,622,2069,623,1792,1839,862,1143,2371,706,1240,2109,1977,894,859,704
```
**Manutenção:** depois de cada lote, somar os 5 ids gravados + os rejeitados que apareceram no re-pull mas não entraram. Se a lista ficar incômoda de carregar, a alternativa é confiar só no `status='classificada'` e re-skipar manualmente os poucos rejeitados que ressurgirem — mas a lista é o método estabelecido.

### 8.2. Candidatos guardados (vistos, bons, FORA da exclusão — usar quando couber)
- **2178 Olhydra** (CR18, elemental) — Destruidor de água; guardado de propósito.
- **766 Animal Lord** (CR20, Clarão) — Destruidor beast-lord celestial. CUIDADO: já há 3 Destruidores Espírito/Clarão (Algoz, Sentença, Berro); usar com parcimônia pra não saturar.
- **649 Elder Tempest** (CR23, elemental) — titã-tempestade; tema tempestade já bem usado.
- **958 Graveyard Revenant** (CR7, morto-vivo) — sufoca/paralisa, revive sem magia específica.
- **890 Fire Giant** (CR9, gigante) — ferreiro de guerra; tema forja já usado (Malho-Quente).
- **511 Gauth** (CR6, aberração) — olho/beholder-kin; tema olho já usado (Cacho-de-Olhos).
- **982 Hippopotamus** (CR4, besta) · **2519 Obliteros** (CR5, besta) · **2079 Verbeeg** (CR4, gigante) · **903 Ghast** (CR2, morto-vivo).

### 8.3. ROSTER VIVO — as 198 já canonizadas (para cross-ref, colisão e balanço)
Ordenado por pilar, depois perigo, depois nome. **Regenerado em 2026-06-29 pós-Bloco 4 (198 linhas).** Colunas `tipo_perigo` e `voz` omitidas — recuperáveis via `camada_narrativa` (JSONB) numa query.

| 1ª palavra | nome | pilar | perigo | archetype | andar | continente | id |
|---|---|---|---|---|---|---|---|
| Bocarra | Bocarra-Surda | Corpo | Ameaça | predator | Superfície | Kethara | 928 |
| Casco | Casco-Falso | Corpo | Ameaça | ambusher | Superfície | Kethara | 2304 |
| Cepo | Cepo-Bruto | Corpo | Ameaça | brute | Superfície | Vyrkhor | 220 |
| Dente | Dente-Curvo | Corpo | Ameaça | predator | Superfície | Vyrkhor | 1115 |
| Duas | Duas-Bocas | Corpo | Ameaça | soldier | Superfície | Thornmarak | 885 |
| Espiral | Espiral-Lodosa | Corpo | Ameaça | ambusher | Superfície | Thornmarak | 913 |
| Faca | Faca-Surda | Corpo | Ameaça | predator | Superfície | Vyrkhor | 989 |
| Faixa | Faixa-Peçonha | Corpo | Ameaça | ambusher | Superfície | Thornmarak | 1936 |
| Ferrão | Ferrão-Seco | Corpo | Ameaça | ambusher | Superfície | Kethara | 926 |
| Ilhota | Ilhota-Funda | Corpo | Ameaça | defender | Superfície | Voranthar | 776 |
| Lombada | Lombada-Blindada | Corpo | Ameaça | defender | Superfície | Kethara | 772 |
| Marfim | Marfim-Pesado | Corpo | Ameaça | brute | Superfície | Thornmarak | 881 |
| Ninhada | Ninhada-Sedenta | Corpo | Ameaça | swarm | Superfície | Kethara | 1970 |
| Novelo | Novelo-Peçonho | Corpo | Ameaça | swarm | Superfície | Voranthar | 1169 |
| Nó | Nó-de-Víboras | Corpo | Ameaça | skirmisher | Superfície | Kethara | 386 |
| Passada | Passada-Longa | Corpo | Ameaça | skirmisher | Superfície | Thornmarak | 2078 |
| Pata | Pata-Peçonha | Corpo | Ameaça | skirmisher | Superfície | Kethara | 936 |
| Revoada | Revoada-Negra | Corpo | Ameaça | swarm | Superfície | Voranthar | 1167 |
| Tora | Tora-Quieta | Corpo | Ameaça | ambusher | Superfície | Kethara | 915 |
| Tranca | Tranca-Caminho | Corpo | Ameaça | defender | Superfície | Vyrkhor | 688 |
| Vau | Vau-Manso | Corpo | Ameaça | brute | Superfície | Kethara | 982 |
| Vela | Vela-Rasante | Corpo | Ameaça | skirmisher | Superfície | Thornmarak | 554 |
| Braço | Braço-do-Fundo | Corpo | Letal | ambusher | Superfície | Voranthar | 930 |
| Brota | Brota-Cabeça | Corpo | Letal | brute | Superfície | Vyrkhor | 510 |
| Cerro | Cerro-Caolho | Corpo | Letal | brute | Superfície | Vyrkhor | 101 |
| Costela | Costela-Errante | Corpo | Letal | predator | Eco | Voranthar | 2443 |
| Geada | Geada-Brava | Corpo | Letal | brute | Superfície | Vyrkhor | 898 |
| Goela | Goela-Crua | Corpo | Letal | predator | Superfície | Vyrkhor | 1183 |
| Lâmina | Lâmina-Teimosa | Corpo | Letal | skirmisher | Eco | Vyrkhor | 718 |
| Pedrada | Pedrada-Surda | Corpo | Letal | brute | Superfície | Thornmarak | 907 |
| Peçonha | Peçonha-Viva | Corpo | Letal | brute | Superfície | Thornmarak | 728 |
| Podridão | Podridão-Lenta | Corpo | Letal | brute | Superfície | Thornmarak | 698 |
| Regelo | Regelo-Faminto | Corpo | Letal | predator | Superfície | Vyrkhor | 2045 |
| Torreão | Torreão-Quieto | Corpo | Letal | defender | Superfície | Kethara | 851 |
| Tronco | Tronco-Sarnento | Corpo | Letal | brute | Superfície | Thornmarak | 629 |
| Borrasca | Borrasca-Velha | Corpo | Destruidor | brute | Superfície | Vyrkhor | 567 |
| Carcaça | Carcaça-Viva | Corpo | Destruidor | brute | Margem | Voranthar | 2245 |
| Monte | Monte-Antigo | Corpo | Destruidor | brute | Superfície | Kethara | 736 |
| Trovão | Trovão-Andante | Corpo | Destruidor | brute | Superfície | Vyrkhor | 1157 |
| Afogado | Afogado-Salgado | Sombra | Ameaça | ambusher | Eco | Thornmarak | 1934 |
| Borrão | Borrão-Lento | Sombra | Ameaça | controller | Eco | Vyrkhor | 1130 |
| Dedos | Dedos-Soltos | Sombra | Ameaça | swarm | Eco | Voranthar | 1160 |
| Friagem | Friagem-Vã | Sombra | Ameaça | striker | Eco | Voranthar | 1218 |
| Hóspede | Hóspede-Pálido | Sombra | Ameaça | lurker | Eco | Voranthar | 905 |
| Laje | Laje-Viva | Sombra | Ameaça | ambusher | Superfície | Voranthar | 2399 |
| Lívido | Lívido-Sôfrego | Sombra | Ameaça | predator | Eco | Vyrkhor | 1190 |
| Montaria | Montaria-Ossuda | Sombra | Ameaça | skirmisher | Eco | Voranthar | 1199 |
| Mão | Mão-Invisível | Sombra | Ameaça | lurker | Eco | Voranthar | 1089 |
| Míngua | Míngua-Fria | Sombra | Ameaça | striker | Eco | Vyrkhor | 1212 |
| Névoa | Névoa-Sedenta | Sombra | Ameaça | controller | Eco | Vyrkhor | 727 |
| Pardo | Pardo-Calado | Sombra | Ameaça | lurker | Superfície | Thornmarak | 1173 |
| Quatro | Quatro-Mãos | Sombra | Ameaça | brute | Eco | Kethara | 2400 |
| Quebra | Quebra-Vontade | Sombra | Ameaça | lurker | Margem | Thornmarak | 545 |
| Rancor | Rancor-Teimoso | Sombra | Ameaça | tactical | Eco | Vyrkhor | 1109 |
| Retalho | Retalho-Quieto | Sombra | Ameaça | ambusher | Margem | Thornmarak | 711 |
| Submerso | Submerso-Lesto | Sombra | Ameaça | ambusher | Eco | Thornmarak | 1933 |
| Verme | Verme-Semente | Sombra | Ameaça | swarm | Eco | Kethara | 563 |
| Anel | Anel-Cego | Sombra | Letal | lurker | Margem | Thornmarak | 966 |
| Beijo | Beijo-Roxo | Sombra | Letal | predator | Eco | Thornmarak | 1189 |
| Breu | Breu-Lâmina | Sombra | Letal | lurker | Eco | Vyrkhor | 2632 |
| Carne | Carne-Avessa | Sombra | Letal | brute | Margem | Kethara | 858 |
| Carniça | Carniça-Coveira | Sombra | Letal | controller | Eco | Vyrkhor | 904 |
| Carraça | Carraça-Insone | Sombra | Letal | predator | Eco | Kethara | 1921 |
| Estandarte | Estandarte-Roto | Sombra | Letal | tactical | Eco | Voranthar | 717 |
| Gargalho | Gargalho-Rubro | Sombra | Letal | predator | Eco | Kethara | 2033 |
| Garra | Garra-de-Longe | Sombra | Letal | skirmisher | Eco | Vyrkhor | 615 |
| Manto | Manto-Cego | Sombra | Letal | lurker | Margem | Vyrkhor | 835 |
| Marechal | Marechal-Roto | Sombra | Letal | tactical | Eco | Voranthar | 857 |
| Matilha | Matilha-Surda | Sombra | Letal | predator | Margem | Thornmarak | 1897 |
| Mau | Mau-Olhado | Sombra | Letal | controller | Superfície | Vyrkhor | 896 |
| Olhar | Olhar-Murcho | Sombra | Letal | artillery | Eco | Vyrkhor | 471 |
| Vasa | Vasa-Salgada | Sombra | Letal | controller | Eco | Voranthar | 1935 |
| Véu | Véu-Ávido | Sombra | Letal | controller | Margem | Voranthar | 1903 |
| Capa | Capa-Vasta | Sombra | Destruidor | controller | Margem | Voranthar | 1920 |
| Cruzado | Cruzado-Cinza | Sombra | Destruidor | tactical | Eco | Voranthar | 856 |
| Sede | Sede-Pálida | Sombra | Destruidor | tactical | Eco | Vyrkhor | 1191 |
| Vazio | Vazio-Faminto | Sombra | Destruidor | brute | Eco | Voranthar | 684 |
| Arauto | Arauto-Trêmulo | Arcano | Ameaça | skirmisher | Margem | Vyrkhor | 2207 |
| Beiral | Beiral-Mudo | Arcano | Ameaça | trapper | Superfície | Thornmarak | 900 |
| Cauda | Cauda-Acesa | Arcano | Ameaça | skirmisher | Superfície | Kethara | 1119 |
| Caveira | Caveira-Acesa | Arcano | Ameaça | artillery | Eco | Voranthar | 891 |
| Fel | Fel-Parado | Arcano | Ameaça | trapper | Superfície | Voranthar | 2625 |
| Funda | Funda-Quieta | Arcano | Ameaça | controller | Superfície | Thornmarak | 1203 |
| Fâmulo | Fâmulo-Quedo | Arcano | Ameaça | striker | Eco | Vyrkhor | 622 |
| Inço | Inço-Rubro | Arcano | Ameaça | brute | Margem | Thornmarak | 1106 |
| Lasca | Lasca-Gélida | Arcano | Ameaça | skirmisher | Eco | Vyrkhor | 2069 |
| Lume | Lume-Falso | Arcano | Ameaça | trapper | Eco | Voranthar | 1213 |
| Pacto | Pacto-Murcho | Arcano | Ameaça | striker | Eco | Vyrkhor | 624 |
| Serpe | Serpe-Fornalha | Arcano | Ameaça | trapper | Superfície | Kethara | 1120 |
| Órbita | Órbita-Pálida | Arcano | Ameaça | artillery | Eco | Kethara | 800 |
| Atadura | Atadura-Régia | Arcano | Letal | controller | Eco | Kethara | 1049 |
| Atalho | Atalho-Falso | Arcano | Letal | controller | Margem | Thornmarak | 712 |
| Borralho | Borralho-Quente | Arcano | Letal | artillery | Superfície | Kethara | 783 |
| Broca | Broca-Viva | Arcano | Letal | brute | Margem | Kethara | 546 |
| Coaxo | Coaxo-Cinzento | Arcano | Letal | skirmisher | Margem | Thornmarak | 960 |
| Conluio | Conluio-Calado | Arcano | Letal | tactical | Eco | Thornmarak | 623 |
| Estiagem | Estiagem-Surda | Arcano | Letal | striker | Eco | Kethara | 1792 |
| Inquilino | Inquilino-Manso | Arcano | Letal | lurker | Eco | Kethara | 1839 |
| Lança | Lança-Afogada | Arcano | Letal | soldier | Superfície | Voranthar | 730 |
| Mazela | Mazela-Crua | Arcano | Letal | artillery | Eco | Kethara | 1842 |
| Mácula | Mácula-Crua | Arcano | Letal | brute | Margem | Voranthar | 810 |
| Polpa | Polpa-Cinza | Arcano | Letal | controller | Margem | Voranthar | 2098 |
| Punho | Punho-de-Terra | Arcano | Letal | brute | Superfície | Vyrkhor | 852 |
| Refugo | Refugo-Gélido | Arcano | Letal | brute | Eco | Vyrkhor | 2382 |
| Rã | Rã-Torta | Arcano | Letal | skirmisher | Margem | Voranthar | 963 |
| Sorriso | Sorriso-Vão | Arcano | Letal | ambusher | Superfície | Thornmarak | 486 |
| Tripa | Tripa-Podre | Arcano | Letal | ambusher | Margem | Voranthar | 2128 |
| Vendaval | Vendaval-Vestido | Arcano | Letal | skirmisher | Superfície | Vyrkhor | 602 |
| Voz | Voz-Funda | Arcano | Letal | lurker | Margem | Voranthar | 540 |
| Vulto | Vulto-de-Fora | Arcano | Letal | brute | Margem | Thornmarak | 709 |
| Capuz | Capuz-Velado | Arcano | Destruidor | controller | Eco | Vyrkhor | 2444 |
| Granito | Granito-Quieto | Arcano | Destruidor | trapper | Superfície | Voranthar | 2398 |
| Grimório | Grimório-Morto | Arcano | Destruidor | artillery | Eco | Vyrkhor | 1015 |
| Maré | Maré-Cega | Arcano | Destruidor | controller | Superfície | Voranthar | 2178 |
| Pira | Pira-Viva | Arcano | Destruidor | artillery | Superfície | Kethara | 2170 |
| Sepulcro | Sepulcro-Avaro | Arcano | Destruidor | tactical | Eco | Kethara | 2373 |
| Asa | Asa-Pálida | Espírito | Ameaça | skirmisher | Clarão | Kethara | 916 |
| Augúrio | Augúrio-Frio | Espírito | Ameaça | controller | Clarão | Thornmarak | 1850 |
| Aurora | Aurora-Morta | Espírito | Ameaça | controller | Eco | Vyrkhor | 2024 |
| Brasa | Brasa-Óssea | Espírito | Ameaça | skirmisher | Eco | Vyrkhor | 892 |
| Carpideira | Carpideira-Rachada | Espírito | Ameaça | artillery | Eco | Vyrkhor | 792 |
| Cinza | Cinza-Faminta | Espírito | Ameaça | brute | Eco | Kethara | 2096 |
| Clarim | Clarim-Solene | Espírito | Ameaça | artillery | Clarão | Thornmarak | 1796 |
| Cornamenta | Cornamenta-Severa | Espírito | Ameaça | defender | Superfície | Vyrkhor | 2012 |
| Escama | Escama-Soberana | Espírito | Ameaça | tactical | Superfície | Voranthar | 1019 |
| Fulgor | Fulgor-Alheio | Espírito | Ameaça | defender | Clarão | Thornmarak | 1186 |
| Guarda | Guarda-Cova | Espírito | Ameaça | tactical | Eco | Vyrkhor | 2440 |
| Lampejo | Lampejo-Órfão | Espírito | Ameaça | lurker | Clarão | Kethara | 1241 |
| Murcho | Murcho-Sôfrego | Espírito | Ameaça | striker | Eco | Voranthar | 2449 |
| Murmúrio | Murmúrio-Torto | Espírito | Ameaça | lurker | Eco | Kethara | 604 |
| Pluma | Pluma-Vígil | Espírito | Ameaça | controller | Clarão | Kethara | 843 |
| Profeta | Profeta-Cego | Espírito | Ameaça | tactical | Margem | Vyrkhor | 1010 |
| Sudário | Sudário-Seco | Espírito | Ameaça | striker | Eco | Kethara | 1048 |
| Voto | Voto-Submerso | Espírito | Ameaça | striker | Eco | Vyrkhor | 1932 |
| Arbítrio | Arbítrio-Justo | Espírito | Letal | tactical | Clarão | Voranthar | 862 |
| Bênção | Bênção-Vazia | Espírito | Letal | controller | Clarão | Thornmarak | 1144 |
| Charada | Charada-Velada | Espírito | Letal | controller | Clarão | Voranthar | 1143 |
| Chifre | Chifre-Mudo | Espírito | Letal | striker | Clarão | Thornmarak | 527 |
| Graça | Graça-Amarga | Espírito | Letal | striker | Clarão | Kethara | 971 |
| Jazigo | Jazigo-Cioso | Espírito | Letal | lurker | Eco | Kethara | 958 |
| Juízo | Juízo-Claro | Espírito | Letal | striker | Clarão | Thornmarak | 1877 |
| Litania | Litania-Funda | Espírito | Letal | artillery | Margem | Voranthar | 1008 |
| Mágoa | Mágoa-de-Pedra | Espírito | Letal | trapper | Eco | Voranthar | 975 |
| Presságio | Presságio-Aceso | Espírito | Letal | artillery | Superfície | Kethara | 850 |
| Rajada | Rajada-Cortante | Espírito | Letal | controller | Superfície | Vyrkhor | 2371 |
| Remendo | Remendo-Pálido | Espírito | Letal | brute | Superfície | Vyrkhor | 706 |
| Sonâmbulo | Sonâmbulo-Pétreo | Espírito | Letal | tactical | Superfície | Vyrkhor | 566 |
| Vigia | Vigia-Sacro | Espírito | Letal | defender | Eco | Thornmarak | 647 |
| Algoz | Algoz-Branco | Espírito | Destruidor | tactical | Clarão | Kethara | 1086 |
| Auréola | Auréola-Severa | Espírito | Destruidor | artillery | Clarão | Thornmarak | 1140 |
| Berro | Berro-Seco | Espírito | Destruidor | artillery | Eco | Voranthar | 861 |
| Colosso | Colosso-Sacro | Espírito | Destruidor | brute | Clarão | Vyrkhor | 1240 |
| Enigma | Enigma-Régio | Espírito | Destruidor | tactical | Clarão | Thornmarak | 1145 |
| Sentença | Sentença-Velada | Espírito | Destruidor | striker | Clarão | Thornmarak | 1864 |
| Égide | Égide-Severa | Espírito | Destruidor | defender | Clarão | Thornmarak | 1870 |
| Cacho | Cacho-de-Olhos | Engenho | Ameaça | artillery | Margem | Vyrkhor | 539 |
| Caco | Caco-Lúcido | Engenho | Ameaça | controller | Clarão | Voranthar | 1146 |
| Chão | Chão-Erguido | Engenho | Ameaça | controller | Superfície | Voranthar | 1018 |
| Concha | Concha-Muda | Engenho | Ameaça | defender | Superfície | Thornmarak | 507 |
| Disfarce | Disfarce-Manso | Engenho | Ameaça | lurker | Margem | Voranthar | 2034 |
| Eleito | Eleito-Torto | Engenho | Ameaça | soldier | Margem | Kethara | 2135 |
| Esgar | Esgar-Torto | Engenho | Ameaça | striker | Margem | Kethara | 2109 |
| Espia | Espia-Miúda | Engenho | Ameaça | lurker | Margem | Voranthar | 512 |
| Grilhão | Grilhão-Frio | Engenho | Ameaça | controller | Margem | Voranthar | 543 |
| Gume | Gume-Pensado | Engenho | Ameaça | soldier | Margem | Thornmarak | 940 |
| Malho | Malho-Quente | Engenho | Ameaça | soldier | Superfície | Kethara | 44 |
| Ossada | Ossada-Rolante | Engenho | Ameaça | brute | Eco | Thornmarak | 1977 |
| Praga | Praga-Lúcida | Engenho | Ameaça | swarm | Superfície | Voranthar | 568 |
| Pêndulo | Pêndulo-Cego | Engenho | Ameaça | lurker | Margem | Vyrkhor | 2103 |
| Sino | Sino-Oco | Engenho | Ameaça | skirmisher | Margem | Thornmarak | 894 |
| Sósia | Sósia-Oco | Engenho | Ameaça | skirmisher | Margem | Kethara | 612 |
| Súcia | Súcia-Lúcida | Engenho | Ameaça | swarm | Superfície | Kethara | 489 |
| Talha | Talha-Pedra | Engenho | Ameaça | trapper | Superfície | Thornmarak | 2224 |
| Converso | Converso-Torto | Engenho | Letal | striker | Margem | Voranthar | 2086 |
| Corrente | Corrente-Régia | Engenho | Letal | soldier | Superfície | Thornmarak | 2316 |
| Cupim | Cupim-de-Pedra | Engenho | Letal | lurker | Superfície | Thornmarak | 1220 |
| Cúpula | Cúpula-Morta | Engenho | Letal | artillery | Eco | Kethara | 859 |
| Fio | Fio-Frio | Engenho | Letal | tactical | Margem | Kethara | 943 |
| Fornalha | Fornalha-Andante | Engenho | Letal | brute | Superfície | Kethara | 878 |
| Lacuna | Lacuna-Faminta | Engenho | Letal | tactical | Margem | Thornmarak | 2131 |
| Menir | Menir-Quedo | Engenho | Letal | tactical | Superfície | Vyrkhor | 2351 |
| Mente | Mente-Fria | Engenho | Letal | controller | Margem | Voranthar | 942 |
| Miolo | Miolo-Regente | Engenho | Letal | tactical | Margem | Voranthar | 501 |
| Penhasco | Penhasco-Vivo | Engenho | Letal | trapper | Superfície | Thornmarak | 1155 |
| Pupila | Pupila-Imunda | Engenho | Letal | controller | Margem | Thornmarak | 1958 |
| Sopro | Sopro-Caçador | Engenho | Letal | lurker | Superfície | Vyrkhor | 997 |
| Sorvo | Sorvo-Calado | Engenho | Letal | lurker | Margem | Voranthar | 1833 |
| Suga | Suga-Juízo | Engenho | Letal | controller | Margem | Voranthar | 2117 |
| Tríade | Tríade-Óssea | Engenho | Letal | tactical | Eco | Vyrkhor | 704 |
| Tufão | Tufão-Preso | Engenho | Letal | controller | Superfície | Kethara | 866 |
| Zunido | Zunido-Surdo | Engenho | Letal | controller | Eco | Voranthar | 457 |
| Cérebro | Cérebro-Murcho | Engenho | Destruidor | artillery | Eco | Vyrkhor | 525 |
| Couraça | Couraça-Afogada | Nenhum | Ameaça | brute | Superfície | Kethara+Thornmarak | 833 |
| Cílio | Cílio-Pensante | Nenhum | Ameaça | predator | Superfície | Vyrkhor+Thornmarak | 964 |
| Mortalha | Mortalha-de-Teto | Nenhum | Ameaça | predator | Superfície | Vyrkhor+Thornmarak | 853 |
| Resquício | Resquício-de-Parede | Nenhum | Ameaça | brute | Superfície | Vyrkhor+Voranthar | 1113 |
| Urso | Urso-das-Funduras | Nenhum | Ameaça | predator | Superfície | Vyrkhor | 817 |
| Ventre | Ventre-de-Vala | Nenhum | Ameaça | brute | Superfície | Thornmarak+Kethara | 1068 |

### 8.4. Índice de PRIMEIRAS PALAVRAS já tomadas (não repetir nenhuma)

Afogado, Algoz, Anel, Arauto, Arbítrio, Asa, Atadura, Atalho, Augúrio, Aurora, Auréola, Beijo, Beiral, Berro, Bocarra, Borralho, Borrasca, Borrão, Brasa, Braço, Breu, Broca, Brota, Bênção, Cacho, Caco, Capa, Capuz, Carcaça, Carne, Carniça, Carpideira, Carraça, Casco, Cauda, Caveira, Cepo, Cerro, Charada, Chifre, Chão, Cinza, Clarim, Coaxo, Colosso, Concha, Conluio, Converso, Cornamenta, Corrente, Costela, Couraça, Cruzado, Cupim, Cérebro, Cílio, Cúpula, Dedos, Dente, Disfarce, Duas, Eleito, Enigma, Escama, Esgar, Espia, Espiral, Estandarte, Estiagem, Faca, Faixa, Fel, Ferrão, Fio, Fornalha, Friagem, Fulgor, Funda, Fâmulo, Gargalho, Garra, Geada, Goela, Granito, Graça, Grilhão, Grimório, Guarda, Gume, Hóspede, Ilhota, Inquilino, Inço, Jazigo, Juízo, Lacuna, Laje, Lampejo, Lança, Lasca, Litania, Lombada, Lume, Lâmina, Lívido, Malho, Manto, Marechal, Marfim, Maré, Matilha, Mau, Mazela, Menir, Mente, Miolo, Montaria, Monte, Mortalha, Murcho, Murmúrio, Mácula, Mágoa, Mão, Míngua, Ninhada, Novelo, Névoa, Nó, Olhar, Ossada, Pacto, Pardo, Passada, Pata, Pedrada, Penhasco, Peçonha, Pira, Pluma, Podridão, Polpa, Praga, Presságio, Profeta, Punho, Pupila, Pêndulo, Quatro, Quebra, Rajada, Rancor, Refugo, Regelo, Remendo, Resquício, Retalho, Revoada, Rã, Sede, Sentença, Sepulcro, Serpe, Sino, Sonâmbulo, Sopro, Sorriso, Sorvo, Submerso, Sudário, Suga, Sósia, Súcia, Talha, Tora, Torreão, Tranca, Tripa, Tronco, Trovão, Tríade, Tufão, Urso, Vasa, Vau, Vazio, Vela, Vendaval, Ventre, Verme, Vigia, Voto, Voz, Vulto, Véu, Zunido, Égide, Órbita.

(Confirmar sempre via query §7.2 — o roster pode ter crescido.)

---

## 9. RUNBOOK DO LOTE (passo a passo)

1. **Re-pull** (§7.1) com a exclusão (§8.1). Lê o pool.
2. **Compor os 5.** Garantir os 3 eixos duros distintos (pilar, archetype, tipo_perigo). Otimizar tipos D&D, 4 continentes, faixa de CR. Aplicar Régua-1 ao `perigo`. Escolher temas FRESCOS (não repetir o que já saturou — consultar roster §8.3, em especial o Engenho, que já cobriu tempestade/pedra/forja/ar-invisível/psionismo).
3. **Nomear** os 5 (estilo §5.11) e **conferir colisão** (§7.2) com variantes de acento. Se colidir, renomear.
4. **Puxar stat blocks** (§7.3). Confirmar: archetype/tipo_perigo batem com a mecânica; quem fala vs quem é mudo (`idiomas`); que efeitos existem (não inventar os ausentes).
5. **Definir** por criatura: `origem`/`andar` (§4.5), `continente` (§4.6, espalhar), `morale_immune`/`morale_modifier` (§5.8), o **2º competidor** = criatura canonizada do mesmo continente (§5.9, roster §8.3).
6. **GATE 1 — apresentar ao Gabriel:** tabela (nome, pilar, id, CR, perigo, archetype, tipo_perigo, continente, tipo) + 1 conceito curto witcher-grey por criatura + decisões/ressalvas. **Esperar "bora".** Nada escrito ainda.
7. **Gravar** (após "bora"): preencher o template (§6.1) por criatura e executar **um `UPDATE` por vez** (Caminho A), ou montar os 5 blocos 🟢 pro Gabriel (Caminho B). Cada `[]` = ok. **Cada coluna aparece UMA vez por UPDATE** (ver §10).
8. **GATE 2 — verificar** (§7.4). Conferir 5 linhas, loot=4, presa=2, comp=2, falas=3/null, status=canonizada.
9. **Contagem + trava** (§7.5). Esperar `canonizada` +5, `fichas_com_proibida=0`. Se >0, achar e corrigir (§7.6).
10. **Fechar** com tabela do lote + **resumo fácil obrigatório** (conclusão primeiro, curto). Oferecer próximo lote / pausa / handoff. **Atualizar a exclusão** (§8.1) somando os 5 ids gravados + rejeitados vistos.

**Próximo passo concreto:** rodar o **Lote 19**. Após gravar, esperar `canonizada = 98`, `classificada = 401`, trava `0`.

---

## 10. PEGADINHAS VIVAS (erros já cometidos — não repetir)

- **"multiple assignments to same column":** cada coluna aparece **uma única vez** por `UPDATE`. (No Lote 16 `sinais_presenca` foi colado 2×; o comando abortou inteiro e **não gravou**.) Revisar o bloco antes de rodar.
- **`jsonb_array_length` estoura em JSON `null`:** para contar falas dos mudos, usar SEMPRE o `CASE WHEN jsonb_typeof(...)='array' THEN ... ELSE NULL END` (já embutido na query §7.4).
- **Rodar a trava TODO lote:** ela pega fichas **antigas** também. No Lote 16 ela pegou "alma" na Ventre-de-Vala (id 1068, fora do lote) — corrigido com `replace()`. Pode haver outras latentes; a query §7.5 cobre tudo.
- **Apóstrofo dentro de `$DESC$`:** evitar (escrever "da água", não "d'água").
- **`uso` no loot:** nunca a palavra "Espírito" — usar pilar ou andar.
- **DRAGÕES têm trilha separada:** se um dracolich/dragão cair no pool (ex.: 11 Adult Blue Dracolich), **não canonizar aqui** — existe o conjunto `FICHAS_36_DRAGOES` para isso. Pular e deixar o id na exclusão.
- **`[]` é sucesso:** `UPDATE` sem `RETURNING` retorna `[]`. Não re-rodar.
- **Banco vence:** se este doc divergir do banco (contagem, roster, exclusão), re-consultar o banco e seguir o banco.

---

## 11. APÊNDICE — Lotes 14–18 e a teia ecológica

**Marcos de cobertura desta leva:** 1º Destruidor celestial (Sentença-Velada, L16); 1º Destruidor besta-colossal (Monte-Antigo, L18); **1ª criatura psiônica** (Grilhão-Frio, L18 — psionismo = Engenho). Engenho já cobriu: tempestade (Tufão), pedra (Talha), forja (Malho), ar-invisível (Sopro), psionismo (Grilhão), olho (Cacho), cópia/sósia (Sósia), mente (Mente/Suga). Streak de "5 tipos D&D distintos" rodou nos Lotes 16–17; **quebrado de propósito no L18** (2 aberração) por dois temas melhores (tartaruga-mundo + psiônico).

**Cross-refs cravados (2º competidor de cada criatura, Lotes 14–18):**
Garra×Sede-Pálida · Carcaça×Granito-Quieto · Sorriso×Bênção-Vazia · Tufão×Cauda-Acesa · Fulgor×Chifre-Mudo · Vazio×Carcaça-Viva · Goela×Regelo-Faminto · Atalho×Sorriso-Vão · Murmúrio×Cinza-Faminta · Talha×Cupim-de-Pedra · Sentença×Fulgor-Alheio · Marechal×Vazio-Faminto · Tranca×Goela-Crua · Broca×Tufão-Preso · Malho×Cauda-Acesa · Pluma×Cinza-Faminta · Míngua×Geada-Brava · Peçonha×Sorriso-Vão · Rã×Marechal-Roto · Sopro×Borrasca-Velha · Monte×Broca-Viva · Clarim×Fulgor-Alheio · Breu×Míngua-Fria · Tripa×Rã-Torta · Grilhão×Marechal-Roto.

— fim do handoff —
