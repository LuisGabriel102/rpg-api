#!/usr/bin/env python3
"""
Backfill de embeddings do Alderyn — knowledge_fragments (vector(1536)).
=======================================================================

>>> AVISO PARA QUEM FOR RELIGAR O query_vec NO jogo.py <<<
>>> Este script INDEXA com input_type="search_document". A BUSCA tem que usar
>>> input_type="search_query" — sao espacos vetoriais diferentes, de proposito.
>>> Usar o MESMO valor nos dois lados quebra o retrieval SEM DAR ERRO NENHUM.

O QUE ESTE SCRIPT FAZ
  Pega cada linha que tem texto mas ainda NAO tem embedding, gera o vetor no
  Amazon Bedrock (cohere.embed-v4:0, 1536 dimensoes nativas) e grava na coluna
  `embedding`. E o que acende a busca semantica que hoje esta desligada —
  `query_vec=None` esta fixo no jogo.py porque nao havia vetor nenhum no banco.

POR QUE cohere.embed-v4:0 E NAO UM TITAN
  A coluna e `vector(1536)`, medida no banco. O Titan V2 devolve 256/512/1024:
  nenhum bate. O Titan G1 devolve 1536 mas e legacy — divida no dia um. O Cohere
  v4 entrega 1536 nativo, sem truncar nem repadear, entao o schema nao muda.

POR QUE O TEXTO E `titulo` + duas quebras de linha + `conteudo`
  `titulo` tem cobertura 501/501 e carrega o assunto de forma condensada — ajuda
  o vetor a ancorar o tema. `conteudo_narrador` foi DELIBERADAMENTE deixado de
  fora: so 91 de 501 linhas o tem (18%). Campo com cobertura parcial cria vies
  de retrieval — as 91 linhas ficariam com texto muito maior que as 410, e o
  volume de texto afeta a norma do vetor. Elas passariam a aparecer mais por
  artefato de tamanho, nao por relevancia. Um campo ou entra para todos, ou nao
  entra.

A TRAVA N1, HERDADA DO gerar_embeddings_alderyn.py
  Indexar e consultar TEM que sair do MESMO modelo. Quando o `query_vec` for
  religado no jogo.py, ele precisa usar cohere.embed-v4:0 a 1536 com
  input_type="search_query". Misturar modelos nao da erro: so transforma a
  busca vetorial em ruido silencioso, que e muito pior que uma excecao.

  Por isso as 3 tabelas de vector(768) — world_facts, eventos_canonicos,
  personagem_decisoes — ficam FORA deste script. Elas sao outro espaco
  semantico, populado por sentence-transformers local. Nao se misturam.

SEGURANCA — o resumo de tudo que esta travado aqui dentro:
  * --dry-run e o DEFAULT. Escrever exige --execute digitado.
  * --limit 5 quando --execute. As 501 exigem --limit 501 explicito.
  * vetor com dimensao != 1536 aborta a linha. Nunca trunca, nunca zera.
  * idempotente por `WHERE embedding IS NULL`. Nao existe --force.
  * commit a cada 10 linhas, nao no fim.
  * credencial nunca e impressa, nem em log de erro.

USO
  # 1. ensaio, nao gasta nada e nao precisa de AWS:
  python infra/aws/backfill_embeddings.py

  # 2. cobaia de 5 linhas de verdade:
  export AWS_ACCESS_KEY_ID=...  AWS_SECRET_ACCESS_KEY=...  AWS_DEFAULT_REGION=us-east-1
  python infra/aws/backfill_embeddings.py --execute

  # 3. a carga inteira, depois que a cobaia estiver conferida:
  python infra/aws/backfill_embeddings.py --execute --limit 501
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
import time

# ---------------------------------------------------------------------------
# Constantes de desenho
# ---------------------------------------------------------------------------

MODELO_ID = "cohere.embed-v4:0"

# A coluna e vector(1536). Este numero nao e preferencia: e o contrato do
# schema. Se um dia mudar, muda no banco primeiro e aqui depois.
# Conferido na doc oficial: output_dimension aceita 256|512|1024|1536, e 1536 e
# o default. Mandamos explicito de qualquer forma — ver o corpo da chamada.
DIMENSAO_ESPERADA = 1536

# ===========================================================================
# input_type — O PAR DE VALORES QUE NAO PODE SER TROCADO
#
# Estas duas constantes existem porque o valor NAO E ARBITRARIO e NAO E O MESMO
# nos dois lados do sistema. O Cohere Embed adiciona tokens especiais conforme o
# input_type e, com isso, projeta o vetor num espaco DIFERENTE para documento e
# para pergunta. O modelo e assimetrico de proposito: e assim que "qual e a
# natureza do Fiador?" fica perto do paragrafo que responde isso, em vez de ficar
# perto de outras perguntas.
#
#   INDEXACAO -> search_document -> usado AQUI, ao gravar os 501 vetores
#   BUSCA     -> search_query    -> usado no jogo.py, ao vetorizar a pergunta
#
# TROCAR OU IGUALAR OS DOIS NAO GERA ERRO NENHUM. A API aceita, o Postgres
# aceita, o indice funciona, e o retrieval simplesmente fica ruim — de um jeito
# que ninguem percebe olhando log, porque nao ha log. E por isso que o valor
# mora numa constante nomeada e comentada, e nao solto no meio do json.dumps.
#
# Conferido na doc oficial da AWS (nao de memoria): input_type e OBRIGATORIO no
# cohere.embed-v4:0 e aceita exatamente search_document, search_query,
# classification e clustering. Nao existe default — omitir e erro de validacao.
INPUT_TYPE_INDEXACAO = "search_document"
INPUT_TYPE_BUSCA = "search_query"  # nao usado aqui; documentado para o jogo.py
# ===========================================================================

# POR QUE "RIGHT" e nao "END": na doc do Embed **v4** os valores aceitos sao
# NONE | LEFT | RIGHT. "END" e da familia v3 (NONE|START|END) e seria recusado
# com ValidationException — que o retry deste script, corretamente, NAO repete.
# RIGHT descarta tokens do fim, que e o comportamento pretendido: preservar o
# comeco do texto, onde mora o titulo.
TRUNCATE = "RIGHT"

# POR QUE 10, e por que o MESMO numero serve para o lote da API e para o commit:
# a Cohere aceita ate 96 textos por chamada, entao 10 e folgado do lado da API.
# O que manda no numero e o outro lado: alinhar lote-de-API com lote-de-commit
# significa que uma queda no meio perde, no maximo, uma chamada em voo. Se os
# dois numeros fossem diferentes, existiria uma janela em que a API ja cobrou
# vetores que o banco ainda nao gravou — dinheiro gasto sem resultado.
TAMANHO_LOTE = 10

# POR QUE 5 e o default do --limit no modo real: a primeira execucao de verdade
# tem que ser uma COBAIA. Cinco linhas provam o caminho inteiro — credencial,
# permissao do IAM, formato da resposta, dimensao, cast ::vector, commit — por
# centavos. Descobrir que o parser da resposta estava errado na linha 400 de 501
# e o tipo de erro que este default existe para impedir.
LIMITE_COBAIA = 5

TABELA_PADRAO = "knowledge_fragments"

# MAPA DE TABELAS — e uma whitelist, e e um mapa, por dois motivos distintos.
#
# POR QUE WHITELIST: o nome da tabela e da coluna entram na query por
# interpolacao de string (identificador nao aceita placeholder %s em SQL), entao
# eles NAO podem vir livres da linha de comando. A whitelist e o que separa
# "parametro" de "injecao de SQL".
#
# POR QUE MAPA, e nao uma lista simples de nomes: porque as 9 tabelas de
# vector(1536) NAO sao intercambiaveis. Medido no banco em 03/09/2026:
#
#   - 5 chamam a coluna vetorial de `embedding`:
#       knowledge_fragments (501), locations (51), regions (29),
#       geographic_features (25), continents (4)
#   - 4 chamam de `descricao_embedding`:
#       ref_faccoes (12), lore_panteao (8), lore_eventos (5), lore_eras (3)
#   - e SO knowledge_fragments tem as colunas `titulo` e `conteudo`.
#     As outras 8 nao tem nenhuma das duas.
#
# Uma lista de nomes permitidos faria `--tabela locations` passar pela validacao
# e SO ENTAO estourar UndefinedColumn no meio do SELECT. O mapa transforma isso
# num erro imediato e explicado: o obstaculo real nao e tecnico, e uma decisao
# em aberto — qual texto de cada tabela deve alimentar o vetor. Enquanto essa
# decisao nao existir, `colunas_texto=None` e a forma honesta de dizer
# "reconheco a tabela, e ainda nao sei o que embeddar nela".
MAPA_TABELAS: dict[str, dict] = {
    "knowledge_fragments": {
        "coluna_vetor": "embedding",
        "colunas_texto": ("titulo", "conteudo"),
        "coluna_id": "id",
        "coluna_atualizado": "atualizado_em",
        "linhas": 501,
    },
    # As 8 abaixo somam 137 linhas e ficam para depois. O nome da coluna
    # vetorial ja esta medido e conferido; falta so decidir a fonte do texto.
    "locations":           {"coluna_vetor": "embedding",            "colunas_texto": None, "linhas": 51},
    "regions":             {"coluna_vetor": "embedding",            "colunas_texto": None, "linhas": 29},
    "geographic_features": {"coluna_vetor": "embedding",            "colunas_texto": None, "linhas": 25},
    "continents":          {"coluna_vetor": "embedding",            "colunas_texto": None, "linhas": 4},
    "ref_faccoes":         {"coluna_vetor": "descricao_embedding",  "colunas_texto": None, "linhas": 12},
    "lore_panteao":        {"coluna_vetor": "descricao_embedding",  "colunas_texto": None, "linhas": 8},
    "lore_eventos":        {"coluna_vetor": "descricao_embedding",  "colunas_texto": None, "linhas": 5},
    "lore_eras":           {"coluna_vetor": "descricao_embedding",  "colunas_texto": None, "linhas": 3},
}

ERROS_QUE_MERECEM_RETRY = ("ThrottlingException", "ServiceUnavailableException")
MAX_TENTATIVAS = 5


# ---------------------------------------------------------------------------
# Higiene de credencial
# ---------------------------------------------------------------------------

# POR QUE esta funcao existe e e usada em TODO print de erro:
# excecao de SDK e de driver de banco tem o habito de carregar a string de
# conexao ou o cabecalho de autenticacao na mensagem. Um traceback que vaza a
# senha do Postgres num log de CI e um vazamento igual ao de commitar o .env —
# so mais dificil de perceber. Toda mensagem de erro passa por aqui antes de
# chegar a tela.
_PADROES_SEGREDO = [
    (re.compile(r"(postgres(?:ql)?://[^:/\s]+:)[^@\s]+(@)", re.I), r"\1<SENHA-OCULTA>\2"),
    (re.compile(r"(AKIA[0-9A-Z]{16})"), "<ACCESS-KEY-ID-OCULTA>"),
    (re.compile(r"(aws_secret_access_key\s*[=:]\s*)\S+", re.I), r"\1<OCULTA>"),
    (re.compile(r"(Signature=)[0-9a-f]{16,}", re.I), r"\1<OCULTA>"),
    (re.compile(r"(Credential=)[^,\s]+", re.I), r"\1<OCULTA>"),
    (re.compile(r"(apikey=)\w+", re.I), r"\1<OCULTA>"),
]


def limpar(texto: object) -> str:
    """Tira qualquer coisa com cara de credencial antes de imprimir."""
    s = str(texto)
    for padrao, troca in _PADROES_SEGREDO:
        s = padrao.sub(troca, s)
    return s


# ---------------------------------------------------------------------------
# Conexao com o Postgres
# ---------------------------------------------------------------------------

def achar_dsn(caminho_env: str | None) -> str:
    """
    Ordem: variavel de ambiente DATABASE_URL primeiro, arquivo .env depois.

    POR QUE o ambiente ganha do arquivo: e o que permite rodar em container ou
    em CI, onde nao existe .env — e e o que evita que uma copia velha de .env
    esquecida no disco sobreponha, sem avisar, a configuracao real.
    """
    do_ambiente = os.environ.get("DATABASE_URL")
    if do_ambiente:
        return do_ambiente.strip()

    candidatos = []
    if caminho_env:
        candidatos.append(caminho_env)
    else:
        aqui = os.path.dirname(os.path.abspath(__file__))
        raiz = os.path.abspath(os.path.join(aqui, "..", ".."))
        candidatos += [os.path.join(raiz, ".env"), os.path.join(aqui, ".env")]

    for caminho in candidatos:
        if not os.path.isfile(caminho):
            continue
        with open(caminho, encoding="utf-8", errors="replace") as fh:
            for linha in fh:
                m = re.match(r"^\s*DATABASE_URL\s*=\s*(.+?)\s*$", linha)
                if m:
                    return m.group(1).strip().strip('"').strip("'")

    raise SystemExit(
        "sem DATABASE_URL.\n"
        "  Exporte a variavel, ou aponte o arquivo com --env-file CAMINHO.\n"
        f"  Procurei em: {', '.join(candidatos) or '(nada)'}"
    )


# ---------------------------------------------------------------------------
# Montagem do texto e do vetor
# ---------------------------------------------------------------------------

def montar_texto(*pedacos: str | None) -> str:
    """
    Junta as colunas de texto com uma linha em branco entre elas — em
    knowledge_fragments isso e titulo + "\\n\\n" + conteudo.

    POR QUE defensivo se `titulo` e 501/501 hoje: cobertura e um retrato, nao
    uma garantia de schema — a coluna e nullable. Um `None` concatenado viraria
    a string "None" dentro do texto embeddado, que nao estoura, nao avisa, e
    envenena o vetor de silencio. E exatamente a classe de bug que este script
    inteiro foi desenhado para nao ter. Pedaco vazio simplesmente nao entra, e
    nao deixa separador orfao para tras.
    """
    return "\n\n".join(p.strip() for p in pedacos if p and p.strip())


def para_pgvector(vetor: list[float]) -> str:
    """
    Lista de floats -> '[0.012,-0.034,...]', que o cast ::vector aceita.

    POR QUE string e nao o adapter do pgvector-python: e o padrao que o resto do
    repo ja usa (ver gerar_embeddings_alderyn.py) e nao adiciona dependencia
    para uma conversao de uma linha. Menos pacote a instalar no ambiente que vai
    rodar isso.
    """
    return "[" + ",".join(repr(float(x)) for x in vetor) + "]"


def estimar_tokens(texto: str) -> int:
    """
    Heuristica de ~4 caracteres por token. E ESTIMATIVA, nao medicao.

    Serve para dimensionar custo antes de gastar, nao para conferir fatura. A
    contagem real vem na resposta da API, e so existe depois de pagar por ela.
    """
    return max(1, len(texto) // 4)


# ---------------------------------------------------------------------------
# Bedrock
# ---------------------------------------------------------------------------

def abrir_cliente_bedrock(regiao: str | None):
    """
    Cria o cliente de embedding, e e AQUI que o boto3 e importado.

    POR QUE O IMPORT E PREGUICOSO (dentro da funcao, nao no topo do arquivo):
    e o que faz o --dry-run rodar numa maquina sem boto3 instalado e sem conta
    AWS nenhuma. Se o import estivesse no topo, o ensaio — que nao chama API
    alguma — morreria no carregamento do modulo por falta de uma dependencia
    que ele nao usa. Ensaio que exige a infra de producao para rodar nao serve
    de ensaio.

    POR QUE a credencial vem da cadeia padrao do boto3 e NUNCA do .env:
    variavel de ambiente, perfil e role de instancia sao os lugares que
    ferramenta de seguranca sabe auditar e que rotacao sabe trocar. Chave de AWS
    dentro do .env da aplicacao e como o segredo vaza junto com o backup.
    """
    try:
        import boto3
        from botocore.exceptions import NoCredentialsError, PartialCredentialsError
    except ImportError:
        raise SystemExit(
            "boto3 nao esta instalado — necessario so no modo --execute.\n"
            "  pip install boto3"
        )

    regiao = regiao or os.environ.get("AWS_DEFAULT_REGION") or os.environ.get("AWS_REGION")
    if not regiao:
        raise SystemExit(
            "sem regiao AWS — exporte AWS_DEFAULT_REGION (ex.: us-east-1).\n"
            "  Tem que ser a MESMA regiao do ARN na politica do iam.tf, senao a\n"
            "  chamada volta AccessDenied e o erro parece ser de permissao."
        )

    cliente = boto3.client("bedrock-runtime", region_name=regiao)

    # Falha cedo e com texto util. POR QUE checar agora e nao na primeira
    # chamada: melhor descobrir que falta credencial antes de ler 501 linhas do
    # banco do que no meio do lote 1.
    try:
        if cliente._request_signer._credentials is None:
            raise NoCredentialsError()
    except (NoCredentialsError, PartialCredentialsError):
        raise SystemExit(
            "sem credencial AWS — rode terraform apply primeiro e exporte as chaves do output:\n"
            "  cd infra/aws\n"
            "  export AWS_ACCESS_KEY_ID=$(terraform output -raw access_key_id)\n"
            "  export AWS_SECRET_ACCESS_KEY=$(terraform output -raw secret_access_key)\n"
            "  export AWS_DEFAULT_REGION=$(terraform output -raw aws_region)"
        )
    except AttributeError:
        # Detalhe interno do botocore nao e contrato publico: se ele mudar, o
        # certo e deixar a primeira chamada de verdade reclamar, nao abortar.
        pass

    return cliente


def extrair_vetores(resposta_bruta: dict, esperados: int) -> list[list[float]]:
    """
    Tira os vetores do JSON de resposta, aceitando os DOIS formatos possiveis.

    POR QUE defensivo — e aqui o motivo e melhor que "boa pratica":
    A DOC OFICIAL DA AWS SE CONTRADIZ neste ponto. A prosa da pagina do Embed v4
    diz que pedir UM unico embedding_type devolve `embeddings` como LISTA de
    listas ("response_type": "embeddings_floats"), e que so varios tipos
    devolvem OBJETO indexado pelo tipo ("embeddings_by_type"). Mas o exemplo de
    codigo oficial da MESMA pagina — com embedding_types = ["float"], um tipo so
    — itera o resultado como se fosse dicionario:

        for i, embedding_type in enumerate(embeddings):
            print(embeddings[embedding_type])

    Ou seja: nao da para saber pela doc qual das duas formas vem no nosso caso.
    Como nao ha credencial AWS para testar contra a API real, aceitar as duas e
    a unica postura honesta — e o `else` levanta erro explicado se vier uma
    terceira. Isto e o que a cobaia de 5 linhas vai resolver na pratica.
    """
    bruto = resposta_bruta.get("embeddings")

    if isinstance(bruto, dict):
        for chave in ("float", "float_", "floats"):
            if chave in bruto:
                bruto = bruto[chave]
                break
        else:
            raise ValueError(
                "resposta trouxe embeddings como objeto com chaves "
                f"{sorted(bruto)}, e nenhuma delas e de float"
            )

    if not isinstance(bruto, list):
        raise ValueError(f"campo 'embeddings' veio como {type(bruto).__name__}, esperava lista")
    if len(bruto) != esperados:
        raise ValueError(f"pedi {esperados} vetores, a API devolveu {len(bruto)}")

    return bruto


def embeddar_lote(cliente, textos: list[str]) -> list[list[float]]:
    """
    Uma chamada de embedding, com retry so no que merece retry.

    POR QUE apenas Throttling e ServiceUnavailable entram no backoff: sao os
    dois erros que dizem "tente de novo mais tarde" — passageiros, do lado da
    AWS. Repetir um ValidationException (texto grande demais) ou um AccessDenied
    (politica errada) seria teimosia: a resposta vai ser identica nas 5
    tentativas, e cada uma custa tempo. Erro de configuracao precisa aparecer
    rapido, nao ser mascarado por retry.
    """
    from botocore.exceptions import ClientError

    corpo = json.dumps({
        "texts": textos,
        # Este script INDEXA documentos, entao e sempre INPUT_TYPE_INDEXACAO.
        # A explicacao de por que existem dois valores, e do que quebra se eles
        # forem igualados, esta na definicao das constantes no topo do arquivo.
        "input_type": INPUT_TYPE_INDEXACAO,
        # POR QUE explicito em vez de confiar no default: 1536 e o contrato da
        # coluna. O default do modelo hoje tambem e 1536, mas depender de default
        # significa que uma mudanca no modelo passaria a gravar outro tamanho em
        # silencio — e a validacao de dimensao la embaixo abortaria as 501 linhas
        # sem que ninguem entendesse por que.
        "embedding_types": ["float"],
        "output_dimension": DIMENSAO_ESPERADA,
        # POR QUE truncar em vez de deixar estourar: o maior `conteudo` medido
        # tem 1839 caracteres — muito abaixo do limite de ~128k tokens do modelo
        # — entao na pratica isso nunca dispara. Esta aqui para o dia em que uma
        # linha nova vier gigante: perder o rabo de um texto e melhor que perder
        # a linha inteira, que e o que "NONE" faria (devolve erro).
        "truncate": TRUNCATE,
    })

    ultimo_erro: Exception | None = None
    for tentativa in range(1, MAX_TENTATIVAS + 1):
        try:
            resposta = cliente.invoke_model(modelId=MODELO_ID, body=corpo)
            return extrair_vetores(json.loads(resposta["body"].read()), len(textos))
        except ClientError as erro:
            codigo = erro.response.get("Error", {}).get("Code", "")
            if codigo not in ERROS_QUE_MERECEM_RETRY or tentativa == MAX_TENTATIVAS:
                raise
            # Backoff exponencial COM jitter. O jitter nao e enfeite: sem ele,
            # chamadas que tomaram throttle juntas voltam juntas e tomam
            # throttle de novo, em manada.
            espera = min(2 ** (tentativa - 1), 16) + random.uniform(0, 0.5)
            print(f"    {codigo} — tentativa {tentativa}/{MAX_TENTATIVAS}, esperando {espera:.1f}s")
            time.sleep(espera)
            ultimo_erro = erro

    raise ultimo_erro if ultimo_erro else RuntimeError("retry terminou sem resultado")


def embeddar_com_degradacao(cliente, textos: list[str]) -> list[list[float] | None]:
    """
    Tenta o lote inteiro; se ele falhar por erro nao-passageiro, cai para
    uma chamada por texto.

    POR QUE esta degradacao existe: a exigencia e "abortar a LINHA e continuar",
    mas a API e chamada em LOTE. Sem este fallback, uma unica linha envenenada
    derrubaria as outras 9 do lote junto com ela — nove linhas boas perdidas por
    causa de uma ruim. Repetindo individualmente, o prejuizo fica contido em
    quem realmente tem problema, e o custo extra so e pago no lote que falhou.
    """
    try:
        return list(embeddar_lote(cliente, textos))
    except Exception as erro:
        print(f"    lote falhou ({limpar(erro)[:160]}) — repetindo linha por linha")

    resultado: list[list[float] | None] = []
    for texto in textos:
        try:
            resultado.append(embeddar_lote(cliente, [texto])[0])
        except Exception as erro:
            print(f"      linha abortada: {limpar(erro)[:160]}")
            resultado.append(None)
    return resultado


# ---------------------------------------------------------------------------
# Fluxo principal
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(
        description="Backfill de embeddings (Bedrock cohere.embed-v4:0) — ensaio por padrao.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    # POR QUE a flag perigosa e a que precisa ser digitada, e nao o contrario:
    # nao existe --dry-run para ligar, porque o ensaio e o estado natural. Quem
    # esquece de digitar algo cai no comportamento seguro. Um script cujo
    # default escreve no banco e um script que vai escrever no banco por acidente.
    ap.add_argument("--execute", action="store_true",
                    help="chama a API e ESCREVE no banco. Sem isto, e so ensaio.")
    ap.add_argument("--limit", type=int, default=None,
                    help=f"maximo de linhas. Default: {LIMITE_COBAIA} com --execute, todas no ensaio.")
    ap.add_argument("--tabela", default=TABELA_PADRAO,
                    help=f"tabela alvo (default {TABELA_PADRAO}).")
    ap.add_argument("--env-file", default=None, help="caminho do .env com DATABASE_URL.")
    ap.add_argument("--region", default=None, help="regiao AWS (default: AWS_DEFAULT_REGION).")
    args = ap.parse_args()

    perfil = MAPA_TABELAS.get(args.tabela)
    if perfil is None:
        print(f"tabela '{args.tabela}' nao esta no mapa.", file=sys.stderr)
        print(f"conhecidas: {', '.join(MAPA_TABELAS)}", file=sys.stderr)
        return 2

    # Recusa ANTES de abrir conexao. POR QUE aqui e nao la dentro: a tabela e
    # reconhecida, mas ninguem decidiu ainda qual texto dela vira vetor. Deixar
    # passar produziria um UndefinedColumn no meio do SELECT — erro de sintaxe
    # de banco para um problema que e, na verdade, de definicao de produto.
    if not perfil.get("colunas_texto"):
        print(f"tabela '{args.tabela}' ({perfil['linhas']} linhas) ainda nao tem fonte de "
              "texto definida.", file=sys.stderr)
        print(f"  coluna vetorial dela: {perfil['coluna_vetor']}", file=sys.stderr)
        print("  Ela nao tem `titulo` nem `conteudo`. Antes de rodar aqui, decida quais",
              file=sys.stderr)
        print("  colunas alimentam o embedding e declare em MAPA_TABELAS.", file=sys.stderr)
        print(f"\n  Esta versao cobre so: {TABELA_PADRAO}", file=sys.stderr)
        return 2

    coluna_vetor = perfil["coluna_vetor"]
    colunas_texto = perfil["colunas_texto"]
    coluna_id = perfil.get("coluna_id", "id")
    coluna_atualizado = perfil.get("coluna_atualizado")

    # NUNCA existe "todas as linhas" no modo real sem numero digitado.
    if args.limit is not None:
        limite = args.limit
    elif args.execute:
        limite = LIMITE_COBAIA
    else:
        limite = None

    modo = "EXECUCAO REAL" if args.execute else "ENSAIO (dry-run)"
    print("=" * 68)
    print(f"  Backfill de embeddings — {modo}")
    print(f"  tabela: {args.tabela}.{coluna_vetor}   modelo: {MODELO_ID}   dim: {DIMENSAO_ESPERADA}")
    print(f"  texto:  {' + '.join(colunas_texto)}")
    print(f"  limite: {limite if limite is not None else 'todas'}   lote/commit: {TAMANHO_LOTE}")
    if not args.execute:
        print("  Nada sera chamado na API e nada sera escrito no banco.")
    print("=" * 68)

    import psycopg

    dsn = achar_dsn(args.env_file)
    comeco = time.time()

    try:
        conexao = psycopg.connect(dsn, connect_timeout=30)
    except Exception as erro:
        print(f"falha ao conectar no Postgres: {limpar(erro)}", file=sys.stderr)
        return 1

    gravadas = com_erro = 0
    tokens_estimados = 0

    with conexao:
        # No ensaio a conexao e declarada read-only. Cinto e suspensorio: mesmo
        # que um UPDATE aparecesse aqui por engano de edicao futura, o servidor
        # recusaria. A trava nao depende de o `if` estar certo.
        if not args.execute:
            conexao.read_only = True

        with conexao.cursor() as cur:
            cur.execute(f"SELECT count(*) FROM {args.tabela} WHERE {coluna_vetor} IS NULL")
            pendentes_total = cur.fetchone()[0]

            # A idempotencia mora nesta clausula: `WHERE embedding IS NULL`.
            # Rodar duas vezes nao reprocessa nada — a segunda execucao
            # simplesmente nao encontra as linhas que a primeira ja gravou. E
            # tambem por isso que NAO existe --force: reprocessar seria pagar de
            # novo por um vetor identico, e o unico motivo real para querer isso
            # e troca de modelo, que muda o espaco semantico inteiro e exige
            # limpar a coluna de proposito, nao uma flag de conveniencia.
            # A ultima coluna de `colunas_texto` e tratada como a obrigatoria (em
            # knowledge_fragments, `conteudo`): e ela que precisa existir para a
            # linha valer um vetor. Linha so com titulo nao e conhecimento.
            texto_principal = colunas_texto[-1]
            sql = (
                f"SELECT {coluna_id}, {', '.join(colunas_texto)} FROM {args.tabela} "
                f"WHERE {coluna_vetor} IS NULL "
                f"  AND {texto_principal} IS NOT NULL AND {texto_principal} <> '' "
                f"ORDER BY {coluna_id}"
            )
            if limite is not None:
                sql += f" LIMIT {int(limite)}"
            cur.execute(sql)
            linhas = cur.fetchall()

        print(f"\nlinhas sem embedding na tabela: {pendentes_total}")
        print(f"linhas nesta rodada:            {len(linhas)}")

        if not linhas:
            print("\nNada a fazer — nao ha linha com texto e sem embedding.")
            return 0

        alvos = [(linha[0], montar_texto(*linha[1:])) for linha in linhas]
        alvos = [(rid, txt) for rid, txt in alvos if txt]
        tokens_estimados = sum(estimar_tokens(t) for _, t in alvos)

        # ---------------- ENSAIO ----------------
        if not args.execute:
            print(f"\ntokens estimados (~4 chars/token): {tokens_estimados:,}")
            print(f"caracteres somados:                {sum(len(t) for _, t in alvos):,}")
            print("\namostra — 3 primeiros textos, truncados em 200 chars:")
            for i, (rid, texto) in enumerate(alvos[:3], 1):
                achatado = texto.replace("\n", "\\n")
                print(f"\n  [{i}] id={rid}")
                print(f"      len={len(texto)} chars, ~{estimar_tokens(texto)} tokens")
                print(f"      {achatado[:200]}{'...' if len(texto) > 200 else ''}")
            print("\n" + "=" * 68)
            print(f"  ENSAIO concluido em {time.time() - comeco:.1f}s.")
            print("  Zero chamadas a API. Zero escritas no banco.")
            print(f"  Para valer, na cobaia de {LIMITE_COBAIA}:  --execute")
            print(f"  Para a carga toda:                 --execute --limit {pendentes_total}")
            print("=" * 68)
            return 0

        # ---------------- EXECUCAO REAL ----------------
        cliente = abrir_cliente_bedrock(args.region)

        for inicio in range(0, len(alvos), TAMANHO_LOTE):
            lote = alvos[inicio:inicio + TAMANHO_LOTE]
            print(f"\nlote {inicio // TAMANHO_LOTE + 1} — {len(lote)} linha(s)")

            vetores = embeddar_com_degradacao(cliente, [t for _, t in lote])

            gravadas_no_lote = 0
            with conexao.cursor() as cur:
                for (rid, _), vetor in zip(lote, vetores):
                    if vetor is None:
                        com_erro += 1
                        continue

                    # VALIDACAO DE DIMENSAO — antes de gravar, sempre.
                    # Truncar para caber ou completar com zero produziria um
                    # vetor que o Postgres aceita e que esta semanticamente
                    # ERRADO: a busca degradaria sem nunca dar erro, e a causa
                    # estaria a meses de distancia de quem fosse investigar.
                    # Linha suspeita fica sem embedding, e `IS NULL` garante que
                    # a proxima rodada tenta de novo.
                    if len(vetor) != DIMENSAO_ESPERADA:
                        print(f"    id={rid}: dimensao {len(vetor)} != {DIMENSAO_ESPERADA}"
                              " — ABORTADA, nao gravada")
                        com_erro += 1
                        continue

                    try:
                        # O `AND <coluna> IS NULL` repetido no UPDATE nao e
                        # redundancia do SELECT: entre ler e gravar existe uma
                        # janela em que outra execucao do script podia ter
                        # preenchido a mesma linha. Com ele, a segunda escrita
                        # simplesmente nao acha a linha em vez de sobrepor um
                        # vetor ja pago.
                        sets = [f"{coluna_vetor} = %s::vector"]
                        if coluna_atualizado:
                            sets.append(f"{coluna_atualizado} = now()")
                        cur.execute(
                            f"UPDATE {args.tabela} SET {', '.join(sets)} "
                            f"WHERE {coluna_id} = %s AND {coluna_vetor} IS NULL",
                            (para_pgvector(vetor), rid),
                        )
                        gravadas_no_lote += 1
                    except Exception as erro:
                        print(f"    id={rid}: UPDATE falhou — {limpar(erro)[:160]}")
                        com_erro += 1

            # COMMIT AQUI, a cada lote — nao no fim do script.
            # Com um commit unico no final, uma queda na linha 480 de 501
            # descartaria as 479 ja pagas: o dinheiro sai, o resultado nao fica.
            # Comitando por lote, o progresso e duravel e o `IS NULL` faz a
            # proxima execucao retomar exatamente de onde parou.
            conexao.commit()
            gravadas += gravadas_no_lote
            print(f"    commit — {gravadas_no_lote} gravada(s) | acumulado {gravadas}/{len(alvos)}")

    duracao = time.time() - comeco
    print("\n" + "=" * 68)
    print(f"  linhas processadas:  {gravadas}")
    print(f"  linhas com erro:     {com_erro}")
    print(f"  tokens estimados:    {tokens_estimados:,}")
    print(f"  tempo total:         {duracao:.1f}s")
    if gravadas and pendentes_total > gravadas:
        print(f"\n  ainda pendentes: ~{pendentes_total - gravadas}. Rode de novo com --limit maior.")
    if gravadas == pendentes_total and gravadas:
        print("\n  Tabela completa. AGORA sim crie o indice: infra/aws/create_hnsw_index.sql")
    print("=" * 68)
    return 0 if com_erro == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
