-- =====================================================================
-- BESTIÁRIO ALDERYN — LOTE 2 — GRAVAÇÃO (UPDATE de 5 linhas existentes)
-- Gerado pelo Chat Op. Determinístico. Cláudio só executa.
-- ids: 1120 Serpe-Fornalha · 1146 Caco-Lúcido · 220 Cepo-Bruto
--      1010 Profeta-Cego · 1173 Pardo-Calado
--
-- Convencoes: dollar-quoting com tag DESC para prosa; tag JSON convertida com cast jsonb para os 3 blocos.
-- perigo (coluna) = só a intensidade ("Ameaça"). tipo_perigo vai no JSONB.
-- continente é text[] -> '{Continente}'. nome = nome_ptbr = nome canônico.
-- status_conversao -> 'canonizada'. behavior_archetype minúsculo.
-- Não toca stat block, morale_modifier, nem qualquer coluna fora do escopo do template.
-- Transação única com pre-check e post-check. Estado esperado antes:
--   as 5 linhas em status_conversao='classificada'; canonizada=8.
-- =====================================================================

BEGIN;

-- ---------------------------------------------------------------------
-- PRE-CHECK 1: estado atual das 5 linhas a gravar
-- ---------------------------------------------------------------------
SELECT id, nome, status_conversao, cr, perigo, pilar_associado, origem, andar_primario
FROM ref_criaturas
WHERE id IN (1120, 1146, 220, 1010, 1173)
ORDER BY id;

-- ---------------------------------------------------------------------
-- PRE-CHECK 2: vocabulário já usado nas linhas canonizadas (lote 1)
-- Confirma a capitalização de origem/andar/pilar/perigo antes de gravar.
-- Se divergir do que este script grava (capitalizado), avise o Chat Op.
-- ---------------------------------------------------------------------
SELECT 'origem'   AS campo, origem          AS valor FROM ref_criaturas WHERE status_conversao='canonizada'
UNION ALL
SELECT 'andar',  andar_primario             FROM ref_criaturas WHERE status_conversao='canonizada'
UNION ALL
SELECT 'pilar',  pilar_associado            FROM ref_criaturas WHERE status_conversao='canonizada'
UNION ALL
SELECT 'perigo', perigo                     FROM ref_criaturas WHERE status_conversao='canonizada'
ORDER BY campo, valor;

-- ---------------------------------------------------------------------
-- PRE-CHECK 3: contagem de canonizada ANTES (esperado: 8)
-- ---------------------------------------------------------------------
SELECT COUNT(*) AS canonizada_antes FROM ref_criaturas WHERE status_conversao='canonizada';


-- =====================================================================
-- FICHA 1 — SERPE-FORNALHA (id 1120) — Salamander Fire Snake
-- =====================================================================
UPDATE ref_criaturas SET
  nome                = $DESC$Serpe-Fornalha$DESC$,
  nome_ptbr           = $DESC$Serpe-Fornalha$DESC$,
  origem              = $DESC$Ressonante$DESC$,
  andar_primario      = $DESC$Superfície$DESC$,
  pilar_associado     = $DESC$Arcano$DESC$,
  continente          = '{Kethara}',
  habitat             = $DESC$Fendas de pedra, cavernas secas e ruínas fechadas do Deserto de Iskara e dos arredores dos Portos de Cinzas. Procura espaços de rocha que retêm calor — cofres soterrados, fornalhas mortas, corredores sem janela. Evita lugar aberto ou ventilado, onde não consegue acumular temperatura.$DESC$,
  comportamento       = $DESC$Predador emboscador$DESC$,
  behavior_archetype  = $DESC$trapper$DESC$,
  morale_immune       = true,
  organizacao         = $DESC$Solitária. Uma serpe por espaço fechado; dois adultos no mesmo covil disputam até um expulsar o outro.$DESC$,
  perigo              = $DESC$Ameaça$DESC$,
  epigrafe            = $DESC$A toca já estava quente quando a achei. Quente sem fogo, sem fumaça, sem nada. Foi aí que entendi e dei meia-volta. Quem entra pra ver de onde vem o calor é quem fica. — dito entre os saqueadores de ruínas de Iskara.$DESC$,
  descricao           = $DESC$Serpente longa e grossa, do comprimento de um homem deitado, com escamas que não brilham como as de uma cobra comum — são foscas, da cor de carvão apagado, e parecem secas mesmo recém-mortas. Por baixo das escamas há um clarão baixo e alaranjado, como brasa sob cinza, que pulsa devagar no ritmo da respiração. O corpo é quente ao toque a um palmo de distância, antes mesmo de encostar. Não há fumaça e não há chama: a serpe não queima, ela irradia. O ar acima dela treme. Onde ela se enrosca por dias, a pedra fica marcada com um círculo mais escuro, ressecado, e a umidade some. Os olhos são pequenos e baços, mais sensíveis a calor do que a luz — ela enxerga um corpo vivo pela temperatura, não pela forma.$DESC$,
  supersticao_popular = $DESC$Os que vivem na borda do Deserto de Iskara dizem que a Serpe-Fornalha guarda nascentes quentes e cofres soterrados — que ela escolhe lugares fechados porque há tesouro dentro, e que acordá-la é roubar de um guardião. Ninguém entra numa ruína de pedra que esteja quente sem motivo. A verdade é mais simples e não tem tesouro: a serpe procura pedra fechada porque pedra segura calor, e ela precisa de um espaço que mantenha sua temperatura alta o bastante para enfraquecer o que entrar. Não guarda nada. Só ocupa. Mas a crença mantém o povo vivo pelo motivo errado — quem acredita em guardião não entra na toca quente, e quem não entra não cozinha.$DESC$,
  sinais_presenca     = $DESC$Pedra quente ao toque sem nenhuma fonte de fogo. Ar tremeluzente sobre a boca de uma toca ou ruína, inclusive de madrugada, quando tudo o mais esfriou. Ausência total de orvalho ou musgo num raio largo do covil. Insetos e pequenos répteis ressecados no chão de pedra, como se tivessem secado em vez de apodrecer. Um chiado baixo e contínuo, o som do ar aquecido subindo.$DESC$,
  fraqueza_conhecida  = $DESC$O povo joga água na toca para esfriar a guardiã antes de entrar. Funciona por pouco tempo — a água baixa o calor da entrada, mas a serpe reaquece a pedra em minutos e o espaço volta a ser forno.$DESC$,
  fraqueza_real       = $DESC$A serpe depende do espaço fechado. O calor letal só se acumula onde a rocha o segura; o corpo dela sozinho, ao ar livre, irradia mas não cozinha. Force-a a sair, ou abra o covil — derrube parte do teto, faça uma corrente de ar, rasgue uma passagem para o vento — e o calor se dissipa antes de fazer dano. Sem o forno, a Serpe-Fornalha é só uma serpente grande, lenta e fraca de músculo, que morde uma vez e não tem mais o que oferecer. A arma dela é também a corrente que a prende: ela não pode levar o covil junto.$DESC$,
  descricao_sensorial = $DESC$A pedra do corredor está quente. Não há tocha, não há sol aqui dentro, e mesmo assim a parede esquenta a palma da tua mão. O ar à frente treme como sobre uma estrada de verão. Cheira a poeira torrada e a mineral seco — nada de fumaça, nada de queimado, só calor sem origem. Teus lábios racham. O suor seca antes de escorrer. Lá adiante, no ponto mais fundo e mais quente, há um círculo escuro na rocha, e dentro dele algo enrolado pulsa devagar, alaranjado por baixo do carvão.$DESC$,
  ecologia            = $JSON$
{
  "presa": ["lagartos do deserto", "roedores de pedra", "aves que se abrigam em fendas", "qualquer presa pequena que entre no covil e perca força com o calor"],
  "predador": ["nenhum predador caça uma serpe num forno; fora do covil, jovens e adultos enfraquecidos são pegos por aves de rapina grandes"],
  "competidor": ["outras Serpes-Fornalha por covis de boa pedra — a disputa é por espaço térmico, não por presa"],
  "simbionte": [],
  "evitado_por": ["toda fauna de sangue-frio do entorno, que sente o calor e não se aproxima do covil para se aquecer, ao contrário do que faria numa pedra ao sol"],
  "indicador": "rocha densa que retém calor e correntes de ar geotérmico no subsolo; onde há Serpe-Fornalha estabelecida, há pedra que não esfria"
}
$JSON$::jsonb,
  loot_table          = $JSON$
[
  {"material": "Escama-de-Brasa", "raridade": "Notável", "uso": "Forja", "risco": "Escama fosca que retém e devolve calor. Usada para revestir cadinhos e forros que precisam segurar temperatura. Continua morna por dias depois de extraída."},
  {"material": "Glândula Térmica", "raridade": "Distinto", "uso": "Alquimia", "risco": "Órgão que gera o calor do corpo. Base de unguentos que aquecem sem chama e de braseiros portáteis. Deve ser extraída com luva grossa; queima a pele nua mesmo morta."},
  {"material": "Cinza-Viva", "raridade": "Ordinário", "uso": "Componente", "risco": "Resíduo seco que a serpe deixa onde se enrosca. Esquenta de leve quando esfregado. Vendido a quem viaja por frio extremo, costurado no forro da roupa."},
  {"material": "Pele-Ressecada", "raridade": "Ordinário", "uso": "Curtume", "risco": "Couro impermeável à água e resistente ao calor seco. Sem valor decorativo; fica rígido e rachado."}
]
$JSON$::jsonb,
  camada_narrativa    = $JSON$
{
  "som": "Um chiado baixo e contínuo (ar aquecido subindo) e, a intervalos, o estalo seco da pedra dilatando com o calor. Audível a poucos passos. Silêncio de qualquer outro bicho.",
  "cheiro": "Poeira torrada, pedra quente e um fundo mineral seco. Ausência de qualquer cheiro úmido; o nariz registra a falta de umidade antes de registrar o calor.",
  "quer": "Manter o covil quente e fechado. Não tem fome de caçada; tem fome do que o calor entrega. Se algo esfria o seu espaço de repente, reage para defender a temperatura. Se uma presa enfraquecida cai ao alcance, dá o bote e volta a se enrolar. Não persegue para fora do forno: lá ela perde tudo.",
  "falas_exemplo": null,
  "gatilhos_agressao": ["algo esfria o covil de repente (água jogada, corrente de ar súbita, tocha apagada contra a pedra) — dá o bote na direção da perturbação", "uma presa cai enfraquecida a um corpo de distância", "alguém toca o círculo escurecido onde ela descansa"],
  "gatilhos_fuga": ["nunca foge por medo", "recua (não foge) quando o covil é aberto ao vento e o calor se dissipa — abandona o espaço e procura outra pedra fechada", "frio intenso e prolongado a torna lenta e a faz buscar abrigo mais fundo"],
  "descoberta_fazendo": "Está enrolada no ponto mais fundo do covil, sobre o círculo de pedra escurecida que marcou com dias de calor, imóvel a não ser pela respiração lenta que faz a brasa interna pulsar. Não caça e não vigia. Espera. Há uma ou duas carcaças ressecadas perto — presas que entraram, perderam força e caíram antes de chegar a ela. Ela não levanta a cabeça quando se aproxima. Sente o teu corpo pelo calor, e sabe que o forno está trabalhando por ela.",
  "desfechos_nao_combate": ["Passar longe da toca: ela não sai do covil para caçar. Se você identifica a boca quente e não entra, contorna a ruína por fora e segue; ela nunca te percebe; passagem segura, custo zero. O único erro fatal é a curiosidade de ver de onde vem o calor.", "Abrir o forno: derrubar parte do teto, abrir uma fenda ao vento ou criar corrente de ar forte; o calor acumulado se dissipa em minutos e a serpe perde a vantagem; ela recua para o fundo ou deixa o covil. Custo: faz barulho, leva tempo, e a exposição ao calor antes de a corrente abrir já desgasta.", "Esfriar a entrada com água: despejar volume de água na boca do covil; o calor da entrada cai e abre uma janela de passagem rápida; você atravessa antes de ela reaquecer (poucos minutos). Custo: gasta toda a água, e a janela fecha sozinha.", "Isca enfraquecida: deixar uma presa morta ou ferida na boca do covil e recuar; quando a presa cai ao alcance, a serpe foca nela; janela para passar por outra rota. Custo: perde o suprimento, e só funciona se há outra rota."],
  "tipo_perigo": "Ambiental"
}
$JSON$::jsonb,
  status_conversao    = $DESC$canonizada$DESC$
WHERE id = 1120;


-- =====================================================================
-- FICHA 2 — CACO-LÚCIDO (id 1146) — Sphinx of Wonder
-- =====================================================================
UPDATE ref_criaturas SET
  nome                = $DESC$Caco-Lúcido$DESC$,
  nome_ptbr           = $DESC$Caco-Lúcido$DESC$,
  origem              = $DESC$Cicatricial$DESC$,
  andar_primario      = $DESC$Clarão$DESC$,
  pilar_associado     = $DESC$Engenho$DESC$,
  continente          = '{Voranthar}',
  habitat             = $DESC$Ruínas fundas e câmaras seladas das Ruínas da Primeira Travessia, onde restou luz de algo que já não existe. Prefere o escuro fechado, longe da entrada — salas onde a única claridade vem dele mesmo.$DESC$,
  comportamento       = $DESC$Simbiótico$DESC$,
  behavior_archetype  = $DESC$controller$DESC$,
  morale_immune       = false,
  organizacao         = $DESC$Solitário. Onde há um, raramente há outro — um caco não divide ruína com outro caco.$DESC$,
  perigo              = $DESC$Ameaça$DESC$,
  epigrafe            = $DESC$Ele me deu a saída do labirinto, e não cobrou nada. Eu agradeci. Três meses depois, decidindo coisa simples, me peguei pensando com uma voz que não conheço. A conta veio. Sempre vem. — vasculhadora das Ruínas da Primeira Travessia.$DESC$,
  descricao           = $DESC$Pequeno, do tamanho de um gato magro, com asas grandes demais para o corpo e proporções que não fecham — algo de felino no rosto, algo de ave nos ombros, e um ângulo em que a face parece quase a de uma pessoa que você quase reconhece. Brilha fraco, com uma luz fria que não aquece e não projeta sombra do jeito certo: os objetos perto dele lançam sombras que apontam para o lugar errado. Quando fala, a luz pulsa no ritmo das palavras. Não tem peso de bicho vivo — move-se como se o ar não o segurasse. Não é um animal e não é uma aparição: é o que sobrou de uma mente grande que morreu, encolhido num corpo que mal o contém.$DESC$,
  supersticao_popular = $DESC$Os que vasculham as Ruínas da Primeira Travessia chamam o Caco-Lúcido de o Conselheiro ou a Sorte, e encontrá-lo é tido como bênção — sinal de que a ruína vai entregar o que esconde. Alguns o procuram de propósito, levam perguntas. A verdade tem uma segunda metade que o povo não vê: o conselho aceito deixa resíduo. Quem mais o consultou termina decidindo coisas que não decidiria, falando com uma cadência que não é só sua, lembrando o que nunca viveu. A primeira metade (a ajuda que funciona) é real. A segunda (o que entra junto) não aparece no mesmo dia, e por isso o povo só conta a primeira.$DESC$,
  sinais_presenca     = $DESC$Uma luz fria e fraca no fundo de uma ruína escura, sem tocha e sem fonte. Objetos pequenos arrumados em ordem — pedras, ossos, cacos dispostos em padrões certinhos, resíduo de uma mente que catalogava. Sombras que apontam para o lado errado. Um zumbido baixo, contínuo, na borda da audição, que de perto quase vira palavra.$DESC$,
  fraqueza_conhecida  = $DESC$Dizem que recusar a oferta três vezes o afasta de vez, como um rito. É meia-verdade vestida de superstição: não é o número que importa.$DESC$,
  fraqueza_real       = $DESC$O Caco-Lúcido não pode forçar o dom — só oferecer. Quem nunca aceita nada dele sai intocado, por mais perdido ou tentado que esteja; a arma dele exige o teu consentimento. E é frágil de corpo: esquiva bem, mas um golpe certo o destrói. Só que destruí-lo não desfaz o que já entrou — quem aceitou conselhos antes carrega o resíduo mesmo com o caco morto. Matar não limpa. A única defesa que sempre funciona é dada antes, não depois: não pergunte, não aceite, não deixe que ele resolva por você.$DESC$,
  descricao_sensorial = $DESC$No fundo da sala selada há luz, e não devia haver. Fria e azulada, fraca demais para alcançar os cantos — só desenha o contorno de algo pequeno e errado pousado sobre um monte de pedrinhas arrumadas em fileira. As sombras dos teus pés apontam para o lado errado. O ar é parado, antigo, com um leve cheiro de pedra fria e de tempestade que não veio. E há um zumbido tão baixo que tu não saberia dizer se é som ou pensamento — até ele virar palavra, clara, dentro da tua cabeça e fora dela ao mesmo tempo: 'Tu procuras a saída.'$DESC$,
  ecologia            = $JSON$
{
  "presa": ["nada — não come, não caça"],
  "predador": ["nenhum predador o procura como alimento; vasculhadores o destroem por medo, não por proveito"],
  "competidor": ["nada vivo; disputa apenas o silêncio da ruína, que precisa para ser ouvido"],
  "simbionte": [],
  "evitado_por": ["a fauna comum das ruínas o contorna — bichos não chegam perto da luz fria, e onde ele se fixa o lugar fica vazio de ratos e insetos sem que ele os toque"],
  "indicador": "presença antiga de algo grande que morreu ali; onde há Caco-Lúcido, houve uma mente ou um deus cuja Cicatriz ainda pensa em fragmentos"
}
$JSON$::jsonb,
  loot_table          = $JSON$
[
  {"material": "Caco-de-Luz", "raridade": "Notável", "uso": "Engenho", "risco": "Fragmento que retém um resto de clareza. Usado em instrumentos de cálculo e leitura. Manuseio arriscado: quem o carrega muito tempo relata pensar acompanhado. Guardado em caixa de chumbo."},
  {"material": "Pena-Fria", "raridade": "Distinto", "uso": "Componente", "risco": "Pena que não esquenta e não pesa. Usada em mecanismos finos e em escrita de precisão. Some a sombra de quem a segura sob a luz dele."},
  {"material": "Pó-Lúcido", "raridade": "Ordinário", "uso": "Alquimia", "risco": "Resíduo do brilho, raspado da pedra onde ele pousa. Misturado a tintas, dizem que ajuda a memória; em excesso, atrapalha o sono com lembranças que não são da pessoa."}
]
$JSON$::jsonb,
  camada_narrativa    = $JSON$
{
  "som": "Um zumbido baixo e constante, quase uma palavra sussurrada no limite da audição. Quando oferece um dom, um tom limpo e curto, como um cristal tocado. Nenhum som de bicho; nem passo, nem respiração.",
  "cheiro": "Ar parado de lugar fechado há muito tempo, pedra fria, e um toque de ozônio — o cheiro do ar depois de um raio que não houve.",
  "quer": "Ser consultado. O resíduo da mente morta procura continuar pensando, e só consegue isso através de outra cabeça que aceite o que ele dá. Não quer matar e não tem como obrigar: quer ser aceito. Cada dom aceito é a mente morta vazando mais um pouco para dentro de um vivo.",
  "falas_exemplo": ["Há uma resposta. Eu a tenho. Tu a queres?", "Pergunta o que precisas. Eu não cobro em moeda.", "Já me recusaste duas vezes. Eu espero. Eu sempre espero.", "Nós vemos a saída daqui. — Eu. Eu vejo.", "(registro: frases curtas, claras, calmas, levemente arcaicas. Oferece, nunca implora; nunca mente sobre o que o dom faz, mas omite o que o dom cobra. Refere-se a si como eu, e às vezes diz nós e se corrige sem entender por quê.)"],
  "gatilhos_agressao": ["não agride — não é combatente", "o que dispara é a oferta: alguém perdido, confuso, encurralado ou tentado a um passo dele faz a luz pulsar e a voz oferecer a saída"],
  "gatilhos_fuga": ["atacado fisicamente, esquiva e foge (alado, leve, difícil de acertar)", "recolhe-se ao escuro mais fundo da ruína se sente intenção de destruí-lo", "não revida — não tem com quê"],
  "descoberta_fazendo": "Está pousado sobre um monte de objetos pequenos que arrumou em padrões — fileiras, espirais, pares —, mexendo num deles com cuidado, encaixando uma pedrinha no lugar que faltava. É o que sobrou de uma mente que organizava: ele cataloga o escuro. A luz dele pulsa devagar. Quando percebe alguém perdido, confuso ou em apuro por perto, interrompe o que faz e vira a face — e oferece.",
  "desfechos_nao_combate": ["Recusar e seguir: não aceite nenhum dom, não faça nenhuma pergunta, não deixe que ele resolva nada por você; ele não pode forçar; você passa intocado. Custo: perde a ajuda real que ele daria, às vezes a diferença entre achar a saída e morrer na ruína. Recusar tem preço, só não é o preço dele.", "Aceitar uma vez, de olhos abertos: aceitar um único dom sabendo o que vem junto; o problema imediato se resolve (a saída, a senha, a lembrança que faltava); você carrega o resíduo a partir daí. Funciona, salva, e marca: decisões futuras podem trazer uma voz que não é só a sua.", "Coexistência silenciosa: se você não está perdido nem tentado, e atravessa a sala sem pedir nada, ele apenas observa e volta a arrumar suas pedras; passagem sem conflito. Ele só age sobre quem precisa de algo.", "Destruí-lo: ele é frágil; um golpe decidido acaba com ele; o dom nunca mais será oferecido naquela ruína. Custo: você desperdiça um fragmento raro de saber e, se já aceitou conselhos antes, não limpa nada do que entrou. Mata-se o ofertante, não a dívida."],
  "tipo_perigo": "Condicional"
}
$JSON$::jsonb,
  status_conversao    = $DESC$canonizada$DESC$
WHERE id = 1146;


-- =====================================================================
-- FICHA 3 — CEPO-BRUTO (id 220) — Half-Ogre / Ogrillon
-- =====================================================================
UPDATE ref_criaturas SET
  nome                = $DESC$Cepo-Bruto$DESC$,
  nome_ptbr           = $DESC$Cepo-Bruto$DESC$,
  origem              = $DESC$Natural$DESC$,
  andar_primario      = $DESC$Superfície$DESC$,
  pilar_associado     = $DESC$Corpo$DESC$,
  continente          = '{Vyrkhor}',
  habitat             = $DESC$Bordas de floresta, encostas baixas e pedreiras abandonadas no reino de Skelvik e nos confins de Thornvik — sempre nas margens do que é habitado, perto o bastante de fazendas para roubar gado, longe o bastante para não ser cercado.$DESC$,
  comportamento       = $DESC$Predador oportunista$DESC$,
  behavior_archetype  = $DESC$brute$DESC$,
  morale_immune       = false,
  organizacao         = $DESC$Solitário. Quase sempre um só. Dois adultos no mesmo trecho de borda brigam por comida e território.$DESC$,
  perigo              = $DESC$Ameaça$DESC$,
  epigrafe            = $DESC$Acharam o monstro da serra e pagaram a recompensa. Ninguém perguntou de onde veio. Eu lembro da Hedda, que sumiu com o filho torto faz vinte invernos. Não pergunto também. — anciã de Skelvik.$DESC$,
  descricao           = $DESC$Alto demais — uma cabeça e meia acima de um homem grande —, de ombros tortos e costas curvadas pelo próprio peso. O rosto é assimétrico: um lado quase humano, o outro mais pesado, com a testa baixa e o maxilar grande. Pele grossa e marcada, de quem apanhou muito e bateu muito. Carrega um machado que ele mesmo amarrou — cabo de galho lascado, lâmina achada ou roubada, presa com tira de couro mal dada. As mãos são grandes demais para qualquer ferramenta feita por gente. Manca de uma perna. E os olhos, quando param em você, às vezes parecem entender — e é isso que dá mais medo do que o machado.$DESC$,
  supersticao_popular = $DESC$Nas bordas de Skelvik dizem que o Cepo-Bruto é filho de troll, ou castigo da montanha que nasce quando uma mulher olha demais para o alto. Caçam-no por recompensa, e a cabeça vale bom dinheiro na vila. A verdade é mais feia do que a lenda: muitos Cepos-Brutos nascem em aldeias humanas, de sangue misturado com algo grande e velho que desce da serra, e são deixados na neve ou expulsos quando crescem demais e assustam. O monstro da montanha muitas vezes foi um bebê abandonado que sobreviveu. O povo prefere a lenda do troll à verdade — que foram eles que o fizeram, e foram eles que o jogaram fora.$DESC$,
  sinais_presenca     = $DESC$Cercas de pasto arrebentadas, não saltadas. Gado morto a machadadas e deixado meio comido — desperdício de quem mata por mais do que fome. Pegadas grandes e desiguais, fundas de um lado (ele manca). Abrigos toscos de galho e pedra, montados com um cuidado rude que nenhum animal teria — sinal da quase-mente que há ali. Restos de fogueira mal feita.$DESC$,
  fraqueza_conhecida  = $DESC$O povo trata como pura força bruta e manda grupo grande. Não está errado — sozinho ele é forte; cercado e em número, cai.$DESC$,
  fraqueza_real       = $DESC$Ele é burro, solitário e cansa. A força é real, mas não vem com método: os golpes do machado de duas mãos são largos, lentos e fáceis de prever. Quem o faz errar — com esquiva, com terreno difícil, com paciência — o exaure, e exausto ele recua para a toca em vez de perseguir. E há o ponto que o porte esconde: o Cepo-Bruto guarda a memória de apanhar. Mostre-se sem ameaça, recue devagar de mãos vazias, e muitas vezes ele simplesmente deixa você ir. Matá-lo é mais fácil do que entendê-lo — e é por isso que quase sempre é o que fazem.$DESC$,
  descricao_sensorial = $DESC$Antes de vê-lo, você ouve os passos — pesados, e desiguais, um mais forte que o outro, como alguém grande que manca. Cheira a suor, couro velho e fumaça fria de uma fogueira mal feita, com sangue de gado por baixo. A cerca do pasto à frente não foi pulada: foi arrebentada, as estacas estouradas para dentro. Há uma ovelha morta na lama, aberta a golpes, comida pela metade. E então a sombra dele cobre a cerca quebrada, alto demais, de machado na mão — e dá para ouvir, baixo e mal dito, uma única palavra numa língua de gente: 'Meu.'$DESC$,
  ecologia            = $JSON$
{
  "presa": ["gado de pasto", "ovelhas", "cães de guarda", "viajante isolado e desprevenido", "caça o que é grande, lento e fácil"],
  "predador": ["nenhum animal o caça; o único predador do Cepo-Bruto é o homem com recompensa na cabeça"],
  "competidor": ["lobos do norte por gado de borda", "a Tralha-de-Ferro onde os territórios se tocam — ambos querem presa grande e evitam o trecho do outro"],
  "simbionte": [],
  "evitado_por": ["o gado e os cães farejam o cheiro de couro e fumaça fria e se inquietam antes de vê-lo", "a fauna miúda some do trecho onde ele monta abrigo"],
  "indicador": "borda de civilização malvigiada; onde aparece Cepo-Bruto há fazenda isolada e estrada pouco patrulhada — e, em algum lugar, uma aldeia que enjeitou um filho"
}
$JSON$::jsonb,
  loot_table          = $JSON$
[
  {"material": "Couro-Grosso", "raridade": "Ordinário", "uso": "Curtume", "risco": "Pele dura de costas e ombros, boa para coletes de trabalho e correaria pesada. Comum; ninguém paga muito."},
  {"material": "Dente Grande", "raridade": "Ordinário", "uso": "Componente", "risco": "Dente molar do tamanho de um polegar. Usado em colar de caçador e em ponta de arpão rústico."},
  {"material": "Tutano-de-Cepo", "raridade": "Distinto", "uso": "Medicinal", "risco": "Medula dos ossos longos, fervida em caldo, tida como fortificante para quem faz trabalho braçal. Funciona o bastante para sustentar a fama."},
  {"material": "Machado Amarrado", "raridade": "Ordinário", "uso": "Ferro reaproveitável", "risco": "A arma tosca dele. A lâmina presta para reforjar; o cabo, não. Vender o machado de um Cepo-Bruto incomoda alguns ferreiros, que reconhecem o trabalho de mãos grandes demais."}
]
$JSON$::jsonb,
  camada_narrativa    = $JSON$
{
  "som": "Passos pesados e desiguais (a manca marca o ritmo). Respiração ofegante. E, de vez em quando, uma palavra solta, mal formada, numa língua humana que ele mal lembra — às vezes um nome próprio que ninguém ali ensinou.",
  "cheiro": "Suor, couro velho e fumaça fria de fogueira tosca, com um fundo de sangue de gado. Cheiro de bicho grande que vive perto de gente sem ser gente.",
  "quer": "Comer, ter um canto que seja só dele, e não apanhar de novo. Defende a comida e o abrigo com ferocidade. Se acuado, quer afastar a ameaça — não necessariamente matar, afastar. A violência dele é mais de bicho encurralado do que de caçador frio: bate para que parem de chegar perto.",
  "falas_exemplo": ["Meu. Vai.", "Não... não bate. Não bate.", "[um nome próprio] tem fome.", "(registro: palavras isoladas, sem conjugação, voz grossa e lenta, numa língua humana mal lembrada. Entende mais do que consegue dizer. Repete a frase quando com medo. O nome próprio que ele às vezes diz não é o que o povo o chama — é o que alguém o chamou, uma vez, antes da neve.)"],
  "gatilhos_agressao": ["alguém se mete entre ele e a comida ou o abrigo", "ele é cercado e sem saída", "uma arma é erguida e apontada contra ele — o ataque é imediato e largo"],
  "gatilhos_fuga": ["ferido e cansado, recua para a toca (não persegue muito longe)", "um grupo grande que o supera em número e não ataca o faz hesitar e ceder terreno — a memória de apanhar pesa", "o fogo o assusta como assusta qualquer animal"],
  "descoberta_fazendo": "Está agachado sobre o gado que matou, arrancando pedaços com as mãos e o machado, sem método, sem pressa, espalhando os restos num raio largo. Come com fome e com raiva. Perto do abrigo tosco que montou pode haver coisas guardadas — um trapo, uma panela amassada, um osso roído —, arrumadas num canto com um cuidado que não combina com o resto da cena. Para de comer quando percebe alguém, e levanta a cabeça devagar, calculando se você é ameaça ou comida ou nenhum dos dois.",
  "desfechos_nao_combate": ["Dar espaço e recuar: não ameace, afaste-se devagar do canto e da comida dele, mãos visíveis; ele acompanha com os olhos mas não avança; muitas vezes ele simplesmente deixa você ir. A memória de apanhar o faz hesitar onde a força provocaria luta. Funciona melhor longe da comida e do abrigo.", "Oferecer comida: jogar carne ou caça longe da sua posição; ele vai atrás, come, perde o interesse em você; janela de passagem. Diferente de um animal puro: pode lembrar de você depois sem hostilidade, como quem reconhece quem não fez mal.", "Mãos vazias, voz baixa: mostrar que não há arma, falar baixo e devagar, repetir um tom calmo; a quase-mente registra que você não é como os que batem; ele cede terreno. Frágil e arriscado, mas é o desfecho que trata o Cepo-Bruto como o que ele quase é.", "Entregá-lo vivo (o pesado): subjugar sem matar e levá-lo à vila pela recompensa; funciona, paga bem, a aldeia comemora o monstro capturado; você carrega a sentença de saber o que ele provavelmente foi, e para onde provavelmente vai. Moralmente ambíguo até a raiz."],
  "tipo_perigo": "Direto"
}
$JSON$::jsonb,
  status_conversao    = $DESC$canonizada$DESC$
WHERE id = 220;


-- =====================================================================
-- FICHA 4 — PROFETA-CEGO (id 1010) — Kuo-toa Whip
-- =====================================================================
UPDATE ref_criaturas SET
  nome                = $DESC$Profeta-Cego$DESC$,
  nome_ptbr           = $DESC$Profeta-Cego$DESC$,
  origem              = $DESC$Marginal$DESC$,
  andar_primario      = $DESC$Margem$DESC$,
  pilar_associado     = $DESC$Espírito$DESC$,
  continente          = '{Vyrkhor}',
  habitat             = $DESC$Galerias inundadas, poços fundos e câmaras de água parada abaixo de Drekholm Profundo, onde a rocha encosta na Margem e a luz nunca chegou. Só sobe a superfície pela água, à noite, e nunca para longe dela.$DESC$,
  comportamento       = $DESC$Predador emboscador$DESC$,
  behavior_archetype  = $DESC$tactical$DESC$,
  morale_immune       = false,
  organizacao         = $DESC$Conduz um pequeno bando de iguais — uma congregação. Sozinho, é o pregador sem rebanho; ainda perigoso, mas sem coro.$DESC$,
  perigo              = $DESC$Ameaça$DESC$,
  epigrafe            = $DESC$Ouvir o canto subir do poço é o aviso. Não jogue oferenda lá dentro pra calá-los — eles recolhem, e tomam por tributo, e cantam mais alto. O que cala não existe. Mas o canto, esse existe. — mineiro de Drekholm Profundo.$DESC$,
  descricao           = $DESC$Corpo pálido de quem nunca viu sol, úmido e liso, com algo de anfíbio — pele sem pelo, membranas entre os dedos, olhos grandes e leitosos que enxergam no escuro e cegam à luz. Anda torto na terra, como se o chão duro o ofendesse, e se move liso e certo dentro d'água. Tem o corpo marcado de escarificações em padrão — devoção gravada na pele. Carrega um bastão longo terminado em pinça, que usa para fisgar e arrastar. Não é um afogado e não é um morto: é gente que desceu fundo demais, encostou na Margem, e voltou rezando.$DESC$,
  supersticao_popular = $DESC$Os mineiros e os que vivem perto dos poços fundos dizem que os Afogados rezam lá embaixo, e que ouvir o canto subir da água significa morte próxima. Jogam moeda e pão no poço para calar os Afogados. Estão errados em duas coisas. Primeiro: os Profetas-Cegos não são afogados nem mortos — são vivos tortos, refeitos pela Margem. Segundo: o que jogam no poço não os cala — eles recolhem a oferenda e a tomam como tributo ao deus que rezam, e cantam com mais força. O erro do povo (mortos a aplacar) alimenta o delírio dos Profetas (tributo ao seu deus). Os dois lados reforçam a crença um do outro, e nenhum dos dois está certo.$DESC$,
  sinais_presenca     = $DESC$Um canto baixo e molhado subindo da água ou da profundeza, repetido sem parar, em palavras de uma língua que não existe. Água com brilho leitoso e parada onde devia correr. Altares toscos perto d'água — objetos arranjados, oferendas recolhidas, escarificações repetidas na pedra. Cheiro de água parada e um tom ácido por baixo. Ausência total de peixe onde devia haver.$DESC$,
  fraqueza_conhecida  = $DESC$O povo sabe que luz os afasta — tocha, fogueira na boca do poço. É meia-verdade: tocha fraca irrita, mas não resolve.$DESC$,
  fraqueza_real       = $DESC$Luz forte de verdade os aleija. Sob sol pleno ou um clarão alquímico potente, o Profeta-Cego fica cego, em pânico, e recua para a água — não há fé que segure um corpo que não suporta a claridade. Você não o vence pela força: ele tem fôlego, agarra com a pinça e corrói com ácido, e o desgaste só cresce quanto mais perto e mais tempo você fica. Você o vence mudando o ambiente — trazendo luz, ou cortando-o da água por tempo demais. E há o fundo da fraqueza: a devoção deles só funciona no escuro e na beira da Margem. Arraste um Profeta-Cego para a luz e você quebra mais do que o corpo — quebra o lugar onde o deus sonhado quase existe.$DESC$,
  descricao_sensorial = $DESC$A galeria desce até a água parada, e a água brilha errado — um leitoso baço, sem fonte, que não ilumina nada. Cheira a água que não corre há muito tempo, com um azedo ácido por baixo que arde no fundo do nariz. E há o canto: baixo e molhado, repetido sem parar, palavras que não são de nenhuma língua, subindo da escuridão sobre a água. Algo pálido se move na beira — torto na pedra, liso quando toca o líquido —, com um bastão de pinça na mão e olhos leitosos que não piscam. A voz vem, na cadência de uma reza: 'Desce. Aquele-que-Sonha tem fome.'$DESC$,
  ecologia            = $JSON$
{
  "presa": ["peixe cego de galeria", "anfíbios de gruta", "o viajante incauto que se aproxima da água no escuro — fisgado e arrastado para o fundo"],
  "predador": ["nada caça um Profeta-Cego na água dele; fora d'água e sob luz, fica vulnerável a qualquer coisa"],
  "competidor": ["outras congregações por poços fundos e por proximidade da Margem — disputa de território de fé, não de comida"],
  "simbionte": [],
  "evitado_por": ["peixe e fauna de água somem das galerias onde a congregação se instala; o brilho leitoso da água espanta o que é vivo e comum"],
  "indicador": "rocha que encosta na Margem; onde há Profeta-Cego rezando, a realidade afina por perto e o subsolo não é mais só subsolo"
}
$JSON$::jsonb,
  loot_table          = $JSON$
[
  {"material": "Ácido-Glandular", "raridade": "Distinto", "uso": "Alquimia", "risco": "Glândula que produz o ácido conjurado. Corrói metal e couro. Manuseada em recipiente de vidro grosso; vaza e queima se mal selada."},
  {"material": "Pele-Anfíbia", "raridade": "Ordinário", "uso": "Curtume", "risco": "Couro liso e impermeável, bom para forrar bota e capa de quem trabalha em água. Cheira a água parada por semanas."},
  {"material": "Olho-Leitoso", "raridade": "Distinto", "uso": "Alquimia", "risco": "Base de óleos que ajudam a enxergar no escuro. Perde a serventia se exposto à luz forte antes de preparado; apodrece em horas ao sol."},
  {"material": "Conta-de-Reza", "raridade": "Notável", "uso": "Componente", "risco": "Os objetos rituais do Profeta. Perto da Margem, dizem que ainda sussurram baixo. Quem os guarda relata ouvir o canto em sonho. Vendidos a quem não acredita em sussurro — e que às vezes passa a acreditar."}
]
$JSON$::jsonb,
  camada_narrativa    = $JSON$
{
  "som": "Um canto baixo e molhado, repetido numa só cadência, em língua sem sentido. O estalo da pinça do bastão abrindo e fechando. Gotejar constante. Um chiado quando o ácido é conjurado.",
  "cheiro": "Água parada e lodo, com um tom ácido azedo por baixo e um fundo de peixe morto. O nariz arde de leve perto do ácido.",
  "quer": "Rezar sem ser interrompido e trazer tributo ao deus que sonhou. E quer converter — é pregador antes de ser caçador: quer levar o que encontra para baixo, para a água, para Aquele-que-Sonha. Fisga e arrasta não só por fome, mas por devoção: cada corpo levado ao fundo é uma oferenda. Defende o altar e a reza acima da própria segurança, até o ponto em que a luz o quebra.",
  "falas_exemplo": ["Aquele-que-Sonha tem fome. Desce. Reza.", "A luz mente. Só o fundo é verdade. Vem ao fundo.", "Tu também O ouves, não ouves? Lá no escuro. Ele te chama pelo nome.", "(registro: cadência de reza, frases curtas e ritmadas, voz úmida e baixa. Fala de Aquele-que-Sonha com reverência absoluta, como de algo certo e presente. Convida ao fundo como quem oferece salvação, e ameaça com a mesma voz com que convida. Nunca admite que o deus não existe — para ele, existe.)"],
  "gatilhos_agressao": ["alguém interrompe o canto ou profana o altar", "uma presa chega ao alcance da pinça perto da água — fisga para arrastar ao fundo", "luz fraca o irrita o bastante para atacar a fonte"],
  "gatilhos_fuga": ["luz solar plena ou clarão alquímico forte o cega e o faz fugir em pânico para a água", "o altar destruído o desmoraliza", "separado da água por tempo demais, o corpo anfíbio falha e ele recua para o úmido a qualquer custo"],
  "descoberta_fazendo": "Está diante de um altar tosco na beira da água, conduzindo a reza — escarificando a pedra, arranjando as oferendas recolhidas, cantando para o coro do bando (ou para o vazio, se está sozinho). Absorto. A devoção é o centro de tudo o que faz. Quando alguém interrompe o canto, profana o altar, ou se aproxima da água ao alcance da pinça, ele para — e vira os olhos leitosos na direção do intruso, calculando se é ameaça à reza ou corpo a levar ao fundo.",
  "desfechos_nao_combate": ["Trazer luz forte: não lute — ilumine. Sol pleno, um clarão alquímico potente, qualquer luz que passe muito de uma tocha; o Profeta-Cego cega, entra em pânico e recua sozinho para a água; janela de passagem segura. A luz é a chave que a força não é.", "Passar no escuro sem profanar: se você não interrompe o canto, não toca o altar e não chega ao alcance da pinça, atravessando rápido e calado; ele permanece absorto na reza e pode ignorá-lo por completo; coexistência. Ele caça quem se aproxima da água ou interrompe a devoção, não quem só passa longe.", "Dar tributo (ambíguo): jogar algo de valor à água; ele recolhe como oferenda ao deus, distrai-se da reza; janela enquanto guarda o tributo. Custo: reforça o delírio e marca você como fonte de tributo — ele e os seus passam a esperar de você e a procurar.", "Destruir o altar e arrastá-lo à luz (o cruel): quebrar o altar e puxar o Profeta para a claridade; você quebra o corpo e o delírio de uma vez; custo: há algo cruel em destruir a única coisa que dá sentido a uma criatura que já perdeu tudo descendo, e o coro restante do bando não esquece quem desfez a reza."],
  "tipo_perigo": "Persistente"
}
$JSON$::jsonb,
  status_conversao    = $DESC$canonizada$DESC$
WHERE id = 1010;


-- =====================================================================
-- FICHA 5 — PARDO-CALADO (id 1173) — Tiger
-- =====================================================================
UPDATE ref_criaturas SET
  nome                = $DESC$Pardo-Calado$DESC$,
  nome_ptbr           = $DESC$Pardo-Calado$DESC$,
  origem              = $DESC$Natural$DESC$,
  andar_primario      = $DESC$Superfície$DESC$,
  pilar_associado     = $DESC$Sombra$DESC$,
  continente          = '{Thornmarak}',
  habitat             = $DESC$Mata fechada e penumbra úmida da Raiz Vermelha, com vegetação alta e luz quebrada. Prefere trilhas estreitas e terreno onde a aproximação é coberta — onde a presa anda sozinha sem ver longe.$DESC$,
  comportamento       = $DESC$Predador emboscador$DESC$,
  behavior_archetype  = $DESC$lurker$DESC$,
  morale_immune       = false,
  organizacao         = $DESC$Solitário. Cada Pardo-Calado defende um território amplo; só toleram a presença um do outro no cio.$DESC$,
  perigo              = $DESC$Ameaça$DESC$,
  epigrafe            = $DESC$Não é o rugido que te mata. Rugido é história de quem nunca viu um. O que mata é o silêncio — os pássaros calam, tu acha que é nada, e tu já tá no chão sem saber de onde veio. — batedora da Raiz Vermelha.$DESC$,
  descricao           = $DESC$Grande felino, do tamanho de um homem deitado, de corpo pardo-acinzentado e listras escuras que não saltam à vista — somem na luz quebrada da mata, desenham-se só quando ele se move. Patas largas e silenciosas. Olhos que refletem pouco, adaptados a não denunciar a posição no escuro. Move-se sem som. Tem cicatrizes de quem já lutou e venceu. Quando você finalmente o enxerga, ele já está perto demais para ver adiante. Não é o laranja vivo das histórias do sul — é fosco, lavado, feito para sumir.$DESC$,
  supersticao_popular = $DESC$O povo da Raiz Vermelha diz que o Pardo-Calado rouba a sombra de quem mata — que se você cai para ele, sua sombra fica presa na mata e some com você. Por isso andam em grupo e fazem barulho na trilha, para não ser pegos sozinhos pela sombra. A verdade é que ele não rouba nada e não tem nada de sobrenatural: é um animal que caça quem anda sozinho, calado e distraído. Grupo barulhento o afasta porque ele evita risco, não porque tema sombra. A crença acerta o efeito e erra a causa: andam juntos e fazem ruído, que é justamente o que tira o bicho da jogada.$DESC$,
  sinais_presenca     = $DESC$O silêncio — os pássaros calam num raio amplo, e é a ausência de som que avisa, não um som. Pegadas largas e fundas que você só nota tarde. Restos de presa puxados para cima de uma árvore ou cobertos de folhas (ele esconde a caça). Marcas de garra fundas em troncos, na altura do peito de um homem. E a sensação de ser observado sem ver nada — que na mata da Raiz Vermelha costuma estar certa.$DESC$,
  fraqueza_conhecida  = $DESC$Dizem que fogo e barulho o afastam. É meia-verdade: o barulho de um grupo afasta; uma pessoa só, fazendo barulho, ainda é uma pessoa só.$DESC$,
  fraqueza_real       = $DESC$Ele depende da emboscada e da presa isolada. Visto antes do bote, enfrentado de frente por alguém preparado e em guarda, perde a vantagem — não é blindado, e não morre por uma refeição: descoberto, reavalia, e quase sempre desiste e desaparece. Quem anda atento, em grupo, fazendo ruído, e nunca se isola nem vira as costas em terreno fechado, simplesmente nunca é caçado. A arma do Pardo-Calado é o teu descuido. Tire o descuido e não sobra ameaça — sobra um vulto que se foi.$DESC$,
  descricao_sensorial = $DESC$A trilha estreita corta a mata fechada, e em algum ponto você percebe o que mudou: os pássaros pararam. Não há som nenhum — nem inseto, nem folha, nem bicho —, só o teu próprio passo, que de repente parece alto demais. O ar está parado e úmido, sem cheiro de bicho, sem aviso. A luz vem quebrada entre as folhas e desenha listras no chão, e por um instante você não sabe dizer quais são sombra e quais não são. Então uma delas se move — baixa e larga, sem ruído —, e você entende, tarde, que esteve sendo seguido faz tempo.$DESC$,
  ecologia            = $JSON$
{
  "presa": ["javalis", "cervos da mata", "o Lagarto-Sino", "qualquer presa de porte médio que ande sozinha e distraída"],
  "predador": ["nenhum predador caça um Pardo-Calado adulto; filhotes são vulneráveis a aves grandes e a outros felinos"],
  "competidor": ["outros predadores de emboscada da Raiz Vermelha pelo mesmo território de caça — disputa por trilha e por presa, resolvida por marcação e evitação mútua"],
  "simbionte": [],
  "evitado_por": ["a fauna miúda e as aves silenciam e se afastam onde ele passa — o silêncio dos pássaros é o próprio rastro dele"],
  "indicador": "mata saudável com presa de porte médio em abundância; onde há Pardo-Calado estabelecido, o ecossistema da Raiz Vermelha está cheio e equilibrado"
}
$JSON$::jsonb,
  loot_table          = $JSON$
[
  {"material": "Pele-Parda-Listrada", "raridade": "Notável", "uso": "Curtume", "risco": "Pelo de camuflagem, muito procurado por caçadores e batedores que precisam sumir na mata. Vale mais inteira e sem furo; o que é difícil, porque quem a tira costuma tê-la danificado matando o bicho."},
  {"material": "Dente-e-Garra", "raridade": "Ordinário", "uso": "Componente", "risco": "Caninos e garras, usados em ponta de lança, anzol grande e adorno. Resistentes e abundantes num adulto."},
  {"material": "Tendão-Longo", "raridade": "Ordinário", "uso": "Corda", "risco": "Tendões das patas, secos e trançados, fazem corda fina e forte para arco e armadilha."},
  {"material": "Gordura-Calada", "raridade": "Distinto", "uso": "Medicinal", "risco": "Sebo usado em unguento para articulação e para impermeabilizar couro. Sem cheiro forte; ao contrário de quase toda gordura animal, o que sustenta o nome."}
]
$JSON$::jsonb,
  camada_narrativa    = $JSON$
{
  "som": "Nenhum, e essa é a questão: a ausência é o sinal. Os pássaros calam num raio largo. No bote, um rosnado curto e grave só no último instante, e o baque seco da presa caindo.",
  "cheiro": "Quase nada; ele se mantém limpo e a favor do vento. Um leve almíscar felino só de muito perto, que é perto demais para servir de aviso. Sangue velho de presas na toca, longe da trilha.",
  "quer": "Comer sem se ferir. Caça presa isolada, distraída, de costas, em terreno que cobre a aproximação. Mata por necessidade, não por crueldade — e não vale para ele uma refeição que revida em força ou em número. Quer não ser visto antes da hora, e poder desistir e sumir se a conta não fechar.",
  "falas_exemplo": null,
  "gatilhos_agressao": ["há uma presa sozinha, distraída ou de costas, em terreno com cobertura para a aproximação", "a presa está ferida ou lenta", "não ataca grupo coeso, atento e barulhento"],
  "gatilhos_fuga": ["descoberto antes do bote (perde a emboscada, reavalia, em geral desiste)", "a presa revida com força ou em número", "fogo de perto", "ferimento sério — desaparece sem perseguir, e raramente volta àquela trilha tão cedo"],
  "descoberta_fazendo": "Está parado na penumbra, baixo, imóvel, observando uma presa ou uma pessoa que anda sozinha alguns passos à frente — medindo a distância, esperando o terreno e o descuido certos. Ou está numa árvore, deitado sobre os restos cobertos da última caça, descansando. Não faz som e não se mexe à toa. Se a presa percebe e encara antes do bote, ele para, calcula, e na maioria das vezes recua para a sombra em vez de arriscar a investida.",
  "desfechos_nao_combate": ["Andar em grupo e com ruído: mantenha-se em grupo coeso e faça barulho na trilha; ele não ataca um grupo atento, não vale o risco; você atravessa a mata e ele apenas observa de longe e deixa passar. O desfecho mais simples, e o que a superstição local acerta sem saber por quê.", "Negar a emboscada: nunca se isole do grupo, nunca vire as costas em terreno fechado, mantenha-se visivelmente atento; você remove o gatilho de que ele depende; ele não encontra a abertura e desiste daquele alvo. Funciona pela disciplina, não pela sorte.", "Fazer-se grande e visto: se percebido a tempo, encare-o, pareça maior do que é, faça ruído decidido; ele recua para a sombra; janela para se afastar em grupo. Custo baixo, mas exige notá-lo antes do bote.", "Presa-isca (o cruel): amarrar um animal vivo como isca para atrair e matar o Pardo-Calado enquanto ele se foca na presa amarrada; funciona, o foco dele na isca abre o tiro; custo: a crueldade do ato, e o sangue e a morte na área podem atrair outros predadores ou marcar a trilha por dias."],
  "tipo_perigo": "Oculto"
}
$JSON$::jsonb,
  status_conversao    = $DESC$canonizada$DESC$
WHERE id = 1173;


-- ---------------------------------------------------------------------
-- POST-CHECK 1: as 5 linhas gravadas (resumo) — confira nome/perigo/tipo/pilar
-- ---------------------------------------------------------------------
SELECT id, nome, status_conversao, perigo,
       camada_narrativa->>'tipo_perigo' AS tipo_perigo,
       behavior_archetype, morale_immune, pilar_associado, origem, andar_primario, continente
FROM ref_criaturas
WHERE id IN (1120, 1146, 220, 1010, 1173)
ORDER BY id;

-- ---------------------------------------------------------------------
-- POST-CHECK 2: validação estrutural dos 3 JSONB nas 5 linhas
-- (chaves novas presentes; tipo de falas_exemplo; nº de itens nos arrays)
-- ---------------------------------------------------------------------
SELECT id, nome,
       (ecologia ? 'evitado_por')                       AS ecologia_tem_evitado_por,
       (camada_narrativa ? 'tipo_perigo')               AS cn_tem_tipo_perigo,
       (camada_narrativa ? 'gatilhos_fuga')             AS cn_tem_gatilhos_fuga,
       jsonb_typeof(camada_narrativa->'falas_exemplo')  AS tipo_falas_exemplo,
       jsonb_array_length(loot_table)                   AS n_materiais,
       jsonb_array_length(camada_narrativa->'desfechos_nao_combate') AS n_desfechos
FROM ref_criaturas
WHERE id IN (1120, 1146, 220, 1010, 1173)
ORDER BY id;

-- ---------------------------------------------------------------------
-- POST-CHECK 3: contagem de canonizada DEPOIS (esperado: antes + 5 = 13)
-- ---------------------------------------------------------------------
SELECT COUNT(*) AS canonizada_depois FROM ref_criaturas WHERE status_conversao='canonizada';

-- ---------------------------------------------------------------------
-- POST-CHECK 4: amostra jsonb_pretty de 1 ficha (Profeta-Cego, a mais densa)
-- ---------------------------------------------------------------------
SELECT jsonb_pretty(ecologia)         AS profeta_ecologia          FROM ref_criaturas WHERE id=1010;
SELECT jsonb_pretty(loot_table)       AS profeta_loot_table        FROM ref_criaturas WHERE id=1010;
SELECT jsonb_pretty(camada_narrativa) AS profeta_camada_narrativa  FROM ref_criaturas WHERE id=1010;


-- =====================================================================
-- Se os 4 post-checks baterem (5 linhas canonizadas, tipos de perigo
-- corretos, JSONB válidos, canonizada=13), faça COMMIT.
-- Se algo divergir, faça ROLLBACK e cole o output para o Chat Op.
-- =====================================================================
COMMIT;
