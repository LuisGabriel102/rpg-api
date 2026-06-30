import { chromium } from "playwright-core";
import { pathToFileURL } from "url";
const EXE = process.env.PW_CHROMIUM || "/opt/pw-browsers/chromium-1194/chrome-linux/chrome";
const URL=pathToFileURL(process.cwd()+"/jogar_definitiva_fatia5.html").href;
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
async function esperarCronista(p){ await p.waitForFunction(()=>!document.querySelector(".cronista-pensando"),null,{timeout:5000}); }
const b=await chromium.launch({executablePath:EXE,args:["--no-sandbox"]});
const c=await b.newContext({viewport:{width:1280,height:900},reducedMotion:"reduce"});
const p=await c.newPage();
const errs=[]; p.on("pageerror",e=>errs.push(String(e)));
await p.goto(URL,{waitUntil:"networkidle"}); await p.waitForTimeout(150);
const fase=(pg)=>pg.evaluate(()=>document.getElementById("luz").getAttribute("data-fase"));
const R=[];
// 1) comecar -> em combate
await p.click(".campo input"); await p.fill(".campo input","encarar o que vem"); await p.keyboard.press("Enter");
await p.waitForFunction(()=>document.body.classList.contains("em-combate"),null,{timeout:4000});
await esperarCronista(p);
// golpe -> card de teste (espera o cronista soltar e o btnRolar habilitar)
await p.fill(".campo input","estocar o peito do lobo"); await p.keyboard.press("Enter");
await esperarCronista(p);
await p.waitForFunction(()=>{const bt=document.getElementById("btnRolar");return bt && !bt.disabled;},null,{timeout:5000});
await p.evaluate(()=>document.activeElement && document.activeElement.blur()); // tira foco do campo p/ o K valer
  await p.keyboard.press("k");          // forca kokusen
await p.click("#btnRolar");            // critico -> dano = vida do lobo -> mata
await p.waitForFunction(()=>!document.body.classList.contains("em-combate"),null,{timeout:5000});
await esperarCronista(p);
R.push(["combate encerrou (kokusen matou o lobo) -> exploracao", true]);
// 2) ancora a luz e confirma
await p.evaluate(()=>document.getElementById("luz").setAttribute("data-fase","dia"));
R.push(["luz ancorada em 'dia' (pre-condicao)", (await fase(p))==="dia"]);
// 3) exploracao pura -> avanca a luz
await p.fill(".campo input","vasculho o chao atras de pegadas"); await p.keyboard.press("Enter");
await esperarCronista(p); await sleep(120);
R.push(["explorar AVANCA a luz (dia -> tarde): #8 nao fica mais estatica", (await fase(p))==="tarde"]);
// 4) controle: a luz NAO avanca em combate
const p2 = await c.newPage();
await p2.goto(URL,{waitUntil:"networkidle"}); await p2.waitForTimeout(120);
await p2.evaluate(()=>document.getElementById("luz").setAttribute("data-fase","dia"));
await p2.click(".campo input"); await p2.fill(".campo input","encarar o que vem"); await p2.keyboard.press("Enter");
await p2.waitForFunction(()=>document.body.classList.contains("em-combate"),null,{timeout:4000});
await esperarCronista(p2);
await p2.fill(".campo input","golpe de traves no flanco"); await p2.keyboard.press("Enter");
await esperarCronista(p2); await sleep(120);
R.push(["a luz NAO avanca em combate (so age no mundo): controle", (await p2.evaluate(()=>document.getElementById("luz").getAttribute("data-fase")))==="dia"]);
await p2.close();
R.push(["sem pageerror", errs.length===0]);
let ok=0; for(const[n,v]of R){ console.log(`  ${v?"\u2713":"\u2717"} ${n}`); if(v)ok++; }
console.log(`\n========== #8 luz progressiva: ${ok}/${R.length} ==========`);
const fails=R.filter(x=>!x[1]); if(fails.length){ console.log("FALHAS:"); fails.forEach(f=>console.log("  - "+f[0])); }
await b.close();
