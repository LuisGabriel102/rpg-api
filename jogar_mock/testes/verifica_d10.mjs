import { chromium } from "playwright-core";
import { pathToFileURL } from "url";
const EXE = process.env.PW_CHROMIUM || "/opt/pw-browsers/chromium-1194/chrome-linux/chrome";
const URL=pathToFileURL(process.cwd()+"/jogar_definitiva_fatia5.html").href;
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const b=await chromium.launch({executablePath:EXE,args:["--no-sandbox"]});
const c=await b.newContext({viewport:{width:1280,height:900},reducedMotion:"reduce"});
const p=await c.newPage();
const errs=[]; p.on("pageerror",e=>errs.push(String(e)));
await p.goto(URL,{waitUntil:"networkidle"}); await p.waitForTimeout(150);
// comecar + acao de golpe (nao-consumada, editavel)
await p.click(".campo input"); await p.fill(".campo input","encarar o que vem"); await p.keyboard.press("Enter");
await p.waitForFunction(()=>document.body.classList.contains("em-combate"),null,{timeout:4000});
await p.fill(".campo input","estocar o peito do lobo"); await p.keyboard.press("Enter");
await p.waitForFunction(()=>{const t=document.querySelector(".acao-jogador");return !!t;},null,{timeout:4000});
await sleep(450); // deixa o "pensando" soltar e a troca registrar
// forca os dois cards visiveis (simula card efemero aberto no instante da edicao)
await p.evaluate(()=>{ document.getElementById("cardIniciativa").classList.add("mostra"); document.getElementById("localCard").classList.add("mostra"); });
const pre = await p.evaluate(()=>({ ini:document.getElementById("cardIniciativa").classList.contains("mostra"), loc:document.getElementById("localCard").classList.contains("mostra"), acoes:document.querySelectorAll(".acao-jogador").length }));
// clica editar na ultima acao
await p.evaluate(()=>{ const bs=document.querySelectorAll(".editar-acao"); if(bs.length) bs[bs.length-1].click(); });
await sleep(120);
const pos = await p.evaluate(()=>({ ini:document.getElementById("cardIniciativa").classList.contains("mostra"), loc:document.getElementById("localCard").classList.contains("mostra"), acoes:document.querySelectorAll(".acao-jogador").length, campo:document.querySelector(".campo input").value }));
const R=[];
R.push(["pre-condicao: ambos os cards visiveis antes de editar", pre.ini && pre.loc]);
R.push(["editar ESCONDE o cardIniciativa (nao fica orfao)", !pos.ini]);
R.push(["editar ESCONDE o localCard (nao fica orfao)", !pos.loc]);
R.push(["a acao editada foi removida da leitura", pos.acoes < pre.acoes]);
R.push(["o texto voltou pro campo (editavel)", pos.campo === "estocar o peito do lobo"]);
R.push(["sem pageerror", errs.length===0]);
let ok=0; for(const[n,v]of R){ console.log(`  ${v?"\u2713":"\u2717"} ${n}`); if(v)ok++; }
console.log(`\n========== #10 cards orfaos: ${ok}/${R.length} ==========`);
await b.close();
