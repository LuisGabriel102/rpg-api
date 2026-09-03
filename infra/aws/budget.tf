# ---------------------------------------------------------------------------
# Orçamento — a rede de segurança da Etapa 1.
#
# POR QUE ISTO EXISTE MESMO COM A POLÍTICA DO iam.tf TÃO APERTADA:
# porque as duas defesas cobrem falhas diferentes. O IAM impede invocar o modelo
# ERRADO; ele não impede invocar o modelo CERTO um milhão de vezes. Um retry sem
# teto, ou um laço que reprocessa as mesmas 501 linhas de knowledge_fragments em
# círculo, passa limpo por qualquer política de permissão — é uso legítimo,
# repetido. O budget é a única peça daqui que percebe isso.
#
# LIMITAÇÃO QUE PRECISA ESTAR ESCRITA: budget da AWS NOTIFICA, não bloqueia.
# Nada aqui interrompe gasto; o que ele compra é o aviso a tempo de alguém
# entrar e desligar. Corte automático exigiria Budget Action com role própria —
# peso que não se justifica num teto de cinco dólares.
# ---------------------------------------------------------------------------

resource "aws_budgets_budget" "alderyn" {
  name = "${var.project_name}-mensal"

  # POR QUE COST e não USAGE: o que dói é a fatura. Orçar por uso exigiria saber
  # de antemão o preço por token de cada modelo para traduzir contagem em risco;
  # em dólar isso já vem somado e comparável.
  budget_type  = "COST"
  limit_amount = var.budget_limit_usd
  limit_unit   = "USD"

  # POR QUE MONTHLY: acompanha o ciclo de cobrança da AWS, então o número que
  # chega no e-mail é o mesmo número que aparece na fatura — não há conversão
  # mental no meio. Um período mais curto zeraria no meio do mês e daria falsa
  # sensação de folga justamente quando a fatura estivesse subindo.
  time_unit = "MONTHLY"

  # ALERTA 1 — o gasto REAL passou de 80% do teto.
  # POR QUE 80 e não 100: em 100% o dinheiro já saiu, e o aviso é só uma
  # constatação. Em 80% ainda existe margem para entrar, olhar o CloudTrail pelo
  # nome do user e matar o que está rodando antes de estourar.
  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 80
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.alert_email]
  }

  # ALERTA 2 — a PROJEÇÃO do mês estoura 100% do teto.
  # POR QUE previsto ALÉM do real, e não em vez dele: o real é honesto mas
  # lento; num teto baixo ele só cruza 80% quando o desperdício já aconteceu. O
  # previsto dispara no dia 3, quando o RITMO de gasto indica que o mês fecharia
  # acima do teto. É este que pega o laço infinito na primeira noite em vez de
  # na terceira semana.
  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = [var.alert_email]
  }
}
