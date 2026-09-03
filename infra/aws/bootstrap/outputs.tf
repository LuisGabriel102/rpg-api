# ---------------------------------------------------------------------------
# Outputs do bootstrap — o que a stack principal precisa saber para se conectar.
# ---------------------------------------------------------------------------

output "bucket_name" {
  description = "Nome do bucket de state. É este valor que vai no -backend-config da stack principal."

  # POR QUE isto é output e não uma string repetida no bloco `backend`:
  # o nome contém o account id, que só é conhecido em runtime. A stack principal
  # usa configuração parcial de backend justamente por isso, e o comando de
  # `init` lê este output em vez de alguém copiar doze dígitos à mão. Um lugar
  # só define o nome; nenhum outro pode divergir dele.
  value = aws_s3_bucket.tfstate.id
}

output "bucket_region" {
  description = "Região do bucket. Precisa bater com a do bloco backend."
  value       = aws_s3_bucket.tfstate.region
}

output "versionamento" {
  description = "Confirmação de que o versionamento ficou ligado."

  # POR QUE vale exportar um valor que o código já fixa em "Enabled":
  # este é o output que se olha depois de um apply para confirmar que a
  # recuperação de state está de fato disponível — e não para descobrir isso no
  # dia em que ela for necessária.
  value = aws_s3_bucket_versioning.tfstate.versioning_configuration[0].status
}
