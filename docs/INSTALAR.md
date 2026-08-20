# Enxerto da Gravura no /jogar — instalação

Conclusão: você substitui **um** arquivo (`jogo.py`) e cria **uma** pasta (`static/`) na raiz do monólito. Nada mais é tocado. O `server.py`, o `auth.py`, o backend — tudo fica como está.

---

## O que tem nesta entrega

- `jogo.py` — a tela `/jogar` com a pele **A Gravura**. Substitui o `jogo.py` atual.
- `static/jogar.js` — a camada cliente compilada (a luz que pousa, o HUD, o input).
- `static/jogar.js.map` — sourcemap (debug; opcional, mas inofensivo).
- `static/estampa_porta.webp` — a estampa da cena (a porta ao cair da noite).
- `client/src/jogar.ts` — a **fonte** TypeScript do `jogar.js`. Só precisa dela se for **mexer** no JS depois. Pra rodar, não precisa.
- `INSTALAR.md` — este arquivo.

---

## Passo a passo

**1. Backup do que existe.** Na raiz do monólito, renomeie o atual:
```
jogo.py  ->  jogo.py.bak
```

**2. Coloque o novo `jogo.py`** na raiz do monólito (no lugar do antigo).

**3. Coloque a pasta `static/`** na **mesma pasta** do `jogo.py` (a raiz). O `jogo.py` procura a estampa e o JS em `./static/` relativo a ele — por isso a pasta tem que ficar ao lado dele.

A estrutura final, na raiz, fica assim:
```
nexus-monolito/
├── jogo.py            <- novo
├── server.py          (intocado)
├── auth.py            (intocado)
├── cronista_prompt.py (intocado)
├── ui_helpers.py      (intocado)
├── static/            <- novo
│   ├── jogar.js
│   ├── jogar.js.map
│   └── estampa_porta.webp
└── ...
```

**4. Mantenha tudo em UTF-8.** O `jogo.py` já vem em UTF-8 com os acentos certos. **Não reabra e reescreva ele pelo PowerShell** sem o método `WriteAllText` com `UTF8Encoding($false)` — senão os acentos corrompem. Se for só copiar o arquivo pro lugar, está seguro.

**5. Suba o servidor** do jeito que você já sobe. Abra `/jogar` (vai pedir o Basic Auth — `/jogar` continua protegido, como antes).

---

## Como testar (sem gastar nada)

O arquivo já vem com `MODO_MOCK = True`. Isso significa: **prosa falsa embutida, custo zero, sem precisar de chave de API.** É pra validar a casca.

O que conferir:
1. A folha abre com o portal **"Vigília Quebrada"** + botão **adentrar**.
2. Clica em **adentrar** → o portal sai, o Cronista (mock) narra a chegada ao povoado.
3. Digita uma ação no campo de baixo → aparece o **eco** (a ação, recuada) e a narração responde.
4. O selo **pressão** (no alto, à direita) mexe a cada turno. Quando chega a **7+**, vira cor de sangue.
5. **recomeçar** (canto esquerdo do campo) → limpa tudo, devolve o portal. Custo zero.

Se tudo isso anda, a casca está sã.

---

## Ligar o Cronista real (Opus 4.8)

Quando quiser trocar a prosa falsa pelo Cronista de verdade:

- Abra o `jogo.py` e troque, lá no alto:
```
MODO_MOCK = True   ->   MODO_MOCK = False
```
- Precisa de `ANTHROPIC_API_KEY` no ambiente (você já tem no `.env`). O cliente só é criado quando o modo real liga — em mock ele nem é tocado.
- O resto do loop é idêntico: o canal duplo (a prosa limpa pro jogador, o bloco `<estado>` invisível), a Pressão 0–10, o prompt caching ligado, e o tratamento de erro que nunca trava a alternância das mensagens.

---

## Depois (baixa prioridade)

A estampa hoje é servida local em `/static/estampa_porta.webp`. Quando ela subir pro R2, é só trocar o `src` da imagem no `jogo.py` (procure por `estampa_porta.webp` no bloco `_BODY`) pela URL do R2:
```
https://imagens.luisgabriel.uk/cenarios/...
```

Recompilar o JS (só se mexer no `.ts`): dentro de `client/`, `npm install` uma vez, depois `npm run build` — ele regenera `static/jogar.js`.
