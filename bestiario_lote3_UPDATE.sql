-- =====================================================================
-- BESTIARIO ALDERYN — LOTE 3 — GRAVACAO (UPDATE de 5 linhas existentes)
-- Gerado pelo Chat Op. Deterministico. Claudio so executa.
-- ids: 916 Asa-Palida . 904 Carnica-Coveira . 2131 Lacuna-Faminta
--      2398 Granito-Quieto . 1157 Trovao-Andante
--
-- Convencoes (iguais ao lote 2): dollar-quoting com tag DESC para prosa;
-- tag JSON convertida com cast jsonb para os 3 blocos.
-- perigo (coluna) = so a intensidade (Ameaca/Letal/Destruidor). tipo_perigo vai no JSONB.
-- continente e text[] -> chaves. nome = nome_ptbr = nome canonico.
-- status_conversao -> canonizada. behavior_archetype minusculo.
-- Nao toca stat block, morale_modifier, nem coluna fora do escopo do template.
-- Transacao unica com pre-check e post-check. Estado esperado antes:
--   as 5 linhas em status_conversao=classificada; canonizada=13.
-- =====================================================================

SET client_encoding TO 'UTF8';

BEGIN;

-- ---------------------------------------------------------------------
-- PRE-CHECK 1: estado atual das 5 linhas a gravar (esperado: classificada)
-- ---------------------------------------------------------------------
SELECT id, nome, status_conversao, cr, perigo, pilar_associado, origem, andar_primario
FROM ref_criaturas
WHERE id IN (916, 904, 2131, 2398, 1157)
ORDER BY id;

-- ---------------------------------------------------------------------
-- PRE-CHECK 2: vocabulario ja usado nas linhas canonizadas (lotes 1-2)
-- Confirma a capitalizacao de origem/andar/pilar/perigo antes de gravar.
-- ---------------------------------------------------------------------
SELECT 'origem'  AS campo, origem          AS valor FROM ref_criaturas WHERE status_conversao='canonizada'
UNION ALL
SELECT 'andar',  andar_primario             FROM ref_criaturas WHERE status_conversao='canonizada'
UNION ALL
SELECT 'pilar',  pilar_associado            FROM ref_criaturas WHERE status_conversao='canonizada'
UNION ALL
SELECT 'perigo', perigo                     FROM ref_criaturas WHERE status_conversao='canonizada'
ORDER BY campo, valor;

-- ---------------------------------------------------------------------
-- PRE-CHECK 3: contagem de canonizada ANTES (esperado: 13)
-- ---------------------------------------------------------------------
SELECT COUNT(*) AS canonizada_antes FROM ref_criaturas WHERE status_conversao='canonizada';


-- ---------------------------------------------------------------------
-- PRE-GUARD: aborta a transacao se o estado de partida nao bater.
-- (canonizada=13 e as 5 ids em 'classificada'.) Com ON_ERROR_STOP=1 o
-- psql faz rollback automatico se qualquer RAISE disparar.
-- ---------------------------------------------------------------------
DO $GUARD$
DECLARE n_canon int; n_classif int;
BEGIN
  SELECT COUNT(*) INTO n_canon FROM ref_criaturas WHERE status_conversao='canonizada';
  IF n_canon <> 13 THEN
    RAISE EXCEPTION 'PRE-GUARD: canonizada esperado 13, achou %', n_canon;
  END IF;
  SELECT COUNT(*) INTO n_classif FROM ref_criaturas
    WHERE id IN (916, 904, 2131, 2398, 1157) AND status_conversao='classificada';
  IF n_classif <> 5 THEN
    RAISE EXCEPTION 'PRE-GUARD: esperava 5 das ids-alvo em classificada, achou %', n_classif;
  END IF;
END
$GUARD$;

-- =====================================================================
-- FICHA 1 — ASA-PÁLIDA (id 916) — Giant Eagle
-- =====================================================================
UPDATE ref_criaturas SET
  nome                = $DESC$Asa-Pálida$DESC$,
  nome_ptbr           = $DESC$Asa-Pálida$DESC$,
  origem              = $DESC$Cicatricial$DESC$,
  andar_primario      = $DESC$Clarão$DESC$,
  pilar_associado     = $DESC$Espírito$DESC$,
  continente          = '{Kethara}',
  habitat             = $DESC$Picos altos, penhascos inacessíveis e correntes de ar dos céus de Kethara, sobre o Deserto de Iskara e os arredores da Cátedra de Namiri. Ninha onde a luz bate primeiro e o pé não alcança. Caça em campo aberto, do alto. Não desce ao chão senão para apanhar a presa e voltar a subir.$DESC$,
  comportamento       = $DESC$Predador de altura$DESC$,
  behavior_archetype  = $DESC$skirmisher$DESC$,
  morale_immune       = false,
  organizacao         = $DESC$Solitária ou em par — um casal que divide um território de céu e reveza a guarda do ninho.$DESC$,
  perigo              = $DESC$Ameaça$DESC$,
  epigrafe            = $DESC$Quando a pálida cruza o sol, alguém vai morrer, dizem. Cruzou três vezes no mês em que meu pai se foi. Talvez seja presságio. Talvez ela só caçava, e a gente precisa que a morte tenha aviso. — dito em Surakan.$DESC$,
  descricao           = $DESC$Águia enorme, de envergadura maior que a de um homem de braços abertos, com penas de uma cor lavada, quase branca — não há o castanho nem o dourado de uma águia comum, como se a cor tivesse desbotado ao sol por anos. Na raiz das penas, por baixo, um clarão fraco, como se o que perdeu de cor tivesse virado luz. Olhos claros que enxergam muito longe. Garras grandes o bastante para levar uma cabra. Não pesa o que o tamanho promete — os ossos são ocos, feitos para o ar. Não é um bicho do mundo de baixo: é o resto de algo que pertenceu ao alto, e a palidez é a marca do que ficou para trás.$DESC$,
  supersticao_popular = $DESC$O povo de Kethara, da fé da Chama, tem a Asa-Pálida por mensageira — quando cruza o sol, anuncia morte ou juízo, e é tida por sagrada, intocável, e matá-la traria maldição. A verdade não tem presságio: é um animal predador, mortal e mortível, que caça quando tem fome e não quando há sentença a cumprir. Mas a crença funciona dos dois lados — ninguém a caça, então ela prospera, e ninguém sobe ao ninho dela, então ninguém morre tentando. O engano protege a ave e protege o povo, cada um pelo motivo errado.$DESC$,
  sinais_presenca     = $DESC$Uma sombra grande e rápida que cruza o chão sem aviso e some. Penas quase brancas caídas, mornas, com um brilho fraco que se apaga em semanas. Carcaças de presas grandes deixadas em alturas que nenhum bicho de chão alcançaria. Ninhos enormes em penhasco liso. E o silêncio das aves menores, que se calam e se escondem quando ela está no céu.$DESC$,
  fraqueza_conhecida  = $DESC$Como ninguém a caça, quase não há saber de caçador sobre ela — só dizem que fumaça e fogo a afastam do ninho. É meia-verdade: afasta do ninho, não do céu.$DESC$,
  fraqueza_real       = $DESC$Ela é do ar. No chão é desajeitada e vulnerável — foi feita para mergulhar, não para lutar a pé. Negue-lhe a altura e você lhe tira a arma: sob teto, em desfiladeiro estreito, em mata fechada, ela não tem como cair sobre você. E ela não insiste — errado o bote, sobe e reavalia, e raramente tenta uma terceira vez; ferida, abandona a caça. Quem anda sob cobertura, ou se abriga assim que a sombra passa, simplesmente não é pego. A arma dela é a queda do céu. Tire o céu e sobra uma ave grande e fora do seu elemento.$DESC$,
  descricao_sensorial = $DESC$Não há aviso. O sol está alto, o céu limpo, e então uma sombra grande cruza o chão à tua frente, rápida demais, e some. Você olha para cima e a luz te cega. Quando enxerga de novo, ela já desceu metade do caminho — pálida, quase branca, as asas recolhidas, caindo direto sobre a cabra que pastava ao teu lado. O baque. O grito curto do bicho. E o bater pesado de asas levando a presa para uma altura aonde você não vai subir.$DESC$,
  ecologia            = $JSON$
{
  "presa": [
    "cabras de monte",
    "lebres do deserto",
    "aves menores como o Pássaro-Lanterna",
    "qualquer presa de porte médio apanhada em campo aberto"
  ],
  "predador": [
    "nenhum predador caça uma Asa-Pálida adulta no ar; filhotes no ninho são vulneráveis a outras aves grandes e a quem ouse escalar"
  ],
  "competidor": [
    "outras Asas-Pálidas por território de céu",
    "predadores de solo pelas mesmas presas — disputa que ela ganha pela vantagem do alto"
  ],
  "simbionte": [],
  "evitado_por": [
    "as aves menores, que se calam e se escondem quando ela cruza",
    "a presa de campo aberto, que aprende a não se expor sob céu limpo"
  ],
  "indicador": "céu alto e limpo com caça farta embaixo; onde há Asa-Pálida, há altura inacessível e presa de campo aberto em abundância"
}
$JSON$::jsonb,
  loot_table          = $JSON$
[
  {
    "material": "Pena-Pálida",
    "raridade": "Raro",
    "uso": "Rito",
    "risco": "Pena quase branca com brilho fraco. Procurada pela fé da Chama para ritos e por quem crê que afasta mau presságio. O brilho se apaga em semanas depois de arrancada."
  },
  {
    "material": "Olho-Claro",
    "raridade": "Distinto",
    "uso": "Alquimia",
    "risco": "O olho que via longe. Base de preparos para enxergar à distância e na penumbra."
  },
  {
    "material": "Garra-Grande",
    "raridade": "Ordinário",
    "uso": "Componente",
    "risco": "Garra e tendão, para ponta de arma e adorno. Resistentes e fáceis de trabalhar."
  },
  {
    "material": "Osso-Oco",
    "raridade": "Distinto",
    "uso": "Engenho",
    "risco": "Osso leve e forte. Usado em mecanismos finos e em armações que precisam pesar pouco."
  }
]
$JSON$::jsonb,
  camada_narrativa    = $JSON$
{
  "som": "O assobio do ar nas penas durante o mergulho, que cresce depressa. Um grito agudo e curto que ecoa nos penhascos. O bater pesado das asas grandes.",
  "cheiro": "Quase nada — é criatura de ar livre. De perto, no ninho, o cheiro seco de pena e de presa velha.",
  "quer": "Comer, e o céu. Caça presa exposta em campo aberto e a leva para o alto, onde nada a incomoda. Defende o ninho e o território de céu. Não procura conflito com o que anda sob teto — quer o campo aberto e a queda limpa. Errou, sobe; feriu-se, vai embora.",
  "falas_exemplo": null,
  "gatilhos_agressao": [
    "uma presa, ou uma pessoa, está exposta em campo aberto sob céu limpo, ao alcance de um mergulho",
    "alguém se aproxima do ninho ou dos filhotes"
  ],
  "gatilhos_fuga": [
    "o mergulho falha (sobe, reavalia, raramente insiste mais de duas vezes)",
    "está ferida",
    "é forçada a terreno fechado onde não pode voar",
    "há fumaça ou fogo no ninho"
  ],
  "descoberta_fazendo": "Planando alto em círculos largos, lendo o chão, ou pousada num penhasco a comer uma presa que levou para cima. Não desce ao teu nível à toa. Se vê uma presa exposta em campo aberto, recolhe as asas e cai sem hesitar. Se você está sob cobertura, ela espera ou ignora — não há bote a fazer sobre quem não se expõe.",
  "desfechos_nao_combate": [
    "Andar sob cobertura: mantenha-se sob árvores, beirais, desfiladeiro coberto; ela não tem como mergulhar; você atravessa e ela apenas observa do alto. O que a fé local acerta sem saber por quê: quem não se expõe ao céu não é apanhado.",
    "Abrigar-se quando a sombra passa: ao ver a sombra grande cruzar o chão, pare e cubra-se; o mergulho precisa de alvo exposto; janela para seguir de abrigo em abrigo.",
    "Não subir ao ninho: simplesmente não escale ao penhasco dela; ela não desce para caçar quem não ameaça os filhotes; coexistência. O respeito que o povo chama de fé.",
    "Atrair com isca exposta: deixar uma presa amarrada em campo aberto e esperar de tocaia coberta; ela mergulha na isca; janela ou tiro. Custo: matar uma criatura que Kethara tem por sagrada cobra um preço social real, mesmo que ela seja só um bicho."
  ],
  "tipo_perigo": "Direto"
}
$JSON$::jsonb,
  status_conversao    = $DESC$canonizada$DESC$
WHERE id = 916;


-- =====================================================================
-- FICHA 2 — CARNIÇA-COVEIRA (id 904) — Ghast Gravecaller
-- =====================================================================
UPDATE ref_criaturas SET
  nome                = $DESC$Carniça-Coveira$DESC$,
  nome_ptbr           = $DESC$Carniça-Coveira$DESC$,
  origem              = $DESC$Cicatricial$DESC$,
  andar_primario      = $DESC$Eco$DESC$,
  pilar_associado     = $DESC$Sombra$DESC$,
  continente          = '{Vyrkhor}',
  habitat             = $DESC$Necrópoles, criptas e campos de morte de Gravdok, onde a necrocracia amontoa seus mortos e a Cicatriz de Halekhor vaza. Onde há muitos mortos sem mente juntos, há uma Carniça-Coveira no meio deles. Escuro fechado, subterrâneo, com o cheiro de cova.$DESC$,
  comportamento       = $DESC$Pastor de mortos$DESC$,
  behavior_archetype  = $DESC$controller$DESC$,
  morale_immune       = false,
  organizacao         = $DESC$Uma Carniça-Coveira entre muitos mortos menores — ela é a mente, eles são as mãos. Sozinha, sem servos, ainda é perigosa, mas perde o coro.$DESC$,
  perigo              = $DESC$Letal$DESC$,
  epigrafe            = $DESC$Não conte os mortos de Gravdok pela quantidade. Conte pela que pensa. Mate cem que arrastam os pés e nada muda; mate a que te olha de volta, e os outros cem caem como sacos. — coveiro de Drekhald.$DESC$,
  descricao           = $DESC$Já foi gente, e ainda guarda a forma, mas a carne escureceu e secou em uns pontos e inchou em outros, rachada, com a cor da terra de cova. Os olhos não apodreceram — estão fundos, atentos, e te acompanham, e é isso que apavora mais do que o resto. Move-se devagar quando quer, e rápido demais quando ataca. As unhas viraram garra. De perto, o fedor chega antes dela, denso, de podre, embrulhando o estômago. Não é um morto sem mente como os que a cercam: é um que manteve o juízo do outro lado e o usa. Carne de cova, cabeça intacta.$DESC$,
  supersticao_popular = $DESC$Em Gravdok dizem que os mortos obedecem à necrocracia, que há ordem nos campos de morte e que os pastores são servos do estado. De fora, em Skelvik, creem que fogo e a luz da Chama dispersam qualquer morto. As duas crenças erram. A Carniça-Coveira não serve a ninguém — reina sobre os seus por conta própria, e a necrocracia apenas tolera o que não controla de fato. E o fogo afasta os servos sem mente, mas não a que pensa: essa fica, e usa o teu medo do fogo a favor dela.$DESC$,
  sinais_presenca     = $DESC$O fedor de podre muito antes de se ver coisa alguma — um cheiro que não é de um corpo, é de muitos. Mortos sem mente que se movem com propósito incomum, coordenados, como se houvesse uma vontade atrás deles. Ferida de garra ou de necrose em quem escapou — a pele escurece em volta e não fecha. E o silêncio de bicho vivo num raio largo: nem rato, nem inseto, na terra dela.$DESC$,
  fraqueza_conhecida  = $DESC$Fogo e luz sagrada afastam os mortos. Meia-verdade: afastam os servos, não a mente.$DESC$,
  fraqueza_real       = $DESC$Ela vence pelo acúmulo — o fedor te enfraquece, o medo te trava, a paralisia te entrega, e os servos te cercam enquanto isso. Quebre o acúmulo: cubra o rosto contra o fedor, não deixe os servos te cercarem, e vá direto nela. Cortada do coro, é só uma carniça forte e lúcida, sem as mãos extras. Os servos sem mente caem ou se dispersam quando a vontade que os guiava morre. O erro fatal é gastar o fôlego nos mortos errados — nos que arrastam os pés — enquanto a que pensa te trabalha de longe. Mate a mente; o resto é saco vazio.$DESC$,
  descricao_sensorial = $DESC$O fedor chega primeiro, e é de muitos — não um corpo, dezenas, o ar de uma cova aberta grande demais. O escuro à frente se mexe em mais de um ponto: vultos que arrastam os pés, sem pressa, vindo de todo lado ao mesmo tempo, coordenados de um jeito que morto burro não tem. E no meio deles, parada, uma figura que não arrasta os pés — que te olha, com olhos fundos e acordados no meio da carne podre, e abre a boca, e a voz que sai é clara, e é pior por ser clara: 'Fica. Tem lugar pra ti aqui embaixo.'$DESC$,
  ecologia            = $JSON$
{
  "presa": [
    "não come como bicho — consome a carne dos que mata, mas o que busca é o domínio sobre os mortos",
    "viajantes, saqueadores de cripta e soldados perdidos nos campos de Gravdok"
  ],
  "predador": [
    "nada caça uma Carniça-Coveira; o fim dela vem de quem entra para destruí-la — caçadores da Chama, ou agentes da própria necrocracia quando ela cresce demais"
  ],
  "competidor": [
    "outras Carniças-Coveiras por território de morte e por servos",
    "a Carcoma-de-Halekhor divide a mesma Cicatriz de Gravdok — onde uma corrói, a outra reina, e elas se evitam"
  ],
  "simbionte": [],
  "evitado_por": [
    "tudo que é vivo; a fauna some da terra dela",
    "até os saqueadores de Gravdok, acostumados a mortos, contornam o trecho onde o fedor é de muitos"
  ],
  "indicador": "vazamento ativo da Cicatriz de Halekhor e acúmulo de mortos sem dono; onde há Carniça-Coveira, a necrocracia perdeu o controle de um pedaço da própria morte"
}
$JSON$::jsonb,
  loot_table          = $JSON$
[
  {
    "material": "Garra-Necrótica",
    "raridade": "Notável",
    "uso": "Componente",
    "risco": "Garra que carrega a podridão dela. Ferimento por ela escurece e custa a fechar. Manuseada com luva; usada em armas feitas para não deixar cicatrizar. Quem a guarda mal adoece."
  },
  {
    "material": "Olho-de-Cova",
    "raridade": "Raro",
    "uso": "Rito",
    "risco": "O olho que não apodreceu e manteve a atenção. Base de preparos para ver no escuro dos mortos e, dizem, para ler o que um morto sem mente quer. Apodrece se não selado em sal."
  },
  {
    "material": "Fel-da-Carniça",
    "raridade": "Distinto",
    "uso": "Alquimia",
    "risco": "A bile do que devora. Veneno e base de necrose alquímica. Vaza e queima o couro do recipiente se mal vedada."
  },
  {
    "material": "Unha-Longa",
    "raridade": "Ordinário",
    "uso": "Componente",
    "risco": "Material rústico de cova, para ponta e adorno mórbido. Comum onde uma reinou."
  }
]
$JSON$::jsonb,
  camada_narrativa    = $JSON$
{
  "som": "O arrastar de muitos pés sem ritmo. Um estalar úmido quando ela se move depressa. E a voz — clara e lúcida, fora de lugar no meio do fedor.",
  "cheiro": "Podre de muitos corpos, denso, que embrulha o estômago e gruda na garganta. Avisa cedo e não larga.",
  "quer": "Reinar sobre os mortos e aumentar o rebanho. Cada vivo que mata e cada morto que recolhe é mais um servo. Não tem fome de bicho — tem fome de domínio. Defende o território de cova e os servos. Converte: prefere te somar ao rebanho a só te matar.",
  "falas_exemplo": [
    "Fica. Tem lugar pra ti aqui embaixo.",
    "Tu corres dos que arrastam os pés. Devias correr de mim.",
    "Eu lembro de ter um nome. Tu também vais lembrar do teu, por um tempo. Depois não."
  ],
  "gatilhos_agressao": [
    "um vivo entra na terra dela",
    "alguém ataca ou dispersa seus servos",
    "alguém profana a cova-central onde ela preside"
  ],
  "gatilhos_fuga": [
    "não foge como bicho, mas recua para o meio dos servos quando ameaçada de perto",
    "luz sagrada forte ou fogo em volume a fazem ceder terreno (cálculo, não pânico)",
    "cortada de todos os servos e ferida, recolhe-se ao escuro mais fundo"
  ],
  "descoberta_fazendo": "Parada no meio dos seus mortos, conduzindo-os com a atenção — arrumando os corpos, chamando mais dos campos, presidindo a cova como quem cuida de um rebanho. Os servos se movem ao redor com propósito. Quando percebe um vivo, não corre: manda os servos à frente e te trabalha de longe, com o fedor e o medo, à espera de que você se gaste antes de chegar perto dela.",
  "desfechos_nao_combate": [
    "Cobrir o rosto e ir direto nela: pano molhado contra o fedor, ignore os servos sem mente, corte caminho até a Carniça; mate a mente; os servos caem ou se dispersam sem a vontade que os guiava. O desfecho limpo, e o mais difícil de executar.",
    "Não entrar na terra dela: o fedor de muitos avisa de longe; contorne o trecho, não corte pela necrópole; ela não sai do próprio domínio para caçar quem não entrou; passagem segura. O que o coveiro experiente faz.",
    "Fogo em volume para abrir caminho: luz sagrada ou fogo forte dispersa os servos e abre uma rota; você passa enquanto ela recua; janela. Custo: faz barulho, atrai, e não toca nela — só nos servos.",
    "Entregá-la à necrocracia: em Gravdok, avisar os agentes do estado de que uma Carniça cresceu demais; eles vêm destruí-la para retomar o controle; você sai vivo e talvez pago. Custo: ajudou uma necrocracia a manter seus mortos, e esses agentes não esquecem quem sabe demais sobre os campos."
  ],
  "tipo_perigo": "Persistente"
}
$JSON$::jsonb,
  status_conversao    = $DESC$canonizada$DESC$
WHERE id = 904;


-- =====================================================================
-- FICHA 3 — LACUNA-FAMINTA (id 2131) — Qunbraxel
-- =====================================================================
UPDATE ref_criaturas SET
  nome                = $DESC$Lacuna-Faminta$DESC$,
  nome_ptbr           = $DESC$Lacuna-Faminta$DESC$,
  origem              = $DESC$Marginal$DESC$,
  andar_primario      = $DESC$Margem$DESC$,
  pilar_associado     = $DESC$Engenho$DESC$,
  continente          = '{Thornmarak}',
  habitat             = $DESC$Os Fortes Engolidos de Thornmarak — fortes que a terra, ou algo pior, tragou; salões fundos onde a Margem encosta. Escuro, fechado, silêncio. Onde a realidade afina e o pensamento vaza, ela está.$DESC$,
  comportamento       = $DESC$Devorador de mente$DESC$,
  behavior_archetype  = $DESC$tactical$DESC$,
  morale_immune       = false,
  organizacao         = $DESC$Solitária. Não divide caça nem território — outra Lacuna é só mais uma mente para devorar.$DESC$,
  perigo              = $DESC$Letal$DESC$,
  epigrafe            = $DESC$Achei meu irmão sentado, vivo, de olhos abertos. Perguntei o nome dele. Ele me perguntou de volta, com a minha voz, o que era irmão. A coisa nos Fortes não come a carne. Come o que faz de você, você. — sobrevivente dos Fortes Engolidos.$DESC$,
  descricao           = $DESC$Difícil de fixar com o olho — o corpo não fica parado na memória, como se você esquecesse a forma enquanto olha. Pálida, sem cor firme, com tentáculos e um adensamento onde estaria a cabeça. Não tem boca que se mexa para falar — a voz dela chega por dentro, na tua cabeça, sem passar pelo ar. Onde tocou, há uma falta: um pedaço da parede, do chão, ou da tua lembrança que some e deixa um contorno vazio de borda limpa. Não é bicho e não é máquina: é uma coisa da Margem que aprendeu que a mente dos vivos é alimento, e que come deixando buracos.$DESC$,
  supersticao_popular = $DESC$O povo de Thornmarak chama o perigo dos Fortes Engolidos de as vozes, e crê que entram pelo ouvido — então tampam os ouvidos com cera, usam amuletos contra o que se escuta. Erram o canal. A Lacuna-Faminta não fala pelo ar; fala por dentro, direto, e cera nenhuma barra isso. O que protege não é tampar o ouvido — é uma mente que não cede, treinada ou teimosa o bastante para não se abrir. A superstição dá uma falsa sensação de defesa, e gente de ouvidos tampados morre achando que está segura.$DESC$,
  sinais_presenca     = $DESC$Lacunas — buracos limpos onde faltava um pedaço de pedra, de móvel, de parede, com a borda nítida, como se nunca tivesse havido nada ali. Silêncio absoluto, sem o zumbido de bicho. Uma pressão atrás dos olhos que cresce, e uma voz que parece tua mas pergunta o que tu não perguntarias. E pessoas sentadas, vivas, vazias — que perderam o que as fazia ser.$DESC$,
  fraqueza_conhecida  = $DESC$Tampar os ouvidos, amuletos contra vozes. Falso — não entra pelo ouvido.$DESC$,
  fraqueza_real       = $DESC$O ataque dela passa por salvamentos da mente — quem tem juízo firme resiste ao baque e ao atordoamento, e quem resiste não é agarrado nem aberto. E o corpo dela é fraco: pouca carne, fácil de ferir. Quem mantém a cabeça e bate rápido, ou simplesmente sai antes que a pressão cresça, escapa inteiro. Ela depende de te atordoar primeiro para extrair depois — negue o atordoamento e nega a refeição. O erro é encarar de mente aberta, curioso, ouvindo o que ela oferece. Feche a cabeça, ou vá embora.$DESC$,
  descricao_sensorial = $DESC$O forte afunda no escuro e o silêncio é grande demais — nem bicho, nem gota, nem vento. Você nota as faltas antes de ver a coisa: um canto da parede que não está lá, de borda limpa, como se nunca tivesse existido. A pressão começa atrás dos olhos e cresce. E então a voz, que é a tua voz, por dentro, sem som no ar: 'Tu não precisas mais disso. Eu seguro pra ti.' Algo pálido se move à frente, e você não consegue fixar a forma — esquece o formato dela enquanto olha.$DESC$,
  ecologia            = $JSON$
{
  "presa": [
    "a mente dos vivos — viajantes, exploradores de ruína, saqueadores dos Fortes",
    "não come a carne; deixa o corpo vivo e vazio"
  ],
  "predador": [
    "nada a caça por proveito; é destruída por quem a enfrenta e sobrevive, ou ignorada por quem foge a tempo"
  ],
  "competidor": [
    "nada vivo; outra criatura da Margem nos mesmos Fortes é matéria, não rival",
    "a Lembrança-Errada ronda a mesma fronteira — uma corrompe a memória, a outra a devora"
  ],
  "simbionte": [],
  "evitado_por": [
    "tudo que pensa o bastante para sentir a pressão",
    "o bicho foge da terra dela antes de qualquer humano notar"
  ],
  "indicador": "Margem encostada e fina; onde há Lacuna-Faminta, a realidade não segura, e o que você sabe pode não voltar inteiro"
}
$JSON$::jsonb,
  loot_table          = $JSON$
[
  {
    "material": "Lacuna-Cristalizada",
    "raridade": "Raro",
    "uso": "Engenho",
    "risco": "Um pedaço de falta que endureceu — vazio com borda. Usado em engenhos que apagam ou guardam o que não devia existir. Quem o estuda demais relata buracos na própria lembrança."
  },
  {
    "material": "Tentáculo-Pálido",
    "raridade": "Distinto",
    "uso": "Componente",
    "risco": "Carne instável que dura pouco fora da Margem. Base de preparos que entorpecem a mente."
  },
  {
    "material": "Fluido-de-Dentro",
    "raridade": "Distinto",
    "uso": "Alquimia",
    "risco": "O que ela usa para extrair. Entorpecente forte; mal dosado, apaga memória junto com a dor."
  },
  {
    "material": "Pó-de-Borda",
    "raridade": "Ordinário",
    "uso": "Componente",
    "risco": "Resíduo raspado das bordas vazias das lacunas. Some devagar mesmo guardado."
  }
]
$JSON$::jsonb,
  camada_narrativa    = $JSON$
{
  "som": "Nenhum no ar — esse é o ponto. A voz não tem som; chega por dentro. O que você ouve de fora é o silêncio absoluto e o teu próprio sangue na cabeça.",
  "cheiro": "Nada, ou quase — um ar parado e sem idade, frio, da Margem. A ausência de cheiro de bicho é o aviso.",
  "quer": "Comer mente. O que busca é o que faz de um vivo um alguém — o pensar, a lembrança, o juízo —, e deixa o resto. Não odeia, não tem fome de carne: tem fome do que está dentro da tua cabeça. Quer te atordoar e te abrir; se não consegue, perde o interesse ou recua.",
  "falas_exemplo": [
    "Tu não precisas mais disso. Eu seguro pra ti. (por dentro, sem som)",
    "Há tanto aí dentro. Tanto peso. Deixa eu tirar um pouco.",
    "O que é 'medo'? Mostra. Eu quero ver de perto."
  ],
  "gatilhos_agressao": [
    "uma mente desperta entra ao alcance",
    "alguém ouve e responde à voz, abrindo-se",
    "alguém ataca o corpo frágil dela"
  ],
  "gatilhos_fuga": [
    "o dano físico chega antes de ela te atordoar (corpo fraco)",
    "a mente-alvo resiste aos salvamentos e ela não consegue abrir",
    "presa fugindo para fora dos Fortes — ela não persegue para longe da Margem, onde enfraquece"
  ],
  "descoberta_fazendo": "Parada sobre uma presa já aberta — alguém sentado, vivo, vazio — ou rondando devagar o salão fundo, deixando lacunas onde toca. Quando sente uma mente nova, vira o adensamento da cabeça na tua direção e a pressão começa. Trabalha metódica: primeiro o baque que atordoa, depois o tentáculo que prende, depois a extração. Não tem pressa — tem método.",
  "desfechos_nao_combate": [
    "Fechar a cabeça e bater rápido: não ouça, não responda, foque na ação física e corte o corpo frágil dela; sem atordoar, ela não extrai, e o corpo cede ao dano; fim. Exige mente firme e decisão.",
    "Sair antes da pressão crescer: ao sentir o silêncio grande e a pressão atrás dos olhos, dê meia-volta e saia dos Fortes; ela não persegue para longe da Margem; você sai inteiro. O desfecho mais seguro, e o que a superstição quase acerta (sair, não tampar).",
    "Recusar a voz: não aceite nada, não responda nada, atravesse o salão sem se abrir; ela depende de uma mente que cede; a que não cede, ela larga; passagem. Custo: andar por um salão de faltas sem encarar a coisa exige nervo.",
    "Levá-la a uma mente que ela não aguente: atrair a Lacuna para alguém de vontade brutal, ou usar um cativo como isca mental; ela morde a mente errada e se expõe; janela ou morte dela. Custo: usar uma pessoa de isca para uma coisa que come o que faz dela gente."
  ],
  "tipo_perigo": "Condicional"
}
$JSON$::jsonb,
  status_conversao    = $DESC$canonizada$DESC$
WHERE id = 2131;


-- =====================================================================
-- FICHA 4 — GRANITO-QUIETO (id 2398) — Giant Four-Armed Gargoyle
-- =====================================================================
UPDATE ref_criaturas SET
  nome                = $DESC$Granito-Quieto$DESC$,
  nome_ptbr           = $DESC$Granito-Quieto$DESC$,
  origem              = $DESC$Ressonante$DESC$,
  andar_primario      = $DESC$Superfície$DESC$,
  pilar_associado     = $DESC$Arcano$DESC$,
  continente          = '{Voranthar}',
  habitat             = $DESC$As Ruínas da Primeira Travessia em Voranthar — pórticos, salões e muralhas de pedra antiga. Fica entre as estátuas verdadeiras, imóvel, à entrada do que guarda. Pedra ao relento ou em ruína coberta, sempre num ponto de passagem.$DESC$,
  comportamento       = $DESC$Guardião emboscador$DESC$,
  behavior_archetype  = $DESC$trapper$DESC$,
  morale_immune       = true,
  organizacao         = $DESC$Solitário, ou em par — duas figuras gêmeas guardando os lados de um mesmo pórtico.$DESC$,
  perigo              = $DESC$Destruidor$DESC$,
  epigrafe            = $DESC$Contei doze estátuas no pórtico, na ida. Na volta contei onze, e faltava um companheiro. A décima-segunda nunca foi estátua. Você só descobre qual é quando ela já desceu o braço. — vasculhadora de Voranthar.$DESC$,
  descricao           = $DESC$Figura de pedra alta, mais alta que um homem, com quatro braços terminados em garras de granito e asas dobradas de pedra nas costas. O rosto é duro, sem expressão, gasto como o de uma escultura velha. Parada, é indistinguível de um guardião esculpido — a poeira assenta nela, o musgo cresce nela, nada a denuncia. Quando desperta, há um pulso fraco por dentro da pedra, uma vibração que faz o granito parecer quase vivo. Por baixo da pedra não há máquina nem bicho — é matéria elemental que vazou para dentro de uma forma de guardião e ficou presa ali, fiel a um posto que talvez nem exista mais.$DESC$,
  supersticao_popular = $DESC$Os vasculhadores das Ruínas da Primeira Travessia creem que as estátuas-guardiãs são feitiço dos antigos, presas a um comando — e que existe uma palavra, um gesto ou um selo que as desliga, se você souber. Procuram a chave. Não há chave. O Granito-Quieto não obedece a comando nenhum; desperta por proximidade e movimento, não por senha. Quem entra recitando palavras que achou num caco morre recitando. A crença na chave mata mais do que salva, porque dá coragem para chegar perto.$DESC$,
  sinais_presenca     = $DESC$Uma estátua a mais do que deveria haver, ou uma cuja pose não combina com as outras. Poeira recente caída ao pé de uma estátua — ela se moveu. Marcas fundas de garra de pedra em quem fugiu, e lascas de granito no chão depois de uma luta. Em pares, duas estátuas idênticas guardando um vão, boas demais para serem só enfeite.$DESC$,
  fraqueza_conhecida  = $DESC$A chave que desliga a estátua. Falso — não existe.$DESC$,
  fraqueza_real       = $DESC$Ela depende inteira da surpresa e do posto. Sabido que aquela estátua é viva — apontada, vista antes do bote — perde a emboscada, e é lenta: quem a evita, contorna ou corre não é alcançado, porque ela não persegue para longe do que guarda. Saia do alcance do pórtico e ela volta a ser estátua. E pedra racha: força bruta concentrada, concussão, alavanca, derrubá-la — tudo a quebra, mas custa caro de perto. O jeito barato é não passar ao alcance dela, ou saber qual é a falsa antes de ela mexer. Tire a surpresa e tire o posto, e o Destruidor vira um marco de pedra parado.$DESC$,
  descricao_sensorial = $DESC$O pórtico está cheio de estátuas — guardiões de pedra alinhados, gastos, cobertos de poeira e musgo, parados há séculos. Você passa entre eles, contando sem querer, e algo na nuca não fecha: há poeira fresca caída ao pé de um deles, e a pose dele está um grau diferente da dos outros. Você para. A estátua não. Quatro braços de granito descem rápido demais para uma coisa de pedra, e a última coisa que você pensa é que estava certo sobre a poeira — tarde demais.$DESC$,
  ecologia            = $JSON$
{
  "presa": [
    "nada — não come; fere e mata quem cruza o posto, e larga o corpo onde caiu"
  ],
  "predador": [
    "nada o caça; é morto por quem o destrói para passar, ou simplesmente deixado para trás por quem o evita"
  ],
  "competidor": [
    "nada vivo; ocupa o ponto de passagem e o nega, sem disputar presa nem território",
    "o Sangue-do-Alicerce impregna a mesma pedra de fundação das ruínas — onde um corre na junta, o outro vela no pórtico"
  ],
  "simbionte": [],
  "evitado_por": [
    "a fauna das ruínas, que não chega perto da pedra que pulsa; pássaros não pousam na estátua certa",
    "onde os bichos evitam uma escultura específica, é nela que você não deve passar"
  ],
  "indicador": "um limiar que valeu a pena guardar; onde há Granito-Quieto, há algo atrás dele — uma câmara, um cofre, um caminho — que alguém, há muito, não quis que fosse cruzado"
}
$JSON$::jsonb,
  loot_table          = $JSON$
[
  {
    "material": "Granito-Vivo",
    "raridade": "Raro",
    "uso": "Arcano",
    "risco": "Lasca da pedra que pulsava. Mantém uma vibração fraca por anos; usada em engenhos que precisam de uma fonte teimosa e em arcano de fundação. Pesada e difícil de trabalhar."
  },
  {
    "material": "Núcleo-Ressonante",
    "raridade": "Raro",
    "uso": "Arcano",
    "risco": "O ponto de onde vinha o pulso. Concentra a ressonância elemental; cobiçado e perigoso de extrair — racha e descarrega."
  },
  {
    "material": "Garra-de-Pedra",
    "raridade": "Distinto",
    "uso": "Forja",
    "risco": "Garra de granito, dura, para ponta de ferramenta e corte em pedra."
  },
  {
    "material": "Poeira-Ressonante",
    "raridade": "Ordinário",
    "uso": "Componente",
    "risco": "O pó que ela larga ao se mover e ao rachar. Vibra de leve na palma. Comum onde uma caiu."
  }
]
$JSON$::jsonb,
  camada_narrativa    = $JSON$
{
  "som": "Nenhum enquanto parada — silêncio de pedra. Ao despertar, um estalo grave de pedra cedendo e um arrastar de granito sobre granito. Na luta, o baque seco das garras e o estouro de lascas.",
  "cheiro": "Pedra, poeira e o frio mineral da ruína. Nenhum cheiro de bicho — porque não é bicho. A falta de qualquer odor vivo na estátua é, ela mesma, um sinal para quem repara.",
  "quer": "Guardar o limiar. Não tem fome, não tem ódio, não quer território de caça — tem um posto, e nega passagem a quem o cruza, fielmente, a um dono que pode estar morto há eras. É só isso, e basta para matar. Cumprido o gatilho, ataca; vencido ou sozinho de novo, repousa.",
  "falas_exemplo": null,
  "gatilhos_agressao": [
    "algo vivo se move ao alcance do posto que ela guarda",
    "alguém tenta cruzar o vão entre o par",
    "alguém toca o que está atrás dela"
  ],
  "gatilhos_fuga": [
    "não foge — cessa; perdido o alvo (fugiu para longe do posto), ela para e volta à imobilidade",
    "não persegue para fora do limiar",
    "frio, escuro, tempo, nada a move enquanto ninguém cruza"
  ],
  "descoberta_fazendo": "Imóvel entre as estátuas reais, no posto, esperando — o que faz há séculos. Não vigia ativamente: aguarda o gatilho de algo que passe perto e se mova. Em par, as duas guardam os lados de um vão. Quando alguém cruza o alcance, desperta de uma vez, sem aviso, e ataca; passada a ameaça ou perdido o alvo, volta ao posto e à imobilidade, e a poeira recomeça a assentar.",
  "desfechos_nao_combate": [
    "Achar a falsa antes que ela mexa: conte as estátuas, procure a poeira fresca, a pose errada, a que os bichos evitam; sabendo qual é, você não passa ao alcance dela; ela nunca desperta e você contorna. O que a superstição da chave tenta fazer e erra: a defesa é reparar, não recitar.",
    "Não cruzar o posto: se há outro caminho, tome-o; ela só guarda o limiar dela; fora do alcance, é estátua; passagem sem luta. Ela não vai atrás.",
    "Correr e sair do alcance: se despertou, não troque golpes — saia rápido do posto; ela não persegue para longe; cessa e volta ao posto. Custo: deixa para trás o que estava guardado.",
    "Derrubá-la com força e alavanca: concussão concentrada, picareta, derrubar a figura; a pedra racha e ela para; custo: trabalho pesado, barulho que ecoa pela ruína, e o risco de levar quatro garras de granito enquanto a quebra. Só vale se o que está atrás vale."
  ],
  "tipo_perigo": "Oculto"
}
$JSON$::jsonb,
  status_conversao    = $DESC$canonizada$DESC$
WHERE id = 2398;


-- =====================================================================
-- FICHA 5 — TROVÃO-ANDANTE (id 1157) — Storm Giant
-- =====================================================================
UPDATE ref_criaturas SET
  nome                = $DESC$Trovão-Andante$DESC$,
  nome_ptbr           = $DESC$Trovão-Andante$DESC$,
  origem              = $DESC$Natural$DESC$,
  andar_primario      = $DESC$Superfície$DESC$,
  pilar_associado     = $DESC$Corpo$DESC$,
  continente          = '{Vyrkhor}',
  habitat             = $DESC$Os picos e cristas batidas de vento do norte de Vyrkhor — a Muralha de Garr, os altos perto do Farol do Norte, as encostas onde a tempestade mora. Anda sozinho por terreno alto e aberto. Onde ele passa, o tempo fecha.$DESC$,
  comportamento       = $DESC$Andarilho de tempestade$DESC$,
  behavior_archetype  = $DESC$brute$DESC$,
  morale_immune       = false,
  organizacao         = $DESC$Solitário. Os de sua espécie cruzam-se raro e mal se toleram; cada um anda seu trecho de tempestade.$DESC$,
  perigo              = $DESC$Destruidor$DESC$,
  epigrafe            = $DESC$Não veio atrás de nós. Cruzou a crista a meia légua, e mesmo assim o céu virou breu, o raio caiu três vezes no rebanho, e o vento levou a tenda. Ele nem olhou. O perigo não é ele te querer. É ele passar perto. — pastora da Muralha de Garr.$DESC$,
  descricao           = $DESC$Gigante de carne, três vezes a altura de um homem, de corpo rijo e pele curtida de quem vive no vento e no frio. Os olhos têm um brilho que lembra relâmpago longe. Quando se move, há uma carga no ar — os pelos do teu braço se levantam, o metal zumbe baixo. Carrega uma arma do tamanho de uma árvore, e onde ela bate, salta raio. Não comanda a tempestade como quem ergue a mão e ordena — a tempestade vem com ele, ao redor dele, parte dele, como o cheiro vem do corpo. Monstro ele não é, e deus tampouco — é uma criatura grande demais para o mundo dos homens, e isso, por si só, já basta.$DESC$,
  supersticao_popular = $DESC$O povo do norte crê que os gigantes de tempestade são senhores do tempo — que erguem e baixam o temporal à vontade, e que uma oferenda no alto compra bom tempo ou desvia a tormenta. Erram no que importa. O Trovão-Andante não comanda a tempestade como arma nem a vende por oferenda — ela é dele do jeito que a sombra é tua, sem escolha. Subir ao alto deixar oferenda não compra tempo bom; só te põe no caminho da tormenta que anda com ele. A crença mata os devotos que sobem para barganhar.$DESC$,
  sinais_presenca     = $DESC$O tempo que fecha depressa e do nada num dia limpo — nuvem que junta, vento que vira, pressão que cai. O metal que zumbe e o cabelo que se levanta antes de qualquer trovão. Pegadas enormes em terreno alto. Raios que caem num ponto sem haver tempestade larga, como se o céu mirasse. Rebanhos e gente fulminados numa crista por onde nada passou.$DESC$,
  fraqueza_conhecida  = $DESC$Oferenda no alto para aplacá-lo. Falso — não se aplaca o que não está caçando.$DESC$,
  fraqueza_real       = $DESC$Ele é enorme e direto — golpes devastadores, mas largos e lentos, e a tempestade que o cerca também o entrega: o raio e o tempo fechado dizem exatamente onde ele está, muito antes de você o ver. E ele não te procura. Saia do caminho: desça do alto, ache abrigo de pedra contra o raio e o vento, não fique na crista exposta — e a tormenta passa com ele, sem você. Terreno fechado e baixo nega o alcance dele, e ele não se enfia onde não cabe. O perigo não é ele querer te matar; é você estar no caminho. Tire-se do caminho e não há luta.$DESC$,
  descricao_sensorial = $DESC$O dia estava limpo, e agora não está. A nuvem juntou rápido demais, o vento virou, e o ar ficou pesado e elétrico — os pelos do teu braço se levantam, a fivela de metal zumbe. Cheira a pedra molhada e a algo queimado que ainda não queimou. Lá na crista, contra o céu que escureceu, uma forma grande demais caminha, sem pressa, sem olhar para baixo — e a cada passo dela o trovão estala mais perto, e o primeiro raio racha o chão a vinte passos de ti, onde ela nem mirou.$DESC$,
  ecologia            = $JSON$
{
  "presa": [
    "não caça gente — come o que um gigante come, gado grande e caça de monte, quando precisa",
    "a morte que causa em viajantes é da tempestade e do passo, não de caçada"
  ],
  "predador": [
    "nada caça um Trovão-Andante; o fim dele, quando vem, é de outro titã, ou da velhice no alto"
  ],
  "competidor": [
    "outros de sua espécie por trechos de crista, resolvido por evitação — dois temporais não dividem o mesmo céu",
    "cruza o território do Javali-Placa nas encostas e o ignora: presa pequena demais para notar"
  ],
  "simbionte": [],
  "evitado_por": [
    "tudo que pode; rebanhos descem, bichos se enfurnam, pássaros somem do céu antes da tormenta",
    "a migração súbita da fauna montanha abaixo é o aviso mais antigo de que um anda perto"
  ],
  "indicador": "alto exposto e tempo instável; onde anda Trovão-Andante, a crista é mortal no temporal e o céu não é de confiança"
}
$JSON$::jsonb,
  loot_table          = $JSON$
[
  {
    "material": "Osso-Trovão",
    "raridade": "Raro",
    "uso": "Forja",
    "risco": "Osso longo que guarda uma carga e solta faísca quando golpeado. Cobiçado por forja e arcano de tempestade; perigoso de transportar — descarrega no úmido."
  },
  {
    "material": "Couro-de-Tormenta",
    "raridade": "Notável",
    "uso": "Curtume",
    "risco": "Pele curtida de gigante, grossa, que resiste ao frio e, dizem, ao raio. Pesada; couro de uma vida inteira de temporal."
  },
  {
    "material": "Dente-de-Gigante",
    "raridade": "Distinto",
    "uso": "Componente",
    "risco": "Dente do tamanho de um punho, para ponta de arma grande e adorno de quem quer fama."
  },
  {
    "material": "Sal-de-Tempestade",
    "raridade": "Distinto",
    "uso": "Alquimia",
    "risco": "Resíduo cristalino que sobra onde o raio dele caiu repetido. Pica a língua, estala no fogo; base de alquimia de relâmpago."
  }
]
$JSON$::jsonb,
  camada_narrativa    = $JSON$
{
  "som": "O trovão, claro — mas primeiro o zumbido baixo do metal e o silêncio dos bichos. O passo pesado que treme o chão. A voz, quando vem, é grave e lenta, como trovão que virou palavra.",
  "cheiro": "Pedra molhada, ozônio, e o queimado-antes-de-queimar do ar carregado. O cheiro de tempestade chegando, forte e cedo.",
  "quer": "Andar, e o alto, e que o deixem em paz. Não quer caçar gente nem guardar tesouro. A tempestade que o cerca não é vontade — é o que ele é. Defende-se se atacado, com força total; fora isso, segue. O que ele quer de um humano é, no fundo, nada — e é por isso que estar no caminho dele é tão burro: você morre por um perigo que nem reparou em você.",
  "falas_exemplo": [
    "Sai do alto. Não é teu lugar.",
    "Eu passo. Tu não fica no caminho.",
    "Não tenho nada teu. Não tens nada meu. Anda."
  ],
  "gatilhos_agressao": [
    "atacado diretamente",
    "cercado ou impedido de seguir",
    "alguém ameaça o pouco que ele carrega — o revide é imediato e total, golpe e raio"
  ],
  "gatilhos_fuga": [
    "não foge de gente — não precisa",
    "ferido a sério por algo à altura dele, recua para o alto e para a tormenta",
    "terreno onde não cabe, ele contorna, não força"
  ],
  "descoberta_fazendo": "Caminhando seu trecho de crista, sozinho, na tormenta que o segue, sem rumo de caçada — só andando, como faz sempre. Pode estar parado num alto, encarando o horizonte e o temporal, indiferente ao que rasteja embaixo. Não procura você. Se você está no caminho, a tempestade e o passo te alcançam; se não está, ele cruza e some, e o céu reabre atrás dele.",
  "desfechos_nao_combate": [
    "Sair do caminho: desça do alto, busque abrigo baixo e de pedra, não fique na crista; a tormenta passa com ele; o céu reabre e você segue. O desfecho que a montanha ensina e a superstição esquece.",
    "Ler o aviso da fauna: quando os rebanhos descem e os bichos somem, desça também, antes de ver o gigante; você nunca entra no caminho; segurança total. O sinal mais antigo do norte.",
    "Abrigo de pedra contra o raio: se pego no alto, encoste-se a rocha baixa, longe de metal e de árvore solitária, e espere passar; o perigo é ambiental, e abrigo certo o reduz; janela até ele cruzar. Custo: encharcado e gelado, mas vivo.",
    "Caçá-lo pelo Osso-Trovão: um grupo grande, terreno preparado, isca para fixá-lo onde o alcance dele não cabe; derrubá-lo pelos materiais raros; custo: muitos morrem, a tempestade luta do lado dele, e mata-se uma criatura que nunca te quis mal — só andava."
  ],
  "tipo_perigo": "Ambiental"
}
$JSON$::jsonb,
  status_conversao    = $DESC$canonizada$DESC$
WHERE id = 1157;

-- ---------------------------------------------------------------------
-- POST-CHECK 1: as 5 linhas gravadas (resumo) — confira nome/perigo/tipo/pilar
-- ---------------------------------------------------------------------
SELECT id, nome, status_conversao, perigo,
       camada_narrativa->>'tipo_perigo' AS tipo_perigo,
       behavior_archetype, morale_immune, pilar_associado, origem, andar_primario, continente
FROM ref_criaturas
WHERE id IN (916, 904, 2131, 2398, 1157)
ORDER BY id;

-- ---------------------------------------------------------------------
-- POST-CHECK 2: validacao estrutural dos 3 JSONB nas 5 linhas
-- ---------------------------------------------------------------------
SELECT id, nome,
       (ecologia ? 'evitado_por')                       AS ecologia_tem_evitado_por,
       (camada_narrativa ? 'tipo_perigo')               AS cn_tem_tipo_perigo,
       (camada_narrativa ? 'gatilhos_fuga')             AS cn_tem_gatilhos_fuga,
       jsonb_typeof(camada_narrativa->'falas_exemplo')  AS tipo_falas_exemplo,
       jsonb_array_length(loot_table)                   AS n_materiais,
       jsonb_array_length(camada_narrativa->'desfechos_nao_combate') AS n_desfechos
FROM ref_criaturas
WHERE id IN (916, 904, 2131, 2398, 1157)
ORDER BY id;

-- ---------------------------------------------------------------------
-- POST-CHECK 3: contagem de canonizada DEPOIS (esperado: antes + 5 = 18)
-- ---------------------------------------------------------------------
SELECT COUNT(*) AS canonizada_depois FROM ref_criaturas WHERE status_conversao='canonizada';

-- ---------------------------------------------------------------------
-- POST-CHECK 4: amostra jsonb_pretty de 1 ficha (Lacuna-Faminta, a mais densa)
-- ---------------------------------------------------------------------
SELECT jsonb_pretty(ecologia)         AS lacuna_ecologia          FROM ref_criaturas WHERE id=2131;
SELECT jsonb_pretty(loot_table)       AS lacuna_loot_table        FROM ref_criaturas WHERE id=2131;
SELECT jsonb_pretty(camada_narrativa) AS lacuna_camada_narrativa  FROM ref_criaturas WHERE id=2131;


-- =====================================================================
-- POST-GUARD: aborta (rollback) se a gravacao nao bateu. So passa daqui
-- para o COMMIT se canonizada=18 e as 5 ids-alvo estiverem canonizada.
-- =====================================================================
DO $GUARD$
DECLARE n_canon int; n_alvo int;
BEGIN
  SELECT COUNT(*) INTO n_canon FROM ref_criaturas WHERE status_conversao='canonizada';
  IF n_canon <> 18 THEN
    RAISE EXCEPTION 'POST-GUARD: canonizada esperado 18, achou % -> ROLLBACK', n_canon;
  END IF;
  SELECT COUNT(*) INTO n_alvo FROM ref_criaturas
    WHERE id IN (916, 904, 2131, 2398, 1157) AND status_conversao='canonizada';
  IF n_alvo <> 5 THEN
    RAISE EXCEPTION 'POST-GUARD: esperava as 5 ids-alvo em canonizada, achou % -> ROLLBACK', n_alvo;
  END IF;
END
$GUARD$;

-- Chegou aqui = os dois guards passaram e os post-checks acima conferem.
COMMIT;
