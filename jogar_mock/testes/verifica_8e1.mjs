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

/* --- faixa de identidade (cabecalho sempre visivel) --- */
const faixa = doc.querySelector(".ficha-faixa");
ok("faixa de identidade existe", !!faixa);
const ffNome = doc.querySelector(".ff-nome b");
ok("ff-nome preserva o nome", ffNome && ffNome.textContent.trim()==="Gabriel", ffNome && ffNome.textContent.trim());
const ffSelos = Array.from(doc.querySelectorAll(".ficha-faixa .ff-selo"));
ok("faixa tem 4 selos (1 vocacao + 3 linhagens)", ffSelos.length===4, "n="+ffSelos.length);

/* --- bloco identidade interno --- */
ok("p-ident interno existe", !!painel.querySelector(".p-ident"));
ok("p-nome-g preservado", !!painel.querySelector(".p-nome-g"));
ok("p-veu preservado", !!painel.querySelector(".p-veu"));

/* --- linhagens: drill-down preservado (a trava nº1) --- */
const grpLin = painel.querySelector(".p-linhagens");
ok("p-linhagens recebeu tipo=linhagem", grpLin && grpLin.getAttribute("data-detalhe-grupo")==="linhagem", grpLin && grpLin.getAttribute("data-detalhe-grupo"));
const linh = Array.from(painel.querySelectorAll(".p-linhagem"));
ok("3 linhagens (HTML intacto)", linh.length===3, "n="+linh.length);
ok("cada linhagem virou tem-detalhe", linh.length===3 && linh.every(x=>x.classList.contains("tem-detalhe")));
ok("cada linhagem preservou o <b> do nome", linh.every(x=>x.querySelector("b")));

const det = doc.querySelector(".ficha-detalhe");
linh[0].click(); await sleep(120);
ok("drill-down ABRE numa linhagem", det && det.classList.contains("aberto"));
let v=doc.querySelector("#fdVoltar"); if(v) v.click(); await sleep(70);

/* --- atributos: tiles, toggle .sel preservado, NAO sao drill-down --- */
const atrs = Array.from(painel.querySelectorAll(".f-atr"));
ok("6 atributos (HTML intacto)", atrs.length===6, "n="+atrs.length);
ok("cada atributo preservou data-atr", atrs.every(x=>x.getAttribute("data-atr")));
ok("atributos NAO sao drill-down", atrs.every(x=>!x.classList.contains("tem-detalhe")));
atrs[0].click(); await sleep(60);
ok("clicar num atributo alterna .sel (treinar)", atrs[0].classList.contains("sel"));
ok("clicar num atributo NAO abre o detalhe", !det.classList.contains("aberto"));
atrs[0].click(); await sleep(40);
ok("clicar de novo desliga .sel", !atrs[0].classList.contains("sel"));

console.log("\n  8e-1 -> PASS="+pass+" FAIL="+fail);
process.exit(fail?1:0);
