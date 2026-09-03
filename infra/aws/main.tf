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

  # POR QUE O STATE É LOCAL NESTA ETAPA (e isso é deliberado, não esquecimento):
  # backend S3 exige um bucket que ainda não existe, e criar o bucket com o
  # mesmo Terraform que guardaria o state dentro dele é o problema do ovo e da
  # galinha. O state migra para S3 — criptografado, com lock — na Etapa 4,
  # quando já houver bucket para apontar.
  #
  # Enquanto for local, o terraform.tfstate fica no disco e NÃO entra no git.
  # O motivo está no outputs.tf: ele carrega a secret access key em texto claro.
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
