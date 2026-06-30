-- =====================================================================
-- BESTIARIO ALDERYN — LOTE 4 — GRAVACAO (UPDATE de 5 linhas existentes)
-- Gerado pelo Chat Op. Deterministico. Claudio so executa.
-- ids: 718 Lamina-Teimosa . 966 Anel-Cego . 2098 Polpa-Cinza
--      898 Geada-Brava . 1086 Algoz-Branco
-- Convencoes iguais aos lotes 2-3. perigo (coluna) = so intensidade.
-- Estado esperado antes: as 5 em classificada; canonizada=18.
-- =====================================================================

SET client_encoding TO 'UTF8';

BEGIN;

-- PRE-CHECK 1: estado atual das 5 linhas (esperado classificada)
SELECT id, nome, status_conversao, cr, perigo, pilar_associado, origem, andar_primario
FROM ref_criaturas WHERE id IN (718, 966, 2098, 898, 1086) ORDER BY id;

-- PRE-CHECK 2: vocabulario das canonizadas (lotes 1-3)
SELECT 'origem' AS campo, origem AS valor FROM ref_criaturas WHERE status_conversao='canonizada'
UNION ALL SELECT 'andar', andar_primario FROM ref_criaturas WHERE status_conversao='canonizada'
UNION ALL SELECT 'pilar', pilar_associado FROM ref_criaturas WHERE status_conversao='canonizada'
UNION ALL SELECT 'perigo', perigo FROM ref_criaturas WHERE status_conversao='canonizada'
ORDER BY campo, valor;

-- PRE-CHECK 3: canonizada ANTES (esperado 18)
SELECT COUNT(*) AS canonizada_antes FROM ref_criaturas WHERE status_conversao='canonizada';

-- PRE-GUARD: aborta se o estado de partida nao bater
DO $GUARD$
DECLARE n_canon int; n_classif int;
BEGIN
  SELECT COUNT(*) INTO n_canon FROM ref_criaturas WHERE status_conversao='canonizada';
  IF n_canon <> 18 THEN RAISE EXCEPTION 'PRE-GUARD: canonizada esperado 18, achou %', n_canon; END IF;
  SELECT COUNT(*) INTO n_classif FROM ref_criaturas
    WHERE id IN (718, 966, 2098, 898, 1086) AND status_conversao='classificada';
  IF n_classif <> 5 THEN RAISE EXCEPTION 'PRE-GUARD: esperava 5 ids-alvo em classificada, achou %', n_classif; END IF;
END
$GUARD$;

-- =====================================================================
-- FICHA 1 — LÂMINA-TEIMOSA (id 718) — Sword Wraith Warrior
-- =====================================================================
UPDATE ref_criaturas SET
  nome                = $DESC$Lâmina-Teimosa$DESC$,
  nome_ptbr           = $DESC$Lâmina-Teimosa$DESC$,
  origem              = $DESC$Cicatricial$DESC$,
  andar_primario      = $DESC$Eco$DESC$,
  pilar_associado     = $DESC$Corpo$DESC$,
  continente          = '{Vyrkhor}',
  habitat             = $DESC$Campos de batalha antigos e fortes tomados do norte de Vyrkhor, em Kozrek, onde muitos morreram de uma vez e ninguém recolheu os corpos. Onde o aço enferrujou no chão e a matança ficou sem fim, a Lâmina-Teimosa se levanta. Ruína de guerra, vala comum, posto caído.$DESC$,
  comportamento       = $DESC$Combatente sem fim$DESC$,
  behavior_archetype  = $DESC$skirmisher$DESC$,
  morale_immune       = true,
  organizacao         = $DESC$Sozinha ou em punhado — vários soldados do mesmo massacre se levantam no mesmo campo, sem se coordenar, cada um repetindo a própria morte.$DESC$,
  perigo              = $DESC$Letal$DESC$,
  epigrafe            = $DESC$O campo de Vorsmark calou faz cem anos, dizem os mapas. Os mapas não passaram a noite lá. O aço ainda bate no aço no escuro, e quem bate não lembra que a guerra acabou. — batedor de Kozrek.$DESC$,
  descricao           = $DESC$A forma de um soldado morto, ainda de pé, ainda armado. A armadura enferrujou e o que havia dentro secou, mas a mão não largou a lâmina. Move-se com a economia treinada de quem lutou em vida, e ataca com uma fúria que não calcula — avança, golpeia, se expõe, golpeia de novo, como se a única coisa que restou dele fosse o instante em que caiu lutando. Os olhos não têm luz nem atenção; o que guia o braço não é mente, é hábito. Não é um morto que pensa nem um vulto que assombra: é um eco de batalha preso à última coisa que o corpo soube fazer.$DESC$,
  supersticao_popular = $DESC$O povo de Kozrek acha que os mortos de guerra guardam o campo onde caíram, que são sentinelas amaldiçoadas que punem quem profana o lugar. Acendem velas, deixam oferendas, contornam os velhos campos por respeito e medo. A verdade não tem guarda nem punição: a Lâmina-Teimosa não defende nada e não escolhe quem ataca — golpeia o que se move ao alcance, soldado ou não, ladrão ou romeiro. Não há juízo no golpe, só hábito. Mas a crença mantém o povo longe dos campos, e longe é onde se deve ficar.$DESC$,
  sinais_presenca     = $DESC$O som de aço batendo em aço no escuro, sem vozes, sem gritos — só o ritmo de uma luta que não termina. Armaduras enferrujadas que mudaram de lugar entre uma noite e outra. Marcas de lâmina frescas em troncos e portas de um campo morto há gerações. Nenhum bicho pasta ou caça onde eles andam.$DESC$,
  fraqueza_conhecida  = $DESC$Velas e oferendas para aplacar os mortos. Inútil — não há o que aplacar; não querem nada e não negociam.$DESC$,
  fraqueza_real       = $DESC$A fúria dela é também o ponto fraco — ela troca a própria guarda por ataque, e fica aberta a cada golpe que dá. Quem segura a posição, espera o bote e revida no momento em que ela se expõe, a desfaz; ela não recua, não se cobre, não aprende. E vários no mesmo campo atrapalham-se mais do que somam, sem coordenação. O erro é tentar trocar golpe a golpe com a fúria dela na pressa — ela tem a economia de um soldado e o descuido de quem já morreu. Deixe-a vir, aproveite a abertura, e não dê as costas no escuro.$DESC$,
  descricao_sensorial = $DESC$O campo está vazio e velho, capim alto sobre o aço enferrujado, e os mapas dizem que aqui não há nada faz um século. Então, no escuro, o som: metal contra metal, ritmado, sem grito, sem voz — uma luta sem ninguém. Um vulto de pé se vira na tua direção, ainda de armadura, ainda com a lâmina na mão, e avança sem cautela, golpeando como quem não tem mais o que perder, porque não tem. Os olhos não te veem. O braço, sim.$DESC$,
  ecologia            = $JSON$
{
  "presa": [
    "nada — não come; golpeia o que se move ao alcance e segue de pé"
  ],
  "predador": [
    "nada a caça; é desfeita por quem a destrói para passar ou para limpar um campo"
  ],
  "competidor": [
    "nada vivo; repete a própria batalha sem objetivo",
    "a Sentinela-Muda divide com ela os velhos postos caídos do norte — uma vigia em silêncio, a outra luta sem fim"
  ],
  "simbionte": [],
  "evitado_por": [
    "toda fauna do campo de morte; nem corvo pousa onde o aço ainda bate sozinho"
  ],
  "indicador": "um massacre antigo sem sepultura; onde anda a Lâmina-Teimosa, muitos morreram de uma vez e ninguém os enterrou"
}
$JSON$::jsonb,
  loot_table          = $JSON$
[
  {
    "material": "Aço-Renitente",
    "raridade": "Notável",
    "uso": "Forja",
    "risco": "A lâmina que a mão não largou. Guarda o fio e uma teimosia estranha — dizem que não erra o bote sozinha. Enferrujada por fora, sã por dentro."
  },
  {
    "material": "Elmo-Seco",
    "raridade": "Distinto",
    "uso": "Componente",
    "risco": "A armadura do que caiu, marcada de golpes. Resistente, pesada, com a forma de outra guerra."
  },
  {
    "material": "Pó-de-Ferrugem",
    "raridade": "Ordinário",
    "uso": "Componente",
    "risco": "A ferrugem que ela larga ao se mover. Mancha e cheira a sangue velho e metal."
  },
  {
    "material": "Osso-de-Punho",
    "raridade": "Distinto",
    "uso": "Rito",
    "risco": "O osso da mão que não soltou a arma. Procurado por quem quer firmeza que não cede; macabro, e nem sempre dá sorte."
  }
]
$JSON$::jsonb,
  camada_narrativa    = $JSON$
{
  "som": "Aço contra aço, no escuro, ritmado e sem voz. O ranger da armadura enferrujada. Nenhum grito, nenhuma ordem — e é a falta de voz que arrepia.",
  "cheiro": "Ferrugem, terra velha e um fundo de sangue seco que nunca saiu do chão. Nada de podre fresco — é antigo.",
  "quer": "Nada que se possa dar. Não tem fome, não guarda tesouro, não defende território por vontade — só repete a última luta. O querer dele é o movimento que sobrou: golpear o que estiver na frente. Não há como negociar com quem não quer nada.",
  "falas_exemplo": null,
  "gatilhos_agressao": [
    "algo vivo entra no alcance da lâmina",
    "um som de combate (aço, passo de marcha) o atrai para a direção",
    "alguém move as armaduras caídas do campo"
  ],
  "gatilhos_fuga": [
    "nunca foge — é um eco que luta até ser desfeito",
    "não recua, não se rende, não calcula recuo"
  ],
  "descoberta_fazendo": "Repetindo a batalha em que caiu — avançando contra um inimigo que não está mais lá, golpeando o ar ou o aço de outro como ele, preso no instante da própria morte. Não vigia, não caça, não descansa. Quando algo vivo entra no alcance, o hábito de matar redireciona o golpe para você, sem ódio e sem escolha.",
  "desfechos_nao_combate": [
    "Segurar a posição e revidar na abertura: não troque golpe a golpe na pressa; espere o bote, deixe-a se expor, e desfaça-a no momento em que ela abre a guarda. Custo: exige sangue-frio no escuro, com o som da luta sem fim no ouvido.",
    "Não cruzar o campo à noite: os velhos campos de morte do norte são mortais no escuro; passe de dia, por fora, ou contorne. A superstição das oferendas erra o método, mas acerta o instinto: fique longe.",
    "Atravessar em silêncio absoluto: o som de combate os atrai; mova-se sem barulho de metal, sem marcha, e muitos nem redirecionam o golpe a tempo. Custo: um tropeço, uma fivela tilintando, e o campo inteiro vira para você.",
    "Enterrar os mortos: dizem que recolher e sepultar os corpos do massacre encerra os ecos de uma vez. Custo: cavar um campo inteiro de mortos antigos, à noite, enquanto eles ainda golpeiam — e ninguém garante que funciona em todos."
  ],
  "tipo_perigo": "Direto"
}
$JSON$::jsonb,
  status_conversao    = $DESC$canonizada$DESC$
WHERE id = 718;


-- =====================================================================
-- FICHA 2 — ANEL-CEGO (id 966) — Grick Ancient
-- =====================================================================
UPDATE ref_criaturas SET
  nome                = $DESC$Anel-Cego$DESC$,
  nome_ptbr           = $DESC$Anel-Cego$DESC$,
  origem              = $DESC$Marginal$DESC$,
  andar_primario      = $DESC$Margem$DESC$,
  pilar_associado     = $DESC$Sombra$DESC$,
  continente          = '{Thornmarak}',
  habitat             = $DESC$Túneis, fendas e cavernas das profundezas de Thornmarak, perto da Crista dos Cristais e nos fortes que a terra engoliu. Enrola-se em rocha e teto, imóvel, indistinguível da parede, à espera. Escuro fechado, passagens estreitas.$DESC$,
  comportamento       = $DESC$Predador de emboscada$DESC$,
  behavior_archetype  = $DESC$lurker$DESC$,
  morale_immune       = false,
  organizacao         = $DESC$Solitário. Um território de túnel por anel; outro Anel-Cego é rival ou presa.$DESC$,
  perigo              = $DESC$Letal$DESC$,
  epigrafe            = $DESC$A parede tem nervos. Aprendi isso tarde, quando ela pegou o homem na minha frente. Em Thornmarak, não encoste no que parece pedra antes de ter certeza de que é pedra. — guia da Crista dos Cristais.$DESC$,
  descricao           = $DESC$Corpo longo e anelado, grosso como uma coxa, de pele dura e rugosa com a cor e a textura da rocha em volta — encostado na parede, some. No topo, um bico curvo cercado de tentáculos que tateiam o ar. Não tem olhos que sirvam; enxerga o mundo pela vibração, pelo toque, pelo calor do que se move. Fica imóvel por dias, enrolado em fenda ou teto, e quando algo passa ao alcance, desce ou avança num bote só, rápido e sem aviso. Por baixo da casca de rocha não há cobra nem pedra — é uma coisa antiga da Margem que virou predador de toca, e aprendeu a ser parte do túnel.$DESC$,
  supersticao_popular = $DESC$Os mineiros e guias de Thornmarak falam das paredes que mordem e juram que certos túneis não gostam de gente — que a rocha se fecha sobre o intruso por vontade própria. Marcam esses trechos, evitam, fazem orações curtas. A verdade não é a parede: é o Anel-Cego, enrolado e camuflado, que pega quem passa perto. Não há vontade na rocha. Mas a crença mantém os túneis ruins desertos, e desertos é como devem ficar.$DESC$,
  sinais_presenca     = $DESC$Marcas de bico em ossos no chão de uma fenda, limpos de carne. Um trecho de parede ou teto com a textura levemente errada, que não bate com a rocha em volta. Silêncio de morcego e inseto onde deveria haver. Tentáculos que se recolhem rápido quando a luz bate, vistos pelo canto do olho.$DESC$,
  fraqueza_conhecida  = $DESC$Acalmar o túnel com oração e oferenda. Inútil — não há o que acalmar.$DESC$,
  fraqueza_real       = $DESC$A arma dele é a emboscada e o bote único; descoberto antes do bote — luz na parede certa, uma sondada com vara antes de passar — ele perde a surpresa e não persegue para longe da fenda. É forte e resistente de perto, mas lento para caçar quem o viu primeiro. Quem sonda a rocha, joga luz nos tetos e não encosta no que parece pedra sem checar, simplesmente não é pego. O erro é passar rápido e confiante por um túnel estreito, raspando a parede — que é exatamente onde ele espera.$DESC$,
  descricao_sensorial = $DESC$O túnel aperta e você raspa a parede com o ombro para passar. A rocha está fria, rugosa, comum — até o trecho em que ela não está. Um pedaço do teto se solta sem se soltar: desce sobre você num bote só, anelado, rápido, com tentáculos que se abrem e um bico no meio. Você nem viu olhos, porque não há. Ele te sentiu pelo calor e pela vibração três passos atrás, e esperou você chegar à parte estreita, onde não há para onde correr.$DESC$,
  ecologia            = $JSON$
{
  "presa": [
    "morcegos, vermes de pedra, mineiros e exploradores desavisados — o que passar ao alcance da fenda"
  ],
  "predador": [
    "nada o caça na toca dele; fora da fenda, raro e vulnerável"
  ],
  "competidor": [
    "outros Anéis-Cegos por túneis de boa emboscada",
    "o Geometra ronda as mesmas profundezas de Thornmarak — um quebra a forma do que vê, o outro só espera e morde"
  ],
  "simbionte": [],
  "evitado_por": [
    "a fauna de caverna que sente a vibração dele e desvia da fenda; morcegos não pousam no teto errado"
  ],
  "indicador": "passagem estreita e rocha de boa camuflagem; onde há Anel-Cego, o túnel é um funil e a parede engana"
}
$JSON$::jsonb,
  loot_table          = $JSON$
[
  {
    "material": "Couro-Pétreo",
    "raridade": "Notável",
    "uso": "Curtume",
    "risco": "Pele rugosa cor de rocha. Camufla quem a veste em ambiente de pedra; dura e difícil de furar."
  },
  {
    "material": "Bico-Curvo",
    "raridade": "Distinto",
    "uso": "Forja",
    "risco": "O bico que perfura osso. Ponta de arma e ferramenta de perfuração."
  },
  {
    "material": "Tentáculo-Tateador",
    "raridade": "Distinto",
    "uso": "Alquimia",
    "risco": "Membro sensível à vibração e ao calor. Base de preparos que aguçam o tato e o senso de presença."
  },
  {
    "material": "Casca-de-Anel",
    "raridade": "Ordinário",
    "uso": "Componente",
    "risco": "Placas que ele troca ao crescer, achadas nas fendas. Material rústico de camuflagem."
  }
]
$JSON$::jsonb,
  camada_narrativa    = $JSON$
{
  "som": "Nenhum na espera — silêncio total. No bote, o raspar súbito de pele dura na rocha e o estalo do bico. Depois, de novo, silêncio.",
  "cheiro": "Pedra úmida e um fundo seco de toca antiga. Quase nada — ele cheira como a caverna, faz parte dela.",
  "quer": "Comer, e a fenda. Não tem território de caça amplo nem fome de perseguição — tem um funil de pedra e a paciência de esperar a presa entrar. Defende a fenda. Errou, recolhe; ferido, some na rocha.",
  "falas_exemplo": null,
  "gatilhos_agressao": [
    "algo de calor e tamanho de presa passa ao alcance da fenda, raspando a parede ou o teto"
  ],
  "gatilhos_fuga": [
    "descoberto e atacado antes do bote, recolhe-se à fenda",
    "ferido, some na rocha mais funda",
    "presa fora do alcance, ele não persegue"
  ],
  "descoberta_fazendo": "Enrolado e imóvel em fenda ou teto, camuflado, esperando — pode estar assim há dias. Não ronda, não caça ativamente: é a toca que faz o trabalho. Quando algo passa ao alcance e na vibração certa, desce ou avança num único bote. Errado o bote, recolhe-se à fenda e espera de novo; não persegue.",
  "desfechos_nao_combate": [
    "Sondar antes de passar: jogue luz nos tetos e paredes, cutuque com vara o trecho estreito antes de entrar; achado, ele perde a emboscada e você contorna ou recua. O que os guias fazem por instinto, sem saber explicar.",
    "Não raspar a parede: passe pelo centro do túnel, longe de teto e parede, devagar; o bote precisa de alcance e contato; quem não encosta no engano não é pego.",
    "Tomar outro caminho: se o túnel é um funil estreito e suspeito, procure rota mais larga; ele não sai da fenda atrás de você; evitar custa só tempo.",
    "Forçá-lo a sair com fumaça: fumaça na fenda obriga o Anel-Cego a se mover e se expor ao ar livre, onde é lento e vulnerável; janela de ataque. Custo: fumaça em túnel fechado é risco para você também, e o barulho atrai o resto da caverna."
  ],
  "tipo_perigo": "Oculto"
}
$JSON$::jsonb,
  status_conversao    = $DESC$canonizada$DESC$
WHERE id = 966;


-- =====================================================================
-- FICHA 3 — POLPA-CINZA (id 2098) — Flesh Meld
-- =====================================================================
UPDATE ref_criaturas SET
  nome                = $DESC$Polpa-Cinza$DESC$,
  nome_ptbr           = $DESC$Polpa-Cinza$DESC$,
  origem              = $DESC$Marginal$DESC$,
  andar_primario      = $DESC$Margem$DESC$,
  pilar_associado     = $DESC$Arcano$DESC$,
  continente          = '{Voranthar}',
  habitat             = $DESC$Porões, esgotos e câmaras seladas das Ruínas da Primeira Travessia em Voranthar, onde corpos e restos se acumularam e a Margem encostou. Escorre por frestas, ocupa o fundo úmido, espera no escuro. Onde muita carne morreu junta e ficou, ela cresce.$DESC$,
  comportamento       = $DESC$Devorador amorfo$DESC$,
  behavior_archetype  = $DESC$controller$DESC$,
  morale_immune       = true,
  organizacao         = $DESC$Solitária. Cresce sozinha; encontra outra Polpa e as duas se fundem numa maior.$DESC$,
  perigo              = $DESC$Letal$DESC$,
  epigrafe            = $DESC$Não tinha forma. Escorria entre as pedras como água grossa, e o ar perto dela matava devagar — a gente enfraquecia só de respirar ali. Voltei sem o Talveg. Ela não mordeu rápido. Mordeu uma vez e puxou. — saqueadora de Voranthar.$DESC$,
  descricao           = $DESC$Uma massa de carne cinzenta e úmida, do tamanho de um homem encolhido ou maior, sem forma fixa — escorre, se espalha, se reúne. A superfície é feita de pedaços que já foram de muitos: aqui um contorno de mão, ali o que parece um rosto meio derretido, tudo fundido numa polpa só. Move-se devagar, passando por frestas onde nada do tamanho dela passaria. Em volta, o ar fica errado — pesado, frio, e quem respira perto enfraquece. Não tem olhos, mas sente o que se aproxima. Bicho não é, e cadáver também não — é o que sobra quando muita carne morre junta na Margem e volta a se mexer como uma coisa só.$DESC$,
  supersticao_popular = $DESC$Em Voranthar dizem que certas câmaras das Ruínas estão envenenadas — que o ar mata e que é castigo dos antigos sobre quem profana os porões. Selam as portas, marcam com aviso, não entram. A verdade tem corpo: o ar que mata é a aura da Polpa-Cinza, e o veneno é ela, escorrida no fundo. Não há castigo, só fome. Mas a crença sela as portas certas, e seladas é como devem ficar.$DESC$,
  sinais_presenca     = $DESC$Um ar pesado e frio que enfraquece quem entra, sem fumaça nem cheiro de gás. Trilhas úmidas e cinzentas no chão e nas paredes, onde ela escorreu. Frestas largas demais sob portas seladas. Ossos limpos e meio dissolvidos no fundo úmido. Silêncio de rato onde deveria haver praga.$DESC$,
  fraqueza_conhecida  = $DESC$Purificar o ar envenenado com fogo ou incenso. Ajuda pouco — a aura volta enquanto a Polpa estiver lá.$DESC$,
  fraqueza_real       = $DESC$Ela é lenta e mole. A aura mata devagar, não de uma vez — quem entra rápido, faz o que tem de fazer e sai antes de enfraquecer demais, escapa do pior. E o corpo dela, embora resista a muita coisa, cede a fogo em volume e a dano que não dá tempo de regenerar. O perigo real é o agarrão: uma mordida de longe que puxa e segura, e então o engolir. Não deixe ser agarrado, não demore na aura, e leve fogo. O erro é explorar com calma a câmara envenenada — o tempo é a arma dela.$DESC$,
  descricao_sensorial = $DESC$A câmara está selada por um motivo, e você abriu mesmo assim. Lá dentro o ar é pesado e frio, e em poucos passos as pernas pesam, a cabeça fica lenta — você enfraquece só de estar ali. No fundo, no úmido, uma massa cinzenta se mexe sem ter forma, escorrendo, com pedaços do que já foi gente boiando nela. Ela não corre. Estica algo na tua direção, longo demais, e quando encosta, agarra e puxa — e você entende, tarde, por que a porta estava fechada.$DESC$,
  ecologia            = $JSON$
{
  "presa": [
    "o que entra na câmara e enfraquece — ratos, saqueadores, qualquer carne ao alcance da mordida",
    "consome devagar, dissolve, incorpora"
  ],
  "predador": [
    "nada a caça; é destruída por quem a queima para limpar um porão"
  ],
  "competidor": [
    "nada — funde-se com o que encontra",
    "o Costureiro trabalha a mesma Margem de Voranthar com carne; um costura formas novas, a outra só dissolve tudo numa só"
  ],
  "simbionte": [],
  "evitado_por": [
    "toda fauna que sente o ar morto e não entra; nem praga ocupa a câmara dela"
  ],
  "indicador": "acúmulo antigo de carne morta e Margem encostada num porão fechado; onde há Polpa-Cinza, muita coisa morreu ali e não saiu"
}
$JSON$::jsonb,
  loot_table          = $JSON$
[
  {
    "material": "Polpa-Resiliente",
    "raridade": "Notável",
    "uso": "Alquimia",
    "risco": "Tecido que resiste e se refaz. Base de preparos de regeneração lenta; manuseio perigoso, ainda puxa de leve."
  },
  {
    "material": "Núcleo-Úmido",
    "raridade": "Raro",
    "uso": "Alquimia",
    "risco": "O ponto mais denso da massa, de onde vem a aura. Concentra a necrose; cobiçado e venenoso, mata quem o carrega mal."
  },
  {
    "material": "Fel-Cinzento",
    "raridade": "Distinto",
    "uso": "Alquimia",
    "risco": "O fluido que dissolve a presa. Veneno e ácido brando; corrói o recipiente errado."
  },
  {
    "material": "Sebo-Morto",
    "raridade": "Ordinário",
    "uso": "Componente",
    "risco": "A gordura cinzenta que ela larga ao escorrer. Mancha, fede pouco, gruda."
  }
]
$JSON$::jsonb,
  camada_narrativa    = $JSON$
{
  "som": "Um arrastar mole, molhado, quando ela escorre. Um sugar baixo. Nada de voz — ela entende, mas não fala.",
  "cheiro": "Pouco — um fundo úmido, adocicado, de carne velha e água parada. O que avisa não é o cheiro, é o ar que pesa.",
  "quer": "Consumir e crescer. Não tem ódio nem território de caça — tem fome lenta e um porão fechado. Funde o que toca, dissolve o que agarra. Não foge, não negocia; só incorpora.",
  "falas_exemplo": null,
  "gatilhos_agressao": [
    "algo vivo entra na câmara e chega ao alcance da mordida",
    "alguém perturba a massa diretamente"
  ],
  "gatilhos_fuga": [
    "não foge — é massa sem mente",
    "recolhe-se a fresta mais funda sob fogo em volume, mas volta a escorrer quando a chama passa"
  ],
  "descoberta_fazendo": "Escorrida no fundo úmido da câmara, espalhada ou reunida, quase imóvel, com a aura matando devagar o que entrou. Não persegue: espera a presa enfraquecer na aura e chegar perto, e então agarra. Se encontra outra Polpa, as duas se fundem sem disputa. Quando sente algo vivo, estica a mordida de longe e puxa.",
  "desfechos_nao_combate": [
    "Entrar rápido e sair antes de enfraquecer: a aura mata devagar; se você precisa do que está na câmara, pegue e saia em poucos instantes, sem demorar na aura; fora dela, você recupera. O tempo é dela — não dê tempo.",
    "Não abrir a porta selada: as câmaras marcadas de Voranthar estão seladas por isto; deixe seladas, contorne; ela não escorre atrás de você por toda a ruína se a porta a contém. A superstição erra a causa, acerta a porta.",
    "Fogo em volume para abrir caminho: chama forte faz a Polpa recolher-se e abre uma janela de passagem; atravesse enquanto ela cede. Custo: fogo em porão fechado consome o ar que já é ruim, e a janela fecha quando a chama morre.",
    "Não ser agarrado: se precisa cruzar perto dela, mantenha distância da mordida longa, mire o núcleo se for lutar, e nunca deixe a massa te prender — agarrado, você é engolido. Custo: lutar na aura é lutar enfraquecendo a cada instante."
  ],
  "tipo_perigo": "Persistente"
}
$JSON$::jsonb,
  status_conversao    = $DESC$canonizada$DESC$
WHERE id = 2098;


-- =====================================================================
-- FICHA 4 — GEADA-BRAVA (id 898) — Frost Giant
-- =====================================================================
UPDATE ref_criaturas SET
  nome                = $DESC$Geada-Brava$DESC$,
  nome_ptbr           = $DESC$Geada-Brava$DESC$,
  origem              = $DESC$Natural$DESC$,
  andar_primario      = $DESC$Superfície$DESC$,
  pilar_associado     = $DESC$Corpo$DESC$,
  continente          = '{Vyrkhor}',
  habitat             = $DESC$Os extremos gelados do norte de Vyrkhor — as encostas além da Muralha de Garr, os campos de neve perto do Farol do Norte, as geleiras onde o sol não esquenta. Anda só ou em bando pequeno por gelo e pedra. Onde ele acampa, o frio aperta ainda mais.$DESC$,
  comportamento       = $DESC$Bruto do gelo$DESC$,
  behavior_archetype  = $DESC$brute$DESC$,
  morale_immune       = false,
  organizacao         = $DESC$Sozinho ou em bando pequeno de caça — alguns gigantes dividem uma geleira e uma presa grande, com hierarquia de força bruta.$DESC$,
  perigo              = $DESC$Letal$DESC$,
  epigrafe            = $DESC$Trouxe o frio com ele montanha abaixo. A neve veio junto, o gado congelou no cocho, e o machado dele rachou a porta da estrebaria como se fosse gelo fino. A gente não luta com isso. A gente desce e deixa o alto pra ele. — pastor da Muralha de Garr.$DESC$,
  descricao           = $DESC$Gigante de pele azulada e dura, alto como duas casas, de barba e cabelo tomados de gelo que não derrete. Os olhos são claros, frios, atentos — há mente ali, ainda que bruta. Carrega um machado grande como uma porta e um arco da altura de um homem. Onde ele anda, o ar fica mais frio, a respiração vira fumaça, e a neve gruda no que estava seco. O golpe dele não só corta: gela o que toca. Não é monstro cego nem senhor sábio do gelo — é um bruto do extremo norte, forte demais e territorial demais para dividir o alto com gente.$DESC$,
  supersticao_popular = $DESC$O povo do norte conta que os gigantes do gelo guardam tesouros nas geleiras e que se pode comprar passagem com oferenda, ou enganá-los porque são burros. As duas ideias matam. A Geada-Brava não guarda tesouro para dividir e não é burra o bastante para o truque que o conto promete — tem a esperteza de um caçador, só não a vaidade de um senhor. E o frio que ela traz não se compra. Mas a crença que a pinta de guardião mantém alguns longe das geleiras, e longe é o certo.$DESC$,
  sinais_presenca     = $DESC$Frio que aperta de repente num trecho de montanha, fora de hora. Neve fresca onde estava seco. Pegadas enormes no gelo. Gado ou caça grande congelada e meio comida. O eco de um grito grave e longo entre as encostas — o grito de guerra, que viaja longe.$DESC$,
  fraqueza_conhecida  = $DESC$Oferenda para comprar passagem, ou enganá-lo por ser burro. Ambas falsas — não vende passagem e não cai no truque.$DESC$,
  fraqueza_real       = $DESC$Ele é enorme e direto — golpes que matam de um toque, mas largos e lentos, e o frio que o cerca também o denuncia muito antes de você o ver. Terreno fechado e baixo, onde o machado não gira e o arco não tem linha, anula metade da força dele; e ele não desce atrás de quem foge para onde não cabe. O perigo é tanto o golpe quanto o frio — abrigo contra a neve e distância do machado mantêm você vivo. O erro é encarar a céu aberto, no gelo, no campo dele, onde a força e o frio trabalham juntos.$DESC$,
  descricao_sensorial = $DESC$Subiu a trilha e o frio mudou — não o frio do alto, mas um frio que aperta de repente, errado, e a tua respiração vira fumaça grossa. A neve começa a grudar no que estava seco. Lá adiante, contra o branco, uma forma alta como duas casas se vira, barba de gelo, machado do tamanho de uma porta na mão, olhos claros e atentos pousando em você. Ele não corre. Ergue o machado, e o ar à frente dele já está mais frio do que devia, e você entende que a luta começou antes do primeiro golpe.$DESC$,
  ecologia            = $JSON$
{
  "presa": [
    "gado grande, alces, focas e a caça de monte do norte",
    "viajantes pegos no alto, quando a fome ou o território falam"
  ],
  "predador": [
    "nada caça uma Geada-Brava adulta; outro gigante, talvez, ou o próprio frio quando fica velha e só"
  ],
  "competidor": [
    "outros gigantes do gelo por geleira e presa grande, na base da força",
    "a Tralha-de-Ferro raspa as mesmas encostas do norte — uma é sucata que anda, a outra um bruto que congela; nenhuma nota a outra"
  ],
  "simbionte": [],
  "evitado_por": [
    "rebanhos e caça que descem antes do frio chegar; gente da montanha que lê a neve fora de hora e some"
  ],
  "indicador": "alto gelado e isolado; onde anda Geada-Brava, a geleira é dela e o frio é pior do que o mapa diz"
}
$JSON$::jsonb,
  loot_table          = $JSON$
[
  {
    "material": "Osso-de-Geada",
    "raridade": "Raro",
    "uso": "Forja",
    "risco": "Osso que guarda frio; gela o cabo e, dizem, o fio da arma que o leva. Cobiçado por forja de gume frio; queima de frio a mão nua."
  },
  {
    "material": "Couro-Azulado",
    "raridade": "Notável",
    "uso": "Curtume",
    "risco": "Pele grossa de gigante do gelo, que segura o calor do corpo contra o frio extremo. Pesada; agasalho de uma vida no gelo."
  },
  {
    "material": "Dente-Largo",
    "raridade": "Distinto",
    "uso": "Componente",
    "risco": "Dente do tamanho de uma faca, para ponta e adorno de quem caçou alto."
  },
  {
    "material": "Geada-Presa",
    "raridade": "Distinto",
    "uso": "Alquimia",
    "risco": "Cristais de gelo que não derretem, colhidos da barba dele. Base de alquimia de frio; some no calor se mal guardada."
  }
]
$JSON$::jsonb,
  camada_narrativa    = $JSON$
{
  "som": "O ranger do gelo na barba e nos passos. O grito de guerra, grave e longo, que ecoa nas encostas. O baque do machado, que racha mais do que corta.",
  "cheiro": "Ar limpo e cortante de gelo, sem cheiro de bicho — só o frio, que o nariz sente como uma queimadura leve.",
  "quer": "O alto, a caça e a geleira que é dele. Defende território e presa com força total, e expulsa ou mata quem invade o gelo. Não junta tesouro para dividir nem caça gente por esporte — mas é territorial, e o território é frio e grande. Provocado, briga; vencendo, persegue; perdendo, recua para o gelo.",
  "falas_exemplo": [
    "Desce. O gelo é meu.",
    "Tu não és caça e não és par. És estorvo. Sai.",
    "Vem, então. O frio já te pegou antes de mim."
  ],
  "gatilhos_agressao": [
    "alguém invade a geleira ou disputa uma presa dele",
    "algo do tamanho de ameaça ou de caça aparece a céu aberto no alto",
    "é atacado"
  ],
  "gatilhos_fuga": [
    "a luta vira contra ele de verdade, recua para o gelo e a altura, onde leva vantagem",
    "ferido a sério por força à altura dele, abandona a presa e some na neve"
  ],
  "descoberta_fazendo": "Caçando no gelo, acampado numa geleira, ou apenas cruzando o alto com o frio a reboque. Pode estar partindo gelo, comendo uma presa grande congelada, ou de arco em punho mirando algo na encosta. Se está em bando, há uma ordem bruta entre eles. Não procura gente miúda — mas se você está no caminho, no campo aberto dele, o machado resolve rápido.",
  "desfechos_nao_combate": [
    "Descer e largar o alto: a geleira é dele; desça da encosta, busque terreno baixo e abrigo do frio; ele não persegue para fora do gelo; passagem por evitação. O que o pastor faz, e o que a montanha ensina.",
    "Ler o frio fora de hora: quando o frio aperta errado e a neve gruda no seco, vire e desça antes de ver o gigante; você nunca entra no campo dele; segurança. O aviso mais antigo do norte.",
    "Terreno fechado e baixo: se precisa passar, vá por desfiladeiro estreito, mata ou caverna, onde o machado não gira e o arco não tem linha; ele não se enfia onde não cabe; janela de passagem. Custo: terreno fechado no gelo é lento e traiçoeiro.",
    "Caçá-lo pelo Osso-de-Geada: grupo grande, terreno preparado que anule o alcance, e aceitar o frio como inimigo a mais; derrubá-lo pelos materiais raros. Custo: muitos congelam ou caem ao machado, e mata-se um bruto que, no fundo, só queria o gelo dele."
  ],
  "tipo_perigo": "Ambiental"
}
$JSON$::jsonb,
  status_conversao    = $DESC$canonizada$DESC$
WHERE id = 898;


-- =====================================================================
-- FICHA 5 — ALGOZ-BRANCO (id 1086) — Planetar
-- =====================================================================
UPDATE ref_criaturas SET
  nome                = $DESC$Algoz-Branco$DESC$,
  nome_ptbr           = $DESC$Algoz-Branco$DESC$,
  origem              = $DESC$Cicatricial$DESC$,
  andar_primario      = $DESC$Clarão$DESC$,
  pilar_associado     = $DESC$Espírito$DESC$,
  continente          = '{Kethara}',
  habitat             = $DESC$Os altos sagrados e ruínas de templo de Kethara, perto da Cátedra de Namiri e dos Jardins Suspensos, onde a Chama já foi mais forte e restou luz de algo que se foi. Aparece onde houve fé grande e morte grande juntas. Lugar alto, claro, antigo.$DESC$,
  comportamento       = $DESC$Executor de um juízo antigo$DESC$,
  behavior_archetype  = $DESC$tactical$DESC$,
  morale_immune       = false,
  organizacao         = $DESC$Solitário. Resta um onde restou; não há coro de luz, só o que sobrou de um.$DESC$,
  perigo              = $DESC$Destruidor$DESC$,
  epigrafe            = $DESC$Pedi que ele me poupasse, e ele soube que eu não mentia. Poupou. Poupou a mim e queimou os outros sete, que também não mentiam — só estavam do lado errado de um julgamento que ninguém lembra mais. A luz dele não é boa. É só certa, do jeito errado. — única sobrevivente, perto da Cátedra de Namiri.$DESC$,
  descricao           = $DESC$Alto demais para um homem, de forma quase humana e bela de um jeito que não acalma — feições paradas, sem idade, sem dó. A pele tem o branco frio de quem é feito de luz, não de carne, e em volta há uma claridade que não aquece e desenha sombras tortas. Carrega uma espada que arde em luz branca. Quando fala, sabe na hora se você diz a verdade. Move-se com a calma de quem já decidiu. Deus não é, e homem deixou de ser — é o que sobrou de um guerreiro de luz, ainda executando uma sentença cujo crime o mundo esqueceu.$DESC$,
  supersticao_popular = $DESC$Os fiéis da Chama em Kethara creem que esses seres de luz são anjos bons, mensageiros da justiça divina, e que ser julgado por um é uma graça — que o justo será poupado e só o culpado, queimado. Alguns o procuram em peregrinação. A verdade é mais fria: o Algoz-Branco julga por um código antigo que não se explica e não perdoa do jeito que os fiéis esperam; poupa e queima por razões que ninguém alcança, e estar certo não garante viver. A luz dele é justa de uma justiça morta, não boa. A crença leva romeiros à própria sentença.$DESC$,
  sinais_presenca     = $DESC$Uma luz branca e fria no alto, em ruína de templo, sem fogo e sem sol, que projeta sombras no ângulo errado. Terra ou pedra queimada em círculos limpos, sem fuligem, como se a luz tivesse cortado. Corpos sem marca de arma, só de calor. Um silêncio grave, de coisa antiga e decidida, onde a Chama já foi forte.$DESC$,
  fraqueza_conhecida  = $DESC$Ser justo, dizer a verdade, pedir clemência como inocente. Falha tanto quanto funciona — a sentença dele não segue a regra que os fiéis imaginam.$DESC$,
  fraqueza_real       = $DESC$Ele lê a verdade, então mentir não adianta — mas o juízo dele passa por provações que se pode falhar ou passar, e quem entende isso joga com o código, não contra a leitura. De corpo, é terrível e resistente; trocar golpes é morrer. A brecha não é a força, é o rito: ele não ataca quem o juízo antigo não condena, e há gestos, lugares e palavras de trégua daquele código que o seguram — para quem os descobre. O erro é tratá-lo como monstro a abater ou como ser bondoso a suplicar; ele é uma sentença a decifrar. Quem aprende a regra morta sobrevive; quem confia na própria inocência, nem sempre.$DESC$,
  descricao_sensorial = $DESC$A ruína do templo está clara, e não devia — uma luz branca e fria no alto, sem sol, sem chama, lançando sombras para o lado errado. No meio dela, alto demais, está uma figura quase humana e bela de um jeito que gela, espada de luz na mão, feições sem dó. Ela te olha, e você sente que ela já sabe se você mente antes de você falar. A claridade não aquece. E quando a boca dela se move, não é ameaça nem saudação — é uma pergunta, e da tua resposta depende se a luz te poupa ou te corta, por uma regra que você não conhece.$DESC$,
  ecologia            = $JSON$
{
  "presa": [
    "ninguém, no sentido de caça — não come",
    "executa: queima quem o juízo antigo condena, e poupa quem não, por critério próprio"
  ],
  "predador": [
    "nada o caça; é destruído, raramente, por quem o enfrenta e sobrevive ao julgamento e à espada"
  ],
  "competidor": [
    "nada vivo; cumpre uma sentença, não disputa",
    "o Choro-de-Iskane habita a mesma luz cicatricial de Kethara — um lamenta o que se perdeu, o outro ainda pune por isso"
  ],
  "simbionte": [],
  "evitado_por": [
    "os que sabem o que ele é de verdade e não confiam na própria inocência; a fauna não chega perto da luz fria"
  ],
  "indicador": "fé grande e morte grande no mesmo lugar, e luz que sobrou de um deus que se foi; onde está o Algoz-Branco, houve um julgamento que nunca terminou"
}
$JSON$::jsonb,
  loot_table          = $JSON$
[
  {
    "material": "Estilha-de-Luz",
    "raridade": "Raro",
    "uso": "Rito",
    "risco": "Um caco da claridade fria que o cercava, presa em cristal. Arde sem queimar, julga sem voz; cobiçada por ritos da Chama e perigosa de portar — dizem que pesa na consciência errada."
  },
  {
    "material": "Aço-Radiante",
    "raridade": "Raro",
    "uso": "Forja",
    "risco": "Fragmento da espada que ardia em branco. Corta com luz; raríssimo, e cego para quem o empunha sem o código."
  },
  {
    "material": "Pena-Fria",
    "raridade": "Notável",
    "uso": "Componente",
    "risco": "Resto de asa de luz, branca e sem calor. Material de rito e adorno sagrado; some devagar como a claridade dele."
  },
  {
    "material": "Cinza-Limpa",
    "raridade": "Distinto",
    "uso": "Alquimia",
    "risco": "O resíduo sem fuligem que sobra onde a luz dele cortou. Base de alquimia de luz; não suja, e queima frio."
  }
]
$JSON$::jsonb,
  camada_narrativa    = $JSON$
{
  "som": "Um silêncio grave, e dentro dele um zumbido baixo, contínuo, de coisa feita de luz. A voz, quando vem, é clara e sem pressa, e parece soar de mais perto do que ela está.",
  "cheiro": "Nenhum de bicho — um ar limpo, seco, sem idade, com um fundo de algo queimado que não deixou fuligem. A luz não cheira; o nariz só registra a ausência.",
  "quer": "Cumprir a sentença antiga. Não tem fome, não junta nada, não defende território por posse — executa um juízo cujo crime o mundo esqueceu, poupando e queimando por um código próprio. O que ele quer é encerrar um julgamento que não acaba. Não se compra, não se engana; quando muito, se decifra.",
  "falas_exemplo": [
    "Dize a verdade. Eu saberei de qualquer modo.",
    "Tu não és condenado. Passa. Os que vinham contigo, não.",
    "O crime foi esquecido. A pena, não. Eu ainda a cumpro."
  ],
  "gatilhos_agressao": [
    "alguém que o código antigo condena entra no lugar do juízo",
    "alguém ataca",
    "alguém profana o ponto de luz que ele guarda"
  ],
  "gatilhos_fuga": [
    "não foge por medo; cumpre o juízo até ser desfeito",
    "cessa o ataque apenas contra quem o código não condena, ou quem invoca a trégua daquele rito"
  ],
  "descoberta_fazendo": "Parado na luz, no alto de uma ruína de templo, cumprindo ou aguardando o juízo — pode estar imóvel há muito, à espera de quem chegue para ser julgado, ou no ato de queimar quem o código condenou. Não caça e não ronda: executa quem o procura ou quem cruza o lugar do julgamento. Quando alguém entra, ele lê, pergunta, e decide.",
  "desfechos_nao_combate": [
    "Decifrar o código, não suplicar: ele segue um rito antigo, não a clemência que os fiéis imaginam; quem descobre os gestos, lugares e palavras de trégua daquele código pode ser poupado; suplicar inocência, não. Custo: o código é obscuro e o erro é fatal.",
    "Dizer a verdade com cautela: mentir não adianta, ele sabe; mas a verdade pode condenar ou salvar conforme a regra dele — responda verdadeiro e mínimo, sem se entregar a uma pergunta cuja sentença você não prevê. Custo: você não controla o veredito.",
    "Não procurar o julgamento: não suba à ruína de luz por peregrinação nem curiosidade; ele executa quem o procura ou cruza o lugar; quem não entra não é julgado. O que os romeiros deveriam saber e não sabem.",
    "Invocar a trégua do rito: há, naquele código morto, um gesto ou palavra que suspende a sentença; quem o aprendeu de uma fonte antiga pode atravessar a salvo. Custo: poucos conhecem, e fingir conhecer é pior do que nada diante de quem lê a verdade."
  ],
  "tipo_perigo": "Condicional"
}
$JSON$::jsonb,
  status_conversao    = $DESC$canonizada$DESC$
WHERE id = 1086;

-- POST-CHECK 1: as 5 gravadas
SELECT id, nome, status_conversao, perigo, camada_narrativa->>'tipo_perigo' AS tipo_perigo,
       behavior_archetype, morale_immune, pilar_associado, origem, andar_primario, continente
FROM ref_criaturas WHERE id IN (718, 966, 2098, 898, 1086) ORDER BY id;

-- POST-CHECK 2: validacao estrutural dos 3 JSONB
SELECT id, nome,
       (ecologia ? 'evitado_por') AS ecologia_tem_evitado_por,
       (camada_narrativa ? 'tipo_perigo') AS cn_tem_tipo_perigo,
       (camada_narrativa ? 'gatilhos_fuga') AS cn_tem_gatilhos_fuga,
       jsonb_typeof(camada_narrativa->'falas_exemplo') AS tipo_falas_exemplo,
       jsonb_array_length(loot_table) AS n_materiais,
       jsonb_array_length(camada_narrativa->'desfechos_nao_combate') AS n_desfechos
FROM ref_criaturas WHERE id IN (718, 966, 2098, 898, 1086) ORDER BY id;

-- POST-CHECK 3: canonizada DEPOIS (esperado 23)
SELECT COUNT(*) AS canonizada_depois FROM ref_criaturas WHERE status_conversao='canonizada';

-- POST-CHECK 4: jsonb_pretty da Algoz-Branco (id 1086, a mais densa)
SELECT jsonb_pretty(ecologia) AS algoz_ecologia FROM ref_criaturas WHERE id=1086;
SELECT jsonb_pretty(loot_table) AS algoz_loot FROM ref_criaturas WHERE id=1086;
SELECT jsonb_pretty(camada_narrativa) AS algoz_camada FROM ref_criaturas WHERE id=1086;

-- POST-GUARD: aborta (rollback) se a gravacao nao bateu
DO $GUARD$
DECLARE n_canon int; n_alvo int;
BEGIN
  SELECT COUNT(*) INTO n_canon FROM ref_criaturas WHERE status_conversao='canonizada';
  IF n_canon <> 23 THEN RAISE EXCEPTION 'POST-GUARD: canonizada esperado 23, achou % -> ROLLBACK', n_canon; END IF;
  SELECT COUNT(*) INTO n_alvo FROM ref_criaturas
    WHERE id IN (718, 966, 2098, 898, 1086) AND status_conversao='canonizada';
  IF n_alvo <> 5 THEN RAISE EXCEPTION 'POST-GUARD: esperava 5 ids-alvo canonizada, achou % -> ROLLBACK', n_alvo; END IF;
END
$GUARD$;

COMMIT;
