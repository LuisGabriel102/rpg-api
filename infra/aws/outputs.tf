# ---------------------------------------------------------------------------
# Outputs — exatamente o que o script de embeddings precisa saber para rodar,
# e nada além disso.
# ---------------------------------------------------------------------------

output "aws_region" {
  description = "Região usada na chamada ao Bedrock. Precisa bater com a do ARN da política."
  # POR QUE exportar uma variável de volta: o cliente boto3 é construído com a
  # região, e ela está costurada dentro do ARN em iam.tf. Se o script chutar a
  # região por conta própria e errar, o sintoma é AccessDenied — erro que parece
  # de permissão e faz perder tempo no lugar errado. Lendo daqui, não divergem.
  value = var.aws_region
}

output "embedding_model_id" {
  description = "Único model id que esta credencial consegue invocar."
  # POR QUE exportar em vez de repetir a string no Python: a política do IAM e a
  # chamada da aplicação passam a ter uma fonte só. Trocar a variável move os
  # dois juntos; string duplicada no código acabaria divergindo, e a divergência
  # apareceria como AccessDenied em produção.
  value = var.embedding_model_id
}

output "iam_user_name" {
  description = "Nome do user de serviço, para achar as chamadas no CloudTrail."
  # POR QUE isto importa na prática: quando o alerta do budget.tf chegar, a
  # primeira pergunta vai ser "quem invocou". Este nome é a chave de busca.
  value = aws_iam_user.embedder.name
}

output "access_key_id" {
  description = "AWS_ACCESS_KEY_ID para o .env do script de embeddings."
  # POR QUE ESTE **NÃO** É sensitive: o access key id é o lado público do par.
  # Ele já aparece em log do CloudTrail e não abre nada sozinho, sem a secret.
  # Marcá-lo sensitive só esconderia à toa um valor que precisa ser copiado à
  # mão — e treinaria a ignorar o aviso justamente no output ao lado, onde ele
  # é sério.
  value = aws_iam_access_key.embedder.id
}

output "secret_access_key" {
  description = "AWS_SECRET_ACCESS_KEY do script. Copie uma vez para o .env e não deixe em nenhum outro lugar."
  value       = aws_iam_access_key.embedder.secret

  # ============================================================
  # ATENÇÃO — E ISTO NÃO É DETALHE DE RODAPÉ:
  #
  # sensitive = true NÃO CRIPTOGRAFA NADA.
  #
  # A única coisa que ele faz é trocar o valor por "(sensitive value)" na saída
  # de plan e apply, para a secret não cair no scrollback do terminal nem no log
  # de um CI. É proteção de EXIBIÇÃO, não de ARMAZENAMENTO.
  #
  # No terraform.tfstate a secret está lá: JSON, texto claro, legível por
  # qualquer um com acesso ao arquivo. O flag abaixo não muda uma vírgula disso.
  #
  # É exatamente daí que vêm as duas regras desta etapa:
  #   1. *.tfstate* bloqueado no .gitignore — este repositório é PÚBLICO, e um
  #      tfstate commitado equivale a publicar a credencial;
  #   2. desde a Etapa 4 o state nem passa pelo disco: mora num bucket S3
  #      criptografado, com acesso público bloqueado e versionamento ligado.
  #      Ver o bloco `backend "s3"` no main.tf e o bucket em bootstrap/.
  #
  # Para ler o valor de propósito, uma vez, ao popular o .env:
  #   terraform output -raw secret_access_key
  # ============================================================
  sensitive = true
}
