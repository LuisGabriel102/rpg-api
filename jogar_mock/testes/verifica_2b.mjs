import { chromium } from "playwright-core";
import { pathToFileURL } from "url";

const EXE = process.env.PW_CHROMIUM || "/opt/pw-browsers/chromium-1194/chrome-linux/chrome";
const URL = pathToFileURL(process.cwd() + "/jogar_definitiva_fatia5.html").href;

const R = [];
const add = (g, ok, nome, med = "") => R.push([g, !!ok, nome, String(med)]);
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function freshPage(ctx) {
  const page = await ctx.newPage();
  const jsErrors = [];
  page.on("pageerror", e => jsErrors.push(String(e)));
  page.on("console", m => { if (m.type() === "error") { const t = m.text(); if (!/net::ERR_|Failed to load resource/.test(t)) jsErrors.push("console.error: " + t); } });
  await page.goto(URL, { waitUntil: "networkidle" });
  await page.waitForTimeout(150);
  return { page, jsErrors };
}
const focoDentro = (page, sel) => page.evaluate(s => { const c = document.querySelector(s); return !!(c && c.contains(document.activeElement) && document.activeElement !== document.body); }, sel);
const temInert = (page, sel) => page.evaluate(s => { const c = document.querySelector(s); return !!c && c.hasAttribute("inert"); }, sel);
const overflow = (page) => page.evaluate(() => document.body.style.overflow);
async function countEscapes(page, sel, n, shift = false) {
  let escapes = 0;
  for (let i = 0; i < n; i++) {
    await page.keyboard.press(shift ? "Shift+Tab" : "Tab");
    const inside = await page.evaluate(s => { const c = document.querySelector(s); return !!(c && c.contains(document.activeElement)); }, sel);
    if (!inside) escapes++;
  }
  return escapes;
}
async function comecarJogo(page) {
  await page.click(".campo input");
  await page.fill(".campo input", "encarar o que vem");
  await page.keyboard.press("Enter");
  await page.waitForFunction(() => document.body.classList.contains("em-combate"), null, { timeout: 4000 });
}
async function subirMedula(page) {
  await page.evaluate(() => document.activeElement && document.activeElement.blur());
  await page.keyboard.press("m"); await sleep(60);
  await page.keyboard.press("m");
  await page.waitForFunction(() => document.getElementById("medulaOverlay").classList.contains("ativo"), null, { timeout: 4000 });
}

// ───────── VAZAMENTO: estado base, Tab não cai nos overlays fechados (era 9 / 1) ─────────
async function base(ctx) {
  const g = "2b base (vazamento fechado)";
  const { page, jsErrors } = await freshPage(ctx);
  await page.evaluate(() => document.activeElement && document.activeElement.blur());
  let dg = 0, dm = 0;
  for (let i = 0; i < 40; i++) {
    await page.keyboard.press("Tab");
    const r = await page.evaluate(() => ({ g: document.getElementById("gaveta").contains(document.activeElement), m: document.getElementById("medulaOverlay").contains(document.activeElement) }));
    if (r.g) dg++; if (r.m) dm++;
  }
  add(g, dg === 0, "Tab 40x NÃO cai na gaveta fechada (era 9)", `dentro=${dg}`);
  add(g, dm === 0, "Tab 40x NÃO cai na medula fechada (era 1)", `dentro=${dm}`);
  add(g, await temInert(page, "#gaveta"), "gaveta fechada está inert", "inert");
  add(g, await temInert(page, "#medulaOverlay"), "medula fechada está inert", "inert");
  add(g, !(await temInert(page, "section.hud")), "conteúdo (hud) NÃO está inert no estado base", "interativo");
  add(g, jsErrors.length === 0, "sem pageerror", `erros=${jsErrors.length}`);
  await page.close();
}

// ───────── GAVETA: foco entra + scroll-lock + isolamento + foco-ao-fechar ─────────
async function gaveta(ctx) {
  const g = "2b gaveta";
  const { page, jsErrors } = await freshPage(ctx);
  const of0 = await overflow(page);
  await page.evaluate(() => document.getElementById("abreGaveta").click());
  await page.waitForTimeout(140);
  add(g, await page.evaluate(() => document.getElementById("gaveta").classList.contains("aberta")), "gaveta abre", "aberta");
  add(g, await focoDentro(page, "#gaveta"), "FOCO ENTRA na gaveta ao abrir (sem foco manual)", "dentro");
  add(g, (await overflow(page)) === "hidden", "scroll-lock: body.overflow=hidden", `overflow=${await overflow(page)}`);
  add(g, await temInert(page, "section.hud"), "fundo isolado: hud está inert", "inert");
  add(g, !(await temInert(page, "#gaveta")), "gaveta NÃO está inert", "interativa");
  const eT = await countEscapes(page, "#gaveta", 12);
  add(g, eT === 0, "Tab preso na gaveta 12x", `escapes=${eT}`);
  await page.keyboard.press("Escape");
  await page.waitForTimeout(140);
  add(g, !(await page.evaluate(() => document.getElementById("gaveta").classList.contains("aberta"))), "Esc fecha a gaveta", "fechada");
  add(g, (await overflow(page)) === of0, "scroll restaurado ao fechar", `overflow="${await overflow(page)}"`);
  add(g, !(await temInert(page, "section.hud")), "fundo desisolado ao fechar", "interativo");
  add(g, await page.evaluate(() => document.activeElement === document.getElementById("abreGaveta")), "FOCO volta ao gatilho (abreGaveta) ao fechar", "no gatilho");
  add(g, jsErrors.length === 0, "sem pageerror", `erros=${jsErrors.length}`);
  await page.close();
}

// ───────── MEDULA sozinha: foco entra + scroll-lock + isolamento + Esc não dispensa ─────────
async function medula(ctx) {
  const g = "2b medula (sozinha)";
  const { page, jsErrors } = await freshPage(ctx);
  await comecarJogo(page);
  await subirMedula(page);
  const m = "#medulaOverlay";
  add(g, await focoDentro(page, m), "FOCO ENTRA na medula ao subir (sem foco manual)", "dentro");
  add(g, (await overflow(page)) === "hidden", "scroll-lock: body.overflow=hidden", `overflow=${await overflow(page)}`);
  add(g, await temInert(page, "section.hud"), "fundo isolado: hud está inert", "inert");
  add(g, !(await temInert(page, m)), "medula NÃO está inert", "interativa");
  const eT = await countEscapes(page, m, 12);
  add(g, eT === 0, "Tab preso na medula 12x", `escapes=${eT}`);
  await page.keyboard.press("Escape");
  await page.waitForTimeout(80);
  add(g, await page.evaluate(s => document.querySelector(s).classList.contains("ativo"), m), "Esc NÃO dispensa a morte", "segue ativa");
  add(g, jsErrors.length === 0, "sem pageerror", `erros=${jsErrors.length}`);
  await page.close();
}

// ───────── A PEGADINHA: medula SOBRE a ficha ─────────
async function pegadinha(ctx) {
  const g = "2b PEGADINHA (medula sobre ficha)";
  const { page, jsErrors } = await freshPage(ctx);
  await comecarJogo(page);
  await page.evaluate(() => document.getElementById("abreFicha").click());
  await page.waitForFunction(() => document.getElementById("ficha").classList.contains("aberta"), null, { timeout: 4000 });
  add(g, true, "ficha aberta durante o jogo", "ok");
  // medula sobe POR CIMA da ficha
  await subirMedula(page);
  add(g, await page.evaluate(() => document.getElementById("ficha").classList.contains("aberta")), "ficha permanece aberta atrás", "aberta");
  add(g, await page.evaluate(() => document.getElementById("medulaOverlay").classList.contains("ativo")), "medula ativa por cima", "ativa");
  add(g, !(await temInert(page, "#medulaOverlay")), "medula NÃO ficou inert (pegadinha resolvida)", "interativa");
  add(g, await temInert(page, "#ficha"), "ficha (atrás) está inert", "inert");
  add(g, await focoDentro(page, "#medulaOverlay"), "FOCO ENTRA na medula (não na ficha)", "na medula");
  const eMed = await countEscapes(page, "#medulaOverlay", 12);
  add(g, eMed === 0, "Tab preso na medula 12x (não vaza pra ficha)", `escapes=${eMed}`);
  add(g, jsErrors.length === 0, "sem pageerror", `erros=${jsErrors.length}`);
  await page.close();
}

// ───────── FICHA sozinha: foco entra + foco-ao-fechar (não-regressão do brasão) ─────────
async function fichaFechar(ctx) {
  const g = "2b ficha (foco-ao-fechar)";
  const { page, jsErrors } = await freshPage(ctx);
  const of0 = await overflow(page);
  await page.evaluate(() => document.getElementById("abreFicha").click());
  await page.waitForFunction(() => document.getElementById("ficha").classList.contains("aberta"), null, { timeout: 4000 });
  add(g, await focoDentro(page, "#ficha"), "FOCO ENTRA na ficha ao abrir", "dentro");
  add(g, (await overflow(page)) === "hidden", "scroll-lock ativo", `overflow=${await overflow(page)}`);
  add(g, await temInert(page, "section.hud"), "fundo isolado (hud inert)", "inert");
  await page.evaluate(() => document.getElementById("fichaFechar").click());
  await page.waitForTimeout(140);
  add(g, !(await page.evaluate(() => document.getElementById("ficha").classList.contains("aberta"))), "ficha fecha", "fechada");
  add(g, await page.evaluate(() => document.activeElement === document.getElementById("abreFicha")), "FOCO volta ao brasão (abreFicha) ao fechar", "no brasão");
  add(g, (await overflow(page)) === of0, "scroll restaurado", `overflow="${await overflow(page)}"`);
  add(g, !(await temInert(page, "section.hud")), "fundo desisolado", "interativo");
  add(g, jsErrors.length === 0, "sem pageerror", `erros=${jsErrors.length}`);
  await page.close();
}

(async () => {
  const browser = await chromium.launch({ executablePath: EXE, args: ["--no-sandbox"] });
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 }, deviceScaleFactor: 2, reducedMotion: "reduce" });
  await base(ctx); await gaveta(ctx); await medula(ctx); await pegadinha(ctx); await fichaFechar(ctx);
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
  console.log(`\n========== 2b (isolamento + foco + pegadinha): ${ok}/${tot} ==========`);
  const fails = R.filter(r => !r[1]);
  if (fails.length) { console.log("\nFALHAS:"); fails.forEach(f => console.log(`  \u2717 [${f[0]}] ${f[2]} \u2014 ${f[3]}`)); }
})();
