# ---------------------------------------------------------------------------
# Variáveis do bootstrap. Mesma regra da stack principal: tudo com default,
# para que um `apply` disparado por script nunca trave num prompt esperando
# digitação que ninguém está lá para fornecer.
# ---------------------------------------------------------------------------

variable "aws_region" {
  description = "Região onde o bucket de state é criado."
  type        = string

  # POR QUE precisa ser a MESMA região da stack principal:
  # o backend S3 lê a região do próprio bloco `backend`, e apontar para um
  # bucket em outra região funciona, mas adiciona latência e uma pegadinha de
  # configuração para nada. Manter as duas iguais é uma variável a menos para
  # errar quando alguém for lembrar disto daqui a seis meses.
  default = "us-east-1"
}

variable "project_name" {
  description = "Prefixo do nome do bucket e valor da tag Project."
  type        = string

  # Precisa bater com o `project_name` da stack principal — é o que faz os
  # recursos dos dois diretórios aparecerem juntos ao filtrar a fatura.
  default = "alderyn"
}
