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
doc.querySelector('[data-aba="personagem"]').click();
await sleep(60);
const painel = doc.querySelector('[data-painel="personagem"]');
const txt = el => (el ? el.textContent.toLowerCase() : "");

/* --- Vocacao & Combate: campos p-campo (8 no total) --- */
const campos = Array.from(painel.querySelectorAll(".p-campo"));
ok("8 p-campo no total (vocacao 4 + combate 4)", campos.length===8, "n="+campos.length);
const grades = Array.from(painel.querySelectorAll(".p-grade"));
ok("2 grades (vocacao e combate)", grades.length===2, "n="+grades.length);
const velados = Array.from(painel.querySelectorAll(".p-campo .v.velado"));
ok("vocacao tem 3 campos velados (vocacao/pilar/caminho)", velados.length===3, "n="+velados.length);
const rotulosCombate = Array.from(painel.querySelectorAll(".p-campo .r")).map(x=>txt(x));
ok("combate preserva defesa/iniciativa/deslocamento/CD", ["defesa","iniciativa","deslocamento"].every(k=>rotulosCombate.some(r=>r.indexOf(k)>=0)));

/* --- Estado vital: 5 barras, e a DISSOLUCAO nunca sai (trava canonica) --- */
const barras = Array.from(painel.querySelectorAll(".p-vitais .p-barra"));
ok("5 barras vitais", barras.length===5, "n="+barras.length);
const rotsVitais = barras.map(b=>txt(b.querySelector(".pb-rot")));
ok("barra Vida presente", rotsVitais.some(r=>r.indexOf("vida")>=0));
ok("barra DISSOLUCAO presente (trava: nunca remover)", rotsVitais.some(r=>r.indexOf("dissolu")>=0), rotsVitais.join(","));
ok("toda barra preservou pb-fill", barras.every(b=>b.querySelector(".pb-fill")));

/* --- Resistencias / Condicoes / Idiomas: tags p-tag --- */
const tags = Array.from(painel.querySelectorAll(".p-tag"));
ok("4 tags no total (resist+vulner+condicao+idioma)", tags.length===4, "n="+tags.length);
ok("tag resistente presente", !!painel.querySelector(".p-tag.resist"));
ok("tag vulneravel presente", !!painel.querySelector(".p-tag.vulner"));
ok("tags NAO sao drill-down", tags.every(x=>!x.classList.contains("tem-detalhe")));
ok("p-campo NAO sao drill-down", campos.every(x=>!x.classList.contains("tem-detalhe")));

/* --- Pressao emocional --- */
const pr = painel.querySelector(".p-pressao");
ok("bloco de pressao emocional presente", !!pr);
ok("pressao preserva o numero (pp-num)", !!(pr && pr.querySelector(".pp-num")));
ok("pressao preserva a barra (pb-fill)", !!(pr && pr.querySelector(".pb-fill")));

console.log("\n  8e-2 -> PASS="+pass+" FAIL="+fail);
process.exit(fail?1:0);
