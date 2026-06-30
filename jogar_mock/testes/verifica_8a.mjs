import { JSDOM } from "jsdom";
import { readFileSync } from "fs";
const html = readFileSync("jogar_definitiva_fatia5.html", "utf-8");
const sleep = ms => new Promise(r => setTimeout(r, ms));

const dom = new JSDOM(html, {
  runScripts: "dangerously", pretendToBeVisual: true,
  beforeParse(w){
    w.matchMedia = q => ({matches:/reduce/i.test(q), media:q, addListener(){}, removeListener(){}, addEventListener(){}, removeEventListener(){}, onchange:null, dispatchEvent(){return false;}});
    w.HTMLElement.prototype.scrollTo = function(){};
    w.Element.prototype.scrollIntoView = function(){};
    w.HTMLElement.prototype.scrollIntoView = function(){};
  }
});
await new Promise(res => dom.window.addEventListener("load", () => setTimeout(res, 80)));
const doc = dom.window.document;

let pass = 0, fail = 0;
const ok = (nome, cond, extra="") => { (cond?pass++:fail++); console.log((cond?"  PASS ":"  FAIL ")+nome+(extra?"  -> "+extra:"")); };

// abrir a ficha
const abre = doc.querySelector("#abreFicha") || doc.querySelector("#abreFichaTopo");
ok("botao de abrir ficha existe", !!abre, abre?abre.id:"");
if(abre) abre.click();
await sleep(60);
// trocar pra aba anima
const abaAnima = doc.querySelector('[data-aba="anima"]');
ok("aba anima existe", !!abaAnima);
if(abaAnima) abaAnima.click();
await sleep(60);

const painel = doc.querySelector('[data-painel="anima"]');
const habs = painel ? Array.from(painel.querySelectorAll(".f-hab")) : [];
ok("4 habilidades no painel anima", habs.length === 4, "n="+habs.length);

const ul = painel ? painel.querySelector(".f-anima") : null;
ok("ul.f-anima recebeu data-detalhe-grupo=habilidade (marcaLista)", !!ul && ul.getAttribute("data-detalhe-grupo")==="habilidade", ul?ul.getAttribute("data-detalhe-grupo"):"sem ul");

ok("todos .f-hab viraram tem-detalhe+role+tabindex", habs.length>0 && habs.every(h => h.classList.contains("tem-detalhe") && h.getAttribute("role")==="button" && h.getAttribute("tabindex")==="0"));

ok("cada card tem icone svg", habs.every(h => h.querySelector(".f-h-ico svg")));
ok("cada card tem barra de grau (.f-h-fill com width)", habs.every(h => { const f=h.querySelector(".f-h-fill"); return f && /%/.test(f.style.width); }));
ok("cada card preservou .f-h-nome", habs.every(h => h.querySelector(".f-h-nome")));
ok("cada card preservou data-hab", habs.every(h => h.getAttribute("data-hab")));
ok("cada card preservou data-grau", habs.every(h => h.getAttribute("data-grau") !== null));

const pronta = painel.querySelector(".f-hab.pronta");
ok("tecer-mana (pronta) tem selo", !!pronta && !!pronta.querySelector(".f-h-selo") && pronta.getAttribute("data-hab")==="tecer-mana");

// DRILL-DOWN: clicar numa habilidade deve abrir o detalhe
const det = doc.querySelector(".ficha-detalhe");
ok("painel de detalhe existe", !!det);
const alvo = habs[0];
alvo && alvo.click();
await sleep(120);
ok("drill-down ABRE ao clicar numa habilidade", !!det && det.classList.contains("aberto"), det?("classes: "+det.className):"");

// fechar e clicar noutra
const voltar = doc.querySelector("#fdVoltar") || (det && det.querySelector("button"));
if(voltar) voltar.click(); await sleep(80);
const alvo2 = habs[2];
alvo2 && alvo2.click(); await sleep(120);
ok("drill-down reabre em outra habilidade", !!det && det.classList.contains("aberto"));

console.log("\n  8a -> PASS="+pass+" FAIL="+fail);
process.exit(fail ? 1 : 0);
