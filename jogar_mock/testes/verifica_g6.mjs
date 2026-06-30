import { chromium } from "playwright-core";
import { pathToFileURL } from "url";

const EXE = process.env.PW_CHROMIUM || "/opt/pw-browsers/chromium-1194/chrome-linux/chrome";
const URL = pathToFileURL(process.cwd() + "/jogar_definitiva_fatia5.html").href;

const R = [];
const add = (g, ok, nome, med = "") => R.push([g, !!ok, nome, String(med)]);

async function freshPage(ctx) {
  const page = await ctx.newPage();
  const jsErrors = [];
  page.on("pageerror", e => jsErrors.push(String(e)));
  page.on("console", m => { if (m.type() === "error") { const t = m.text(); if (!/net::ERR_|Failed to load resource/.test(t)) jsErrors.push("console.error: " + t); } });
  await page.goto(URL, { waitUntil: "networkidle" });
  await page.waitForTimeout(150);
  return { page, jsErrors };
}

// Verifica que trocar de aba SEMPRE volta o scroll ao topo (era 737, deve virar 0)
// e que o scroll DENTRO da aba continua funcionando após o conserto.
async function verifica(ctx) {
  const g = "G6 conserto";
  const { page, jsErrors } = await freshPage(ctx);
  await page.evaluate(() => document.getElementById("abreFicha").click());
  await page.waitForTimeout(120);

  // sequência de trocas (default = personagem). Antes de cada troca, rola a aba atual ao fundo.
  const sequencia = ["mundo", "codice", "jornada", "anima", "personagem"];
  for (const aba of sequencia) {
    await page.evaluate(() => { const fc = document.querySelector(".ficha-corpo"); fc.scrollTop = 99999; });
    await page.waitForTimeout(40);
    const antes = await page.evaluate(() => document.querySelector(".ficha-corpo").scrollTop);
    await page.evaluate(a => document.querySelector(`[data-aba="${a}"]`).click(), aba);
    await page.waitForTimeout(120);
    const top = await page.evaluate(() => document.querySelector(".ficha-corpo").scrollTop);
    add(g, top === 0, `troca p/ ${aba}: scroll volta a 0 (rolado a ${antes} antes)`, `scrollTop=${top}`);
  }

  // o scroll dentro de uma aba alta AINDA funciona (o reset não quebrou a rolagem)
  await page.evaluate(() => document.querySelector('[data-aba="codice"]').click());
  await page.waitForTimeout(80);
  const rolavel = await page.evaluate(() => { const fc = document.querySelector(".ficha-corpo"); fc.scrollTop = 99999; return fc.scrollTop; });
  add(g, rolavel > 0, "scroll dentro da aba ainda funciona após o conserto", `scrollTop=${rolavel}`);

  add(g, jsErrors.length === 0, "sem pageerror de JS", `erros=${jsErrors.length}`);
  await page.close();
}

(async () => {
  const browser = await chromium.launch({ executablePath: EXE, args: ["--no-sandbox"] });
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 }, deviceScaleFactor: 2, reducedMotion: "reduce" });
  await verifica(ctx);
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
  console.log(`\n========== conserto G6: ${ok}/${tot} ==========`);
  const fails = R.filter(r => !r[1]);
  if (fails.length) { console.log("\nFALHAS:"); fails.forEach(f => console.log(`  \u2717 [${f[0]}] ${f[2]} \u2014 ${f[3]}`)); }
})();
