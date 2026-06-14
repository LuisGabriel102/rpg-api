"""Tema visual compartilhado da Oficina: CSS vitral (listas) e pergaminho (detalhes) + tokens de cor."""

CSS_VITRAL = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=IM+Fell+English:ital@0;1&family=IM+Fell+English+SC&family=Spectral:ital@0;1&display=swap" rel="stylesheet">
<style>
.q-layout,.q-page-container,.q-page{width:100%!important;max-width:none!important;}
.nicegui-content{width:100%!important;max-width:none!important;padding:0!important;gap:0!important;align-items:stretch!important;}
body{margin:0;}
.gp-screen{position:relative;font-family:'Spectral',Georgia,serif;color:#e8dcc0;min-height:100vh;width:100%;background:linear-gradient(180deg,#0a0d1a 0%,#10141f 50%,#13161f 100%);box-sizing:border-box;}
.gp-inner{max-width:1180px;margin:0 auto;padding:26px 28px 40px;}
.gp-rule{height:1px;width:100%;background:linear-gradient(90deg,#5c4413,#c9a227 40%,transparent);margin:16px 0 22px;border:none;}
.gp-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px;}
.criatura-card{background:#0c0e16!important;border:1px solid #b8902f!important;border-radius:5px!important;box-shadow:inset 0 1px 0 rgba(255,238,190,.14);transition:border-color .25s,transform .2s;cursor:pointer;overflow:hidden;}
.criatura-card:hover{border-color:#f0d98a!important;transform:translateY(-2px);}
.bestiario-title{font-family:'IM Fell English',serif!important;letter-spacing:.5px;color:#f3e7c4!important;}
.bestiario-body{font-family:'Spectral',Georgia,serif!important;line-height:1.5;color:#c0a36a!important;}
.gp-filtros{background:rgba(12,14,22,.72)!important;border:1px solid #5c4413!important;border-radius:5px!important;box-shadow:inset 0 1px 0 rgba(255,238,190,.10)!important;}
.gp-filtros .q-field__control{background:rgba(10,11,17,.55)!important;border-radius:4px;font-family:'Spectral',Georgia,serif;}
.gp-filtros .q-field--outlined .q-field__control:before{border:1px solid #6e561f!important;}
.gp-filtros .q-field--outlined .q-field__control:hover:before{border-color:#b8902f!important;}
.gp-filtros .q-field--outlined .q-field__control:after{border-color:#c9a227!important;}
.gp-filtros .q-field__native,.gp-filtros .q-field__input,.gp-filtros .q-field__native span{color:#e8dcc0!important;font-family:'Spectral',Georgia,serif;}
.gp-filtros .q-field__label{color:#9a8a5a!important;font-family:'Spectral',Georgia,serif;}
.gp-filtros .q-icon,.gp-filtros .q-select__dropdown-icon{color:#b8902f!important;}
.gp-filtros .q-field__native::placeholder{color:#7a6f55!important;}
.q-menu{background:#0c0e16!important;border:1px solid #6e561f!important;color:#e8dcc0!important;}
.q-menu .q-item{color:#d8cba8!important;font-family:'Spectral',Georgia,serif;}
.q-menu .q-item:hover,.q-menu .q-item--active,.q-menu .q-item.q-manual-focusable--focused{background:rgba(184,144,47,.18)!important;color:#f3e7c4!important;}
</style>
"""


CSS_PERGAMINHO = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=Crimson+Text:ital,wght@0,400;0,600;1,400&display=swap');
.bestiario-title { font-family:'Cinzel',serif !important; letter-spacing:2px; }
.bestiario-body  { font-family:'Crimson Text',Georgia,serif !important; line-height:1.7; color:#2a1c0e; }
.section-header {
    font-family:'Cinzel',serif !important; font-size:12px; font-weight:600;
    letter-spacing:3px; text-transform:uppercase; color:#58180d;
    border-bottom:1px solid rgba(88,24,13,0.25); padding-bottom:8px; margin-bottom:12px;
}
.epigrafe-box {
    border-left:2px solid #922610; padding:12px 16px;
    background:rgba(146,38,16,0.05);
    font-family:'Crimson Text',Georgia,serif !important; font-style:italic; color:#5a4632;
}
.weakness-box {
    background:#f6ead0; border:1px solid rgba(88,24,13,0.22);
    border-radius:3px; padding:14px 16px;
}
.eco-row { display:flex; gap:12px; padding:6px 0; border-bottom:1px solid rgba(88,24,13,0.1); }
.eco-label {
    font-family:'Cinzel',serif !important; font-size:11px; color:#58180d;
    letter-spacing:1px; text-transform:uppercase; min-width:90px;
}
.tag-pill {
    font-family:'Cinzel',serif !important; font-size:10px; letter-spacing:1.5px;
    text-transform:uppercase; padding:3px 10px;
    border:1px solid rgba(88,24,13,0.35); border-radius:2px; color:#6e2410;
}
</style>
"""


# Tokens de cor — pras telas futuras nao hardcodar hex.
VIT = {
    "bg_top": "#0a0d1a", "bg_mid": "#10141f", "bg_bot": "#13161f",
    "ouro": "#b8902f", "ouro_claro": "#c9a227", "ouro_brilho": "#e8c66a", "ouro_max": "#f0d98a",
    "texto": "#e8dcc0", "titulo": "#f3e7c4", "titulo_claro": "#f6ecd2",
    "secundario": "#c0a36a", "secundario_fraco": "#9a8a5a",
    "borda": "#b8902f", "borda_hover": "#f0d98a", "card_bg": "#0c0e16",
}
PERG = {
    "folha": "#fdf1dc", "caixa": "#f6ead0", "pagina": "#efe3c9",
    "arte_bg": "#efe2c4", "rodape": "#e6d8ba",
    "tijolo": "#58180d", "tijolo_regua": "#922610", "tijolo_pill": "#6e2410",
    "texto": "#2a1c0e", "texto_folha": "#1d1107",
    "secundario": "#5a4632", "rodape_id": "#7a6648",
}
