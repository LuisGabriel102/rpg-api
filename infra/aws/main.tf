# ---------------------------------------------------------------------------
# Alderyn — Etapa 1 da infra AWS: acesso ao Bedrock para gerar embeddings.
#
# POR QUE esta stack existe:
# o banco tem 12 tabelas com coluna vetorial e nenhum embedding gravado —
# query_vec=None está fixo no jogo.py desde a decisão de custo antiga. Antes de
# escrever um único vetor precisamos de uma porta de entrada no Bedrock que seja
# barata de auditar e impossível de usar para outra coisa. É só isso que mora
# aqui: nenhuma rede, nenhum banco, nenhum compute.
# ---------------------------------------------------------------------------

terraform {
  # POR QUE >= 1.5: é a partir dela que existem os blocos `check` e o `import`
  # declarativo. Travar o piso evita que uma máquina com 1.2 instalada gere,
  # sem avisar, um plano diferente do que foi revisado aqui.
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source = "hashicorp/aws"
      # POR QUE ~> 5.0: aceita qualquer 5.x — é em minor que chegam os model ids
      # novos do Bedrock — e recusa o 6.0, que muda contrato de recurso sem
      # pedir licença. Atualização de major passa a ser decisão, não acidente.
      version = "~> 5.0"
    }
  }

  # ETAPA 4 — o state saiu do disco e foi para o S3.
  #
  # POR QUE ISTO IMPORTA MAIS AQUI DO QUE EM QUALQUER OUTRA STACK:
  # este tfstate carrega a secret access key do usuário embedder em texto claro
  # (ver outputs.tf). No disco, ele dependia de um .gitignore para não vazar num
  # repositório PÚBLICO — uma proteção que é uma linha de texto e um descuido de
  # distância. No S3 ele fica criptografado, num bucket com acesso público
  # bloqueado nos quatro flags e com versionamento ligado.
  #
  # CONFIGURAÇÃO PARCIAL — o `bucket` NÃO está declarado aqui de propósito.
  # O nome dele termina no account id, que não é conhecido no momento em que
  # este arquivo é escrito e que não deve ficar registrado num repo público.
  # Ele entra no `init`, lido direto do output do bootstrap:
  #
  #   terraform init -backend-config="bucket=$(terraform -chdir=bootstrap output -raw bucket_name)"
  #
  # PARA VALIDAR ESTE ARQUIVO SEM CONTA AWS: `terraform init -backend=false`.
  # Um `init` normal tenta conectar ao bucket e falha por falta de credencial —
  # o que é o comportamento correto dele, não um defeito da configuração.
  backend "s3" {
    # Caminho do objeto dentro do bucket. O prefixo por componente deixa espaço
    # para as próximas etapas (o ECS da Etapa 3) morarem no mesmo bucket sem
    # disputar a mesma chave.
    key    = "bedrock-embeddings/terraform.tfstate"
    region = "us-east-1"

    # Criptografa o objeto na escrita. Redundante com a criptografia padrão que
    # o bootstrap configurou no bucket, e mantido assim de propósito: se alguém
    # um dia apontar este backend para outro bucket, sem SSE por padrão, o state
    # continua sendo gravado criptografado.
    encrypt = true

    # A TRAVA DE CONCORRÊNCIA — e o motivo de NÃO haver `dynamodb_table` aqui.
    #
    # Conferido na doc oficial da HashiCorp: "DynamoDB-based locking is
    # deprecated and will be removed in a future minor version". O caminho atual
    # é `use_lockfile`, que faz a trava por escrita condicional no próprio S3,
    # gravando um objeto .tflock ao lado do state.
    #
    # Uma tabela DynamoDB aqui funcionaria hoje e quebraria numa minor futura —
    # além de ser mais um recurso para criar, pagar e lembrar de destruir. Quem
    # encontrar tutorial mais antigo vai ver `dynamodb_table`: está velho.
    use_lockfile = true
  }
}

provider "aws" {
  region = var.aws_region

  # POR QUE default_tags: todo recurso nasce marcado sem ninguém precisar
  # lembrar de taguear à mão. É isso que torna a fatura filtrável por Project no
  # Cost Explorer — e é o que faz o alerta do budget.tf apontar para uma causa
  # em vez de mostrar um número solto.
  default_tags {
    tags = {
      Project   = var.project_name
      ManagedBy = "terraform"
    }
  }
}

# POR QUE ler a identidade em runtime em vez de fixar o número da conta:
# o account id entra em ARN e em mensagem de erro. Lido daqui, a stack roda em
# qualquer conta (a sua hoje, uma de teste amanhã) sem editar uma linha — e o
# número da conta não fica escrito num repositório PÚBLICO.
# Quem consome isto de fato é a Etapa 3, ao montar o ARN da task role do ECS.
data "aws_caller_identity" "current" {}
