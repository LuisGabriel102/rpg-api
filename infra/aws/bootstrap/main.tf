# ---------------------------------------------------------------------------
# Bootstrap da Etapa 4 — o balde que guarda a memória de toda a infra.
#
# POR QUE ISTO É UM DIRETÓRIO SEPARADO, e não mais um arquivo em infra/aws/:
# é o problema do ovo e da galinha, e ele é real, não teórico. O backend S3 da
# stack principal precisa que o bucket JÁ EXISTA no momento do `init` — antes de
# qualquer plano, antes de qualquer recurso. Se a mesma stack criasse o bucket e
# guardasse o próprio state dentro dele, dois absurdos apareceriam: no primeiro
# `init` o backend apontaria para um bucket que ainda não foi criado, e num
# `destroy` o Terraform tentaria apagar o bucket que contém o state que ele está
# lendo naquele instante — serrando o galho em que está sentado.
#
# A saída é a convencional: este diretório tem state LOCAL e cria só o bucket.
# A stack principal, ao lado, aponta o backend para ele. Os dois nunca se
# gerenciam mutuamente.
#
# O STATE LOCAL DAQUI É ACEITÁVEL, e por um motivo específico: ele descreve
# quatro recursos que nunca mudam depois de criados e que não guardam segredo
# nenhum. Se este tfstate for perdido, nada de irrecuperável acontece — o bucket
# continua existindo na AWS e volta para o controle do Terraform com um
# `terraform import`. Compare com o tfstate da stack principal, que carrega a
# secret access key em texto claro: aquele é o que precisa sair do disco.
# ---------------------------------------------------------------------------

terraform {
  # Mesmo piso da stack principal, pelo mesmo motivo: garantir que a máquina que
  # roda isto gera o plano que foi revisado, e não outro.
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # SEM bloco `backend` aqui, DE PROPÓSITO. Este é o único lugar do projeto onde
  # state local é a resposta certa, e não uma etapa pendente.
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project   = var.project_name
      ManagedBy = "terraform"
      # Distingue este diretório da stack principal na fatura e no console.
      Component = "tfstate-bootstrap"
    }
  }
}

# POR QUE o account id é lido e não escrito:
# ele entra no NOME do bucket, e nome de bucket S3 vive num namespace GLOBAL —
# compartilhado entre todas as contas AWS do mundo. "alderyn-tfstate" é um nome
# que outra pessoa pode ter registrado, e nesse caso a criação falha com
# BucketAlreadyExists sem que haja o que fazer a respeito. O account id como
# sufixo torna a colisão impossível na prática, e lido em runtime ele não fica
# escrito num repositório PÚBLICO.
data "aws_caller_identity" "current" {}
