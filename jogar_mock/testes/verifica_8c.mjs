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
doc.querySelector('[data-aba="codice"]').click();
await sleep(60);
const painel = doc.querySelector('[data-painel="codice"]');

const listas = Array.from(painel.querySelectorAll(".cod-lista"));
ok("4 listas no Codice", listas.length===4, "n="+listas.length);
const tipos = listas.map(l=>l.getAttribute("data-detalhe-grupo"));
ok("cada lista recebeu um tipo (criatura/lugar/lore/pessoa)", tipos.every(t=>["criatura","lugar","lore","pessoa"].includes(t)), tipos.join(","));

const todos = Array.from(painel.querySelectorAll(".cod-item"));
const revelados = todos.filter(x=>!x.classList.contains("velado"));
const velados = todos.filter(x=>x.classList.contains("velado"));
ok("itens totais = 17 (HTML intacto)", todos.length===17, "n="+todos.length);
ok("revelados viraram tem-detalhe", revelados.length>0 && revelados.every(x=>x.classList.contains("tem-detalhe")), "revelados="+revelados.length);
ok("velados NAO sao clicaveis (sem tem-detalhe)", velados.length>0 && velados.every(x=>!x.classList.contains("tem-detalhe")), "velados="+velados.length);
ok("cada item preservou cod-selo + cod-nome", todos.every(x=>x.querySelector(".cod-selo")&&x.querySelector(".cod-nome")));

const det = doc.querySelector(".ficha-detalhe");
revelados[0].click(); await sleep(120);
ok("drill-down ABRE num item revelado", det && det.classList.contains("aberto"));
const voltar = doc.querySelector("#fdVoltar") || (det && det.querySelector("button"));
if(voltar) voltar.click(); await sleep(80);
// clicar num velado NAO deve abrir
const detAntes = det.classList.contains("aberto");
velados[0].click(); await sleep(100);
ok("clicar num VELADO nao abre detalhe", !det.classList.contains("aberto"));

console.log("\n  8c -> PASS="+pass+" FAIL="+fail);
process.exit(fail?1:0);
