# ---------------------------------------------------------------------------
# O bucket de state, e as quatro proteções que ele precisa ter.
#
# O que mora aqui dentro é o registro do que existe na AWS — e, no caso da
# stack principal, a secret access key do usuário embedder em texto claro. Cada
# bloco abaixo existe por causa de uma forma específica de perder isso ou de
# vazar isso.
# ---------------------------------------------------------------------------

locals {
  # POR QUE o account id entra no nome:
  # nome de bucket S3 é GLOBAL, não é por conta. Um nome curto e óbvio como
  # "alderyn-tfstate" tem chance real de já estar tomado por um desconhecido, e
  # o erro (BucketAlreadyExists) não tem contorno além de escolher outro nome.
  # O account id é único por definição e transforma colisão em impossibilidade.
  #
  # Nome de bucket também tem regras próprias: minúsculas, 3 a 63 caracteres,
  # sem underscore. "alderyn-tfstate-<12 dígitos>" dá 28 caracteres e passa em
  # todas — desde que `project_name` continue em minúsculas e sem underscore.
  bucket_name = "${var.project_name}-tfstate-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket" "tfstate" {
  bucket = local.bucket_name

  # ESTA É A TRAVA MAIS IMPORTANTE DO ARQUIVO.
  #
  # `prevent_destroy` faz o Terraform RECUSAR qualquer plano que apague este
  # bucket — inclusive um `terraform destroy` rodado aqui dentro, que passa a
  # falhar com erro em vez de executar. É deliberado e é o comportamento
  # desejado.
  #
  # POR QUE: apagar este bucket não apaga "um bucket". Apaga a memória de toda a
  # infraestrutura — o Terraform perde o registro do que existe, e o que já está
  # criado na AWS vira órfão, invisível para o código e cobrando em silêncio.
  # Recuperar disso é reimportar recurso por recurso, à mão.
  #
  # Para remover de verdade, um dia, é preciso apagar este bloco `lifecycle`
  # primeiro, num commit próprio. Esse atrito é o ponto: torna impossível
  # destruir o bucket por acidente ou no meio de outra operação.
  lifecycle {
    prevent_destroy = true
  }
}

# POR QUE VERSIONAMENTO — e aqui vale ser preciso sobre o motivo.
#
# A doc oficial do backend S3 diz, textualmente, que é "highly recommended that
# you enable Bucket Versioning on the S3 bucket to allow for state recovery in
# the case of accidental deletions and human error". O motivo declarado pela
# HashiCorp é RECUPERAÇÃO — poder voltar a uma versão anterior do state depois
# de um erro humano ou de uma escrita ruim.
#
# Observação honesta, porque a diferença importa para quem for ler isto depois:
# a doc NÃO afirma que o lockfile nativo (use_lockfile) *depende* de
# versionamento para funcionar. Ela trata as duas coisas separadamente. O
# versionamento está ligado aqui pelo motivo que a doc de fato dá — um state
# corrompido ou sobrescrito é irrecuperável sem ele — e não por uma dependência
# técnica do mecanismo de trava, que não está documentada.
resource "aws_s3_bucket_versioning" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id

  versioning_configuration {
    status = "Enabled"
  }
}

# POR QUE criptografia em repouso, mesmo num bucket privado:
# o conteúdo é state do Terraform, e o da stack principal carrega a secret
# access key em texto claro dentro do JSON. Bucket privado protege contra acesso
# pela API; SSE protege o dado gravado no disco da AWS. São camadas diferentes,
# e a segunda é grátis.
#
# SSE-S3 (AES256) basta e é a escolha certa AQUI: chave gerenciada pela AWS, sem
# custo e sem nada para administrar. SSE-KMS daria trilha de auditoria por
# chamada e política de chave própria, ao custo de uma chave KMS mensal e de
# mais uma permissão para acertar. Para um state de uma stack pequena, esse
# preço não se paga.
resource "aws_s3_bucket_server_side_encryption_configuration" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# POR QUE OS QUATRO FLAGS, e não só um:
# eles cobrem caminhos distintos de exposição, e deixar qualquer um de fora
# mantém uma porta aberta. Os dois primeiros barram a CRIAÇÃO de permissão
# pública nova; os dois últimos IGNORAM e RESTRINGEM o que por acaso já exista.
# Ligar os quatro é o que torna "público" um estado inalcançável para este
# bucket, mesmo que alguém, um dia, aplique uma ACL distraída.
#
# Num bucket que guarda credencial em texto claro, isto não é excesso: é a
# diferença entre um erro de configuração e um incidente.
resource "aws_s3_bucket_public_access_block" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id

  block_public_acls       = true # recusa ACL pública nova
  block_public_policy     = true # recusa policy de bucket pública nova
  ignore_public_acls      = true # ignora ACL pública que já exista
  restrict_public_buckets = true # bloqueia acesso anônimo e entre contas
}
