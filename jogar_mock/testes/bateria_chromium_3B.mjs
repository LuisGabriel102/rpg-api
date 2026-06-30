import { chromium } from "playwright-core";
import { pathToFileURL } from "url";

const EXE = process.env.PW_CHROMIUM || "/opt/pw-browsers/chromium-1194/chrome-linux/chrome";
const URL = pathToFileURL(process.cwd() + "/jogar_definitiva_fatia5.html").href;

const R = [];
const add = (g, ok, nome, med = "") => R.push([g, !!ok, nome, String(med)]);
const sleep = ms => new Promise(r => setTimeout(r, ms));

// ───────── helpers (idênticos aos do 3A, seção 12) ─────────
async function freshPage(ctx) {
  const page = await ctx.newPage();
  const jsErrors = [];
  page.on("pageerror", e => jsErrors.push(String(e)));
  page.on("console", m => { if (m.type() === "error") { const t = m.text(); if (!/net::ERR_|Failed to load resource/.test(t)) jsErrors.push("console.error: " + t); } });
  await page.goto(URL, { waitUntil: "networkidle" });
  await page.waitForTimeout(150);
  return { page, jsErrors };
}
async function focusFirstIn(page, sel) {
  await page.evaluate(s => {
    const c = document.querySelector(s); if (!c) return;
    const f = c.querySelector('a[href],button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex="-1"]),[role="button"]:not([aria-disabled="true"])');
    if (f) f.focus();
  }, sel);
}
async function countEscapes(page, sel, n, shift = false) {
  let escapes = 0;
  for (let i = 0; i < n; i++) {
    await page.keyboard.press(shift ? "Shift+Tab" : "Tab");
    const inside = await page.evaluate(s => { const c = document.querySelector(s); return !!(c && c.contains(document.activeElement)); }, sel);
    if (!inside) escapes++;
  }
  return escapes;
}
async function comecarJogo(page) { // 1a ação → jaComecou + combate
  await page.click(".campo input");
  await page.fill(".campo input", "encarar o que vem");
  await page.keyboard.press("Enter");
  await page.waitForFunction(() => document.body.classList.contains("em-combate"), null, { timeout: 4000 });
}

// ───────── G1 · Combate — ciclo de vida (parte Chromium) ─────────
async function G1(ctx) {
  const g = "G1 combate (Chromium)";
  try {
    const { page, jsErrors } = await freshPage(ctx);
    add(g, !(await page.evaluate(() => document.body.classList.contains("em-combate"))), "inicial: sem em-combate", "ok");
    await comecarJogo(page);
    add(g, await page.evaluate(() => document.body.classList.contains("em-combate")), "após ação inicial → em-combate", "em-combate");
    const tens = await page.evaluate(() => getComputedStyle(document.querySelector(".stat.t")).display);
    add(g, tens !== "none", "tensão (.stat.t) visível em combate", `display=${tens}`);
    add(g, jsErrors.length === 0, "sem pageerror de JS", `erros=${jsErrors.length}`);
    await page.close();
  } catch (e) { add(g, false, "EXCEÇÃO no grupo", e.message); }
}

// ───────── G3 · Tensão (parte Chromium) ─────────
async function G3(ctx) {
  const g = "G3 tensão (Chromium)";
  try {
    const { page, jsErrors } = await freshPage(ctx);
    const fora = await page.evaluate(() => getComputedStyle(document.querySelector(".stat.t")).display);
    add(g, fora === "none", "fora de combate: .stat.t display:none", `display=${fora}`);
    await comecarJogo(page);
    const dentro = await page.evaluate(() => getComputedStyle(document.querySelector(".stat.t")).display);
    add(g, dentro !== "none", "em combate: .stat.t visível", `display=${dentro}`);
    add(g, jsErrors.length === 0, "sem pageerror de JS", `erros=${jsErrors.length}`);
    await page.close();
  } catch (e) { add(g, false, "EXCEÇÃO no grupo", e.message); }
}

// ───────── G11 · Caos / spam ─────────
async function G11(ctx) {
  const g = "G11 caos/spam";
  try {
    const { page, jsErrors } = await freshPage(ctx);
    await comecarJogo(page);
    await page.evaluate(() => document.activeElement && document.activeElement.blur());
    // K/F sem card de teste aberto → guarda 'testeAtivo' falha → nada deve acontecer
    for (let i = 0; i < 10; i++) { await page.keyboard.press("k"); await page.keyboard.press("f"); }
    add(g, await page.evaluate(() => document.body.classList.contains("em-combate")), "K/F sem card aberto não muda o estado (segue em combate)", "em-combate");
    // spam de Esc com nada aberto → no-op
    for (let i = 0; i < 10; i++) await page.keyboard.press("Escape");
    add(g, await page.evaluate(() => !document.getElementById("ficha").classList.contains("aberta") && !document.getElementById("gaveta").classList.contains("aberta")), "spam de Esc sem nada aberto → no-op (nada abriu)", "limpo");
    // multi-click no brasão → 1 só #ficha (sem duplicar)
    await page.evaluate(() => { for (let i = 0; i < 6; i++) document.getElementById("abreFicha").click(); });
    await page.waitForTimeout(60);
    add(g, (await page.evaluate(() => document.querySelectorAll("#ficha").length)) === 1, "multi-click no brasão → 1 só #ficha", "ok");
    add(g, await page.evaluate(() => document.getElementById("ficha").classList.contains("aberta")), "ficha aberta e coerente após o spam de cliques", "aberta");
    // fecha 6× e confere que nenhum inert ficou preso nos filhos do body
    await page.evaluate(() => { const f = document.getElementById("fichaFechar"); for (let i = 0; i < 6; i++) f.click(); });
    await page.waitForTimeout(60);
    const OVL = ["ficha", "gaveta", "medulaOverlay", "fichaDetalhe"]; // overlays fechados ficam inert (isolamento 2b)
    const vazou = await page.evaluate((ovl) => Array.prototype.filter.call(document.body.children, c => c.hasAttribute("inert") && ovl.indexOf(c.id) === -1).map(c => c.id || c.className), OVL);
    add(g, vazou.length === 0, "nenhum inert vazado no CONTEÚDO de fundo (overlays fechados = ok)", JSON.stringify(vazou));
    add(g, jsErrors.length === 0, "sem pageerror de JS no caos", `erros=${jsErrors.length}`);
    await page.close();
  } catch (e) { add(g, false, "EXCEÇÃO no grupo", e.message); }
}

// ───────── G13 · Viewport (desktop) ─────────
async function G13(ctx) {
  const g = "G13 viewport (desktop)";
  try {
    const { page, jsErrors } = await freshPage(ctx);
    // sem overflow horizontal em 4 tamanhos desktop (scrollWidth <= clientWidth = definição canônica)
    for (const [w, h] of [[1920, 1080], [1024, 768], [1280, 2000], [1280, 500]]) {
      await page.setViewportSize({ width: w, height: h });
      await page.waitForTimeout(80);
      const ov = await page.evaluate(() => ({ sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth, iw: window.innerWidth }));
      add(g, ov.sw <= ov.cw, `sem overflow horizontal ${w}x${h}`, JSON.stringify(ov));
    }
    // resize COM a ficha aberta → trap segura
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.evaluate(() => document.getElementById("abreFicha").click());
    await page.waitForTimeout(80);
    await page.setViewportSize({ width: 900, height: 700 });
    await page.waitForTimeout(80);
    const eF = await countEscapes(page, "#ficha", 20);
    add(g, eF === 0, "resize com a ficha aberta: Tab preso 20×", `escapes=${eF}`);
    // resize COM o detalhe aberto → trap do detalhe segura
    await page.evaluate(() => { const it = document.querySelector("#ficha .tem-detalhe"); it && it.click(); });
    await page.waitForTimeout(80);
    add(g, await page.evaluate(() => document.getElementById("fichaDetalhe").classList.contains("aberto")), "detalhe abriu (pré-condição do resize)", "aberto");
    await page.setViewportSize({ width: 1100, height: 600 });
    await page.waitForTimeout(80);
    const eD = await countEscapes(page, "#fichaDetalhe", 15);
    add(g, eD === 0, "resize com o detalhe aberto: Tab preso 15×", `escapes=${eD}`);
    add(g, jsErrors.length === 0, "sem pageerror de JS", `erros=${jsErrors.length}`);
    await page.close();
  } catch (e) { add(g, false, "EXCEÇÃO no grupo", e.message); }
}

// ───────── G14 · Performance / vazamentos (parte Chromium) ─────────
async function G14(ctx) {
  const g = "G14 perf/leaks (Chromium)";
  try {
    const { page, jsErrors } = await freshPage(ctx);
    await page.evaluate(() => { const a = document.getElementById("abreFicha"), f = document.getElementById("fichaFechar"); for (let i = 0; i < 50; i++) { a.click(); f.click(); } });
    await page.evaluate(() => document.getElementById("abreFicha").click());
    await page.waitForTimeout(80);
    const e60 = await countEscapes(page, "#ficha", 60);
    add(g, e60 === 0, "após 50 ciclos abre/fecha: Tab preso 60×", `escapes=${e60}`);
    await page.evaluate(() => document.getElementById("fichaFechar").click());
    await page.waitForTimeout(80);
    const limpo = await page.evaluate(() => ({
      suj: Array.prototype.filter.call(document.body.children, c => c.hasAttribute("inert") && ["ficha", "gaveta", "medulaOverlay", "fichaDetalhe"].indexOf(c.id) === -1).length,
      ov: document.body.style.overflow,
      f: document.querySelectorAll("#ficha").length,
      d: document.querySelectorAll("#fichaDetalhe").length
    }));
    add(g, limpo.suj === 0, "cleanup: nenhum inert preso no CONTEÚDO (overlays fechados = ok)", `inert presos=${limpo.suj}`);
    add(g, limpo.ov === "", "body.style.overflow restaurado (vazio)", `overflow="${limpo.ov}"`);
    add(g, limpo.f === 1 && limpo.d === 1, "DOM estável: 1 #ficha e 1 #fichaDetalhe", `ficha=${limpo.f} detalhe=${limpo.d}`);
    add(g, jsErrors.length === 0, "sem pageerror de JS", `erros=${jsErrors.length}`);
    await page.close();
  } catch (e) { add(g, false, "EXCEÇÃO no grupo", e.message); }
}

// ───────── G16 · Sanidade / regressão final ─────────
// Consolida os INVARIANTES que não mudam com o conserto (traps + ordem do Esc).
// A DIREÇÃO do bug de scroll (737→0) fica documentada SÓ no G6 do 3A — ponto único
// de inversão pós-conserto. Aqui o scroll entra como invariante (rolável + troca
// sem erro) + medida reportada.
async function G16(ctx) {
  const g = "G16 sanidade/regressão";
  try {
    const { page, jsErrors } = await freshPage(ctx);
    // (1) trap da ficha — invariante
    await page.evaluate(() => document.getElementById("abreFicha").click());
    await page.waitForTimeout(80);
    const eF = await countEscapes(page, "#ficha", 60);
    add(g, eF === 0, "ficha: Tab preso 60× (trap que funciona)", `escapes=${eF}`);
    // (2) trap do detalhe — invariante (precede a ficha)
    await page.evaluate(() => { const it = document.querySelector("#ficha .tem-detalhe"); it && it.click(); });
    await page.waitForTimeout(80);
    add(g, await page.evaluate(() => document.getElementById("fichaDetalhe").classList.contains("aberto")), "detalhe abriu sobre a ficha", "aberto");
    const eD = await countEscapes(page, "#fichaDetalhe", 20);
    add(g, eD === 0, "detalhe: Tab preso 20× (precede a ficha)", `escapes=${eD}`);
    // (3) Esc na ordem — invariante
    await page.keyboard.press("Escape");
    await page.waitForTimeout(60);
    const ord1 = await page.evaluate(() => ({ det: document.getElementById("fichaDetalhe").classList.contains("aberto"), ficha: document.getElementById("ficha").classList.contains("aberta") }));
    add(g, !ord1.det && ord1.ficha, "Esc fecha o detalhe primeiro (ficha permanece)", `det=${ord1.det} ficha=${ord1.ficha}`);
    await page.keyboard.press("Escape");
    await page.waitForTimeout(60);
    add(g, await page.evaluate(() => !document.getElementById("ficha").classList.contains("aberta")), "2º Esc fecha a ficha", "fechou");
    // (4) scroll de aba — invariante: rolável + troca sem erro. Medida reportada (não asserta direção).
    await page.evaluate(() => document.getElementById("abreFicha").click());
    await page.waitForTimeout(100);
    const rolou = await page.evaluate(() => { const fc = document.querySelector(".ficha-corpo"); fc.scrollTop = 99999; return fc.scrollTop; });
    add(g, rolou > 0, ".ficha-corpo rolável (scroll dentro da aba funciona)", `scrollTop=${rolou}`);
    await page.evaluate(() => document.querySelector('[data-aba="mundo"]').click());
    await page.waitForTimeout(120);
    const aposReal = await page.evaluate(() => document.querySelector(".ficha-corpo").scrollTop);
    add(g, jsErrors.length === 0, "troca de aba sem erro de JS", `erros=${jsErrors.length}`);
    add(g, true, "scroll pós-troca medido (informativo; direção do bug = G6 do 3A)", `scrollTopAposTroca=${aposReal}`);
    await page.close();
  } catch (e) { add(g, false, "EXCEÇÃO no grupo", e.message); }
}

// ───────── runner ─────────
(async () => {
  const browser = await chromium.launch({ executablePath: EXE, args: ["--no-sandbox"] });
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 }, deviceScaleFactor: 2, reducedMotion: "reduce" });

  await G1(ctx); await G3(ctx); await G11(ctx); await G13(ctx); await G14(ctx); await G16(ctx);

  await browser.close();

  const grupos = [...new Set(R.map(r => r[0]))];
  let ok = 0, tot = 0;
  for (const grp of grupos) {
    const rows = R.filter(r => r[0] === grp);
    const gok = rows.filter(r => r[1]).length;
    ok += gok; tot += rows.length;
    console.log(`\n=== ${grp} — ${gok}/${rows.length} ===`);
    for (const [, pass, nome, med] of rows) console.log(`  ${pass ? "\u2713" : "\u2717"} ${nome}${med ? "  \u00b7  " + med : ""}`);
  }
  console.log(`\n========== TOTAL Chromium 3B: ${ok}/${tot} ==========`);
  const fails = R.filter(r => !r[1]);
  if (fails.length) { console.log("\nFALHAS:"); fails.forEach(f => console.log(`  \u2717 [${f[0]}] ${f[2]} \u2014 ${f[3]}`)); }
})();
