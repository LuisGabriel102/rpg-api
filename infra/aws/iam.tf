# ---------------------------------------------------------------------------
# IAM — a peça central da Etapa 1.
#
# POR QUE tanto cuidado concentrado aqui:
# esta é a única credencial do projeto que fala com a AWS, e ela vai existir
# como par de chaves em texto claro na máquina que roda o script de embeddings.
# O desenho parte do princípio de que a chave um dia vaza. Partindo dali, a
# pergunta que importa não é "como impedir o vazamento", é "o que o portador
# consegue fazer depois". A resposta pretendida: transformar texto em vetor, e
# absolutamente nada mais.
# ---------------------------------------------------------------------------

data "aws_iam_policy_document" "bedrock_embed" {
  statement {
    sid    = "InvocarSomenteOModeloDeEmbedding"
    effect = "Allow"

    # POR QUE APENAS InvokeModel:
    # é o verbo que devolve vetor, e é o fim da lista. Ficam de fora, de propósito:
    #   - InvokeModelWithResponseStream — streaming não faz sentido para
    #     embedding, e é superfície de ataque de graça;
    #   - os List*/Get* de catálogo — o model id já é conhecido e está travado
    #     na variável, não há o que a credencial precise descobrir;
    #   - CreateModelCustomizationJob e afins — fine-tuning e provisioned
    #     throughput são as chamadas genuinamente CARAS do Bedrock. Uma chave que
    #     não as tem não consegue gerar fatura de quatro dígitos nem por acidente.
    actions = ["bedrock:InvokeModel"]

    # POR QUE O ARN É COMPLETO E NUNCA "*":
    # esta é a linha que carrega o valor de segurança do arquivo inteiro. Com
    # resource = "*", a MESMA chave invocaria Claude Opus, Llama e geração de
    # imagem — todos com preço por token ordens de magnitude acima de embedding
    # — e o estrago só apareceria na fatura, depois. Com o ARN fixado no model
    # id, qualquer chamada a outro modelo volta AccessDenied na hora e de graça:
    # o pedido é recusado antes de virar consumo.
    #
    # O campo da conta fica VAZIO no meio do ARN de propósito (dois-pontos
    # seguidos). Foundation model é recurso do serviço, compartilhado, não da
    # conta — e é essa a forma que a AWS documenta. Preencher com o account id
    # produziria uma política que nunca casa, ou seja, um AccessDenied
    # permanente difícil de diagnosticar.
    resources = [
      "arn:aws:bedrock:${var.aws_region}::foundation-model/${var.embedding_model_id}",
    ]
  }
}

# POR QUE UM IAM USER COM ACCESS KEY, E NÃO UMA ROLE:
# role só é assumível por quem já tem identidade dentro da AWS — EC2, ECS,
# Lambda. O script de embeddings roda FORA: na máquina local, contra o Postgres
# da Neon. Não existe identidade AWS ali para assumir role nenhuma, então o par
# de chaves é o único mecanismo que de fato funciona hoje.
#
# ISSO É TEMPORÁRIO, E ESTÁ ASSUMIDO COMO TAL:
# na Etapa 3 o script vira task no ECS e ganha uma task role carregando esta
# mesma política — o arquivo é reaproveitado, só troca quem a veste. Neste
# momento este user é apagado e a chave morre com ele. O ganho de manter o
# escopo tão apertado é que, até lá, o pior caso de um vazamento é alguém gastar
# embedding dentro de um teto de cinco dólares.
resource "aws_iam_user" "embedder" {
  name = "${var.project_name}-embedder"

  # POR QUE path /service/: separa identidade de máquina de identidade de
  # pessoa. Rende filtro por caminho em auditoria e deixa evidente, só de olhar
  # a listagem, que ninguém deveria estar entrando no console com este user.
  path = "/service/"
}

# POR QUE POLÍTICA INLINE (user_policy) E NÃO UMA MANAGED POLICY:
# política inline morre junto com o user. Managed policy sobreviveria ao
# `terraform destroy` como órfã — e uma política solta com permissão de Bedrock
# esquecida na conta é exatamente o tipo de resto que ninguém revisa e que
# reaparece anexado a outra coisa meses depois.
resource "aws_iam_user_policy" "bedrock_embed" {
  name   = "${var.project_name}-bedrock-embed"
  user   = aws_iam_user.embedder.name
  policy = data.aws_iam_policy_document.bedrock_embed.json
}

# POR QUE A CHAVE NASCE AQUI DENTRO:
# criada pelo Terraform, ela é a única chave do user e compartilha o ciclo de
# vida do resto — um `destroy` revoga de verdade. Chave criada à mão no console
# fica invisível para o código, não aparece em plan nenhum e sobrevive a tudo.
#
# O PREÇO, DITO NA CARA: a secret vai para o terraform.tfstate em texto claro.
# É daí que saem as duas travas desta etapa — *.tfstate* no .gitignore (o repo é
# PÚBLICO) e a migração do state para S3 criptografado na Etapa 4. O detalhe do
# que `sensitive` faz e do que ele NÃO faz está no outputs.tf.
resource "aws_iam_access_key" "embedder" {
  user = aws_iam_user.embedder.name
}
