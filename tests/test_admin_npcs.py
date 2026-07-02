# -*- coding: utf-8 -*-
"""
Central de Admin — Aba NPCs (Onda 1): testes PUROS, sem banco/UI/R2.

Cobre os helpers testaveis de pages/admin_npcs.py:
  - _validar_upload: gate de tipo/tamanho ANTES do R2
  - _dot_status: bolinha verde (tem imagem-mae) / vermelha (sem retrato)
  - _r2_key_da_url: key R2 = ultimo segmento da URL publica
  - dossie (Onda 1): parentesco, cores por tipo/status, intensidade dominante,
    chips/linhas do 'Quem e', consolidacao de vinculos (simetrico/assimetrico)

A transacao definir_como_mae NAO tem teste puro (decisao Gabriel): a seguranca
dela vem do indice unico parcial no banco + post-check em codigo + o teste vivo
com a Elara. Import do modulo nao exige credencial R2 (import lazy no handler).
"""
from pages.admin_npcs import (
    _MAX_UPLOAD_MB,
    _chips_identidade,
    _consolidar_vinculos,
    _cor_status_parente,
    _cor_tipo_vinculo,
    _dot_status,
    _intensidade_dominante,
    _legenda_mae,
    _linhas_perfil,
    _nome_outro_lado,
    _normalizar_chip,
    _r2_key_da_url,
    _rotulo_parentesco,
    _rotulo_tipo_vinculo,
    _subtitulo_familia,
    _validar_upload,
)


# ── _validar_upload ─────────────────────────────────────────────────────────

def test_upload_jpeg_png_webp_passam():
    for ct in ("image/jpeg", "image/png", "image/webp"):
        assert _validar_upload(ct, 1024) is None


def test_upload_content_type_maiusculo_passa():
    # navegadores variam a caixa; o gate normaliza
    assert _validar_upload("IMAGE/JPEG", 1024) is None


def test_upload_tipo_errado_rejeita():
    assert _validar_upload("image/gif", 1024) is not None
    assert _validar_upload("application/pdf", 1024) is not None
    assert _validar_upload("application/octet-stream", 1024) is not None


def test_upload_sem_content_type_rejeita():
    assert _validar_upload(None, 1024) is not None
    assert _validar_upload("", 1024) is not None


def test_upload_vazio_rejeita():
    assert _validar_upload("image/png", 0) is not None


def test_upload_acima_do_teto_rejeita():
    teto = _MAX_UPLOAD_MB * 1024 * 1024
    assert _validar_upload("image/png", teto) is None          # exatamente no teto: passa
    assert _validar_upload("image/png", teto + 1) is not None  # 1 byte acima: rejeita


# ── _dot_status ─────────────────────────────────────────────────────────────

def test_dot_verde_quando_tem_mae():
    cor, rotulo = _dot_status(True)
    assert cor == "#22c55e"
    assert "imagem-mãe" in rotulo


def test_dot_vermelho_quando_sem_retrato():
    cor, rotulo = _dot_status(False)
    assert cor == "#ef4444"
    assert "sem retrato" in rotulo


# ── _r2_key_da_url ──────────────────────────────────────────────────────────

def test_r2_key_e_o_ultimo_segmento():
    assert _r2_key_da_url(
        "https://imagens.luisgabriel.uk/npc_41_2026-07-01_20-00-00-123_a1b2c3.webp"
    ) == "npc_41_2026-07-01_20-00-00-123_a1b2c3.webp"


def test_r2_key_url_vazia_nao_quebra():
    assert _r2_key_da_url("") == ""
    assert _r2_key_da_url(None) == ""


# ── _legenda_mae (Bloco 2: nome do NPC, nao id/arquivo cru) ────────────────

def test_legenda_mae_usa_nome_do_npc():
    assert _legenda_mae("Elara", 41) == "Elara · canônica"


def test_legenda_mae_sem_nome_cai_no_id():
    assert _legenda_mae(None, 77) == "NPC #77 · canônica"
    assert _legenda_mae("", 77) == "NPC #77 · canônica"


# ── dossiê: _rotulo_parentesco ──────────────────────────────────────────────

def test_parentesco_mapeados():
    assert _rotulo_parentesco("filho_mae") == "mãe"
    assert _rotulo_parentesco("filho_pai") == "pai"
    assert _rotulo_parentesco("conjuges") == "cônjuge"
    assert _rotulo_parentesco("irmaos") == "irmão(ã)"


def test_parentesco_mae_filho_resolve_pelo_sexo():
    assert _rotulo_parentesco("mae_filho", "masculino") == "filho"
    assert _rotulo_parentesco("mae_filho", "feminino") == "filha"
    assert _rotulo_parentesco("mae_filho", None) == "filho(a)"  # nao inventa


def test_parentesco_desconhecido_fica_cru():
    assert _rotulo_parentesco("primo_distante") == "primo_distante"


# ── dossiê: cores ───────────────────────────────────────────────────────────

def test_cor_tipo_vinculo_mapa_e_fallback():
    # mapa completo (13 DISTINCT do banco, escolha b do Op em 2026-07-02)
    assert _cor_tipo_vinculo("amor") == "#d15b74"
    assert _cor_tipo_vinculo("lealdade") == "#c9a45c"
    assert _cor_tipo_vinculo("respeito") == "#8a93b0"
    assert _cor_tipo_vinculo("neutro") == "#8a8a8a"
    assert _cor_tipo_vinculo("manipulacao") == "#a678d4"
    assert _cor_tipo_vinculo("AMIZADE") == "#6bb06b"      # case-insensitive
    assert _cor_tipo_vinculo("obsessao") == "#b8934a"     # fora do mapa
    assert _cor_tipo_vinculo(None) == "#b8934a"           # NULL nao quebra


def test_rotulo_tipo_vinculo_acentos_e_fallback():
    # so 3 ganham acento; conhecidos ficam como estao; futuro capitaliza
    assert _rotulo_tipo_vinculo("manipulacao") == "manipulação"
    assert _rotulo_tipo_vinculo("protecao") == "proteção"
    assert _rotulo_tipo_vinculo("divida") == "dívida"
    assert _rotulo_tipo_vinculo("respeito") == "respeito"
    assert _rotulo_tipo_vinculo("lealdade") == "lealdade"
    assert _rotulo_tipo_vinculo("obsessao") == "Obsessao"  # fora do mapa
    assert _rotulo_tipo_vinculo(None) == ""                # NULL nao quebra


def test_cor_status_parente():
    assert _cor_status_parente("vivo") == "#6bb06b"
    assert _cor_status_parente("morto") == "#8a8a8a"
    assert _cor_status_parente(None) == "#8a8a8a"


# ── dossiê: _intensidade_dominante ──────────────────────────────────────────

def test_intensidade_dominante_pega_a_maior():
    v = {"confianca": 90, "afeicao": 98, "respeito": 80, "medo": 15}
    assert _intensidade_dominante(v) == ("afeição", 98)


def test_intensidade_dominante_ignora_null():
    v = {"confianca": None, "afeicao": None, "respeito": None, "medo": 70}
    assert _intensidade_dominante(v) == ("medo", 70)


def test_intensidade_dominante_tudo_null_vira_none():
    assert _intensidade_dominante({}) is None
    assert _intensidade_dominante(
        {"confianca": None, "afeicao": None, "respeito": None, "medo": None}
    ) is None


# ── dossiê: _subtitulo_familia ──────────────────────────────────────────────

def test_subtitulo_familia_todos_vivos():
    assert _subtitulo_familia([{"status_parente": "vivo"}] * 3) == "3 · todos vivos"


def test_subtitulo_familia_conta_mortos():
    parentes = [{"status_parente": "vivo"}] * 3 + [{"status_parente": "morto"}]
    assert _subtitulo_familia(parentes) == "4 · 3 vivo(s), 1 morto(s)"


# ── dossiê: chips + perfil (regra de ouro: vazio nao entra) ─────────────────

def test_chips_identidade_so_preenchidos():
    chips = _chips_identidade({
        "raca": "velmenor", "idade_aparente": 45,
        "localizacao_atual": "A Cátedra, Namiri",
        "facoes": ["Clã Varekhor"], "arc_phase": "stable",
    })
    assert chips == ["velmenor", "45 anos", "A Cátedra, Namiri",
                     "Clã Varekhor", "arco stable"]


def test_chips_identidade_npc_pelado_vira_vazio():
    assert _chips_identidade({}) == []


def test_normalizar_chip_colide_local_e_faccao():
    # a regra fechada pelo dado real da Elara
    assert _normalizar_chip("A Cátedra, Namiri") == _normalizar_chip("Cátedra de Namiri")
    assert _normalizar_chip("Clã Varekhor") != _normalizar_chip("Cátedra de Namiri")
    assert _normalizar_chip("") == ""


def test_chips_dedupe_local_vence_faccao_homonima():
    chips = _chips_identidade({
        "localizacao_atual": "A Cátedra, Namiri",
        "facoes": ["Clã Varekhor", "Cátedra de Namiri"],
    })
    # identidade antes de facção; Clã Varekhor (distinto) sobrevive
    assert chips == ["A Cátedra, Namiri", "Clã Varekhor"]


def test_chips_dedupe_nao_apaga_distintos():
    chips = _chips_identidade({
        "localizacao_atual": "Namiri",
        "facoes": ["Clã Varekhor", "Cátedra de Namiri"],
    })
    assert chips == ["Namiri", "Clã Varekhor", "Cátedra de Namiri"]


def test_linhas_perfil_pula_vazios():
    linhas = _linhas_perfil({
        "medo_principal": "perder o controle",
        "abertura": 65,
        "valores": ["a família"],
    })
    assert [r for r, _ in linhas] == ["medo principal", "Big Five", "valores"]
    assert ("Big Five", "abertura 65") in linhas


def test_linhas_perfil_npc_pelado_vira_vazio():
    assert _linhas_perfil({}) == []


# ── dossiê: vínculos (nome do outro lado + consolidacao) ────────────────────

def test_nome_outro_lado():
    assert _nome_outro_lado({"nome_outro": "Kael"}) == "Kael"
    assert _nome_outro_lado({"personagem_alvo_id": 1}) == "Protagonista"
    # alvo duplo-NULL (dado quebrado) nao estoura
    assert _nome_outro_lado({"nome_outro": None, "personagem_alvo_id": None}) \
        == "(sem alvo)"


def test_consolidar_simetrico_vira_uma_linha_sem_direcao():
    ida = {"nome_outro": "Irina", "tipo": "amor", "eh_origem": True, "afeicao": 90}
    volta = {"nome_outro": "Irina", "tipo": "amor", "eh_origem": False, "afeicao": 80}
    linhas = _consolidar_vinculos([ida, volta])
    assert len(linhas) == 1
    assert linhas[0]["direcao"] is None
    assert linhas[0]["intensidade"] == ("afeição", 90)  # perspectiva da origem


def test_consolidar_assimetrico_mostra_os_dois_lados():
    # witcher-grey (caso real: Serethan, o pai): ela dá familiar, recebe
    # manipulacao — os dois lados aparecem, nao suaviza
    da = {"nome_outro": "Serethan", "tipo": "familiar", "eh_origem": True}
    recebe = {"nome_outro": "Serethan", "tipo": "manipulacao", "eh_origem": False}
    linhas = _consolidar_vinculos([da, recebe])
    assert len(linhas) == 2
    assert (linhas[0]["direcao"], linhas[1]["direcao"]) == ("dá", "recebe")
    assert (linhas[0]["tipo"], linhas[1]["tipo"]) == ("familiar", "manipulacao")


def test_consolidar_protagonista_leva_nota():
    v = {"nome_outro": None, "personagem_alvo_id": 1, "tipo": "amor",
         "eh_origem": True, "afeicao": 98,
         "historia_com_protagonista": "Se viu nele desde o nascimento."}
    linhas = _consolidar_vinculos([v])
    assert linhas[0]["nome"] == "Protagonista"
    assert linhas[0]["nota"] == "Se viu nele desde o nascimento."
    assert linhas[0]["intensidade"] == ("afeição", 98)


def test_consolidar_vazio_nao_quebra():
    assert _consolidar_vinculos([]) == []


# ── _descartar_candidata (Fusao Atelie->Central, Fatia 1) ───────────────────
# Sem banco: _conectar e trocado por uma conexao falsa. O que se prova aqui:
# (1) o SQL leva o guard "status <> 'canonica'" — descarte nunca apaga a mae;
# (2) RETURNING vazio -> False (canonica/inexistente), linha -> True;
# (3) a conexao fecha nos dois caminhos.

import asyncio

import pages.admin_npcs as admin_npcs


class _ConexaoFalsa:
    def __init__(self, row):
        self._row = row
        self.sql = None
        self.fechada = False

    async def fetchrow(self, sql, *args):
        self.sql = sql
        return self._row

    async def close(self):
        self.fechada = True


def _com_conexao_falsa(monkeypatch, row):
    conn = _ConexaoFalsa(row)

    async def _conectar_falso():
        return conn

    monkeypatch.setattr(admin_npcs, "_conectar", _conectar_falso)
    return conn


def test_descartar_deleta_nao_canonica(monkeypatch):
    conn = _com_conexao_falsa(monkeypatch, row={"id": 7})
    assert asyncio.run(admin_npcs._descartar_candidata(7)) is True
    assert conn.fechada


def test_descartar_guard_no_sql_barra_canonica(monkeypatch):
    conn = _com_conexao_falsa(monkeypatch, row={"id": 7})
    asyncio.run(admin_npcs._descartar_candidata(7))
    assert "status <> 'canonica'" in conn.sql
    assert "DELETE FROM npc_imagens" in conn.sql


def test_descartar_zero_linhas_retorna_false(monkeypatch):
    # canonica (guard barrou) ou id inexistente: RETURNING vazio -> False
    conn = _com_conexao_falsa(monkeypatch, row=None)
    assert asyncio.run(admin_npcs._descartar_candidata(999999)) is False
    assert conn.fechada

