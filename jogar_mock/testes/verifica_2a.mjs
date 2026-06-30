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
async function comecarJogo(page) {
  await page.click(".campo input");
  await page.fill(".campo input", "encarar o que vem");
  await page.keyboard.press("Enter");
  await page.waitForFunction(() => document.body.classList.contains("em-combate"), null, { timeout: 4000 });
}
async function abrirMedula(page) {
  await page.evaluate(() => document.activeElement && document.activeElement.blur());
  await page.keyboard.press("m"); await sleep(60);
  await page.keyboard.press("m");
  await page.waitForFunction(() => document.getElementById("medulaOverlay").classList.contains("ativo"), null, { timeout: 4000 });
}

// ───────── GAVETA — trap de Tab (após foco manual; foco-ao-abrir vem na 2b) ─────────
async function gaveta(ctx) {
  const g = "2a gaveta (trap Tab)";
  const { page, jsErrors } = await freshPage(ctx);
  await page.evaluate(() => document.getElementById("abreGaveta").click());
  await page.waitForTimeout(120);
  add(g, await page.evaluate(() => document.getElementById("gaveta").classList.contains("aberta")), "gaveta abre", "aberta");
  await focusFirstIn(page, "#gaveta");
  const eT = await countEscapes(page, "#gaveta", 15);
  add(g, eT === 0, "Tab preso na gaveta 15× (camadaAtiva generalizada)", `escapes=${eT}`);
  await focusFirstIn(page, "#gaveta");
  const eS = await countEscapes(page, "#gaveta", 15, true);
  add(g, eS === 0, "Shift+Tab preso na gaveta 15×", `escapes=${eS}`);
  add(g, jsErrors.length === 0, "sem pageerror de JS", `erros=${jsErrors.length}`);
  await page.close();
}

// ───────── MEDULA sozinha — trap de Tab + Esc não dispensa ─────────
async function medula(ctx) {
  const g = "2a medula (trap Tab)";
  const { page, jsErrors } = await freshPage(ctx);
  await comecarJogo(page);
  await abrirMedula(page);
  const med = "#medulaOverlay";
  add(g, await page.evaluate(s => document.querySelector(s).classList.contains("ativo"), med), "medula sobe (M×2)", "ativo");
  await focusFirstIn(page, med);
  const eT = await countEscapes(page, med, 12);
  add(g, eT === 0, "Tab preso na medula 12× (camadaAtiva generalizada)", `escapes=${eT}`);
  await focusFirstIn(page, med);
  const eS = await countEscapes(page, med, 12, true);
  add(g, eS === 0, "Shift+Tab preso na medula 12×", `escapes=${eS}`);
  await page.keyboard.press("Escape");
  await page.waitForTimeout(60);
  add(g, await page.evaluate(s => document.querySelector(s).classList.contains("ativo"), med), "Esc NÃO dispensa a morte (regra inegociável)", "segue ativa");
  add(g, jsErrors.length === 0, "sem pageerror de JS", `erros=${jsErrors.length}`);
  await page.close();
}

(async () => {
  const browser = await chromium.launch({ executablePath: EXE, args: ["--no-sandbox"] });
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 }, deviceScaleFactor: 2, reducedMotion: "reduce" });
  await gaveta(ctx); await medula(ctx);
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
  console.log(`\n========== 2a (trap gaveta+medula): ${ok}/${tot} ==========`);
  const fails = R.filter(r => !r[1]);
  if (fails.length) { console.log("\nFALHAS:"); fails.forEach(f => console.log(`  \u2717 [${f[0]}] ${f[2]} \u2014 ${f[3]}`)); }
})();
