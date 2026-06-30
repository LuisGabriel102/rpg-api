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
doc.querySelector('[data-aba="mundo"]').click();
await sleep(60);

const painel = doc.querySelector('[data-painel="mundo"]');
const itens = Array.from(painel.querySelectorAll(".f-item"));
ok("6 itens no inventario", itens.length===6, "n="+itens.length);
const ul = painel.querySelector(".f-inv");
ok("ul.f-inv recebeu data-detalhe-grupo=item", ul && ul.getAttribute("data-detalhe-grupo")==="item");
ok("todos .f-item viraram tem-detalhe+role+tabindex", itens.every(x=>x.classList.contains("tem-detalhe")&&x.getAttribute("role")==="button"&&x.getAttribute("tabindex")==="0"));
ok("cada item tem icone svg", itens.every(x=>x.querySelector(".f-i-ico svg")));
ok("cada item preservou .f-i-nome", itens.every(x=>x.querySelector(".f-i-nome")));
const racao = itens.find(x=>/Ração/.test(x.textContent));
ok("racao tem badge de quantidade (.f-i-qtd)", !!racao && !!racao.querySelector(".f-i-qtd"));
const pingente = itens.find(x=>/Pingente/.test(x.textContent));
ok("pingente (heranca) tem classe heranca", !!pingente && pingente.classList.contains("heranca"));

const det = doc.querySelector(".ficha-detalhe");
itens[0].click(); await sleep(120);
ok("drill-down ABRE ao clicar num item", det && det.classList.contains("aberto"));
const voltar = doc.querySelector("#fdVoltar") || (det && det.querySelector("button"));
if(voltar) voltar.click(); await sleep(80);
itens[5].click(); await sleep(120);
ok("drill-down reabre noutro item (pingente)", det && det.classList.contains("aberto"));

console.log("\n  8b -> PASS="+pass+" FAIL="+fail);
process.exit(fail?1:0);
