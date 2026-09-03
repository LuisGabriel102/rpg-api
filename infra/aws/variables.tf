# ---------------------------------------------------------------------------
# Variáveis da Etapa 1.
#
# POR QUE TODAS TÊM DEFAULT:
# variável sem default faz o Terraform abrir um prompt e esperar digitação. Num
# apply disparado por script — ou por um agente — isso não é uma pergunta, é um
# processo travado para sempre sem dizer o motivo. Com default, `apply` roda
# reto e quem quiser mudar algo passa -var explicitamente.
# ---------------------------------------------------------------------------

variable "aws_region" {
  description = "Região AWS onde o acesso ao Bedrock é criado."
  type        = string

  # POR QUE us-east-1: tem o catálogo de foundation models mais completo e é a
  # primeira a receber modelo novo. Embedding é chamada servidor-a-servidor num
  # script de carga, então estar longe do Brasil não custa latência que jogador
  # nenhum sinta.
  default = "us-east-1"
}

variable "project_name" {
  description = "Prefixo de nome e valor da tag Project em todo recurso."
  type        = string

  # POR QUE variável e não string solta espalhada: este valor costura o nome do
  # IAM user, o nome do budget e o filtro de custo. Um lugar só para mudar
  # significa que os três nunca saem de sincronia.
  default = "alderyn"
}

variable "embedding_model_id" {
  description = "O único model id do Bedrock que a credencial pode invocar."
  type        = string

  # POR QUE cohere.embed-v4:0, e não um Titan:
  # as 9 tabelas alvo são vector(1536). O Titan V2 devolve 256/512/1024 — nenhum
  # bate. O Titan G1 devolve 1536 mas é legacy, ou seja, dívida no dia um. O
  # Cohere Embed v4 entrega 1536 nativo, sem truncar nem repadear, então o
  # schema do banco continua exatamente como está.
  default = "cohere.embed-v4:0"
}

variable "budget_limit_usd" {
  description = "Teto mensal de gasto, em USD, que dispara os alertas."
  type        = string

  # POR QUE string e não number: a API de budgets da AWS recebe o limite como
  # string e o provider repassa como veio. Declarar number aqui só adicionaria
  # uma conversão implícita que reaparece como diff fantasma em todo plan.
  #
  # POR QUE 5: a carga inicial inteira — 501 linhas de knowledge_fragments mais
  # 137 das outras 8 tabelas — custa centavos. Cinco dólares não atrapalham
  # nenhum trabalho legítimo e gritam alto se algo entrar em laço invocando o
  # modelo sem parar.
  default = "5"
}

variable "alert_email" {
  description = "E-mail que recebe os alertas de orçamento."
  type        = string

  # POR QUE fica escrito no código: é endereço de dono de projeto, não
  # credencial. Deixá-lo explícito garante que o alerta tem destino sem depender
  # de um arquivo .tfvars — que é justamente o que o .gitignore desta etapa
  # bloqueia, e que portanto não existe para quem clonar o repo.
  default = "luis.gabrielalbrecht21@gmail.com"
}
