# Runbook do dia D — ligar os embeddings do Alderyn

Este documento existe porque o raciocínio que produziu esta stack viveu em conversa, e conversa reseta. O que está escrito aqui foi medido, não lembrado. Onde não foi possível medir, está marcado com `?` em vez de preenchido por dedução.

O estado no momento em que isto foi escrito é o seguinte. A tabela `knowledge_fragments` tem 501 linhas e nenhuma delas tem embedding — a coluna existe, é `vector(1536)`, e está inteiramente nula. O texto que vira vetor é a concatenação de `titulo`, duas quebras de linha, e `conteudo`, o que dá cerca de 308 mil caracteres, estimados em aproximadamente 77 mil tokens. O modelo escolhido é `cohere.embed-v4:0` com `output_dimension` 1536. As três tabelas de `vector(768)` estão fora deste trabalho porque pertencem a outro espaço semântico, populado por um modelo local. As outras oito tabelas de 1536 somam 137 linhas e estão declaradas no script com `colunas_texto=None` de propósito: nenhuma delas tem `titulo` nem `conteudo`, e decidir qual texto alimenta o vetor de cada uma é uma decisão em aberto, não um item pendente de digitação.

Uma observação prática antes de começar. O `terraform` foi instalado via winget e **não está no PATH** desta máquina — checado, e é o tipo de detalhe que faz perder cinco minutos no começo. O binário fica sob o diretório de pacotes do winget; para localizá-lo sem procurar à mão:

```bash
find "$LOCALAPPDATA/Microsoft/WinGet/Packages" -name terraform.exe 2>/dev/null | head -1
```

Ou adicione ao PATH de uma vez, ou guarde o caminho numa variável e use `"$TF"` no lugar de `terraform` nos comandos abaixo. Os blocos usam sintaxe de shell POSIX, do Git Bash. No PowerShell, troque `export NOME=valor` por `$env:NOME = "valor"`.

## 1. O passo manual que o Terraform não faz

Comece por aqui, porque esta é a etapa que não está no código e que causa o erro mais confuso quando é esquecida.

Habilitar o acesso a um foundation model do Bedrock é uma ação de console, feita uma vez por conta e por região. O Terraform não a executa e não tem como executá-la. Entre no console da AWS, vá em **Bedrock → Model access → Manage model access**, localize o Cohere Embed v4 e habilite. A região do console precisa ser a mesma do `aws_region` da stack, que é `us-east-1` por padrão.

Sem esse passo, toda chamada volta `AccessDeniedException` **mesmo com a política IAM perfeitamente correta**. A mensagem não distingue os dois casos, e é aí que se perde tempo: a tendência natural é reler a política, que está certa, em vez de olhar o console. Faça isso primeiro e essa hipótese sai do caminho.

## 2. Terraform: init, plan, apply

Com o acesso ao modelo habilitado e uma credencial AWS de administrador disponível no ambiente, entre no diretório da stack e rode os três comandos na ordem. O `plan` não é cerimônia: ele é a última chance de ver o que vai ser criado antes de existir.

```bash
cd infra/aws
terraform init
terraform plan
terraform apply
```

O `apply` cria quatro coisas e nada além disso: um usuário IAM chamado `alderyn-embedder` sob o caminho `/service/`, uma política inline que permite exclusivamente `bedrock:InvokeModel` no ARN de um único modelo, um par de chaves de acesso para esse usuário, e um orçamento mensal de cinco dólares com alerta em 80% do real e 100% do previsto.

Terminado o apply, exporte as chaves para as variáveis que o boto3 procura por conta própria. O script de backfill nunca lê credencial de arquivo `.env`; ele usa a cadeia padrão do boto3, que é o que ferramenta de auditoria e rotação sabem inspecionar.

```bash
export AWS_ACCESS_KEY_ID=$(terraform output -raw access_key_id)
export AWS_SECRET_ACCESS_KEY=$(terraform output -raw secret_access_key)
export AWS_DEFAULT_REGION=$(terraform output -raw aws_region)
```

O `-raw` é necessário no `secret_access_key` porque ele está marcado como `sensitive`. Vale repetir o que o `outputs.tf` já diz: `sensitive` esconde o valor da saída de `plan` e `apply`, e não criptografa absolutamente nada — a chave está em texto claro dentro do `terraform.tfstate`, que por isso está bloqueado no `.gitignore`.

Confirme que a credencial chegou antes de gastar qualquer coisa:

```bash
aws sts get-caller-identity
```

Se o `aws` CLI não estiver instalado, o próprio script de backfill faz essa verificação e falha com mensagem explícita antes de chamar a API.

## 3. A cobaia de cinco linhas

Nunca rode as 501 direto. O script foi desenhado para tornar isso difícil de fazer por acidente: o modo padrão é ensaio, e mesmo com `--execute` o limite default é cinco.

Antes de gastar, rode o ensaio, que não chama a API e não escreve no banco. Ele lê as linhas, monta os textos, imprime os três primeiros truncados e estima os tokens.

```bash
python infra/aws/backfill_embeddings.py
```

Se o ensaio informar 501 linhas pendentes e algo em torno de 77 mil tokens, o caminho até o banco está bom. Agora a cobaia de verdade:

```bash
python infra/aws/backfill_embeddings.py --execute
```

Cinco linhas exercitam o caminho inteiro — credencial, acesso ao modelo, política do IAM, formato da resposta, validação de dimensão, o cast `::vector` e o commit. Por centavos. É deliberadamente barato descobrir aqui que algo está errado, em vez de na linha 400 de 501.

## 4. Conferir os cinco vetores antes de continuar

Não confie no "gravadas: 5" impresso na tela. Vá ao banco e olhe. A verificação precisa checar duas coisas distintas: que o vetor não é nulo, e que ele tem exatamente 1536 dimensões. A segunda é a que importa, porque um vetor de tamanho errado é aceito pela coluna apenas se casar com o tipo, e a checagem confirma que o que foi gravado é o que se esperava.

A função `vector_dims` foi confirmada disponível neste banco, que roda pgvector 0.8.0.

```sql
SELECT id,
       embedding IS NOT NULL          AS tem_vetor,
       vector_dims(embedding)         AS dimensoes,
       round(vector_norm(embedding)::numeric, 4) AS norma,
       atualizado_em
FROM knowledge_fragments
WHERE embedding IS NOT NULL
ORDER BY atualizado_em DESC
LIMIT 5;
```

As cinco linhas devem voltar com `tem_vetor` verdadeiro, `dimensoes` igual a 1536 e `atualizado_em` com a data de hoje. A `norma` está aí como sinal de vida: um vetor de zeros teria norma zero, e um vetor real fica bem longe disso.

O agregado que responde de uma vez se há algo torto no conjunto:

```sql
SELECT count(*)                                              AS com_vetor,
       count(*) FILTER (WHERE vector_dims(embedding) <> 1536) AS dimensao_errada,
       min(vector_dims(embedding))                            AS menor_dim,
       max(vector_dims(embedding))                            AS maior_dim
FROM knowledge_fragments
WHERE embedding IS NOT NULL;
```

O valor de `dimensao_errada` tem que ser zero. Se não for, pare: o script foi escrito para abortar a linha nesse caso em vez de truncar ou preencher com zero, então uma linha com dimensão errada gravada indicaria que algo saiu do desenho e merece investigação antes de multiplicar o problema por cem.

## 5. A carga completa

Só depois que as cinco estiverem conferidas. As 501 exigem o número digitado explicitamente — não existe atalho para "todas".

```bash
python infra/aws/backfill_embeddings.py --execute --limit 501
```

O script comita a cada dez linhas, então uma queda no meio não descarta o que já foi pago. A cláusula `WHERE embedding IS NULL` torna a operação idempotente: se cair, rode o mesmo comando de novo e ele retoma exatamente de onde parou, sem reprocessar nada. Não existe e não deve existir uma flag de forçar reprocessamento; o único motivo legítimo para regerar tudo é troca de modelo, e isso muda o espaço semântico inteiro, exigindo limpar a coluna de propósito.

Ao terminar, confirme que não sobrou nada:

```sql
SELECT count(*) FILTER (WHERE embedding IS NULL) AS ainda_sem_vetor,
       count(*) FILTER (WHERE embedding IS NOT NULL) AS com_vetor
FROM knowledge_fragments;
```

## 6. O índice HNSW, e só agora

Com as 501 gravadas e conferidas, crie o índice.

```bash
psql "$DATABASE_URL" -f infra/aws/create_hnsw_index.sql
```

A ordem não é preferência de estilo. HNSW é um grafo de navegação construído a partir dos vetores que existem no instante da criação. Criado antes do backfill, sobre uma coluna inteiramente nula, ele nasce vazio — e aí cada um dos 501 `UPDATE` seguintes paga o custo de inserir um nó no grafo, uma linha por vez, em vez de uma construção única em lote. O resultado é mais lento de produzir e pior de qualidade, porque um grafo montado incrementalmente fica menos bem conectado que um montado de uma vez com todos os pontos à vista.

O arquivo usa `vector_cosine_ops`, em consistência com os três índices vetoriais que já existem no banco. Isso importa além da estética: o operador do índice tem que casar com o operador da consulta, e um índice L2 é silenciosamente ignorado por uma query que usa distância de cosseno. O planner cai em sequential scan, ninguém recebe erro, e o sintoma é só latência.

O índice é criado apenas em `knowledge_fragments`. As outras oito tabelas de 1536 têm entre 3 e 51 linhas, e nesse volume o HNSW perde para o sequential scan — o planner corretamente o ignora, e o índice fica cobrando disco e desacelerando escrita sem entregar nada.

## 7. Religar o `query_vec` no jogo — escopo separado

Isto **não faz parte deste runbook** e não deve ser feito na mesma sessão. Está registrado aqui apenas para que a dependência não se perca.

Hoje o `jogo.py` tem `query_vec=None` fixo, e a busca semântica está desligada. Depois que os vetores existirem e o índice estiver criado, religar isso é um trabalho próprio, com seu próprio teste.

O ponto crítico dessa tarefa futura: a busca precisa vetorizar a pergunta com `input_type="search_query"`, enquanto este backfill indexa com `input_type="search_document"`. São espaços vetoriais diferentes, por desenho do modelo — é assim que uma pergunta fica próxima do parágrafo que a responde, em vez de próxima de outras perguntas. Usar o mesmo valor nos dois lados não gera erro em lugar nenhum: a API aceita, o Postgres aceita, o índice funciona, e o retrieval simplesmente fica ruim, em silêncio. O modelo e a dimensão também precisam bater exatamente: `cohere.embed-v4:0` a 1536.

## Risco conhecido nº 1 — o sufixo `:0` do model id

A documentação da AWS é ambígua quanto ao identificador do modelo. A prosa da página do Embed v4 diz que o model id é `cohere.embed-v4`, sem sufixo, enquanto os exemplos de código da mesma página usam `cohere.embed-v4:0`. A stack adotou a forma com `:0`, que é a dos exemplos de código, e ela aparece em dois lugares que precisam concordar: o ARN da política em `iam.tf` e a variável `embedding_model_id`.

O que torna isso perigoso é o sintoma. Se o sufixo estiver errado, o ARN da política não casa com o recurso invocado, e o retorno é `AccessDenied` — que parece problema de permissão, não de nome de modelo. Some-se a isso que a falta do passo de model access do item 1 produz um erro parecido, e há duas causas distintas competindo pela mesma mensagem.

A regra de diagnóstico, então, é esta. Se vier `AccessDenied` **com o model access já habilitado no console**, o suspeito número um é o sufixo do model id, não a política IAM. Para testar, troque o valor e reaplique — a variável existe exatamente para que isso seja uma linha, não uma edição de código:

```bash
terraform apply -var="embedding_model_id=cohere.embed-v4"
```

Se passar a funcionar, fixe o valor novo no default do `variables.tf` para que a próxima pessoa não repita a descoberta.

## Risco conhecido nº 2 — o formato da resposta

A documentação oficial se contradiz sobre a forma do campo `embeddings` na resposta. A prosa afirma que pedir um único `embedding_types` devolve uma lista de listas, com `response_type` igual a `embeddings_floats`, e que apenas vários tipos devolvem um objeto indexado pelo tipo. Mas o exemplo de código da mesma página, usando `embedding_types = ["float"]` — um tipo só —, itera o resultado como se fosse dicionário.

Não é possível decidir pela documentação qual das duas formas chega no nosso caso, e sem credencial AWS não houve como testar contra a API real. Por isso o `extrair_vetores` do script aceita as duas formas deliberadamente. Isso não é excesso de zelo: é a documentação não permitindo escolher.

A cobaia de cinco linhas do item 3 é o que resolve isso na prática, e é mais um motivo para ela existir. Se chegar uma terceira forma, não prevista por nenhuma das duas leituras, o script levanta um `ValueError` explicado dizendo o que veio — em vez de gravar lixo no banco em silêncio, que é o desfecho ruim de verdade.

## Correção registrada — não rode `terraform destroy` nesta stack

Em conversa anterior ficou recomendado destruir a stack ao fim de cada sessão, como higiene de ambiente efêmero. **Isso está errado para esta stack, e a correção fica registrada aqui porque conversa reseta e hábito permanece.**

O raciocínio original vale para infraestrutura que cobra por tempo ligado. Não é o caso do que existe aqui. Um usuário IAM não custa nada por existir. Uma política não custa nada. Um orçamento da AWS não custa nada — ele é o mecanismo que avisa sobre custo, não uma fonte dele. A única coisa que gera fatura nesta stack é a invocação do modelo, que é cobrada por token consumido e não por recurso provisionado. Destruir e recriar não economiza um centavo.

E há um custo real em destruir. Se o `query_vec` do jogo passar a chamar o Bedrock em tempo de execução para vetorizar a pergunta do jogador, essa chamada precisa de uma credencial viva. `terraform destroy` apaga o usuário IAM e revoga a chave, o que desligaria a busca semântica do jogo — em produção, sem aviso, e com um sintoma que parece bug de aplicação. Trocar a chave também obriga a reexportar as variáveis de ambiente em todo lugar que as consome.

O `destroy` volta a fazer sentido na Etapa 3, quando houver ECS. Aí sim existe recurso que cobra por hora ligada, e derrubar o que não está em uso passa a economizar dinheiro de verdade. Até lá, o que protege o bolso é o orçamento do item 2 e o escopo da política, que impede a chave de invocar qualquer modelo além deste.

## Ordem resumida

Habilite o model access no console. Rode `init`, `plan` e `apply`, e exporte as três variáveis. Rode o ensaio sem flag nenhuma. Rode `--execute` para a cobaia de cinco. Confira as cinco no banco com as queries do item 4. Rode `--execute --limit 501`. Confira que não sobrou nula nenhuma. Só então crie o índice HNSW. Religar o `query_vec` fica para outro dia e outra sessão.
