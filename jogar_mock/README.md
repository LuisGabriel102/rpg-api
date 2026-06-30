# jogar_mock — ficha do /jogar (estilo C)

`jogar_definitiva_fatia5.html` e o MOCK de design da ficha (sandbox: motor falso, simulador
de combate, area de leitura, e a ficha estilo C com 5 abas + drill-down). E a fonte de
verdade do DESIGN da ficha.

A ficha viva em producao foi EXTRAIDA deste mock para `ficha_c.py` (na raiz do repo) e
enxertada no `/jogar-c`. Regra: se mudar a ficha aqui no mock, re-extraia para o `ficha_c.py`.

## Testes (276 asserts no total)

Pasta `testes/`. Cada arquivo e um runner standalone. Rode de dentro de `jogar_mock/`
(os testes leem `jogar_definitiva_fatia5.html` do diretorio corrente).

Sao 15 arquivos: 7 rodam so com Node (jsdom), 8 precisam de um Chromium (Playwright).

### jsdom (so Node, sem browser)
bateria_jsdom, verifica_8a, verifica_8b, verifica_8c, verifica_8d, verifica_8e1, verifica_8e2

### Chromium (Playwright)
bateria_chromium_3A, bateria_chromium_3B, verifica_2a, verifica_2b,
verifica_d8, verifica_d9, verifica_d10, verifica_g6

O caminho do Chromium vem da env `PW_CHROMIUM`. No Windows, aponte para um chrome.exe
de Chromium do Playwright (ou instale com `npx playwright install chromium`).

## Como rodar

    cd jogar_mock
    npm --prefix testes install
    # jsdom (exemplo):
    node testes/verifica_8e2.mjs
    # Chromium (exemplo, Windows PowerShell):
    $env:PW_CHROMIUM="C:\caminho\para\chrome.exe"; node testes/bateria_chromium_3A.mjs

Esperado: cada arquivo imprime `PASS=N FAIL=0`.
