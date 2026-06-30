# -*- coding: utf-8 -*-
"""
ficha_c.py  —  Ficha de personagem estilo C (slide-over) para o /jogar.

Extraida do mock validado (jogar_definitiva_fatia5.html, abas 8a-8e + drill-down)
e fechada aqui como modulo unico. Os 6 testes da ficha (8a..8e2 = 75 asserts)
passam contra ela isolada; 0 pageerror.

A ficha e ADITIVA: nao toca o motor (streaming / dado / atmosfera). Traz a paleta
C inteira ESCOPADA em .ficha (os tokens vivem em `.ficha{...}`, nao em :root), entao
nao ha colisao com o :root do /jogar (--osso, --leitura, --frio, --breu, --ground etc.
ficam isolados dentro da ficha).

COMO INTEGRAR (no /jogar-c, atras de um flag):
  - FICHA_C_CSS  -> CSS CRU (sem <style>). Envelope ao injetar, igual o _CSS:
                    ui.add_head_html(f"<style>{FICHA_C_CSS}</style>")  (depois do _CSS atual)
  - FICHA_C_BODY -> ui.add_body_html(FICHA_C_BODY)  (nivel <body>, FORA do .alderyn-stage,
                    pra o position:fixed do slide-over ser relativo a viewport)
  - FICHA_C_JS   -> ui.run_javascript(FICHA_C_JS)   (depois que o BODY existe)
  - Botao de abrir: AUTO-MONTADO pelo proprio FICHA_C_JS no .head (irmao de
                    #abrir-config), com retry ate o Vue do NiceGUI montar o _BODY no DOM.
                    A INTEGRACAO NAO precisa criar o botao — basta injetar CSS/BODY/JS.
                    Inofensivo onde nao existe .head (ex.: testes usam #abreFichaTopo).
                    O JS tambem liga a abertura a #abrir-ficha / #abreFichaTopo / #abreFicha
                    que ja existam. Obs.: o .head some no modo foco -> a ficha tambem some
                    (consistente com #abrir-config). Pra ficha no foco, um gatilho fixed
                    top-level (estilo #sair-foco) resolveria depois.

HOOKS (Scope A — ligar valores VIVOS; o backend so chama):
  - window.fichaSetPressao(n, rotulo)  n=0..10. Atualiza numero + barra da Pressao.
                                       rotulo opcional; default e placeholder ajustavel.
                                       Ligar onde o /jogar computa pressao_atual (apos
                                       o setPressao do motor, em narrar()).
  - window.fichaSetAtributos(mods)     mods={"FOR":0,"DEX":1,...}. Hoje so os 6 mods
                                       existem no banco (mod_forca..mod_carisma).
                                       Best-effort: so chama se um personagem estiver
                                       carregado; senao a ficha mantem o placeholder.

O resto da ficha (vocacao/nivel/linhagens/vital/divida) e PLACEHOLDER de proposito —
o dado real vem incremental (Andar 2/3). O drill-down ja vem pronto pra trocar
DETALHES[tipo][ref] por um fetch na fiacao quando houver dado.
"""

FICHA_C_CSS = """
.ficha{
    --breu:#0c0a08; --ground:#15110c; --painel:#1d1812; --painel2:#272017;
    --vida:#e8413a; --vida-esc:#6e1d18;
    --vigor:#6fae5a; --vigor-esc:#2f5524;
    --mana:#36a6e0; --mana-esc:#1a4d68;
    --fadiga:#9286a8; --fadiga-esc:#433a52;
    --dissol:#8348a0; --dissol-esc:#3a1f4a;
    --fogo:#f0902c; --ouro:#cba94f; --ouro-viv:#e7c468; --ouro-esc:#6b521f;
    --osso:#d6c6a2; --osso-fraco:#988868; --leitura:#ebdec2;
    --frio:#5a93b8;
    --linha:rgba(203,169,79,.22);
  }
.stat.v .ico{color:var(--vida); filter:drop-shadow(0 0 5px rgba(232,65,58,.5))}
.v .trilho i{background:linear-gradient(90deg,var(--vida-esc),var(--vida));
    box-shadow:0 0 10px rgba(232,65,58,.5); animation:bater 3s ease-in-out infinite}
@keyframes bater{50%{box-shadow:0 0 16px rgba(232,65,58,.8)}}
.cronica.ativa .cronica-cab .cr-nome{color:var(--ouro-viv)}
.cap.atual{color:var(--osso); cursor:default}
.cap.atual .marca{opacity:1}
.ficha{position:fixed; inset:0; z-index:62; opacity:0; pointer-events:none; transition:opacity .3s ease}
.ficha.aberta{opacity:1; pointer-events:auto}
.ficha-fundo{position:absolute; inset:0; background:rgba(8,6,4,.66)}
.ficha-painel{position:absolute; inset:0; display:flex; flex-direction:column;
    background:radial-gradient(125% 80% at 50% 0%, #1a140c 0%, #100c07 55%, #0b0805 100%)}
.ficha-faixa{display:flex; align-items:center; gap:16px; flex:0 0 auto;
    padding:11px 22px; border-bottom:1px solid #2c2419;
    background:linear-gradient(180deg, rgba(39,32,23,.5), rgba(15,11,6,.12))}
.ff-ident{display:flex; align-items:center; gap:12px; min-width:0}
.ff-retrato{width:44px; height:44px; flex:0 0 auto; border-radius:9px; overflow:hidden;
    border:1px solid var(--osso-fraco); color:var(--osso-fraco);
    background:radial-gradient(circle at 50% 34%, #221a12, #0c0805);
    display:flex; align-items:center; justify-content:center; box-shadow:inset 0 0 14px rgba(0,0,0,.55)}
.ff-retrato svg{width:30px; height:30px}
.ff-nome{display:flex; flex-direction:column; min-width:0}
.ff-nome b{font-family:"Fraunces",serif; font-weight:600; font-size:18px;
    letter-spacing:.04em; color:var(--leitura); line-height:1.1}
.ff-nome span{font-family:"IBM Plex Mono",monospace; font-size:10px; letter-spacing:.1em;
    text-transform:uppercase; color:var(--osso-fraco); margin-top:3px;
    overflow:hidden; text-overflow:ellipsis; white-space:nowrap}
.ff-slots{display:flex; align-items:center; gap:24px; margin-left:auto}
.ff-slot{display:flex; align-items:center; gap:10px}
.ff-slot-rot{font-family:"IBM Plex Mono",monospace; font-size:9px; letter-spacing:.18em;
    text-transform:uppercase; color:var(--osso-fraco)}
.ff-selos3{display:flex; gap:5px}
.ff-selo{width:24px; height:24px; flex:0 0 auto; display:flex; align-items:center;
    justify-content:center; font-family:"Fraunces",serif; font-size:13px; color:#4a4640;
    border:1px solid #4a4640; border-radius:6px; background:#100d09}
.ficha-faixa .ficha-fechar{margin-left:6px; flex:0 0 auto}
.ficha-fechar{background:none; border:none; color:var(--osso-fraco); font-size:22px;
    line-height:1; cursor:pointer; padding:2px 8px; border-radius:3px; transition:.2s}
.ficha-fechar:hover{color:var(--vida)}
.ficha-abas{display:flex; gap:1px; flex:0 0 auto; padding:0 12px;
    border-bottom:1px solid var(--ouro-esc); background:rgba(8,6,4,.45);
    overflow-x:auto; overflow-y:hidden; scrollbar-width:none}
.ficha-abas::-webkit-scrollbar{display:none}
.ficha-aba{appearance:none; -webkit-appearance:none; background:none; border:none;
    cursor:pointer; font-family:"IBM Plex Mono",monospace; font-size:11px;
    letter-spacing:.13em; text-transform:uppercase; color:var(--osso-fraco);
    padding:13px 17px 11px; border-bottom:2px solid transparent; white-space:nowrap;
    transition:color .2s ease, border-color .2s ease}
.ficha-aba:hover{color:var(--osso)}
.ficha-aba.ativa{color:var(--ouro-viv); border-bottom-color:var(--ouro)}
.ficha-aba:focus-visible{outline:1px solid var(--ouro-esc); outline-offset:-3px}
.ficha-corpo{flex:1 1 auto; overflow-y:auto; overflow-x:hidden; padding:0}
.ficha-aba-painel{display:none; max-width:780px; margin:0 auto; padding:6px 0 30px}
.ficha-aba-painel.ativa{display:block; animation:abaEntra .26s ease}
@keyframes abaEntra{from{opacity:0; transform:translateY(6px)} to{opacity:1; transform:none}}
@media (max-width:560px){
.ficha-faixa{flex-wrap:wrap; gap:10px 14px; padding:10px 15px}
.ff-nome b{font-size:16px}
.ficha-faixa .ficha-fechar{order:2; margin-left:auto}
.ff-slots{order:3; width:100%; margin-left:0; gap:20px; justify-content:flex-start;
      padding-top:9px; border-top:1px solid rgba(107,82,31,.3)}
.ficha-aba{padding:11px 13px 9px; font-size:10px; letter-spacing:.08em}
.ficha-aba-painel{padding:6px 15px 26px}
}
.p-bloco + .p-bloco{margin-top:24px}
.p-tit{font-family:"IBM Plex Mono",monospace; font-size:9.5px; letter-spacing:.16em;
    text-transform:uppercase; color:var(--osso-fraco); margin:0 0 10px; display:flex;
    align-items:center; gap:10px}
.p-tit::after{content:""; flex:1; height:1px;
    background:linear-gradient(90deg, var(--ouro-esc), transparent)}
.p-tit .f-prov{color:var(--ouro-esc); text-transform:none; letter-spacing:.04em; font-size:9px}
.p-ident{display:flex; align-items:center; gap:18px; padding:16px 18px;
    background:#15110c; border:1px solid #2c2419; border-radius:10px}
.p-retrato-g{width:92px; height:92px; flex:0 0 auto; border-radius:10px; overflow:hidden;
    border:1px solid var(--osso-fraco); color:var(--osso-fraco);
    background:radial-gradient(circle at 50% 34%, #261d14, #0c0805);
    display:flex; align-items:center; justify-content:center; box-shadow:inset 0 0 22px rgba(0,0,0,.6)}
.p-retrato-g svg{width:64px; height:64px}
.p-ident-txt{min-width:0}
.p-nome-g{font-family:"Fraunces",serif; font-weight:600; font-size:30px; letter-spacing:.02em;
    color:var(--leitura); line-height:1.05; margin:0}
.p-origem{font-family:"IBM Plex Mono",monospace; font-size:11px; letter-spacing:.12em;
    text-transform:uppercase; color:var(--osso-fraco); margin-top:7px}
.p-veu{font-family:"Spectral",serif; font-style:italic; font-size:13.5px; color:var(--osso-fraco);
    margin-top:9px; max-width:48ch; line-height:1.45}
.p-grade{display:grid; gap:10px 12px; grid-template-columns:repeat(4,1fr); margin-top:2px}
.p-campo{background:#15110c; border:1px solid #2c2419; border-radius:10px; padding:11px 13px; min-width:0}
.p-campo .r{font-family:"IBM Plex Mono",monospace; font-size:9px; letter-spacing:.16em;
    text-transform:uppercase; color:var(--osso-fraco); display:block}
.p-campo .v{font-family:"Fraunces",serif; font-size:20px; color:var(--osso); margin-top:6px;
    display:block; overflow:hidden; text-overflow:ellipsis; white-space:nowrap}
.p-campo .v.velado{color:#4a4640}
.f-mod{margin-left:7px; font-family:"IBM Plex Mono",monospace; font-size:11px; color:var(--ouro)}
.p-linhagens{display:grid; gap:12px; grid-template-columns:repeat(3,1fr); margin-top:2px}
.p-linhagem{background:#15110c; border:2px solid #2c2419; border-radius:10px; padding:15px 14px;
    text-align:center; transition:transform .15s ease, border-color .15s ease}
.p-linhagem:hover{transform:translateY(-2px); border-color:#3a342b}
.p-selo-g{width:42px; height:42px; margin:0 auto 11px; display:flex; align-items:center;
    justify-content:center; font-family:"Fraunces",serif; font-size:21px; color:#4a4640;
    border:1px dashed #4a4640; border-radius:8px; background:#100d09}
.p-linhagem b{display:block; font-family:"IBM Plex Mono",monospace; font-size:10px;
    letter-spacing:.14em; text-transform:uppercase; color:var(--osso)}
.p-estado{display:inline-block; margin-top:8px; font-family:"IBM Plex Mono",monospace; font-size:9px;
    letter-spacing:.12em; text-transform:uppercase; color:var(--osso-fraco);
    border:1px solid #4a4640; border-radius:999px; padding:2px 10px}
.p-linhagem p{font-family:"Spectral",serif; font-style:italic; font-size:12.5px; color:var(--osso-fraco);
    margin:11px 0 0; line-height:1.4}
.p-linhagem[data-desperto]{border-color:#f0c14a; box-shadow:0 0 22px rgba(240,193,74,.34)}
.p-linhagem[data-desperto] .p-selo-g{border-style:solid; border-color:#f0c14a; color:#f0c14a; box-shadow:0 0 12px rgba(240,193,74,.5)}
.p-linhagem[data-desperto] .p-estado{border-color:#f0c14a; color:#f0c14a}
.p-vitais{display:flex; flex-direction:column; gap:11px; margin-top:2px}
.p-barra{display:grid; grid-template-columns:104px 1fr 58px; align-items:center; gap:12px}
.pb-rot{font-family:"IBM Plex Mono",monospace; font-size:10px; letter-spacing:.1em;
    text-transform:uppercase; color:var(--osso-fraco)}
.pb-trilho{height:13px; border-radius:7px; background:#100d09;
    border:1px solid #2c2419; overflow:hidden; display:block}
.pb-fill{height:100%; border-radius:6px 0 0 6px; display:block; box-shadow:inset 0 1px 0 rgba(255,255,255,.12)}
.pb-num{font-family:"IBM Plex Mono",monospace; font-size:11px; color:var(--osso); text-align:right}
.p-lista{display:flex; flex-wrap:wrap; gap:8px; margin-top:2px}
.p-tag{font-family:"IBM Plex Mono",monospace; font-size:10px; letter-spacing:.06em;
    border:1px solid #2c2419; border-radius:8px; padding:7px 12px; color:var(--osso); background:#15110c}
.p-tag.resist{border-color:#3c5a3a; color:#9fc290; background:#101a10}
.p-tag.vulner{border-color:#6a2f2f; color:#d49a9a; background:#1a0f0f}
.p-tag .sev{color:var(--osso-fraco); margin-left:7px}
.p-vazio{font-family:"Spectral",serif; font-style:italic; font-size:13px; color:var(--osso-fraco); margin:9px 0 0}
.p-pressao{background:linear-gradient(180deg, rgba(58,28,28,.45), rgba(15,11,6,.2)); border:1px solid #6a2f2f;
    border-radius:10px; padding:13px 16px; margin-top:2px}
.pp-topo{display:flex; align-items:baseline; justify-content:space-between; gap:12px}
.pp-est{font-family:"IBM Plex Mono",monospace; font-size:10px; letter-spacing:.14em;
    text-transform:uppercase; color:#d49a9a}
.pp-num{font-family:"Fraunces",serif; font-size:18px; color:var(--leitura)}
.p-pressao .pb-trilho{height:10px; border-radius:6px; margin-top:9px; background:#0c0606; border:1px solid #3a1414}
.p-pressao .pb-fill{background:linear-gradient(90deg,#8a3a3a,#c85a4a); box-shadow:inset 0 1px 0 rgba(255,255,255,.1)}
@media (max-width:560px){
.p-grade{grid-template-columns:repeat(2,1fr)}
.p-linhagens{grid-template-columns:1fr}
.p-ident{gap:14px}
.p-retrato-g{width:78px; height:78px}
.p-retrato-g svg{width:54px; height:54px}
.p-nome-g{font-size:25px}
.p-barra{grid-template-columns:88px 1fr 52px; gap:9px}
}
.a-tom{font-family:"Spectral",serif; font-style:italic; font-size:13px; color:var(--osso-fraco);
    line-height:1.5; margin:0 0 14px; max-width:56ch}
.a-quadro{border:1px solid var(--ouro-esc); border-radius:8px; overflow:hidden;
    background:rgba(20,16,10,.4)}
.a-divida{display:flex; flex-direction:column; gap:10px; margin-top:2px}
.a-cic{display:flex; gap:13px; align-items:flex-start;
    background:linear-gradient(180deg, rgba(34,26,40,.45), rgba(12,9,14,.3));
    border:1px solid #4a3a55; border-left:3px solid #6a4f7a; border-radius:7px; padding:13px 15px}
.a-cic-glifo{flex:0 0 auto; width:26px; height:26px; color:#9a86b0;
    display:flex; align-items:center; justify-content:center}
.a-cic-glifo svg{width:24px; height:24px}
.a-cic-corpo{min-width:0}
.a-cic-corpo b{display:block; font-family:"IBM Plex Mono",monospace; font-size:11px;
    letter-spacing:.1em; text-transform:uppercase; color:#c3b0d4}
.a-cic-corpo p{font-family:"Spectral",serif; font-size:13px; color:var(--osso-fraco);
    margin:6px 0 0; line-height:1.45}
.m-moeda{display:flex; align-items:center; gap:16px; padding:4px 0}
.m-disco{width:52px; height:52px; flex:0 0 auto; border-radius:50%;
    display:flex; align-items:center; justify-content:center;
    font-family:"Fraunces",serif; font-size:18px; color:#3a2c12;
    background:radial-gradient(circle at 38% 32%, #b98a4a, #7a5824 70%, #4e3815);
    border:1px solid #5a431c;
    box-shadow:inset 0 1px 2px rgba(255,220,150,.4), inset 0 -2px 4px rgba(0,0,0,.5), 0 2px 5px rgba(0,0,0,.4)}
.m-corpo{min-width:0}
.m-nome{font-family:"Fraunces",serif; font-size:17px; color:var(--ouro-viv); line-height:1.15}
.m-nome span{font-family:"Spectral",serif; font-style:italic; font-size:12px; color:var(--osso-fraco)}
.m-denom{display:flex; gap:16px; margin-top:7px; flex-wrap:wrap}
.m-d{font-family:"IBM Plex Mono",monospace; font-size:11px; color:var(--osso-fraco)}
.m-d b{color:var(--osso); font-weight:600}
.m-d.zero{opacity:.42}
.l-lacos{display:grid; gap:12px; grid-template-columns:repeat(2,1fr); margin-top:2px}
.l-laco{display:flex; gap:12px; align-items:flex-start; padding:11px 13px;
    border:1px solid var(--ouro-esc); border-radius:7px; background:rgba(20,16,10,.4)}
.l-selo{width:34px; height:34px; flex:0 0 auto; border-radius:50%;
    display:flex; align-items:center; justify-content:center;
    font-family:"Fraunces",serif; font-size:16px; color:var(--osso);
    background:rgba(203,169,79,.1); border:1px solid var(--ouro-esc)}
.l-corpo{min-width:0; flex:1}
.l-top{display:flex; align-items:baseline; gap:8px}
.l-nome{font-family:"Fraunces",serif; font-size:15px; color:var(--leitura); flex:1}
.l-rel{font-family:"IBM Plex Mono",monospace; font-size:9px; letter-spacing:.14em;
    text-transform:uppercase; color:var(--ouro-esc); flex:none}
.l-det{font-family:"Spectral",serif; font-size:12px; color:var(--osso-fraco);
    margin-top:4px; line-height:1.45}
.pc-vazio{display:flex; gap:13px; align-items:center; padding:14px 16px;
    border:1px dashed var(--ouro-esc); border-radius:8px; background:rgba(16,18,22,.35)}
.pc-glifo{width:30px; height:30px; flex:0 0 auto; color:#7d8aa5; opacity:.7}
.pc-glifo svg{width:100%; height:100%; display:block}
.pc-corpo{min-width:0}
.pc-corpo b{display:block; font-family:"IBM Plex Mono",monospace; font-size:11px;
    letter-spacing:.1em; text-transform:uppercase; color:#9aa6bd}
.pc-corpo p{font-family:"Spectral",serif; font-size:12.5px; color:var(--osso-fraco);
    margin:5px 0 0; line-height:1.45}
.cal-era{display:flex; align-items:baseline; gap:10px; flex-wrap:wrap; margin-bottom:12px}
.cal-era .ce-ano{font-family:"Fraunces",serif; font-size:18px; color:var(--leitura)}
.cal-era .ce-mes{font-family:"IBM Plex Mono",monospace; font-size:10px; letter-spacing:.16em;
    text-transform:uppercase; color:var(--ouro-viv)}
.cal-era .ce-nota{font-family:"Spectral",serif; font-style:italic; font-size:11px; color:var(--osso-fraco)}
.cal-meses{display:flex; flex-wrap:wrap; gap:5px; margin-bottom:18px}
.cal-mes{font-family:"IBM Plex Mono",monospace; font-size:9.5px; letter-spacing:.04em;
    padding:4px 8px; border-radius:4px; color:var(--osso-fraco);
    border:1px solid rgba(107,82,31,.3); white-space:nowrap}
.cal-mes.atual{color:var(--breu); background:linear-gradient(180deg,var(--ouro-viv),var(--ouro));
    border-color:var(--ouro-viv); font-weight:600}
.cal-luas{display:grid; grid-template-columns:repeat(2,1fr); gap:14px}
.lua{display:flex; gap:13px; align-items:flex-start; padding:13px;
    border:1px solid var(--ouro-esc); border-radius:8px; background:rgba(20,16,10,.4)}
.lua-disco{width:40px; height:40px; flex:0 0 auto; color:var(--osso)}
.lua-disco svg{width:100%; height:100%; display:block}
.lua-corpo{min-width:0; flex:1}
.lua-nome{font-family:"Fraunces",serif; font-size:15px; color:var(--leitura)}
.lua-est{font-family:"IBM Plex Mono",monospace; font-size:9px; letter-spacing:.14em;
    text-transform:uppercase; color:var(--ouro-esc); margin-top:3px}
.lua-det{font-family:"Spectral",serif; font-size:11.5px; color:var(--osso-fraco);
    margin-top:6px; line-height:1.4}
.lua.silenciada{border-color:#3c4250; background:rgba(16,18,22,.4)}
.lua.silenciada .lua-disco{color:#6a7a9c}
.lua.silenciada .lua-nome{color:#aeb6c6}
.lua.silenciada .lua-est{color:#6a7a9c}
@media (max-width:560px){
.l-lacos{grid-template-columns:1fr}
.cal-luas{grid-template-columns:1fr}
}
.cod-lista{display:grid; grid-template-columns:repeat(2,1fr); gap:11px; padding:14px 16px; align-items:start}
.cod-item{display:flex; gap:11px; align-items:flex-start; padding:12px;
    border:1px solid #2c2419; border-radius:10px; background:#15110c;
    transition:transform .15s ease, border-color .15s ease}
.cod-item:hover{transform:translateY(-2px); border-color:var(--ouro-esc)}
.cod-selo{width:34px; height:34px; flex:0 0 auto; border-radius:9px;
    display:flex; align-items:center; justify-content:center;
    font-family:"Fraunces",serif; font-size:15px; font-weight:600; color:var(--ouro);
    background:radial-gradient(circle at 38% 32%, rgba(120,96,40,.4), rgba(16,13,9,.7));
    border:1px solid var(--ouro-esc)}
.cod-corpo{flex:1 1 auto; min-width:0}
.cod-top{display:flex; flex-direction:column; gap:2px}
.cod-nome{font-family:"Fraunces",serif; font-weight:500; font-size:14px; color:var(--leitura); letter-spacing:.01em}
.cod-tag{font-family:"IBM Plex Mono",monospace; font-size:8px; letter-spacing:.09em;
    text-transform:uppercase; color:var(--osso-fraco)}
.cod-meta{font-family:"IBM Plex Mono",monospace; font-size:8.5px; letter-spacing:.06em;
    text-transform:uppercase; color:var(--ouro-esc); margin-top:5px}
.cod-det{font-family:"Spectral",serif; font-style:italic; font-size:12px;
    line-height:1.45; color:var(--osso-fraco); margin-top:6px}
.cod-item.velado{opacity:.55; border-style:dashed; border-color:rgba(107,82,31,.4)}
.cod-item.velado .cod-selo{color:var(--osso-fraco); background:transparent;
    border:1px dashed rgba(107,82,31,.55)}
.cod-item.velado .cod-nome{font-family:"Spectral",serif; font-style:italic;
    font-size:12.5px; color:var(--osso-fraco); letter-spacing:.02em}
.jor-lista{position:relative; padding:8px 16px 8px 38px}
.jor-lista::before{content:""; position:absolute; left:13px; top:18px; bottom:18px; width:2px;
    background:linear-gradient(180deg, var(--ouro-esc), rgba(107,82,31,.2))}
.jor-marco{position:relative; padding:12px 14px; margin-bottom:11px;
    border:1px solid #2c2419; border-radius:10px; background:#15110c}
.jor-marco:last-child{margin-bottom:0}
.jor-marco::before{content:""; position:absolute; left:-30px; top:16px; width:12px; height:12px; border-radius:50%;
    border:2px solid #15110c}
.jor-marco.menor::before{background:var(--osso-fraco)}
.jor-marco.sig::before{background:var(--osso)}
.jor-marco.maior::before{background:var(--ouro); box-shadow:0 0 10px rgba(240,193,74,.6)}
.jor-marco.unico::before{background:var(--fogo); box-shadow:0 0 14px rgba(255,148,54,.85)}
.jor-marco.velado{border-style:dashed; border-color:rgba(107,82,31,.4); opacity:.55}
.jor-marco.velado::before{background:transparent; border:2px dashed rgba(107,82,31,.6)}
.jor-top{display:flex; align-items:center; justify-content:space-between; gap:10px}
.jor-nome{font-family:"Fraunces",serif; font-weight:500; font-size:14px; color:var(--leitura); letter-spacing:.01em}
.jor-peso{font-family:"IBM Plex Mono",monospace; font-size:8px; letter-spacing:.12em; text-transform:uppercase;
    flex:0 0 auto; padding:2px 7px; border-radius:20px; border:1px solid #3a3226; color:var(--osso-fraco)}
.jor-peso.sig{color:var(--osso); border-color:var(--ouro-esc)}
.jor-peso.maior{color:#1d130a; background:var(--ouro); border-color:var(--ouro)}
.jor-peso.unico{color:#1d130a; background:var(--fogo); border-color:var(--fogo)}
.jor-quando{font-family:"IBM Plex Mono",monospace; font-size:9px; letter-spacing:.06em;
    text-transform:uppercase; color:var(--ouro-esc); margin-top:4px}
.jor-det{font-family:"Spectral",serif; font-style:italic; font-size:12px; line-height:1.45;
    color:var(--osso-fraco); margin-top:6px}
.jor-marco.velado .jor-nome{font-family:"Spectral",serif; font-style:italic; font-size:12.5px; color:var(--osso-fraco)}
.led-item{position:relative; border:1px solid #2c2419; border-left:3px solid var(--ouro);
    border-radius:10px; background:#15110c; padding:14px 16px}
.led-quando{font-family:"IBM Plex Mono",monospace; font-size:8.5px; letter-spacing:.12em;
    text-transform:uppercase; color:var(--ouro-esc); margin-bottom:7px}
.led-escolha{font-family:"Spectral",serif; font-size:13.5px; line-height:1.5; color:var(--leitura)}
.led-conseq{margin-top:11px; padding-top:11px; border-top:1px solid rgba(107,82,31,.3)}
.led-selo{display:inline-block; font-family:"IBM Plex Mono",monospace; font-size:8px;
    letter-spacing:.14em; text-transform:uppercase; color:#1d130a; background:var(--fogo);
    padding:2px 7px; border-radius:20px; margin-bottom:6px}
.led-conseq-txt{font-family:"Spectral",serif; font-style:italic; font-size:12px; line-height:1.45; color:var(--osso)}
.f-item.tem-detalhe:hover .f-i-nome, .l-laco.tem-detalhe:hover .l-nome, .cod-item.tem-detalhe:hover .cod-nome, .jor-marco.tem-detalhe:hover .jor-nome, .f-hab.tem-detalhe:hover .f-h-nome, .p-linhagem.tem-detalhe:hover b{color:var(--ouro-viv); transition:color .18s ease}
.led-item.tem-detalhe:hover .led-escolha{color:var(--leitura)}
.a-cic.tem-detalhe:hover .a-cic-corpo b{color:var(--ouro-viv)}
.ficha-detalhe{position:absolute; inset:0; z-index:8; opacity:0; pointer-events:none;
    transition:opacity .3s ease}
.ficha-detalhe.aberto{opacity:1; pointer-events:auto}
.fd-fundo{position:absolute; inset:0; background:rgba(8,6,4,.74);
    backdrop-filter:blur(2px); -webkit-backdrop-filter:blur(2px)}
.fd-folha{position:absolute; top:0; right:0; height:100%; width:min(620px,100%);
    background:var(--painel); border-left:1px solid var(--ouro-esc);
    box-shadow:-24px 0 60px rgba(0,0,0,.5); display:flex; flex-direction:column;
    transform:translateX(26px); transition:transform .34s cubic-bezier(.22,.61,.36,1)}
.ficha-detalhe.aberto .fd-folha{transform:translateX(0)}
.fd-cab{flex:0 0 auto; display:flex; align-items:center; gap:14px;
    padding:16px 22px; border-bottom:1px solid rgba(107,82,31,.28); background:rgba(0,0,0,.18)}
.fd-voltar{background:none; border:none; cursor:pointer; color:var(--osso);
    font-family:"IBM Plex Mono",monospace; font-size:12px; letter-spacing:.06em; padding:4px 2px}
.fd-voltar:hover{color:var(--ouro-viv)}
.fd-tipo{font-family:"IBM Plex Mono",monospace; font-size:10px; letter-spacing:.18em;
    text-transform:uppercase; color:var(--ouro-esc); margin-left:auto}
.fd-corpo{flex:1 1 auto; overflow-y:auto; overflow-x:hidden; padding:24px 24px 40px}
.ficha ::-webkit-scrollbar{width:10px; height:10px}
.ficha ::-webkit-scrollbar-track{background:rgba(8,6,4,.3)}
.ficha ::-webkit-scrollbar-thumb{background:linear-gradient(180deg,#5a4520,#382b14);
    border-radius:6px; border:2px solid transparent; background-clip:padding-box}
.ficha ::-webkit-scrollbar-thumb:hover{background:linear-gradient(180deg,#6b521f,#473716);
    background-clip:padding-box}
.ficha ::-webkit-scrollbar-corner{background:transparent}
.f-secao-tit .f-prov{color:var(--ouro-esc); text-transform:none; letter-spacing:.04em; font-size:9px}
.f-atrs{list-style:none; margin:0; padding:2px 0 6px; display:grid;
    grid-template-columns:repeat(3,1fr); gap:11px}
.f-atr{display:flex; flex-wrap:wrap; align-items:baseline; gap:0 8px; width:100%; text-align:left;
    background:#15110c; border:1px solid #2c2419; border-radius:10px; cursor:pointer;
    padding:11px 13px 12px; transition:transform .15s ease, border-color .15s ease}
.f-atr:hover{transform:translateY(-2px); border-color:#3a342b}
.f-atr:focus-visible{outline:none; border-color:var(--ouro)}
.f-atr .f-sigla{order:1; width:100%; font-family:"IBM Plex Mono",monospace; font-size:9px;
    letter-spacing:.16em; text-transform:uppercase; color:var(--osso-fraco); margin-bottom:5px}
.f-atr .f-valor{order:2; font-family:"Fraunces",serif; font-size:24px; color:var(--osso); line-height:1; min-width:auto; text-align:left}
.f-atr .f-mod{order:3; margin-left:0; font-family:"IBM Plex Mono",monospace; font-size:11px; color:var(--ouro)}
.f-atr .f-rotulo{order:4; width:100%; font-family:"Spectral",serif; font-size:12px; color:var(--osso-fraco); margin-top:4px; flex:none}
.f-atr .f-treino{order:5; width:100%; font-family:"IBM Plex Mono",monospace; font-size:8px;
    letter-spacing:.12em; text-transform:uppercase; color:var(--ouro-viv); opacity:0; transition:.16s; margin-top:6px}
.f-atr:hover .f-treino{opacity:.7}
.f-atr.sel{border-color:var(--ouro); background:rgba(203,169,79,.06); box-shadow:0 0 16px rgba(203,169,79,.18)}
.f-atr.sel .f-rotulo, .f-atr.sel .f-sigla, .f-atr.sel .f-valor{color:var(--ouro-viv)}
.f-atr.sel .f-treino{opacity:1}
.f-inv{list-style:none; margin:0; padding:14px 16px; display:grid; grid-template-columns:repeat(2,1fr); gap:11px}
.f-item{position:relative; display:flex; gap:11px; padding:12px; border:1px solid #2c2419; border-radius:10px;
    background:#15110c; cursor:pointer; transition:transform .15s ease, border-color .15s ease}
.f-item:hover{transform:translateY(-2px); border-color:var(--ouro-esc)}
.f-i-ico{flex:none; width:38px; height:38px; border-radius:8px; background:#100d09; border:1px solid #3a3226;
    color:var(--osso-fraco); display:flex; align-items:center; justify-content:center}
.f-i-ico svg{width:20px; height:20px}
.f-i-corpo{flex:1; min-width:0}
.f-item .f-i-top{display:flex; align-items:center; gap:8px}
.f-item .f-i-nome{font-family:"Fraunces",serif; font-weight:500; font-size:13.5px; color:var(--leitura); flex:1; transition:color .18s ease}
.f-item .f-i-qtd{font-family:"IBM Plex Mono",monospace; font-size:10px; color:#100d09; background:var(--osso-fraco);
    padding:1px 7px; border-radius:20px; flex:none; font-weight:600}
.f-item .f-i-det{font-family:"Spectral",serif; font-style:italic; font-size:11.5px; color:var(--osso-fraco);
    margin-top:4px; line-height:1.4}
.f-item[data-rar="comum"]{border-color:#2c2419}
.f-item[data-rar="incomum"]{border-color:#7d8a6e}
.f-item[data-rar="incomum"] .f-i-ico{border-color:#7d8a6e; color:#9caa89}
.f-item[data-rar="raro"]{border-color:#5b7da3; box-shadow:0 0 16px rgba(91,125,163,.3)}
.f-item[data-rar="raro"] .f-i-ico{border-color:#5b7da3; color:#7ba0c8}
.f-item[data-rar="lendario"]{border-color:#b5602e; box-shadow:0 0 18px rgba(181,96,46,.34)}
.f-item[data-rar="lendario"] .f-i-ico{border-color:#b5602e; color:#d98a4e}
.f-item.heranca .f-i-ico{border-color:#9a9488; color:#cdc6b8}
.f-i-eq{font-family:"IBM Plex Mono",monospace; font-size:9px; letter-spacing:.08em; text-transform:uppercase;
    color:var(--ouro-viv); border:1px solid var(--ouro-esc); border-radius:4px; padding:1px 6px; flex:none}
.f-inv-vazio{grid-column:1 / -1; padding:16px 6px; text-align:center; font-family:"Spectral",serif;
    font-style:italic; font-size:13px; color:var(--osso-fraco)}
.ficha.aberta .f-alma-tom{animation:almaSurge 1.1s ease .3s forwards}
@keyframes almaSurge{from{opacity:0; transform:translateY(4px)} to{opacity:1; transform:none}}
.f-anima{list-style:none; margin:0; padding:14px 16px; display:grid; grid-template-columns:repeat(2,1fr); gap:13px}
.f-hab{position:relative; display:flex; gap:11px; padding:13px; border:2px solid #2c2419; border-radius:10px;
    background:#15110c; cursor:pointer; transition:transform .15s ease, border-color .15s ease}
.f-hab:hover{transform:translateY(-2px)}
.f-h-ico{flex:none; width:40px; height:40px; border-radius:8px; background:#100d09; border:1px solid currentColor;
    display:flex; align-items:center; justify-content:center}
.f-h-ico svg{width:21px; height:21px}
.f-h-corpo{flex:1; min-width:0}
.f-h-top{display:flex; align-items:center; gap:8px}
.f-h-nome{font-family:"Fraunces",serif; font-weight:500; font-size:14.5px; color:var(--leitura); flex:1; transition:color .18s ease}
.f-h-selo{font-family:"IBM Plex Mono",monospace; font-size:9px; text-transform:uppercase; letter-spacing:.1em;
    padding:2px 6px; border-radius:4px; flex:none; display:none}
.f-hab.pronta .f-h-selo{display:inline-block; color:#1d130a; background:#ff9436; box-shadow:0 0 14px rgba(255,148,54,.7)}
.f-h-grau{font-family:"IBM Plex Mono",monospace; font-size:9.5px; letter-spacing:.1em; text-transform:uppercase; margin-top:3px}
.f-h-barra{height:7px; border-radius:4px; background:#100d09; border:1px solid #2c2419; overflow:hidden; margin-top:9px}
.f-h-fill{display:block; height:100%; border-radius:3px}
.f-h-nota{font-family:"IBM Plex Mono",monospace; font-size:9px; color:var(--osso-fraco); margin-top:7px; letter-spacing:.05em}
.f-hab[data-grau="0"]{border-color:#34302a; opacity:.6}
.f-hab[data-grau="0"] .f-h-ico{color:#4a4640}
.f-hab[data-grau="0"] .f-h-grau{color:#4a4640}
.f-hab[data-grau="0"] .f-h-fill{background:#4a4640}
.f-hab[data-grau="1"]{border-color:#ede0c4; box-shadow:0 0 14px rgba(237,224,196,.28)}
.f-hab[data-grau="1"] .f-h-ico{color:#ede0c4}
.f-hab[data-grau="1"] .f-h-grau{color:#ede0c4}
.f-hab[data-grau="1"] .f-h-fill{background:#ede0c4; box-shadow:0 0 8px rgba(237,224,196,.5)}
.f-hab[data-grau="2"]{border-color:#f0c14a; box-shadow:0 0 24px rgba(240,193,74,.42)}
.f-hab[data-grau="2"] .f-h-ico{color:#f0c14a; box-shadow:0 0 10px rgba(240,193,74,.4)}
.f-hab[data-grau="2"] .f-h-grau{color:#f0c14a}
.f-hab[data-grau="2"] .f-h-fill{background:#f0c14a; box-shadow:0 0 12px rgba(240,193,74,.8)}
.f-hab[data-grau="3"]{border-color:#ff9436; box-shadow:0 0 26px rgba(255,148,54,.4)}
.f-hab[data-grau="3"] .f-h-ico{color:#ff9436; box-shadow:0 0 13px rgba(255,148,54,.55)}
.f-hab[data-grau="3"] .f-h-grau{color:#ff9436}
.f-hab[data-grau="3"] .f-h-fill{background:#ff9436; box-shadow:0 0 14px rgba(255,148,54,.9)}
.f-hab[data-grau="4"]{border-color:#ff6a2c; box-shadow:0 0 26px rgba(255,106,44,.42)}
.f-hab[data-grau="4"] .f-h-ico{color:#ff6a2c; box-shadow:0 0 13px rgba(255,106,44,.55)}
.f-hab[data-grau="4"] .f-h-grau{color:#ff6a2c}
.f-hab[data-grau="4"] .f-h-fill{background:#ff6a2c; box-shadow:0 0 14px rgba(255,106,44,.9)}
.f-hab[data-grau="5"]{border-color:#ff4d42; box-shadow:0 0 28px rgba(255,77,66,.45)}
.f-hab[data-grau="5"] .f-h-ico{color:#ff4d42; box-shadow:0 0 15px rgba(255,77,66,.6)}
.f-hab[data-grau="5"] .f-h-grau{color:#ff4d42}
.f-hab[data-grau="5"] .f-h-fill{background:#ff4d42; box-shadow:0 0 16px rgba(255,77,66,.95)}
.f-hab.pronta{animation:habPulso 2.6s ease-in-out infinite}
@keyframes habPulso{0%,100%{box-shadow:0 0 26px rgba(255,148,54,.42)}50%{box-shadow:0 0 40px rgba(255,148,54,.72)}}
.f-hab.tem-detalhe:hover{border-color:var(--ouro-viv)}
"""

FICHA_C_BODY = """
<aside class="ficha" id="ficha" aria-hidden="true">
    <div class="ficha-fundo" id="fichaFundo"></div>
    <nav class="ficha-painel" aria-label="ficha do personagem">
      <div class="ficha-faixa">
        <div class="ff-ident">
          <div class="ff-retrato">
            <svg viewBox="0 0 100 100" fill="currentColor" aria-hidden="true">
              <ellipse cx="50" cy="40" rx="16" ry="19"/>
              <path d="M50 58 C33 58 19 70 17 100 L83 100 C81 70 67 58 50 58Z"/>
            </svg>
          </div>
          <div class="ff-nome">
            <b>Gabriel</b>
            <span>estrada do norte &middot; ano 312</span>
          </div>
        </div>
        <div class="ff-slots">
          <div class="ff-slot">
            <span class="ff-slot-rot">vocação</span>
            <span class="ff-selo" title="ainda não revelada">?</span>
          </div>
          <div class="ff-slot">
            <span class="ff-slot-rot">linhagens</span>
            <span class="ff-selos3">
              <span class="ff-selo" title="ainda não revelada">?</span>
              <span class="ff-selo" title="ainda não revelada">?</span>
              <span class="ff-selo" title="ainda não revelada">?</span>
            </span>
          </div>
        </div>
        <button type="button" class="ficha-fechar" id="fichaFechar" aria-label="fechar">&times;</button>
      </div>
      <nav class="ficha-abas" role="tablist" aria-label="seções da ficha">
        <button type="button" role="tab" class="ficha-aba ativa" data-aba="personagem" aria-selected="true">Personagem</button>
        <button type="button" role="tab" class="ficha-aba" data-aba="anima" aria-selected="false">Ânima</button>
        <button type="button" role="tab" class="ficha-aba" data-aba="mundo" aria-selected="false">Mundo</button>
        <button type="button" role="tab" class="ficha-aba" data-aba="codice" aria-selected="false">Códice</button>
        <button type="button" role="tab" class="ficha-aba" data-aba="jornada" aria-selected="false">Jornada</button>
      </nav>
      <div class="ficha-corpo">
        <section class="ficha-aba-painel ativa" data-painel="personagem" role="tabpanel" aria-label="Personagem">

        <div class="p-bloco">
          <div class="p-ident">
            <div class="p-retrato-g">
              <svg viewBox="0 0 100 100" fill="currentColor" aria-hidden="true">
                <ellipse cx="50" cy="38" rx="17" ry="20"/>
                <path d="M50 58 C31 58 17 71 15 100 L85 100 C83 71 69 58 50 58Z"/>
              </svg>
            </div>
            <div class="p-ident-txt">
              <h2 class="p-nome-g">Gabriel</h2>
              <div class="p-origem">estrada do norte &middot; ano 312</div>
              <div class="p-veu">Um nome, uma estrada, e pouco mais. O que você é por baixo disso ainda não se mostrou &mdash; e talvez não peça licença quando se mostrar.</div>
            </div>
          </div>
        </div>

        <div class="p-bloco">
          <div class="p-tit">Vocação &amp; caminho <span class="f-prov">a revelar</span></div>
          <div class="p-grade">
            <div class="p-campo"><span class="r">vocação</span><span class="v velado">?</span></div>
            <div class="p-campo"><span class="r">pilar</span><span class="v velado">?</span></div>
            <div class="p-campo"><span class="r">caminho</span><span class="v velado">?</span></div>
            <div class="p-campo"><span class="r">nível</span><span class="v">1</span></div>
          </div>
        </div>

        <div class="p-bloco">
          <div class="p-tit">Linhagens <span class="f-prov">3 sangues &middot; nenhum desperto</span></div>
          <div class="p-linhagens">
            <div class="p-linhagem">
              <div class="p-selo-g">?</div>
              <b>primeiro sangue</b>
              <span class="p-estado">dormente</span>
              <p>Corre em você desde antes da memória. Ainda não falou.</p>
            </div>
            <div class="p-linhagem">
              <div class="p-selo-g">?</div>
              <b>segundo sangue</b>
              <span class="p-estado">selado</span>
              <p>Alguém o trancou antes de você nascer. O lacre ainda segura.</p>
            </div>
            <div class="p-linhagem">
              <div class="p-selo-g">?</div>
              <b>terceiro sangue</b>
              <span class="p-estado">latente</span>
              <p>O mais fundo dos três. Quando acordar, não vai ser gentil.</p>
            </div>
          </div>
        </div>

        <div class="p-bloco">
          <div class="p-tit">Atributos <span class="f-prov">provisório &middot; toque pra treinar</span></div>
          <ul class="f-atrs" id="fAtrs">
            <li><button type="button" class="f-atr" data-atr="FOR"><span class="f-sigla">FOR</span><span class="f-rotulo">Força</span><span class="f-valor">11</span><span class="f-mod">+0</span><span class="f-treino">treinar</span></button></li>
            <li><button type="button" class="f-atr" data-atr="DEX"><span class="f-sigla">DEX</span><span class="f-rotulo">Destreza</span><span class="f-valor">13</span><span class="f-mod">+1</span><span class="f-treino">treinar</span></button></li>
            <li><button type="button" class="f-atr" data-atr="CON"><span class="f-sigla">CON</span><span class="f-rotulo">Constituição</span><span class="f-valor">12</span><span class="f-mod">+1</span><span class="f-treino">treinar</span></button></li>
            <li><button type="button" class="f-atr" data-atr="INT"><span class="f-sigla">INT</span><span class="f-rotulo">Inteligência</span><span class="f-valor">14</span><span class="f-mod">+2</span><span class="f-treino">treinar</span></button></li>
            <li><button type="button" class="f-atr" data-atr="SAB"><span class="f-sigla">SAB</span><span class="f-rotulo">Sabedoria</span><span class="f-valor">12</span><span class="f-mod">+1</span><span class="f-treino">treinar</span></button></li>
            <li><button type="button" class="f-atr" data-atr="CHA"><span class="f-sigla">CHA</span><span class="f-rotulo">Carisma</span><span class="f-valor">10</span><span class="f-mod">+0</span><span class="f-treino">treinar</span></button></li>
          </ul>
        </div>

        <div class="p-bloco">
          <div class="p-tit">Estado vital <span class="f-prov">provisório</span></div>
          <div class="p-vitais">
            <div class="p-barra"><span class="pb-rot">Vida</span><span class="pb-trilho"><span class="pb-fill" style="width:93%; background:var(--vida)"></span></span><span class="pb-num">28/30</span></div>
            <div class="p-barra"><span class="pb-rot">Vigor</span><span class="pb-trilho"><span class="pb-fill" style="width:91%; background:var(--vigor)"></span></span><span class="pb-num">20/22</span></div>
            <div class="p-barra"><span class="pb-rot">Mana</span><span class="pb-trilho"><span class="pb-fill" style="width:75%; background:var(--mana)"></span></span><span class="pb-num">12/16</span></div>
            <div class="p-barra"><span class="pb-rot">Fadiga</span><span class="pb-trilho"><span class="pb-fill" style="width:30%; background:var(--fadiga)"></span></span><span class="pb-num">3/10</span></div>
            <div class="p-barra"><span class="pb-rot">Dissolução</span><span class="pb-trilho"><span class="pb-fill" style="width:2%; background:var(--dissol)"></span></span><span class="pb-num">0/10</span></div>
          </div>
        </div>

        <div class="p-bloco">
          <div class="p-tit">Combate <span class="f-prov">provisório</span></div>
          <div class="p-grade">
            <div class="p-campo"><span class="r">defesa</span><span class="v">13</span></div>
            <div class="p-campo"><span class="r">iniciativa</span><span class="v">+1</span></div>
            <div class="p-campo"><span class="r">deslocamento</span><span class="v">9 m</span></div>
            <div class="p-campo"><span class="r">CD de magia</span><span class="v">12</span></div>
          </div>
        </div>

        <div class="p-bloco">
          <div class="p-tit">Resistências &amp; vulnerabilidades <span class="f-prov">provisório</span></div>
          <div class="p-lista">
            <span class="p-tag resist">frio <span class="sev">resistente</span></span>
            <span class="p-tag vulner">fogo <span class="sev">vulnerável</span></span>
          </div>
        </div>

        <div class="p-bloco">
          <div class="p-tit">Condições</div>
          <div class="p-lista">
            <span class="p-tag">joelho ralado <span class="sev">leve</span></span>
          </div>
        </div>

        <div class="p-bloco">
          <div class="p-tit">Tensão <span class="f-prov">só aparece quando alta</span></div>
          <div class="p-pressao">
            <div class="pp-topo"><span class="pp-est">tensa</span><span class="pp-num">7/10</span></div>
            <span class="pb-trilho"><span class="pb-fill" style="width:70%"></span></span>
          </div>
          <p class="p-vazio">Em calma, esta seção fica fora da ficha. Aparece quando a corda começa a esticar &mdash; mostrada aqui só pra você ver a forma dela.</p>
        </div>

        <div class="p-bloco">
          <div class="p-tit">Idiomas <span class="f-prov">a confirmar no canon</span></div>
          <div class="p-lista">
            <span class="p-tag">comum do norte</span>
          </div>
        </div>

        </section>

        <section class="ficha-aba-painel" data-painel="anima" role="tabpanel" aria-label="Ânima">

        <div class="p-bloco">
          <div class="p-tit">Habilidades <span class="f-prov">provisório &middot; toque pra cultivar</span></div>
          <p class="a-tom">A Ânima desperta apanhando, não estudando. Cada habilidade ganha grau com o uso sob risco &mdash; e o que você nunca arrisca, nunca acorda.</p>
          <div class="a-quadro">
            <ul class="f-anima">
              <li class="f-hab" data-grau="2" data-hab="espada-arcana">
                <span class="f-h-ico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><line x1="6" y1="18" x2="16" y2="8"/><line x1="14" y1="6" x2="18" y2="10"/><line x1="4" y1="20" x2="7" y2="17"/></svg></span>
                <div class="f-h-corpo">
                  <div class="f-h-top"><span class="f-h-nome">Espada Arcana</span></div>
                  <div class="f-h-grau">Praticante</div>
                  <div class="f-h-barra"><i class="f-h-fill" style="width:62%"></i></div>
                  <div class="f-h-nota">5 de 8 marcas pro próximo grau</div>
                </div>
              </li>
              <li class="f-hab" data-grau="1" data-hab="estocada-precisa">
                <span class="f-h-ico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3.2"/><line x1="12" y1="1.5" x2="12" y2="5"/><line x1="12" y1="19" x2="12" y2="22.5"/><line x1="1.5" y1="12" x2="5" y2="12"/><line x1="19" y1="12" x2="22.5" y2="12"/></svg></span>
                <div class="f-h-corpo">
                  <div class="f-h-top"><span class="f-h-nome">Estocada Precisa</span></div>
                  <div class="f-h-grau">Aprendiz</div>
                  <div class="f-h-barra"><i class="f-h-fill" style="width:67%"></i></div>
                  <div class="f-h-nota">2 de 3 marcas pro próximo grau</div>
                </div>
              </li>
              <li class="f-hab pronta" data-grau="3" data-hab="tecer-mana">
                <span class="f-h-ico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round" aria-hidden="true"><path d="M12 2 L13.8 10.2 L22 12 L13.8 13.8 L12 22 L10.2 13.8 L2 12 L10.2 10.2 Z"/></svg></span>
                <div class="f-h-corpo">
                  <div class="f-h-top"><span class="f-h-nome">Tecer Mana</span><span class="f-h-selo">pronta</span></div>
                  <div class="f-h-grau">Veterano</div>
                  <div class="f-h-barra"><i class="f-h-fill" style="width:100%"></i></div>
                  <div class="f-h-nota">pronta pra avançar</div>
                </div>
              </li>
              <li class="f-hab" data-grau="0" data-hab="guarda-defensiva">
                <span class="f-h-ico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round" aria-hidden="true"><path d="M12 3 L20 6 V12 C20 17 16 20 12 21.5 C8 20 4 17 4 12 V6 Z"/></svg></span>
                <div class="f-h-corpo">
                  <div class="f-h-top"><span class="f-h-nome">Guarda Defensiva</span></div>
                  <div class="f-h-grau">Adormecida</div>
                  <div class="f-h-barra"><i class="f-h-fill" style="width:0%"></i></div>
                  <div class="f-h-nota">ainda não despertou</div>
                </div>
              </li>
            </ul>
          </div>
        </div>

        <div class="p-bloco">
          <div class="p-tit">Dívida viva <span class="f-prov">provisório &middot; o que o poder cobrou</span></div>
          <div class="a-divida">
            <div class="a-cic">
              <div class="a-cic-glifo"><svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M13 2 L9 10 L15 14 L10 22" stroke="currentColor" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/></svg></div>
              <div class="a-cic-corpo">
                <b>primeiro tributo</b>
                <p>Algo em você cobrou antes de você entender o que era. A marca ficou &mdash; e não vai embora.</p>
              </div>
            </div>
          </div>
          <p class="a-tom">Toda dívida aqui é permanente: não cura, não se paga de volta, só se carrega. Por ora, uma marca só &mdash; mas a Ânima ainda é jovem.</p>
        </div>

        </section>
        <section class="ficha-aba-painel" data-painel="mundo" role="tabpanel" aria-label="Mundo">

        <div class="p-bloco">
          <div class="p-tit">Inventário <span class="f-prov">provisório &middot; o que você carrega</span></div>
          <div class="a-quadro">
            <ul class="f-inv">
              <li class="f-item">
                <span class="f-i-ico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 20 L8 16"/><path d="M8 16 L18 6 L20 8 L10 18 Z"/></svg></span>
                <div class="f-i-corpo">
                  <div class="f-i-top"><span class="f-i-nome">Faca de mato</span></div>
                  <div class="f-i-det">gasta de uso, fio ainda firme.</div>
                </div>
              </li>
              <li class="f-item">
                <span class="f-i-ico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M8 4 L12 7 L16 4"/><path d="M8 4 C5 8 5 16 6 20 L18 20 C19 16 19 8 16 4"/></svg></span>
                <div class="f-i-corpo">
                  <div class="f-i-top"><span class="f-i-nome">Capa de lã encerada</span></div>
                  <div class="f-i-det">pesada da chuva do norte.</div>
                </div>
              </li>
              <li class="f-item">
                <span class="f-i-ico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M10 3 L14 3 L14 6 L15 8 L15 19 C15 20.1 14.1 21 13 21 L11 21 C9.9 21 9 20.1 9 19 L9 8 L10 6 Z"/><line x1="9.3" y1="12" x2="14.7" y2="12"/></svg></span>
                <div class="f-i-corpo">
                  <div class="f-i-top"><span class="f-i-nome">Cantil de couro</span></div>
                  <div class="f-i-det">pela metade.</div>
                </div>
              </li>
              <li class="f-item">
                <span class="f-i-ico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="5" y="9" width="14" height="11" rx="2"/><path d="M9 9 L12 5 L15 9"/></svg></span>
                <div class="f-i-corpo">
                  <div class="f-i-top"><span class="f-i-nome">Ração de viagem</span><span class="f-i-qtd">&times;3</span></div>
                  <div class="f-i-det">pão duro e carne seca.</div>
                </div>
              </li>
              <li class="f-item">
                <span class="f-i-ico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M8 8 C8 6 16 6 16 8 L18 18 C18 20 6 20 6 18 Z"/><path d="M9 8 C9 5 15 5 15 8"/></svg></span>
                <div class="f-i-corpo">
                  <div class="f-i-top"><span class="f-i-nome">Bolsa surrada</span></div>
                  <div class="f-i-det">algumas moedas de cobre.</div>
                </div>
              </li>
              <li class="f-item heranca">
                <span class="f-i-ico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7 4 C9 8 15 8 17 4"/><path d="M12 8 L15 13 L12 19 L9 13 Z"/></svg></span>
                <div class="f-i-corpo">
                  <div class="f-i-top"><span class="f-i-nome">Pingente de prata</span></div>
                  <div class="f-i-det">herança sem brilho; você nunca o tira.</div>
                </div>
              </li>
            </ul>
          </div>
        </div>

        <div class="p-bloco">
          <div class="p-tit">Moeda <span class="f-prov">[simulada] &middot; não existe no canon ainda</span></div>
          <div class="m-moeda">
            <div class="m-disco">Kr</div>
            <div class="m-corpo">
              <div class="m-nome">Korren <span>&mdash; a moeda gasta do norte</span></div>
              <div class="m-denom">
                <span class="m-d"><b>11</b> de cobre</span>
                <span class="m-d zero"><b>0</b> de prata</span>
                <span class="m-d zero"><b>0</b> de ouro</span>
              </div>
            </div>
          </div>
        </div>

        <div class="p-bloco">
          <div class="p-tit">Laços <span class="f-prov">provisório &middot; quem você conhece</span></div>
          <div class="l-lacos">
            <div class="l-laco">
              <div class="l-selo">E</div>
              <div class="l-corpo">
                <div class="l-top"><span class="l-nome">Elara</span><span class="l-rel">mãe</span></div>
                <div class="l-det">Ensina você a conter o que transborda. Tem paciência de sobra &mdash; e respostas de menos.</div>
              </div>
            </div>
            <div class="l-laco">
              <div class="l-selo">K</div>
              <div class="l-corpo">
                <div class="l-top"><span class="l-nome">Kael</span><span class="l-rel">pai</span></div>
                <div class="l-det">O sobrenome que abre portas &mdash; e o peso de saber que muita gente come do que a família planta.</div>
              </div>
            </div>
            <div class="l-laco">
              <div class="l-selo">T</div>
              <div class="l-corpo">
                <div class="l-top"><span class="l-nome">Torin</span><span class="l-rel">meio-irmão</span></div>
                <div class="l-det">Respeito à distância. Uma tensão que nenhum dos dois nomeia &mdash; e que nenhum dos dois começou.</div>
              </div>
            </div>
            <div class="l-laco">
              <div class="l-selo">S</div>
              <div class="l-corpo">
                <div class="l-top"><span class="l-nome">Serethan</span><span class="l-rel">avô</span></div>
                <div class="l-det">Aparece sempre nos momentos certos. Há um interesse dele por você que ninguém na casa sabe explicar.</div>
              </div>
            </div>
          </div>
        </div>

        <div class="p-bloco">
          <div class="p-tit">Pactos e votos <span class="f-prov">provisório &middot; nenhum firmado</span></div>
          <div class="pc-vazio">
            <div class="pc-glifo"><svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M4 7 C9 7 9 12 12 12" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/><path d="M20 17 C15 17 15 12 12 12" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/><circle cx="4" cy="7" r="1.3" fill="currentColor"/><circle cx="20" cy="17" r="1.3" fill="currentColor"/></svg></div>
            <div class="pc-corpo">
              <b>nenhum pacto firmado</b>
              <p>Nada foi assinado, nenhum fio te prende. Enquanto não houver preço cobrado, este lugar fica em silêncio.</p>
            </div>
          </div>
          <p class="a-tom">Dizem que, quando uma escolha pesa demais, o Fiador aparece para mediá-la: não chega, não mente, nunca força. Mostra o preço em voz baixa e some no instante em que você assina &mdash; depois, a realidade cobra sozinha. Um Voto Vinculante é o mesmo acerto, feito contra si mesmo. Quem lê o termo inteiro escapa barato; quem assina às pressas, não.</p>
        </div>

        <div class="p-bloco">
          <div class="p-tit">Calendário <span class="f-prov">canônico &middot; Vigília Quebrada</span></div>
          <div class="cal-era">
            <span class="ce-ano">Ano 312 VQ</span>
            <span class="ce-mes">mês de Ashiran</span>
            <span class="ce-nota">o primeiro sopro &mdash; data ainda provisória</span>
          </div>
          <div class="cal-meses">
            <span class="cal-mes atual">Ashiran</span>
            <span class="cal-mes">Velathi</span>
            <span class="cal-mes">Korami</span>
            <span class="cal-mes">Sureth</span>
            <span class="cal-mes">Namesh</span>
            <span class="cal-mes">Dravith</span>
            <span class="cal-mes">Vareshi</span>
            <span class="cal-mes">Gravmora</span>
            <span class="cal-mes">Iskara</span>
            <span class="cal-mes">Thornath</span>
            <span class="cal-mes">Vyrmara</span>
            <span class="cal-mes">Morvenath</span>
          </div>
          <div class="cal-luas">
            <div class="lua">
              <div class="lua-disco"><svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="1" opacity=".4"/><path d="M12 3 A9 9 0 0 1 12 21 A5 9 0 0 0 12 3 Z" fill="currentColor"/></svg></div>
              <div class="lua-corpo">
                <div class="lua-nome">Mórven</div>
                <div class="lua-est">crescente &middot; a lua viva</div>
                <div class="lua-det">Rege os meses; o tempo anda por ela. Contar luas é contar meses.</div>
              </div>
            </div>
            <div class="lua silenciada">
              <div class="lua-disco"><svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="1.1" stroke-dasharray="2 3" opacity=".75"/></svg></div>
              <div class="lua-corpo">
                <div class="lua-nome">Vélith</div>
                <div class="lua-est">silenciada &middot; fora do céu</div>
                <div class="lua-det">Some desde a catástrofe. Quando volta, a magia maior cresce e o povo tranca a porta.</div>
              </div>
            </div>
          </div>
        </div>

        </section>
                <section class="ficha-aba-painel" data-painel="codice" role="tabpanel" aria-label="Códice">
        <div class="p-bloco">
          <div class="p-tit">Bestiário <span class="f-prov">[simulado] &middot; registro de campo</span></div>
          <div class="a-quadro">
            <div class="cod-lista">
          <div class="cod-item">
            <div class="cod-selo">C</div>
            <div class="cod-corpo">
              <div class="cod-top"><div class="cod-nome">Cães-de-Vala</div><div class="cod-tag">criatura</div></div>
              <div class="cod-meta">Fraqueza: fogo &middot; Estrada do Norte</div>
              <div class="cod-det">Matilha magra que segue quem anda só. Não é criatura de pilar &mdash; é fome velha, e fome não recua fácil.</div>
            </div>
          </div>
          <div class="cod-item">
            <div class="cod-selo">M</div>
            <div class="cod-corpo">
              <div class="cod-top"><div class="cod-nome">Mariposa-de-Sebo</div><div class="cod-tag">criatura</div></div>
              <div class="cod-meta">Fraqueza: luz forte &middot; Casa de Namiri</div>
              <div class="cod-det">Come a chama das velas e engorda no escuro. O perigo nunca foi ela &mdash; foi o escuro que ela deixa.</div>
            </div>
          </div>
          <div class="cod-item velado">
            <div class="cod-selo">?</div>
            <div class="cod-corpo">
              <div class="cod-top"><div class="cod-nome">Não descoberto</div><div class="cod-tag">rastro sem nome</div></div>
            </div>
          </div>
          <div class="cod-item velado">
            <div class="cod-selo">?</div>
            <div class="cod-corpo">
              <div class="cod-top"><div class="cod-nome">Não descoberto</div><div class="cod-tag">registro selado</div></div>
            </div>
          </div>
            </div>
          </div>
          <p class="a-tom">O registro inteiro das criaturas não cabe aqui &mdash; e a maior parte do que anda por Alderyn você nunca cruzou. Anota-se só o pouco que sobreviveu ao encontro.</p>
        </div>
        <div class="p-bloco">
          <div class="p-tit">Lugares conhecidos <span class="f-prov">provisório &middot; só o que você pisou</span></div>
          <div class="a-quadro">
            <div class="cod-lista">
          <div class="cod-item">
            <div class="cod-selo">N</div>
            <div class="cod-corpo">
              <div class="cod-top"><div class="cod-nome">Namiri</div><div class="cod-tag">Kethara &middot; natal</div></div>
              <div class="cod-det">A cidade onde você nasceu, no norte de chuvas longas. Conhece as ruas de cor &mdash; e os silêncios da casa, melhor ainda.</div>
            </div>
          </div>
          <div class="cod-item">
            <div class="cod-selo">E</div>
            <div class="cod-corpo">
              <div class="cod-top"><div class="cod-nome">Estrada do Norte</div><div class="cod-tag">Kethara &middot; percorrida</div></div>
              <div class="cod-det">A linha de terra batida que liga Namiri ao resto. Você sabe onde ela é segura &mdash; e onde é melhor não parar.</div>
            </div>
          </div>
          <div class="cod-item velado">
            <div class="cod-selo">?</div>
            <div class="cod-corpo">
              <div class="cod-top"><div class="cod-nome">Vyrkhor</div><div class="cod-tag">além do mar &middot; só de nome</div></div>
            </div>
          </div>
          <div class="cod-item velado">
            <div class="cod-selo">?</div>
            <div class="cod-corpo">
              <div class="cod-top"><div class="cod-nome">Thornmarak</div><div class="cod-tag">além do mar &middot; só de nome</div></div>
            </div>
          </div>
          <div class="cod-item velado">
            <div class="cod-selo">?</div>
            <div class="cod-corpo">
              <div class="cod-top"><div class="cod-nome">Voranthar</div><div class="cod-tag">além do mar &middot; só de nome</div></div>
            </div>
          </div>
            </div>
          </div>
          <p class="a-tom">O mapa com a névoa do que falta vem depois. Por enquanto o mundo é grande do jeito que sempre foi: três continentes que você só conhece de nome, e um mar que nunca atravessou.</p>
        </div>
        <div class="p-bloco">
          <div class="p-tit">Lore <span class="f-prov">canônico &middot; o que se sabe da era</span></div>
          <div class="a-quadro">
            <div class="cod-lista">
          <div class="cod-item">
            <div class="cod-selo">V</div>
            <div class="cod-corpo">
              <div class="cod-top"><div class="cod-nome">A Vigília Quebrada</div><div class="cod-tag">era atual &middot; ano 312</div></div>
              <div class="cod-det">O nome da era em que você nasceu. Algo se quebrou antes de você &mdash; e o mundo ainda conta os anos a partir da quebra, não do conserto.</div>
            </div>
          </div>
          <div class="cod-item">
            <div class="cod-selo">P</div>
            <div class="cod-corpo">
              <div class="cod-top"><div class="cod-nome">Os Cinco Pilares</div><div class="cod-tag">corpo &middot; sombra &middot; arcano &middot; espírito &middot; engenho</div></div>
              <div class="cod-det">As cinco formas de a força do mundo passar por uma pessoa. Toda vocação nasce de um deles &mdash; e ninguém escolhe de graça por onde a força entra.</div>
            </div>
          </div>
          <div class="cod-item">
            <div class="cod-selo">D</div>
            <div class="cod-corpo">
              <div class="cod-top"><div class="cod-nome">Os deuses que calaram</div><div class="cod-tag">panteão &middot; em colapso</div></div>
              <div class="cod-det">Houve deuses. A maioria silenciou ou caiu. Reza-se mais por hábito que por resposta &mdash; e alguns nomes é melhor não dizer alto.</div>
            </div>
          </div>
          <div class="cod-item velado">
            <div class="cod-selo">?</div>
            <div class="cod-corpo">
              <div class="cod-top"><div class="cod-nome">Não decifrado</div><div class="cod-tag">fragmento ilegível</div></div>
            </div>
          </div>
            </div>
          </div>
          <p class="a-tom">A história inteira da Vigília Quebrada não cabe numa ficha &mdash; e boa parte dela foi perdida de propósito. Aqui fica só o que chegou até você inteiro o bastante pra confiar.</p>
        </div>
        <div class="p-bloco">
          <div class="p-tit">Pessoas conhecidas <span class="f-prov">provisório &middot; fora de casa</span></div>
          <div class="a-quadro">
            <div class="cod-lista">
          <div class="cod-item">
            <div class="cod-selo">F</div>
            <div class="cod-corpo">
              <div class="cod-top"><div class="cod-nome">Friede</div><div class="cod-tag">Namiri &middot; mais velha</div></div>
              <div class="cod-det">Uma das poucas mais velhas que reparou em você. Sabe coisas que não ensina de graça &mdash; e repara mais do que diz.</div>
            </div>
          </div>
          <div class="cod-item velado">
            <div class="cod-selo">?</div>
            <div class="cod-corpo">
              <div class="cod-top"><div class="cod-nome">Não conhecido</div><div class="cod-tag">um nome que ainda não cruzou o seu</div></div>
            </div>
          </div>
          <div class="cod-item velado">
            <div class="cod-selo">?</div>
            <div class="cod-corpo">
              <div class="cod-top"><div class="cod-nome">Não conhecido</div><div class="cod-tag">registro vazio</div></div>
            </div>
          </div>
          <div class="cod-item velado">
            <div class="cod-selo">?</div>
            <div class="cod-corpo">
              <div class="cod-top"><div class="cod-nome">Não conhecido</div><div class="cod-tag">fora do seu alcance</div></div>
            </div>
          </div>
            </div>
          </div>
          <p class="a-tom">Fora de casa você conhece pouca gente &mdash; e nem todo nome que você guarda foi por afeto. O resto do mundo ainda não passou por você.</p>
        </div>
        </section>
                <section class="ficha-aba-painel" data-painel="jornada" role="tabpanel" aria-label="Jornada">
        <div class="p-bloco">
          <div class="p-tit">Marcos de Vida <span class="f-prov">provisório &middot; de onde você veio</span></div>
          <div class="a-quadro">
            <div class="jor-lista">
            <div class="jor-marco unico">
              <div class="jor-top"><div class="jor-nome">Nascido em Namiri</div><div class="jor-peso unico">Único</div></div>
              <div class="jor-quando">Kethara &middot; o começo</div>
              <div class="jor-det">O começo de tudo. Segundo de quatro, numa casa onde o sobrenome pesa mais que o nome de quem o carrega.</div>
            </div>
            <div class="jor-marco maior">
              <div class="jor-top"><div class="jor-nome">A Ânima acordou</div><div class="jor-peso maior">Maior</div></div>
              <div class="jor-quando">infância &middot; apanhando</div>
              <div class="jor-det">Tua primeira habilidade não foi ensinada &mdash; foi arrancada de você num susto. A Ânima desperta assim: doendo antes de obedecer.</div>
            </div>
            <div class="jor-marco sig">
              <div class="jor-top"><div class="jor-nome">Elara te ensinou a conter</div><div class="jor-peso sig">Significativo</div></div>
              <div class="jor-quando">infância &middot; em casa</div>
              <div class="jor-det">Tua mãe te mostrou como segurar o que transborda. Menos um truque, mais um aviso: o que não se contém, se paga.</div>
            </div>
            <div class="jor-marco menor">
              <div class="jor-top"><div class="jor-nome">O primeiro inverno que você lembra</div><div class="jor-peso menor">Menor</div></div>
              <div class="jor-quando">infância &middot; Namiri</div>
              <div class="jor-det">As chuvas longas do norte, batendo no telhado a noite inteira. Pequeno demais pra virar história &mdash; grande o bastante pra ter ficado.</div>
            </div>
            <div class="jor-marco velado">
              <div class="jor-top"><div class="jor-nome">Ainda não vivido</div></div>
              <div class="jor-quando">—</div>
            </div>
            <div class="jor-marco velado">
              <div class="jor-top"><div class="jor-nome">Ainda não vivido</div></div>
              <div class="jor-quando">—</div>
            </div>
            </div>
          </div>
          <p class="a-tom">A maior parte da sua vida ainda não aconteceu. Os marcos se escrevem sozinhos conforme você vive &mdash; e nenhum deles se apaga depois.</p>
        </div>
        <div class="p-bloco">
          <div class="p-tit">Ledger de decisões <span class="f-prov">[exemplo] &middot; escolhas que ficam</span></div>
          <div class="led-lista">
            <div class="led-item">
              <div class="led-quando">na praça de Namiri &middot; infância</div>
              <div class="led-escolha">Você achou uma moeda caída de alguém na praça. Ninguém viu cair, ninguém viu você. Você guardou.</div>
              <div class="led-conseq">
                <div class="led-selo">consequência &middot; permanente</div>
                <div class="led-conseq-txt">Pequena demais pra alguém sentir falta &mdash; grande o bastante pra você nunca esquecer. Foi a primeira vez que a escolha foi só sua, e ela ficou.</div>
              </div>
            </div>
          </div>
          <p class="a-tom">Aqui fica o peso. Toda escolha que custou alguma coisa entra neste registro &mdash; e não sai. O jogo não te castiga por escolher; ele só não deixa você desescolher.</p>
        </div>
        </section>

      </div>
      <div class="ficha-detalhe" id="fichaDetalhe" aria-hidden="true" role="dialog" aria-modal="true" aria-label="detalhe do item">
        <div class="fd-fundo" id="fdFundo"></div>
        <div class="fd-folha" role="document">
          <div class="fd-cab">
            <button type="button" class="fd-voltar" id="fdVoltar">&lsaquo; voltar</button>
            <span class="fd-tipo" id="fdTipo"></span>
          </div>
          <div class="fd-corpo" id="fdCorpo"></div>
        </div>
      </div>
    </nav>
  </aside>
"""

FICHA_C_JS = r"""
(function(){
  var ficha = document.getElementById("ficha");
  if(!ficha) return;
  var fichaFundo = document.getElementById("fichaFundo");
  var fichaFechar = document.getElementById("fichaFechar");
  function abrirFicha(){ ficha.classList.add("aberta"); ficha.setAttribute("aria-hidden","false"); }
  function fecharFicha(){ ficha.classList.remove("aberta"); ficha.setAttribute("aria-hidden","true"); }
  function ligarGatilho(b){
    if(!b || b.dataset.fichaWired) return;
    b.dataset.fichaWired = "1";
    b.addEventListener("click", function(e){ e.preventDefault(); abrirFicha(); });
    b.addEventListener("keydown", function(e){ if(e.key==="Enter"||e.key===" "||e.key==="Spacebar"){ e.preventDefault(); abrirFicha(); } });
  }
  // liga a gatilhos que JA existem: vivo usa #abrir-ficha; harness/testes usam #abreFichaTopo/#abreFicha.
  ["abrir-ficha","abreFichaTopo","abreFicha"].forEach(function(id){ ligarGatilho(document.getElementById(id)); });

  // garante o botao "ficha" no .head (irmao de #abrir-config). O NiceGUI re-renderiza o
  // _BODY (warning "Re-rendering affected elements") e pode apagar o botao; um MutationObserver
  // re-afirma sempre que sumir, e tambem cobre o .head nascer depois (Vue assincrono).
  // Inofensivo onde nao existe .head (ex.: testes usam #abreFichaTopo).
  function garantirBotao(){
    var head = document.querySelector(".head");
    if(!head) return;
    if(document.getElementById("abrir-ficha")) return;
    var b = document.createElement("button");
    b.type="button"; b.className="engr"; b.id="abrir-ficha";
    b.title="Ficha do personagem"; b.setAttribute("aria-label","Ficha");
    b.innerHTML='<i class="ti ti-user" aria-hidden="true"></i>ficha';
    var cfg = document.getElementById("abrir-config");
    if(cfg && cfg.parentNode===head) head.insertBefore(b, cfg); else head.appendChild(b);
    ligarGatilho(b);
  }
  garantirBotao();
  if(document.body && window.MutationObserver){
    var _obsFicha = new MutationObserver(function(){
      if(!document.getElementById("abrir-ficha")) garantirBotao();
    });
    _obsFicha.observe(document.body, { childList:true, subtree:true });
  }

  if(fichaFundo){ fichaFundo.addEventListener("click", fecharFicha); }
  if(fichaFechar){ fichaFechar.addEventListener("click", fecharFicha); }
  document.addEventListener("keydown", function(e){
    var det = document.querySelector(".ficha-detalhe.aberto");
    if(e.key==="Escape" && !det && ficha.classList.contains("aberta")){ fecharFicha(); }
  });

  // ---- hooks pro backend vivo ligar valores reais (Scope A) ----
  window.fichaSetPressao = function(n, rotulo){
    n = Math.max(0, Math.min(10, Math.round(n||0)));
    var blk = document.querySelector(".p-pressao"); if(!blk) return;
    var num = blk.querySelector(".pp-num"); if(num) num.textContent = n + "/10";
    var fill = blk.querySelector(".pb-fill"); if(fill) fill.style.width = (n*10) + "%";
    var est = blk.querySelector(".pp-est");
    if(est){ est.textContent = rotulo || (n>=7 ? "no limite" : n>=4 ? "tensa" : "serena"); }
  };
  // Combate Fatia 1 — Tensao (1-10): reusa o bloco .p-pressao. Em combate a barra
  // APARECE e mostra a Tensao; fora de combate (null/0) a secao inteira some.
  // (Nao relabela: o titulo segue "Pressao emocional" -- debito cosmetico p/ depois.)
  window.fichaSetTensao = function(n){
    var blk = document.querySelector(".p-pressao"); if(!blk) return;
    var sec = blk.closest(".p-bloco") || blk;   // secao inteira: titulo + barra + nota
    var v = (n == null) ? 0 : Math.max(0, Math.min(10, Math.round(n)));
    if(v <= 0){ sec.style.display = "none"; return; }   // fora de combate: escondida
    sec.style.display = "";                               // em combate: visivel
    var num = blk.querySelector(".pp-num"); if(num) num.textContent = v + "/10";
    var fill = blk.querySelector(".pb-fill"); if(fill) fill.style.width = (v*10) + "%";
    var est = blk.querySelector(".pp-est");
    if(est){ est.textContent = v>=7 ? "no limite" : v>=4 ? "tensa" : "serena"; }
  };
  window.fichaSetAtributos = function(mods){
    if(!mods) return;
    Object.keys(mods).forEach(function(sig){
      var btn = document.querySelector('.f-atr[data-atr="'+sig+'"]'); if(!btn) return;
      var el = btn.querySelector(".f-mod"); var v = mods[sig];
      if(el && v != null) el.textContent = (v>=0?"+":"") + v;
    });
  };
  // Fio 1 — vitais: HP por enquanto (cresce 1 bloco por barra: Vigor/Mana/Fadiga/Dissolucao).
  // Casa a barra pelo texto do .pb-rot e escopa .pb-num/.pb-fill AO .p-barra casado.
  window.fichaSetVitais = function(v){
    if(!v) return;
    function setBarra(rotulo, atual, maximo){
      if(atual == null || maximo == null) return;
      var alvo = null;
      document.querySelectorAll(".p-vitais .p-barra").forEach(function(b){
        var r = b.querySelector(".pb-rot");
        if(r && r.textContent.trim() === rotulo) alvo = b;
      });
      if(!alvo) return;
      var max = Math.round(maximo), at = Math.max(0, Math.round(atual));
      var pct = (max > 0) ? Math.max(0, Math.min(100, Math.round(at / max * 100))) : 0;
      var num = alvo.querySelector(".pb-num"); if(num) num.textContent = at + "/" + max;
      var fill = alvo.querySelector(".pb-fill"); if(fill) fill.style.width = pct + "%"; // so width; background sobrevive
    }
    setBarra("Vida", v.hp_atual, v.hp_maximo);
    setBarra("Mana", v.mp_atual, v.mp_maximo);
    setBarra("Vigor", v.vigor_atual, v.vigor_maximo);
    setBarra("Fadiga", v.fadiga_atual, v.fadiga_maximo);
    setBarra("Dissolução", v.divida_viva, 100);
  };
  // Fio 1 — identidade: vocacao + nivel. Casa o campo pelo texto do .r, escreve no .v e
  // tira o 'velado' (que renderiza o placeholder "?").
  window.fichaSetIdentidade = function(d){
    if(!d) return;
    function setCampo(rotulo, valor){
      if(valor == null || valor === "") return;
      document.querySelectorAll(".p-campo").forEach(function(c){
        var r = c.querySelector(".r");
        if(r && r.textContent.trim() === rotulo){
          var vEl = c.querySelector(".v");
          if(vEl){ vEl.textContent = valor; vEl.classList.remove("velado"); }
        }
      });
    }
    setCampo("vocação", d.classe);
    setCampo("nível", (d.nivel != null) ? String(d.nivel) : null);
  };

  // Inventario-EXIBICAO: troca os itens-semente fake do grid .f-inv pela posse real.
  // Lista vazia (ou sem itens) -> "Mochila vazia." limpa, nunca os fakes nem erro.
  // raridade -> data-rar (classe de cor ja no CSS); item custom sem raridade vira 'comum'.
  window.fichaSetInventario = function(items){
    var ul = document.querySelector(".f-inv"); if(!ul) return;
    var RAR = {comum:1, incomum:1, raro:1, lendario:1};
    function esc(s){ return String(s==null?"":s).replace(/[&<>"]/g, function(c){
      return c==="&"?"&amp;":c==="<"?"&lt;":c===">"?"&gt;":"&quot;"; }); }
    if(!items || !items.length){
      ul.innerHTML = '<li class="f-inv-vazio">Mochila vazia.</li>';
      return;
    }
    var ICO = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"'
      + ' stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
      + '<path d="M5 8 L12 4 L19 8 L19 17 L12 21 L5 17 Z"/><path d="M5 8 L12 12 L19 8"/>'
      + '<path d="M12 12 L12 21"/></svg>';
    ul.innerHTML = items.map(function(it){
      var rar = String(it.raridade || "comum").toLowerCase(); if(!RAR[rar]) rar = "comum";
      var nome = esc(it.nome || "Item sem nome");
      var det = it.descricao ? String(it.descricao) : "";
      if(det.length > 140) det = det.slice(0, 137) + "...";
      var qtd = (it.quantidade != null && it.quantidade > 1)
        ? '<span class="f-i-qtd">&times;' + (it.quantidade | 0) + '</span>' : '';
      var eq = it.equipado ? '<span class="f-i-eq">equipado</span>' : '';
      var linha = det ? '<div class="f-i-det">' + esc(det) + '</div>' : '';
      var tipo = it.tipo ? ' title="' + esc(it.tipo) + '"' : '';
      return '<li class="f-item" data-rar="' + rar + '"' + tipo + '>'
        + '<span class="f-i-ico">' + ICO + '</span>'
        + '<div class="f-i-corpo"><div class="f-i-top"><span class="f-i-nome">' + nome + '</span>'
        + qtd + eq + '</div>' + linha + '</div></li>';
    }).join("");
  };

  if(ficha){

    Array.prototype.slice.call(ficha.querySelectorAll(".f-atr")).forEach(function(b){
      b.addEventListener("click", function(){ b.classList.toggle("sel"); });
    });
    /* BLOCO 7: clique numa habilidade agora abre o detalhe (drill-down), nao alterna .sel */
    /* BLOCO 0 — troca das 5 abas da ficha */
    var fichaAbas = Array.prototype.slice.call(ficha.querySelectorAll(".ficha-aba"));
    var fichaPaineis = Array.prototype.slice.call(ficha.querySelectorAll(".ficha-aba-painel"));
    function trocarAba(nome){
      fichaAbas.forEach(function(b){
        var on = b.getAttribute("data-aba") === nome;
        b.classList.toggle("ativa", on);
        b.setAttribute("aria-selected", on ? "true" : "false");
      });
      fichaPaineis.forEach(function(p){
        p.classList.toggle("ativa", p.getAttribute("data-painel") === nome);
      });
      var fc = ficha.querySelector(".ficha-corpo");
      if(fc) fc.scrollTop = 0;
    }
    fichaAbas.forEach(function(b){
      b.addEventListener("click", function(){ trocarAba(b.getAttribute("data-aba")); });
      b.addEventListener("keydown", function(e){
        if(e.key === "Enter" || e.key === " " || e.key === "Spacebar"){ e.preventDefault(); trocarAba(b.getAttribute("data-aba")); }
      });
    });

    /* ============================================================
       BLOCO 7 — DRILL-DOWN (toque-pra-detalhar). Uma mecanica, 5 abas.
       DADOS [simulado] = forma real (shape de resposta do banco).
       Claude Code troca DETALHES[tipo][ref] por um fetch na fiacao.
       ============================================================ */
    (function(){
      var fd = document.getElementById("fichaDetalhe");
      if(!fd) return;
      var fdCorpo  = document.getElementById("fdCorpo");
      var fdTipo   = document.getElementById("fdTipo");
      var fdFundo  = document.getElementById("fdFundo");
      var fdVoltar = document.getElementById("fdVoltar");
      var origem = null;

      var ROTULO = { habilidade:"habilidade", item:"item", laco:"laço", pessoa:"pessoa",
        linhagem:"linhagem", criatura:"criatura", lugar:"lugar", lore:"saber",
        marco:"marco de vida", decisao:"decisão", tributo:"dívida viva" };

      var DETALHES = {
        linhagem: {
          "primeiro-sangue": { nome:"Primeiro sangue", sub:"linhagem · dormente",
            sobre:"Corre em você desde antes da memória. Até hoje não falou — nem pra ajudar, nem pra cobrar.",
            campos:[["estado","dormente"],["concede","nada utilizável enquanto dorme"],["o preço","o que não acordou ainda não pediu nada"],["de quem veio","ainda velado",true]] },
          "segundo-sangue": { nome:"Segundo sangue", sub:"linhagem · selado",
            sobre:"Alguém o trancou antes de você nascer. O lacre ainda segura — e quem o pôs não está por perto pra explicar.",
            campos:[["estado","selado"],["concede","o que daria, retém"],["o preço","já foi pago por você uma vez; o lacre é a dívida"],["quem selou","ainda velado",true]] },
          "terceiro-sangue": { nome:"Terceiro sangue", sub:"linhagem · latente",
            sobre:"O mais fundo dos três. Não dorme como o primeiro nem está preso como o segundo — espera.",
            campos:[["estado","latente"],["concede","nada gentil, quando vier"],["o preço","cobrado de uma vez no instante em que acordar"],["o que é","ainda velado",true]] }
        },
        habilidade: {
          "espada-arcana": { nome:"Espada Arcana", sub:"habilidade · Praticante",
            sobre:"Fio de mana correndo pela lâmina. Corta o que aço não corta — e exige a mão firme que você ainda não tem sempre.",
            campos:[["quem ensinou","ninguém. Despertou num susto; Elara só mostrou como não se cortar com ela"],["a sombra","mana mal-tecida volta como queimadura na própria mão"],["maestria","com domínio, o fio dobra o alcance do golpe — e dobra o que cobra"],["progresso","5 de 8 marcas pro próximo grau"]] },
          "estocada-precisa": { nome:"Estocada Precisa", sub:"habilidade · Aprendiz",
            sobre:"Um golpe só, no ponto certo, no instante certo. Quando entra, entra fundo.",
            campos:[["quem ensinou","ninguém. Tentativa e erro, osso e hematoma"],["a sombra","errar a janela deixa a guarda inteira aberta"],["maestria","no ponto exato, ignora parte da defesa do alvo"],["progresso","2 de 3 marcas pro próximo grau"]] },
          "tecer-mana": { nome:"Tecer Mana", sub:"habilidade · Veterano",
            sobre:"Puxar e organizar a mana antes de usá-la. A base de quase tudo que vem depois.",
            campos:[["quem ensinou","Elara, em parte. O resto você arrancou apanhando"],["a sombra","tecer rápido demais gasta o vigor antes da mana"],["maestria","o tear segura mais fios de uma vez"],["progresso","pronta pra avançar de grau"]] },
          "guarda-defensiva": { nome:"Guarda Defensiva", sub:"habilidade · adormecida",
            sobre:"Ainda não despertou. Sabe-se que existe em você — não como será quando acordar.",
            campos:[["quem ensinou","—"],["a sombra","—"],["maestria","não há o que cultivar antes do despertar"],["progresso","ainda não despertou"]] }
        },
        item: {
          "faca-de-mato": { nome:"Faca de mato", sub:"item · sempre à mão",
            sobre:"Gasta de uso, fio ainda firme. Serve mais pra corda e pão que pra briga — mas corta o que precisa." },
          "capa-de-la-encerada": { nome:"Capa de lã encerada", sub:"item · vestida",
            sobre:"Pesada da chuva do norte. Segura o frio e a água; em troca, pesa o dobro quando encharca." },
          "cantil-de-couro": { nome:"Cantil de couro", sub:"item · pela metade",
            sobre:"Couro velho, costura refeita mais de uma vez. Está na metade — e a próxima fonte de água não está marcada." },
          "racao-de-viagem": { nome:"Ração de viagem", sub:"item · três unidades",
            sobre:"Pão duro e carne seca. Não é bom, mas dura — e o que dura é o que importa na estrada." },
          "bolsa-surrada": { nome:"Bolsa surrada", sub:"item · no cinto",
            sobre:"Algumas moedas de cobre no fundo. Pouco pra comprar, o bastante pra não dormir com fome uma noite." },
          "pingente-de-prata": { nome:"Pingente de prata", sub:"item · você nunca o tira",
            sobre:"Herança sem brilho. De quem veio, ninguém na casa diz em voz alta — e você aprendeu a não perguntar.",
            campos:[["origem","não dita",true]] }
        },
        laco: {
          "elara": { nome:"Elara", sub:"laço · mãe",
            sobre:"Ensina você a conter o que transborda. Tem paciência de sobra — e respostas de menos.",
            campos:[["relação","mãe"],["o que dá","controle, e um aviso constante de que poder cobra"],["o que cala","sabe mais do que ensina"]] },
          "kael": { nome:"Kael", sub:"laço · pai",
            sobre:"O sobrenome que abre portas — e o peso de saber que muita gente come do que a família planta.",
            campos:[["relação","pai"],["o que dá","um nome com peso, pra bem e pra mal"],["o que cobra","que você seja à altura dele"]] },
          "torin": { nome:"Torin", sub:"laço · meio-irmão",
            sobre:"Respeito à distância. Uma tensão que nenhum dos dois nomeia — e que nenhum dos dois começou.",
            campos:[["relação","meio-irmão"],["entre vocês","uma rivalidade fria, sem causa declarada"]] },
          "serethan": { nome:"Serethan", sub:"laço · avô",
            sobre:"Aparece sempre nos momentos certos. Há um interesse dele por você que ninguém na casa sabe explicar.",
            campos:[["relação","avô (lado materno)"],["o que mostra","atenção, presentes, perguntas demais"],["o que esconde","a razão do interesse",true]] }
        },
        criatura: {
          "caes-de-vala": { nome:"Cães-de-Vala", sub:"criatura · Estrada do Norte",
            sobre:"Matilha magra que segue quem anda só. Não é criatura de pilar — é fome velha, e fome não recua fácil.",
            campos:[["fraqueza","fogo"],["como agem","cercam pela retaguarda, atacam em número"],["onde","Estrada do Norte, ao anoitecer"]] },
          "mariposa-de-sebo": { nome:"Mariposa-de-Sebo", sub:"criatura · Casa de Namiri",
            sobre:"Come a chama das velas e engorda no escuro. O perigo nunca foi ela — foi o escuro que ela deixa.",
            campos:[["fraqueza","luz forte"],["o risco real","apaga a luz e deixa você cego no quarto"],["onde","cantos da casa, perto das velas"]] }
        },
        lugar: {
          "namiri": { nome:"Namiri", sub:"lugar · Kethara · natal",
            sobre:"A cidade onde você nasceu, no norte de chuvas longas. Conhece as ruas de cor — e os silêncios da casa, melhor ainda.",
            campos:[["você sabe","cada rua, cada atalho, cada hora segura"],["o que pesa","os silêncios de casa dizem mais que as ruas"]] },
          "estrada-do-norte": { nome:"Estrada do Norte", sub:"lugar · Kethara · percorrida",
            sobre:"A linha de terra batida que liga Namiri ao resto. Você sabe onde ela é segura — e onde é melhor não parar.",
            campos:[["você sabe","os trechos seguros e os que não são"],["o perigo","matilha à noite; pouca gente pra ouvir um grito"]] }
        },
        lore: {
          "a-vigilia-quebrada": { nome:"A Vigília Quebrada", sub:"saber · era atual · ano 312",
            sobre:"O nome da era em que você nasceu. Algo se quebrou antes de você — e o mundo ainda conta os anos a partir da quebra, não do conserto.",
            campos:[["o que se sabe","a contagem começa na catástrofe, não numa fundação"],["o que falta","o que exatamente quebrou — e se dá pra consertar"]] },
          "os-cinco-pilares": { nome:"Os Cinco Pilares", sub:"saber · os cinco caminhos da força",
            sobre:"As cinco formas de a força do mundo passar por uma pessoa. Toda vocação nasce de um deles — e ninguém escolhe de graça por onde a força entra.",
            campos:[["os cinco","corpo, sombra, arcano, espírito, engenho"],["a regra","cada pilar dá de um jeito e cobra de outro"]] },
          "os-deuses-que-calaram": { nome:"Os deuses que calaram", sub:"saber · panteão em colapso",
            sobre:"Houve deuses. A maioria silenciou ou caiu. Reza-se mais por hábito que por resposta — e alguns nomes é melhor não dizer alto.",
            campos:[["o que restou","templos, hábitos, silêncio"],["o cuidado","certos nomes ainda respondem — e nem sempre bem",true]] }
        },
        pessoa: {
          "friede": { nome:"Friede", sub:"pessoa · Namiri · mais velha",
            sobre:"Uma das poucas mais velhas que reparou em você. Sabe coisas que não ensina de graça — e repara mais do que diz.",
            campos:[["onde","Namiri"],["o que oferece","conhecimento, por um preço"],["o que faz","observa mais do que comenta"]] }
        },
        marco: {
          "nascido-em-namiri": { nome:"Nascido em Namiri", sub:"marco · Único · o começo",
            sobre:"O começo de tudo. Segundo de quatro, numa casa onde o sobrenome pesa mais que o nome de quem o carrega.",
            campos:[["peso","Único"],["onde","Namiri, Kethara"],["o que ficou","a posição na casa — nem o primeiro, nem esquecido"]] },
          "a-anima-acordou": { nome:"A Ânima acordou", sub:"marco · Maior · infância",
            sobre:"Tua primeira habilidade não foi ensinada — foi arrancada de você num susto. A Ânima desperta assim: doendo antes de obedecer.",
            campos:[["peso","Maior"],["quando","infância, num susto"],["o que mudou","o poder deixou de ser ideia e virou peso real"]] },
          "elara-te-ensinou-a-conter": { nome:"Elara te ensinou a conter", sub:"marco · Significativo · infância",
            sobre:"Tua mãe te mostrou como segurar o que transborda. Menos um truque, mais um aviso: o que não se contém, se paga.",
            campos:[["peso","Significativo"],["quem","Elara, tua mãe"],["a lição","conter é mais barato que remediar"]] },
          "o-primeiro-inverno-que-voce-lembra": { nome:"O primeiro inverno que você lembra", sub:"marco · Menor · infância",
            sobre:"As chuvas longas do norte, batendo no telhado a noite inteira. Pequeno demais pra virar história — grande o bastante pra ter ficado.",
            campos:[["peso","Menor"],["onde","Namiri"],["por que ficou","a primeira lembrança que é só sua"]] }
        },
        decisao: {
          "d0": { nome:"A moeda na praça", sub:"decisão · praça de Namiri · infância",
            sobre:"Você achou uma moeda caída de alguém na praça. Ninguém viu cair, ninguém viu você. Você guardou.",
            campos:[["consequência","permanente"],["o que ficou","pequena demais pra alguém sentir falta — grande o bastante pra você nunca esquecer"],["o que foi","a primeira escolha que foi só sua"]] }
        },
        tributo: {
          "primeiro-tributo": { nome:"Primeiro tributo", sub:"dívida viva · permanente",
            sobre:"Algo em você cobrou antes de você entender o que era. A marca ficou — e não vai embora.",
            campos:[["natureza","permanente; não cura, não se paga de volta"],["o que cobrou","ainda não está claro — só a marca está",true],["o que resta","carregar"]] }
        }
      };

      function esc(t){ return String(t==null?"":t)
        .replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;"); }
      function slug(t){ return String(t==null?"":t).toLowerCase()
        .normalize("NFD").replace(/[\u0300-\u036f]/g,"")
        .replace(/[^a-z0-9]+/g,"-").replace(/^-+|-+$/g,""); }

      function render(d){
        var h = '<div class="fd-nome">' + esc(d.nome || "Sem nome") + '</div>';
        if(d.sub)   h += '<div class="fd-sub">' + esc(d.sub) + '</div>';
        if(d.sobre) h += '<p class="fd-txt">' + esc(d.sobre) + '</p>';
        if(d.campos && d.campos.length){
          d.campos.forEach(function(c, i){
            var cls = "fd-valor" + (c[2] ? " fd-velado" : "");
            var pri = (i === 0) ? " fd-primeiro" : "";
            h += '<div class="fd-campo' + pri + '"><span class="fd-rotulo">' + esc(c[0]) +
                 '</span><span class="' + cls + '">' + esc(c[1]) + '</span></div>';
          });
        }
        return h;
      }

      function abrir(tipo, ref, el){
        var grupo = DETALHES[tipo] || {};
        var d = grupo[ref] || null;
        fdTipo.textContent = ROTULO[tipo] || tipo;
        fdCorpo.innerHTML = d ? render(d)
          : '<div class="fd-nome">Sem registro</div><p class="fd-txt">Nada anotado aqui ainda.</p>';
        fdCorpo.scrollTop = 0;
        origem = el || null;
        if(origem) origem.classList.add("detalhe-ativo");
        fd.classList.add("aberto");
        fd.setAttribute("aria-hidden", "false");
        fdVoltar.focus();
      }
      function fechar(){
        fd.classList.remove("aberto");
        fd.setAttribute("aria-hidden", "true");
        if(origem){ origem.classList.remove("detalhe-ativo"); try{ origem.focus(); }catch(e){} origem = null; }
      }

      /* --- init: marcar as listas com o tipo --- */
      function marcaLista(sel, tipo){
        Array.prototype.slice.call(ficha.querySelectorAll(sel)).forEach(function(l){
          l.setAttribute("data-detalhe-grupo", tipo);
        });
      }
      marcaLista(".p-linhagens", "linhagem");
      marcaLista(".f-anima", "habilidade");
      marcaLista(".f-inv", "item");
      marcaLista(".l-lacos", "laco");
      marcaLista(".jor-lista", "marco");
      marcaLista(".led-lista", "decisao");
      marcaLista(".a-divida", "tributo");

      /* codice: 4 .cod-lista identicas -> tipo pelo titulo do bloco-pai */
      Array.prototype.slice.call(ficha.querySelectorAll('[data-painel="codice"] .p-bloco')).forEach(function(bloco){
        var titEl = bloco.querySelector(".p-tit"); if(!titEl) return;
        var t = titEl.textContent.toLowerCase(), tipo = null;
        if(t.indexOf("bestiario") >= 0 || t.indexOf("besti\u00e1rio") >= 0) tipo = "criatura";
        else if(t.indexOf("lugares") >= 0) tipo = "lugar";
        else if(t.indexOf("lore") >= 0) tipo = "lore";
        else if(t.indexOf("pessoas") >= 0) tipo = "pessoa";
        var lista = bloco.querySelector(".cod-lista");
        if(tipo && lista) lista.setAttribute("data-detalhe-grupo", tipo);
      });

      /* --- init: tornar os itens clicaveis (velados ficam de fora) --- */
      var SEL_ITEM = {
        linhagem:".p-linhagem", habilidade:".f-hab", item:".f-item", laco:".l-laco",
        criatura:".cod-item:not(.velado)", lugar:".cod-item:not(.velado)",
        lore:".cod-item:not(.velado)", pessoa:".cod-item:not(.velado)",
        marco:".jor-marco:not(.velado)", decisao:".led-item", tributo:".a-cic"
      };
      Array.prototype.slice.call(ficha.querySelectorAll("[data-detalhe-grupo]")).forEach(function(grupo){
        var tipo = grupo.getAttribute("data-detalhe-grupo");
        var sel = SEL_ITEM[tipo]; if(!sel) return;
        Array.prototype.slice.call(grupo.querySelectorAll(sel)).forEach(function(item){
          item.classList.add("tem-detalhe");
          item.setAttribute("role", "button");
          item.setAttribute("tabindex", "0");
        });
      });

      /* ref do item: data-hab pronto, senao slug do nome, decisao por indice */
      function refDo(item, tipo){
        var dh = item.getAttribute("data-hab"); if(dh) return dh;
        if(tipo === "decisao"){
          var pai = item.parentNode;
          return "d" + Array.prototype.indexOf.call(pai.children, item);
        }
        var nomeEl = item.querySelector(".cod-nome, .f-h-nome, .l-nome, .f-i-nome, .jor-nome, b");
        return nomeEl ? slug(nomeEl.textContent) : null;
      }

      function disparar(item){
        var grupo = item.closest("[data-detalhe-grupo]"); if(!grupo) return;
        var tipo = grupo.getAttribute("data-detalhe-grupo");
        abrir(tipo, refDo(item, tipo), item);
      }

      /* --- delegacao: um listener cobre todas as abas --- */
      ficha.addEventListener("click", function(e){
        if(!e.target || !e.target.closest) return;
        var item = e.target.closest(".tem-detalhe");
        if(item && ficha.contains(item)) disparar(item);
      });
      ficha.addEventListener("keydown", function(e){
        if(e.key !== "Enter" && e.key !== " " && e.key !== "Spacebar") return;
        if(!e.target || !e.target.closest) return;
        var item = e.target.closest(".tem-detalhe");
        if(item && ficha.contains(item)){ e.preventDefault(); disparar(item); }
      });
      fdFundo.addEventListener("click", fechar);
      fdVoltar.addEventListener("click", fechar);

      /* Esc fecha o detalhe ANTES da ficha (capture + stopImmediatePropagation) */
      document.addEventListener("keydown", function(e){
        if(e.key === "Escape" && fd.classList.contains("aberto")){
          fechar();
          e.stopImmediatePropagation();
        }
      }, true);
    })();
  
  }
})();
"""
