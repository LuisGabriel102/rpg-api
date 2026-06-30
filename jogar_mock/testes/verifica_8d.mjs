import { JSDOM } from "jsdom";
import { readFileSync } from "fs";
const html = readFileSync("jogar_definitiva_fatia5.html", "utf-8");
const sleep = ms => new Promise(r => setTimeout(r, ms));
const dom = new JSDOM(html, { runScripts:"dangerously", pretendToBeVisual:true, beforeParse(w){
  w.matchMedia = q => ({matches:/reduce/i.test(q), media:q, addListener(){}, removeListener(){}, addEventListener(){}, removeEventListener(){}, onchange:null, dispatchEvent(){return false;}});
  w.HTMLElement.prototype.scrollTo=function(){}; w.Element.prototype.scrollIntoView=function(){}; w.HTMLElement.prototype.scrollIntoView=function(){};
}});
await new Promise(res => dom.window.addEventListener("load", () => setTimeout(res, 80)));
const doc = dom.window.document;
let pass=0, fail=0;
const ok=(n,c,e="")=>{(c?pass++:fail++);console.log((c?"  PASS ":"  FAIL ")+n+(e?"  -> "+e:""));};

(doc.querySelector("#abreFicha")||doc.querySelector("#abreFichaTopo")).click();
await sleep(60);
doc.querySelector('[data-aba="jornada"]').click();
await sleep(60);
const painel = doc.querySelector('[data-painel="jornada"]');

const jorLista = painel.querySelector(".jor-lista");
const ledLista = painel.querySelector(".led-lista");
ok("jor-lista recebeu tipo=marco", jorLista && jorLista.getAttribute("data-detalhe-grupo")==="marco");
ok("led-lista recebeu tipo=decisao", ledLista && ledLista.getAttribute("data-detalhe-grupo")==="decisao");

const marcos = Array.from(painel.querySelectorAll(".jor-marco"));
const mRevel = marcos.filter(x=>!x.classList.contains("velado"));
const mVel = marcos.filter(x=>x.classList.contains("velado"));
ok("6 marcos (HTML intacto)", marcos.length===6, "n="+marcos.length);
ok("marcos revelados viraram tem-detalhe", mRevel.length===4 && mRevel.every(x=>x.classList.contains("tem-detalhe")), "revelados="+mRevel.length);
ok("marcos velados NAO clicaveis", mVel.length===2 && mVel.every(x=>!x.classList.contains("tem-detalhe")), "velados="+mVel.length);
ok("cada marco preservou jor-nome", marcos.every(x=>x.querySelector(".jor-nome")));

const leds = Array.from(painel.querySelectorAll(".led-item"));
ok("led-item virou tem-detalhe", leds.length===1 && leds[0].classList.contains("tem-detalhe"));
ok("ledger preservou led-escolha", leds.every(x=>x.querySelector(".led-escolha")));

const det = doc.querySelector(".ficha-detalhe");
mRevel[0].click(); await sleep(120);
ok("drill-down ABRE num marco revelado", det && det.classList.contains("aberto"));
let v=doc.querySelector("#fdVoltar"); if(v) v.click(); await sleep(70);
mVel[0].click(); await sleep(90);
ok("clicar num marco velado NAO abre", !det.classList.contains("aberto"));
leds[0].click(); await sleep(120);
ok("drill-down ABRE numa decisao do ledger", det && det.classList.contains("aberto"));

console.log("\n  8d -> PASS="+pass+" FAIL="+fail);
process.exit(fail?1:0);
