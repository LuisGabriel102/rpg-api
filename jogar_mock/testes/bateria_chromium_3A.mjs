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
async function comecarJogo(page) { // 1a ação → jaComecou + combate
  await page.click(".campo input");
  await page.fill(".campo input", "encarar o que vem");
  await page.keyboard.press("Enter");
  await page.waitForFunction(() => document.body.classList.contains("em-combate"), null, { timeout: 4000 });
}
async function abrirMedula(page) { // pressupõe jogo começado; M duas vezes (Segundo Fôlego → Rolo)
  await page.evaluate(() => document.activeElement && document.activeElement.blur());
  await page.keyboard.press("m"); await sleep(60);
  await page.keyboard.press("m");
  await page.waitForFunction(() => document.getElementById("medulaOverlay").classList.contains("ativo"), null, { timeout: 4000 });
}

// ───────── G6 · o BUG (scroll da aba não volta ao topo) ─────────
async function G6(ctx) {
  const g = "G6 scroll-aba (BUG)";
  try {
    const { page, jsErrors } = await freshPage(ctx);
    await page.evaluate(() => document.getElementById("abreFicha").click());
    await page.waitForTimeout(120);
    const rolou = await page.evaluate(() => { const fc = document.querySelector(".ficha-corpo"); fc.scrollTop = 99999; return fc.scrollTop; });
    add(g, rolou > 0, ".ficha-corpo é rolável (scroll dentro da aba funciona)", `scrollTopAposRolar=${rolou}`);
    // trocar p/ OUTRA aba alta — anima cabe no viewport (maxScroll=0) e mascararia o bug; mundo tem ~737
    await page.evaluate(() => document.querySelector('[data-aba="mundo"]').click());
    await page.waitForTimeout(180);
    const depois = await page.evaluate(() => document.querySelector(".ficha-corpo").scrollTop);
    add(g, depois === 0, "trocar de aba volta o scroll ao topo (conserto G6)", `scrollTopAposTroca=${depois}`);
    add(g, jsErrors.length === 0, "sem exceção de JS", `erros=${jsErrors.length}`);
    await page.close();
  } catch (e) { add(g, false, "EXCEÇÃO no grupo", e.message); }
}

// ───────── G4 · Morte / medula (trap + pegadinha medula-sobre-ficha) ─────────
async function G4(ctx) {
  const g = "G4 medula";
  try {
    // medula sozinha
    {
      const { page, jsErrors } = await freshPage(ctx);
      await comecarJogo(page);
      await abrirMedula(page);
      const med = "#medulaOverlay";
      add(g, await page.evaluate(s => document.querySelector(s).classList.contains("ativo"), med), "M (×2) faz a medula subir", "ativo");
      const focoDentro = await page.evaluate(s => document.querySelector(s).contains(document.activeElement), med);
      add(g, focoDentro === true, "foco entra na medula ao subir (observer)", `foco dentro=${focoDentro}`);
      await focusFirstIn(page, med);
      const escapes = await countEscapes(page, med, 10);
      add(g, escapes === 0, "Tab preso na medula (trap)", `escapes=${escapes}`);
      await page.keyboard.press("Escape");
      await page.waitForTimeout(60);
      add(g, await page.evaluate(s => document.querySelector(s).classList.contains("ativo"), med), "Esc NÃO dispensa a morte (medula segue ativa)", "ativo");
      add(g, jsErrors.length === 0, "sem exceção de JS", `erros=${jsErrors.length}`);
      await page.close();
    }
    // morte POR CIMA da ficha aberta — a PEGADINHA
    {
      const { page } = await freshPage(ctx);
      await comecarJogo(page);
      await page.evaluate(() => document.getElementById("abreFicha").click());
      await page.waitForTimeout(100);
      await abrirMedula(page);
      const est = await page.evaluate(() => ({ med: document.getElementById("medulaOverlay").classList.contains("ativo"), ficha: document.getElementById("ficha").classList.contains("aberta") }));
      add(g, est.med && est.ficha, "morte POR CIMA da ficha: medula sobe e ficha permanece aberta atrás", `medula=${est.med} ficha=${est.ficha}`);
      const peg = await page.evaluate(() => ({
        focoMedula: document.getElementById("medulaOverlay").contains(document.activeElement),
        medInert: document.getElementById("medulaOverlay").hasAttribute("inert"),
        fichaInert: document.getElementById("ficha").hasAttribute("inert")
      }));
      add(g, peg.focoMedula, "PEGADINHA: foco entra na medula (não na ficha)", "na medula");
      add(g, !peg.medInert, "PEGADINHA: medula não fica inert", "interativa");
      add(g, peg.fichaInert, "PEGADINHA: ficha (atrás) fica inert", "inert");
      const escPeg = await countEscapes(page, "#medulaOverlay", 12);
      add(g, escPeg === 0, "PEGADINHA: Tab preso na medula (não vaza pra ficha)", `escapes=${escPeg}`);
      await page.close();
    }
  } catch (e) { add(g, false, "EXCEÇÃO no grupo", e.message); }
}

// ───────── G8 · Gaveta (trap consertado) ─────────
async function G8(ctx) {
  const g = "G8 gaveta (Chromium)";
  try {
    const { page, jsErrors } = await freshPage(ctx);
    await page.evaluate(() => document.getElementById("abreGaveta").click());
    await page.waitForTimeout(80);
    add(g, await page.evaluate(() => document.getElementById("gaveta").classList.contains("aberta")), "gaveta abre", "aberta");
    add(g, await page.evaluate(() => document.getElementById("gaveta").contains(document.activeElement)), "foco entra na gaveta ao abrir (observer)", "dentro");
    await focusFirstIn(page, "#gaveta");
    const escapes = await countEscapes(page, "#gaveta", 17);
    add(g, escapes === 0, "Tab preso na gaveta (trap)", `escapes=${escapes}`);
    add(g, jsErrors.length === 0, "sem exceção de JS", `erros=${jsErrors.length}`);
    await page.close();
  } catch (e) { add(g, false, "EXCEÇÃO no grupo", e.message); }
}

// ───────── G9 · Camadas empilhadas — precedência ─────────
async function G9(ctx) {
  const g = "G9 camadas";
  try {
    const { page, jsErrors } = await freshPage(ctx);
    await page.evaluate(() => document.getElementById("abreGaveta").click());
    await page.waitForTimeout(60);
    add(g, await page.evaluate(() => document.getElementById("gaveta").classList.contains("aberta")), "gaveta abriu", "ok");
    await page.evaluate(() => document.getElementById("abreFicha").click());
    await page.waitForTimeout(80);
    add(g, await page.evaluate(() => document.getElementById("ficha").classList.contains("aberta")), "ficha abriu", "ok");
    add(g, await page.evaluate(() => !document.getElementById("gaveta").classList.contains("aberta")), "abrir a ficha FECHA a gaveta", "fechou");
    add(g, await page.evaluate(() => !!document.getElementById("abreGaveta").closest("[inert]")), "gatilho da gaveta fica inerte sob a ficha", "inerte");

    // drill-down sobre a ficha
    await page.evaluate(() => { const it = document.querySelector("#ficha .tem-detalhe"); it && it.click(); });
    await page.waitForTimeout(80);
    add(g, await page.evaluate(() => document.getElementById("fichaDetalhe").classList.contains("aberto")), "drill-down abriu sobre a ficha", "aberto");
    await focusFirstIn(page, "#fichaDetalhe");
    const esc = await countEscapes(page, "#fichaDetalhe", 15);
    add(g, esc === 0, "Tab preso no detalhe (precede a ficha) 15×", `escapes=${esc}`);
    await page.keyboard.press("Escape");
    await page.waitForTimeout(60);
    const dep1 = await page.evaluate(() => ({ det: document.getElementById("fichaDetalhe").classList.contains("aberto"), ficha: document.getElementById("ficha").classList.contains("aberta") }));
    add(g, !dep1.det && dep1.ficha, "Esc fecha o detalhe primeiro (ficha permanece)", `det=${dep1.det} ficha=${dep1.ficha}`);
    await page.keyboard.press("Escape");
    await page.waitForTimeout(60);
    add(g, await page.evaluate(() => !document.getElementById("ficha").classList.contains("aberta")), "2º Esc fecha a ficha", "fechou");
    add(g, jsErrors.length === 0, "sem exceção de JS (ignorando webfont offline)", `erros=${jsErrors.length}`);
    await page.close();
  } catch (e) { add(g, false, "EXCEÇÃO no grupo", e.message); }
}

// ───────── G10 · Teclado / a11y na ficha ─────────
async function G10(ctx) {
  const g = "G10 teclado/ficha";
  try {
    const { page, jsErrors } = await freshPage(ctx);
    await page.evaluate(() => document.getElementById("abreFicha").click());
    await page.waitForTimeout(80);
    const esc60 = await countEscapes(page, "#ficha", 60);
    add(g, esc60 === 0, "Tab preso na ficha 60×", `escapes=${esc60}`);
    const escS30 = await countEscapes(page, "#ficha", 30, true);
    add(g, escS30 === 0, "Shift+Tab preso na ficha 30×", `escapes=${escS30}`);
    await page.evaluate(() => document.getElementById("fichaFechar").click());
    await page.waitForTimeout(80);
    add(g, await page.evaluate(() => document.activeElement === document.getElementById("abreFicha")), "ao fechar a ficha, foco volta ao brasão", "ok");
    // Enter abre
    await page.evaluate(() => document.getElementById("abreFicha").focus());
    await page.keyboard.press("Enter");
    await page.waitForTimeout(80);
    add(g, await page.evaluate(() => document.getElementById("ficha").classList.contains("aberta")), "Enter no brasão abre a ficha", "abriu");
    await page.evaluate(() => document.getElementById("fichaFechar").click());
    await page.waitForTimeout(80);
    // Espaço abre
    await page.evaluate(() => document.getElementById("abreFicha").focus());
    await page.keyboard.press("Space");
    await page.waitForTimeout(80);
    add(g, await page.evaluate(() => document.getElementById("ficha").classList.contains("aberta")), "Espaço no brasão abre a ficha", "abriu");
    // anel de foco visível (keyboard → :focus-visible)
    await page.keyboard.press("Tab");
    await page.waitForTimeout(40);
    const foco = await page.evaluate(() => {
      const el = document.activeElement; if (!el) return null;
      const cs = getComputedStyle(el);
      return { tag: el.tagName, outlineStyle: cs.outlineStyle, outlineWidth: cs.outlineWidth, fv: el.matches(":focus-visible") };
    });
    const anel = foco && (foco.outlineStyle !== "none" || foco.fv === true);
    add(g, !!anel, "anel de foco visível ao navegar por teclado", JSON.stringify(foco));
    add(g, jsErrors.length === 0, "sem exceção de JS", `erros=${jsErrors.length}`);
    await page.close();
  } catch (e) { add(g, false, "EXCEÇÃO no grupo", e.message); }
}

// ───────── G7 · Drill-down — trap do detalhe (Chromium) ─────────
async function G7(ctx) {
  const g = "G7 detalhe (Chromium)";
  try {
    const { page, jsErrors } = await freshPage(ctx);
    await page.evaluate(() => document.getElementById("abreFicha").click());
    await page.waitForTimeout(80);
    await page.evaluate(() => { const it = document.querySelector("#ficha .tem-detalhe"); it && it.click(); });
    await page.waitForTimeout(80);
    add(g, await page.evaluate(() => document.getElementById("fichaDetalhe").classList.contains("aberto")), "detalhe abriu", "aberto");
    await focusFirstIn(page, "#fichaDetalhe");
    const e20 = await countEscapes(page, "#fichaDetalhe", 20);
    add(g, e20 === 0, "Tab preso no detalhe 20×", `escapes=${e20}`);
    const eS20 = await countEscapes(page, "#fichaDetalhe", 20, true);
    add(g, eS20 === 0, "Shift+Tab preso no detalhe 20×", `escapes=${eS20}`);
    // corrida abrir/fechar 30×
    await page.evaluate(() => {
      for (let i = 0; i < 30; i++) {
        const it = document.querySelector("#ficha .tem-detalhe"); if (it) it.click();
        const v = document.getElementById("fdVoltar"); if (v) v.click();
      }
    });
    await page.waitForTimeout(80);
    add(g, await page.evaluate(() => !document.getElementById("fichaDetalhe").classList.contains("aberto")), "corrida abrir/fechar 30× sem travar (detalhe fechado ao fim)", "fechado");
    add(g, await page.evaluate(() => document.getElementById("ficha").classList.contains("aberta")), "ficha ainda aberta e responsiva após a corrida", "aberta");
    add(g, jsErrors.length === 0, "sem exceção de JS", `erros=${jsErrors.length}`);
    await page.close();
  } catch (e) { add(g, false, "EXCEÇÃO no grupo", e.message); }
}

// ───────── runner ─────────
(async () => {
  const browser = await chromium.launch({ executablePath: EXE, args: ["--no-sandbox"] });
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 }, deviceScaleFactor: 2, reducedMotion: "reduce" });

  await G6(ctx); await G4(ctx); await G8(ctx); await G9(ctx); await G10(ctx); await G7(ctx);

  await browser.close();

  const grupos = [...new Set(R.map(r => r[0]))];
  let ok = 0, tot = 0;
  for (const grp of grupos) {
    const rows = R.filter(r => r[0] === grp);
    const gok = rows.filter(r => r[1]).length;
    ok += gok; tot += rows.length;
    console.log(`\n=== ${grp} — ${gok}/${rows.length} ===`);
    for (const [, pass, nome, med] of rows) console.log(`  ${pass ? "✓" : "✗"} ${nome}${med ? "  ·  " + med : ""}`);
  }
  console.log(`\n========== TOTAL Chromium 3A: ${ok}/${tot} ==========`);
  const fails = R.filter(r => !r[1]);
  if (fails.length) { console.log("\nFALHAS:"); fails.forEach(f => console.log(`  ✗ [${f[0]}] ${f[2]} — ${f[3]}`)); }
})();
