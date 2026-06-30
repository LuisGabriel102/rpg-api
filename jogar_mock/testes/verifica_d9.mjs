import { chromium } from "playwright-core";
import { pathToFileURL } from "url";
const EXE = process.env.PW_CHROMIUM || "/opt/pw-browsers/chromium-1194/chrome-linux/chrome";
const URL=pathToFileURL(process.cwd()+"/jogar_definitiva_fatia5.html").href;
const b=await chromium.launch({executablePath:EXE,args:["--no-sandbox"]});
const c=await b.newContext({viewport:{width:1280,height:900},reducedMotion:"reduce"});
const p=await c.newPage();
const errs=[]; p.on("pageerror",e=>errs.push(String(e)));
await p.goto(URL,{waitUntil:"networkidle"}); await p.waitForTimeout(150);
const PAYLOAD = '<img src=x onerror="window.__XSS_FIRED=true"><b>negrito</b> & "aspas" \'simples\' <script>window.__XSS2=1<\/script>';
await p.click(".campo input");
await p.fill(".campo input", PAYLOAD);
await p.keyboard.press("Enter");
await p.waitForSelector(".acao-jogador", { timeout: 4000 });
await p.waitForTimeout(200);
const r = await p.evaluate(() => {
  const linha = document.querySelector(".acao-jogador");
  return {
    xssFired: window.__XSS_FIRED === true,
    xss2: window.__XSS2 === 1,
    temImg: !!linha.querySelector("img"),
    temB: !!linha.querySelector("b"),
    temScript: !!linha.querySelector("script"),
    textoLiteral: linha.innerText.indexOf("<img") !== -1 && linha.innerText.indexOf("<b>") !== -1
  };
});
const R=[];
R.push(["onerror NÃO disparou (img não virou elemento)", !r.xssFired]);
R.push(["script inline NÃO executou", !r.xss2]);
R.push(["nenhum <img> injetado no DOM", !r.temImg]);
R.push(["nenhum <b> injetado no DOM", !r.temB]);
R.push(["nenhum <script> injetado no DOM", !r.temScript]);
R.push(["o texto aparece LITERAL (<img, <b> como texto)", r.textoLiteral]);
R.push(["sem pageerror", errs.length===0]);
let ok=0; for(const[n,v]of R){ console.log(`  ${v?"\u2713":"\u2717"} ${n}`); if(v)ok++; }
console.log(`\n========== #9 XSS: ${ok}/${R.length} ==========`);
await b.close();
