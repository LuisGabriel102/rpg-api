"""
Bloco 3 da migracao de storage R2 -> banco (SPEC gravura/imagem-mae).

One-shot: le cada imagem CANONICA que ainda mora no R2 (npc_imagens com
status='canonica', imagem_bytes IS NULL, url http) e grava os bytes no banco
(imagem_bytes + imagem_mime), virando a url para a rota interna
'/npc-imagem/<id>' e sincronizando o ponteiro npcs.imagem_url do NPC dono
NA MESMA transacao por linha.

Garantias:
- IDEMPOTENTE: o UPDATE tem guard "AND imagem_bytes IS NULL" — rodar 2x nao
  re-migra nem sobrescreve; a segunda rodada pula tudo.
- NAO-DESTRUTIVO: nao deleta nada do R2 (isso e o Bloco 5), preserva r2_key
  como historico, nao toca linhas que ja sao '/npc-imagem/'.
- FALHA ISOLADA: download que falhar e LOGADO e o lote segue; nada de bytes
  vazios ou mime chutado gravados no banco.

Rodar: .venv\\Scripts\\python.exe scripts\\migrar_imagens_r2_para_banco.py
"""

import os

import httpx
import psycopg
from dotenv import load_dotenv

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(RAIZ, ".env"))

TIMEOUT_S = 30

_MIME_POR_EXTENSAO = {
    "webp": "image/webp",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
}


def detectar_mime(corpo: bytes, url: str) -> "str | None":
    """PURO: mime pelos magic bytes (fonte de verdade); extensao da url como
    fallback. None = formato desconhecido -> a linha NAO migra (nao chuta)."""
    if corpo[:4] == b"RIFF" and corpo[8:12] == b"WEBP":
        return "image/webp"
    if corpo[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if corpo[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    extensao = url.rsplit(".", 1)[-1].lower() if "." in url.rsplit("/", 1)[-1] else ""
    return _MIME_POR_EXTENSAO.get(extensao)


def migrar_linha(conn, client, imagem_id: int, npc_id: int, url: str):
    """Migra UMA canonica. Retorna (status, detalhe) com status em
    {'migrada', 'pulada', 'falha'}. Banco so e tocado se o download e o mime
    estiverem integros; imagem + ponteiro do NPC dono na MESMA transacao."""
    resposta = client.get(url)
    if resposta.status_code != 200:
        return ("falha", f"HTTP {resposta.status_code} no download")
    corpo = resposta.content
    if not corpo:
        return ("falha", "download com corpo vazio")
    mime = detectar_mime(corpo, url)
    if mime is None:
        return ("falha", "formato de imagem desconhecido (magic bytes + extensao)")

    with conn.transaction():
        cur = conn.execute(
            "UPDATE npc_imagens "
            "SET imagem_bytes = %s, imagem_mime = %s, url = '/npc-imagem/' || id "
            "WHERE id = %s AND imagem_bytes IS NULL",
            (corpo, mime, imagem_id),
        )
        if cur.rowcount == 0:
            # guard de idempotencia: alguem ja gravou bytes nessa linha
            return ("pulada", "guard: imagem_bytes ja preenchido")
        conn.execute(
            "UPDATE npcs SET imagem_url = %s WHERE id = %s",
            (f"/npc-imagem/{imagem_id}", npc_id),
        )
    return ("migrada", f"{len(corpo)} bytes, {mime}")


def main() -> None:
    # autocommit no nivel da conexao + conn.transaction() por linha =
    # cada canonica commita sozinha; uma falha nao segura lock do lote.
    conn = psycopg.connect(os.environ["DATABASE_URL"], autocommit=True)
    try:
        cur = conn.execute(
            "SELECT id, npc_id, url, (imagem_bytes IS NOT NULL) "
            "FROM npc_imagens WHERE status = 'canonica' ORDER BY id"
        )
        canonicas = cur.fetchall()

        migradas, puladas, falhas = [], [], []
        with httpx.Client(timeout=TIMEOUT_S) as client:
            for imagem_id, npc_id, url, tem_bytes in canonicas:
                if url.startswith("/npc-imagem/") or tem_bytes:
                    puladas.append((imagem_id, "ja no banco"))
                    continue
                if not url.startswith("http"):
                    falhas.append((imagem_id, f"url inesperada: {url!r}"))
                    continue
                try:
                    status, detalhe = migrar_linha(conn, client, imagem_id, npc_id, url)
                except Exception as exc:  # download/transacao: loga e segue
                    falhas.append((imagem_id, repr(exc)))
                    continue
                if status == "migrada":
                    migradas.append((imagem_id, detalhe))
                    print(f"  migrada  id={imagem_id} npc={npc_id} ({detalhe})")
                elif status == "pulada":
                    puladas.append((imagem_id, detalhe))
                else:
                    falhas.append((imagem_id, detalhe))
                    print(f"  FALHA    id={imagem_id} npc={npc_id}: {detalhe}")

        print("\n=== RELATORIO ===")
        print(f"migradas: {len(migradas)}")
        print(f"puladas (ja no banco): {len(puladas)}")
        print(f"falhas: {len(falhas)}")
        for imagem_id, motivo in falhas:
            print(f"  - id={imagem_id}: {motivo}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
