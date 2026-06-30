import { JSDOM } from "jsdom";
import { readFileSync } from "fs";
const html = readFileSync("jogar_definitiva_fatia5.html", "utf-8");

const sleep = ms => new Promise(r => setTimeout(r, ms));
async function until(fn, timeout = 1800, step = 15) {
  const t0 = Date.now();
  while (Date.now() - t0 < timeout) { try { if (fn()) return true; } catch (e) {} await sleep(step); }
  return false;
}
async function boot() {
  const errs = [];
  const dom = new JSDOM(html, {
    runScripts: "dangerously", pretendToBeVisual: true,
    beforeParse(w) {
      w.matchMedia = function (q) {
        const reduced = /prefers-reduced-motion\s*:\s*reduce/i.test(q);
        return { matches: reduced, media: q, onchange: null, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {}, dispatchEvent() { return false; } };
      };
      w.HTMLElement.prototype.scrollTo = function () {};
      w.Element.prototype.scrollIntoView = function () {};
      w.HTMLElement.prototype.scrollIntoView = function () {};
      w.addEventListener("error", e => errs.push(String((e.error && e.error.stack) || e.message)));
    }
  });
  await new Promise(res => dom.window.addEventListener("load", () => setTimeout(res, 70)));
  return { dom, win: dom.window, doc: dom.window.document, errs };
}
function send(doc, text) {
  const campo = doc.querySelector(".campo input");
  const btn = doc.querySelector(".enviar");
  campo.value = text;
  btn.click();
}
function press(win, doc, key) {
  const ae = doc.activeElement;
  const campo = doc.querySelector(".campo input");
  if (ae === campo && ae.blur) ae.blur();
  doc.dispatchEvent(new win.KeyboardEvent("keydown", { key, bubbles: true }));
}
const W = el => (el && el.style ? (el.style.width || "(vazio)") : "(sem el)");
const PCT = el => (el && el.style && el.style.width ? parseInt(el.style.width, 10) : NaN);

const R = []; // [grupo, ok, nome, medida]
const add = (grupo, ok, nome, medida = "") => R.push([grupo, !!ok, nome, String(medida)]);

// ───────────────────────── G1 · Combate — ciclo de vida ─────────────────────────
async function G1() {
  const g = "G1 combate";
  try {
    const { doc, errs } = await boot();
    add(g, !doc.body.classList.contains("em-combate"), "antes da ação: sem em-combate", "ok");
    send(doc, "avançar pela estrada");
    const entrou = await until(() => doc.body.classList.contains("em-combate"));
    add(g, entrou, "ação inicial → entra em em-combate", `em-combate=${doc.body.classList.contains("em-combate")}`);
    const ci = doc.getElementById("cardIniciativa");
    const subiu = await until(() => ci && ci.classList.contains("mostra"));
    add(g, subiu, "card de iniciativa subiu (#cardIniciativa.mostra)", `mostra=${ci && ci.classList.contains("mostra")}`);
    add(g, doc.body.classList.contains("em-combate"), "estado coerente: em-combate presente", "presente");
    add(g, errs.length === 0, "sem erro de JS no grupo", `erros=${errs.length}`);
  } catch (e) { add(g, false, "EXCEÇÃO no grupo", e.message); }
}

// ───────────────────────── G2 · Barras (clamps) ─────────────────────────
async function G2() {
  const g = "G2 barras";
  try {
    const { win, doc, errs } = await boot();
    const vidaBar = doc.querySelector(".stat.v .trilho i");
    const vigorBar = doc.querySelector(".stat.g .trilho i");
    const manaBar = doc.querySelector(".stat.m .trilho i");
    const fadigaBar = doc.querySelector(".stat.f .trilho i");
    const medula = doc.getElementById("medulaOverlay");
    const origRandom = win.Math.random;

    send(doc, "encarar o que vem"); // 1a ação → jaComecou + combate
    await until(() => doc.body.classList.contains("em-combate"));
    add(g, PCT(vigorBar) > 0, "vigor inicial > 0", `vigor=${W(vigorBar)}`);
    const manaAntes = W(manaBar);

    // M (1ª): Segundo Fôlego — vigor→0, vida→1, SEM medula
    press(win, doc, "m");
    await sleep(40);
    add(g, PCT(vigorBar) === 0, "vigor trava em 0 (Segundo Fôlego), nunca negativo", `vigor=${W(vigorBar)}`);
    add(g, PCT(vidaBar) > 0, "vida reergue após Segundo Fôlego (não-negativa)", `vida=${W(vidaBar)}`);
    add(g, !medula.classList.contains("ativo"), "1× M não abre a medula (Segundo Fôlego primeiro)", `medula.ativo=${medula.classList.contains("ativo")}`);

    // M (2ª): vigor==0 → entra no Rolo da Medula
    press(win, doc, "m");
    const medulaSubiu = await until(() => medula.classList.contains("ativo"));
    add(g, medulaSubiu, "2× M (vigor=0) → medula sobe", `medula.ativo=${medula.classList.contains("ativo")}`);

    // forçar PASSA (random alto → d10=10, total 22 ≥ 11)
    win.Math.random = () => 0.99;
    doc.getElementById("medulaBtn").click();
    const passou = await until(() => !medula.classList.contains("ativo"));
    win.Math.random = origRandom;
    add(g, passou, "medula resolve (passa), sem limbo", `medula.ativo=${medula.classList.contains("ativo")}`);
    add(g, PCT(fadigaBar) === 100, "clamp MÁX: fadiga vai a 100% ao passar na medula", `fadiga=${W(fadigaBar)}`);
    add(g, PCT(vidaBar) > 0, "vida reergue após a medula (3/28 ≈ 11%)", `vida=${W(vidaBar)}`);
    add(g, W(manaBar) === manaAntes, "MP intacta ao mexer em vida/vigor/fadiga", `mana antes=${manaAntes} depois=${W(manaBar)}`);

    // M (3ª): de volta ao Rolo, agora forçar FALHA (random 0 → d10=1, total 4 < 11)
    press(win, doc, "m");
    const medula2 = await until(() => medula.classList.contains("ativo"));
    win.Math.random = () => 0;
    if (medula2) doc.getElementById("medulaBtn").click();
    const falhou = await until(() => medula.classList.contains("flatline"));
    win.Math.random = origRandom;
    add(g, falhou, "medula resolve (falha → flatline), sem limbo", `flatline=${medula.classList.contains("flatline")}`);
    add(g, PCT(vidaBar) === 0, "clamp MÍN: vida vai a 0 ao falhar (nunca < 0)", `vida=${W(vidaBar)}`);
    add(g, errs.length === 0, "sem erro de JS no grupo", `erros=${errs.length}`);
  } catch (e) { add(g, false, "EXCEÇÃO no grupo", e.message); }
}

// ───────────────────────── G3 · Tensão ─────────────────────────
async function G3() {
  const g = "G3 tensão";
  try {
    const { win, doc, errs } = await boot();
    const pips = doc.querySelectorAll(".stat.t .pips span");
    const onCount = () => Array.prototype.filter.call(pips, p => p.classList.contains("on")).length;
    add(g, pips.length === 5, "cap de pips = 5 (escala 1–10, mock usa 5)", `pips no DOM=${pips.length}`);
    add(g, onCount() === 0, "fora de combate: nenhum pip aceso", `pips on=${onCount()}`);

    send(doc, "encarar o lobo"); // combate
    await until(() => doc.body.classList.contains("em-combate"));
    send(doc, "estocar o peito do lobo"); // ataque em combate → card de teste
    const btnRolar = doc.getElementById("btnRolar");
    const cardPronto = await until(() => btnRolar && btnRolar.disabled === false);
    add(g, cardPronto, "ataque em combate abre o card de teste (rolar liberado)", `btnRolar.disabled=${btnRolar && btnRolar.disabled}`);

    const origRandom = win.Math.random;
    win.Math.random = () => 0; // golpe errado (sem koku que mataria o lobo)
    if (cardPronto) btnRolar.click(); // reduz → resolverGolpe síncrono → subirTensao
    win.Math.random = origRandom;
    add(g, onCount() === 1, "rolar um golpe em combate sobe a tensão", `pips on=${onCount()}`);
    add(g, doc.body.classList.contains("em-combate"), "tensão existe só em combate (em-combate ativo)", "ativo");
    add(g, errs.length === 0, "sem erro de JS no grupo", `erros=${errs.length}`);
  } catch (e) { add(g, false, "EXCEÇÃO no grupo", e.message); }
}

// ───────────────────────── G5 · Narrador / Cronista ─────────────────────────
async function G5() {
  const g = "G5 narrador";
  try {
    // vazio não cria ação
    {
      const { doc } = await boot();
      const n0 = doc.querySelectorAll(".acao-jogador").length;
      send(doc, "");
      send(doc, "   ");
      const n1 = doc.querySelectorAll(".acao-jogador").length;
      add(g, n0 === 0 && n1 === 0, "enviar vazio não cria ação", `antes=${n0} depois=${n1}`);
    }
    // texto cria ação + pensando bloqueia 2º + spam
    {
      const { doc } = await boot();
      send(doc, "olhar ao redor");      // cria 1 ação e liga 'pensando'
      send(doc, "de novo");             // bloqueado por 'pensando'
      send(doc, "e de novo");           // bloqueado
      send(doc, "e mais uma");          // bloqueado
      const n = doc.querySelectorAll(".acao-jogador").length;
      add(g, n === 1, "texto cria ação; 'pensando' bloqueia 2º; spam → no máx 1 nova", `ações=${n}`);
    }
    // < escapado (sem injeção)
    {
      const { doc } = await boot();
      send(doc, "<b>x</b><script>alert(1)</script>");
      const linha = doc.querySelector(".acao-jogador");
      const semTag = linha && !linha.querySelector("b") && !linha.querySelector("script");
      const temLiteral = linha && /<b>/.test(linha.textContent);
      add(g, semTag && temLiteral, "< escapado (sem injeção de tag)", `semTag=${semTag} literal=${temLiteral}`);
    }
    // texto gigante / emoji / acento / bloco enorme não quebra
    {
      const { doc, errs } = await boot();
      const gigante = ("Ânima é tudo. NÃO recuo. 🐺⚔️ ").repeat(140); // ~3900 chars com emoji+acento
      send(doc, gigante);
      const linha = doc.querySelector(".acao-jogador");
      const ok = !!linha && linha.textContent.length > 1000 && errs.length === 0;
      add(g, ok, "texto gigante/emoji/acento não quebra (renderizou)", `len=${linha ? linha.textContent.length : 0} erros=${errs.length}`);
    }
  } catch (e) { add(g, false, "EXCEÇÃO no grupo", e.message); }
}

// ───────────────────────── G7 · Drill-down (31 + velado) ─────────────────────────
async function G7() {
  const g = "G7 drill-down";
  try {
    const { win, doc, errs } = await boot();
    doc.getElementById("abreFicha").click(); // fluxo real: abrir a ficha
    const fd = doc.getElementById("fichaDetalhe");
    const fdCorpo = doc.getElementById("fdCorpo");
    const fdVoltar = doc.getElementById("fdVoltar");

    const itens = Array.prototype.slice.call(doc.querySelectorAll(".tem-detalhe"));
    add(g, itens.length === 31, "31 itens .tem-detalhe presentes", `count=${itens.length}`);

    let abriu = 0, comConteudo = 0, semRegistro = 0, comVelado = 0;
    for (const it of itens) {
      it.click();
      if (fd.classList.contains("aberto")) {
        abriu++;
        const txt = (fdCorpo.textContent || "").trim();
        if (txt.length > 0) comConteudo++;
        if (/Sem registro/i.test(txt)) semRegistro++;
        if (fdCorpo.querySelector(".fd-velado")) comVelado++;
      }
      fdVoltar.click(); // fechar
    }
    add(g, abriu === 31 && comConteudo === 31, "todos os 31 abrem o detalhe com conteúdo", `abriu=${abriu} comConteudo=${comConteudo} semRegistro=${semRegistro}`);
    add(g, comVelado >= 1, "campo velado renderiza .fd-velado (sem revelar)", `detalhes com .fd-velado=${comVelado}`);

    const velados = doc.querySelectorAll(".velado").length;
    const veladosClicaveis = doc.querySelectorAll(".velado.tem-detalhe").length;
    add(g, veladosClicaveis === 0, "itens velados NÃO são clicáveis", `velados=${velados} clicáveis=${veladosClicaveis}`);

    // abrir item → trocar aba por trás → detalhe segue coerente
    itens[0].click();
    const abas = doc.querySelectorAll(".ficha-aba");
    if (abas[1]) abas[1].click(); // trocarAba por trás
    add(g, fd.classList.contains("aberto"), "abrir item → trocar aba por trás → detalhe coerente (aberto)", `aberto=${fd.classList.contains("aberto")}`);
    fdVoltar.click();
    add(g, errs.length === 0, "sem erro de JS no grupo", `erros=${errs.length}`);
  } catch (e) { add(g, false, "EXCEÇÃO no grupo", e.message); }
}

// ───────────────────────── G8 · Gaveta / Crônicas ─────────────────────────
async function G8() {
  const g = "G8 gaveta";
  try {
    const { doc, errs } = await boot();
    const gaveta = doc.getElementById("gaveta");
    doc.getElementById("abreGaveta").click();
    add(g, gaveta.classList.contains("aberta"), "gaveta abre", `aberta=${gaveta.classList.contains("aberta")}`);

    const ativa = doc.querySelector(".cronica.ativa");
    const ativaArquivar = ativa && ativa.querySelector(".cr-arquivar");
    const ativaRenomear = ativa && ativa.querySelector(".cr-renomear");
    add(g, !!ativa && !ativaArquivar && !!ativaRenomear, "crônica ATIVA só tem 'renomear' (sem 'arquivar')", `arquivar=${!!ativaArquivar} renomear=${!!ativaRenomear}`);

    const encerrada = doc.querySelector(".cronica:not(.ativa)");
    const encOk = encerrada && encerrada.querySelector(".cr-renomear") && encerrada.querySelector(".cr-arquivar");
    add(g, !!encOk, "crônica encerrada tem renomear E arquivar (casca)", `tem ambos=${!!encOk}`);

    // trocar de capítulo → fecha a gaveta
    const cap = doc.querySelector(".cap:not(.atual)");
    if (cap) cap.click();
    add(g, !gaveta.classList.contains("aberta"), "trocar de capítulo seleciona e fecha a gaveta", `aberta=${gaveta.classList.contains("aberta")} cap.sel=${cap && cap.classList.contains("sel")}`);
    add(g, errs.length === 0, "sem erro de JS no grupo", `erros=${errs.length}`);
  } catch (e) { add(g, false, "EXCEÇÃO no grupo", e.message); }
}

// ───────────────────────── G12 · Máquina de estados ─────────────────────────
async function G12() {
  const g = "G12 estados";
  try {
    // antes do jogo: M não dispara medula
    {
      const { win, doc } = await boot();
      const medula = doc.getElementById("medulaOverlay");
      press(win, doc, "m"); // jaComecou=false
      await sleep(40);
      add(g, !medula.classList.contains("ativo"), "antes do jogo (jaComecou=false): M não dispara medula", `medula.ativo=${medula.classList.contains("ativo")}`);
    }
    // morte sobre a ficha + morrendo trava re-entrada + resolve
    {
      const { win, doc, errs } = await boot();
      const medula = doc.getElementById("medulaOverlay");
      const ficha = doc.getElementById("ficha");
      const origRandom = win.Math.random;
      doc.getElementById("abreFicha").click(); // ficha aberta
      send(doc, "encarar"); // combate + jaComecou
      await until(() => doc.body.classList.contains("em-combate"));
      press(win, doc, "m");   // Segundo Fôlego
      await sleep(30);
      press(win, doc, "m");   // Rolo da Medula
      const subiu = await until(() => medula.classList.contains("ativo"));
      add(g, subiu && ficha.classList.contains("aberta"), "morte sobe POR CIMA da ficha aberta (sem travar)", `medula=${medula.classList.contains("ativo")} ficha=${ficha.classList.contains("aberta")}`);

      const errBefore = errs.length;
      press(win, doc, "m"); // durante a morte, M não re-entra
      await sleep(30);
      add(g, medula.classList.contains("ativo") && errs.length === errBefore, "durante a morte, M não re-entra (morrendo trava)", `ainda ativo=${medula.classList.contains("ativo")}`);

      win.Math.random = () => 0.99; // resolve (passa)
      doc.getElementById("medulaBtn").click();
      const resolveu = await until(() => !medula.classList.contains("ativo"));
      win.Math.random = origRandom;
      add(g, resolveu, "a morte resolve (passa → sai), não fica em limbo", `medula.ativo=${medula.classList.contains("ativo")}`);
      add(g, errs.length === 0, "sem erro de JS no grupo", `erros=${errs.length}`);
    }
  } catch (e) { add(g, false, "EXCEÇÃO no grupo", e.message); }
}

// ───────────────────────── G14 · Performance / vazamentos ─────────────────────────
async function G14() {
  const g = "G14 perf";
  try {
    const { doc, errs } = await boot();
    const abre = doc.getElementById("abreFicha");
    const fecha = doc.getElementById("fichaFechar");
    const ficha = doc.getElementById("ficha");
    for (let i = 0; i < 50; i++) { abre.click(); fecha.click(); }
    add(g, !ficha.classList.contains("aberta"), "abrir/fechar ficha 50× → estado final limpo (fechada)", `aberta=${ficha.classList.contains("aberta")}`);
    abre.click();
    add(g, ficha.classList.contains("aberta"), "após 50 ciclos, ficha ainda abre (sem travar)", `aberta=${ficha.classList.contains("aberta")}`);
    add(g, doc.querySelectorAll("#ficha").length === 1, "DOM estável: 1 só #ficha (sem duplicação)", `#ficha=${doc.querySelectorAll("#ficha").length}`);
    fecha.click();

    const leitura = doc.querySelector(".leitura");
    const nosAntes = leitura.childElementCount;
    for (let i = 0; i < 5; i++) {
      send(doc, "seguir adiante " + i);
      await until(() => doc.querySelector(".campo .enviar").disabled === false, 1500); // espera 'pensando' soltar
      await sleep(20);
    }
    const nosDepois = leitura.childElementCount;
    add(g, nosDepois > nosAntes, "muitas mensagens → leitura cresce (DOM acumula sem erro)", `de ${nosAntes} p/ ${nosDepois} nós`);
    add(g, errs.length === 0, "sem erro de JS no grupo", `erros=${errs.length}`);
  } catch (e) { add(g, false, "EXCEÇÃO no grupo", e.message); }
}

// ───────────────────────── G15 · Integridade visual + tom ─────────────────────────
async function G15() {
  const g = "G15 tom";
  try {
    // sobre o arquivo
    add(g, html.indexOf("\uFFFD") === -1, "mojibake 0 no arquivo inteiro (U+FFFD)", `count=${(html.match(/\uFFFD/g) || []).length}`);
    add(g, /[áéíóúâêôãõç]/i.test(html), "acentuação viva no arquivo (á é í ó ú ã õ ç)", "presente");

    // sobre a PROSA VISÍVEL (a coluna de leitura do Cronista)
    const { doc } = await boot();
    const leitura = doc.querySelector(".leitura");
    const prosa = (leitura.textContent || "");
    const fantasmas = (prosa.match(/\bfantasma\b/gi) || []).length;
    const almas = (prosa.match(/\balmas?\b/gi) || []).length;
    const espiritos = (prosa.match(/\besp[ií]rito\b/gi) || []).length; // só permitido como pilar (na ficha, não na leitura)
    add(g, fantasmas === 0 && almas === 0 && espiritos === 0, "nenhuma alma/fantasma/espírito como ser na prosa visível", `fantasma=${fantasmas} alma=${almas} espírito=${espiritos}`);
    const demonios = (prosa.match(/\bdem[oô]nio?s?\b/gi) || []).length;
    add(g, demonios === 0, "nenhum demônio na prosa visível", `demônio=${demonios}`);
    const numeros = (prosa.match(/\d/g) || []).length;
    add(g, numeros === 0, "nenhum número na prosa renderizada do Cronista", `dígitos na leitura=${numeros}`);

    // linhagens veladas usam dormente/selado/latente (na ficha)
    const ficha = doc.getElementById("ficha");
    const fichaTxt = ficha ? (ficha.textContent || "") : "";
    const usaVelados = /dormente/i.test(fichaTxt) && /selado/i.test(fichaTxt) && /latente/i.test(fichaTxt);
    add(g, usaVelados, "linhagens veladas usam dormente/selado/latente (não revelam)", `tem os três estados=${usaVelados}`);
  } catch (e) { add(g, false, "EXCEÇÃO no grupo", e.message); }
}

// ───────────────────────── runner ─────────────────────────
(async () => {
  await G1(); await G2(); await G3(); await G5(); await G7(); await G8(); await G12(); await G14(); await G15();

  const grupos = [...new Set(R.map(r => r[0]))];
  let ok = 0, tot = 0;
  for (const grp of grupos) {
    const rows = R.filter(r => r[0] === grp);
    const gok = rows.filter(r => r[1]).length;
    ok += gok; tot += rows.length;
    console.log(`\n=== ${grp} — ${gok}/${rows.length} ===`);
    for (const [, pass, nome, med] of rows) {
      console.log(`  ${pass ? "✓" : "✗"} ${nome}${med ? "  ·  " + med : ""}`);
    }
  }
  console.log(`\n========== TOTAL jsdom: ${ok}/${tot} ==========`);
  const fails = R.filter(r => !r[1]);
  if (fails.length) { console.log("\nFALHAS:"); fails.forEach(f => console.log(`  ✗ [${f[0]}] ${f[2]} — ${f[3]}`)); }
})();
