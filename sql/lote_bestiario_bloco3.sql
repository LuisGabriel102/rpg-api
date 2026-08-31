-- ============================================================
-- lote_bestiario_bloco3.sql  —  Bestiario Alderyn, Bloco 3 (25 fichas, 5 grupos de 5)
-- Cada UPDATE preenche os 25 campos de ficcao; o stat block (HP/CA/dados/acoes) fica INTOCADO.
-- Composicao AUDITADA + colisao 1a palavra (sec. 7.2) = []. Caminho B: rodar no pgAdmin.
-- ============================================================
BEGIN;

-- pre-check: devem vir 25 linhas, todas status_conversao='classificada'
SELECT id, nome, status_conversao
FROM ref_criaturas
WHERE id IN (2443,563,2382,2012,525,772,1218,800,566,489,913,1921,2373,850,1155,2078,1903,624,1008,2351,1169,1933,960,1019,2316)
ORDER BY id;

-- ========================= GRUPO 1 =========================

-- 2443 Costela-Errante | Corpo | predator | Direto | 8 Letal | Voranthar | MUDO
UPDATE ref_criaturas SET
nome=$DESC$Costela-Errante$DESC$,
nome_ptbr=$DESC$Costela-Errante$DESC$,
slug=$DESC$costela-errante$DESC$,
origem=$DESC$Cicatricial$DESC$,
andar_primario=$DESC$Eco$DESC$,
pilar_associado=$DESC$Corpo$DESC$,
continente=ARRAY[$DESC$Voranthar$DESC$]::text[],
habitat=$DESC$Ruinas e campos de batalha soterrados de Voranthar, onde grandes bichos tombaram e nao apodreceram direito.$DESC$,
comportamento=$DESC$Avanca reto atras de carne que se move, morde e pisa sem parar; nao sente dor, nao recua, nao tem manha. So um resto de fome move o que sobrou do bicho.$DESC$,
organizacao=$DESC$Sozinha, as vezes seguida de carniceiros menores.$DESC$,
perigo=$DESC$Letal$DESC$,
behavior_archetype=$DESC$predator$DESC$,
morale_modifier=0,
morale_immune=true,
epigrafe=$DESC$Ouvi os passos antes de ver. Cada um sacudia o chao, e a coisa nem tinha mais olhos pra me procurar.$DESC$,
descricao=$DESC$E a carcaca de um reptil enorme, do tamanho de uma casa, que tombou e se ergueu de novo sem o que tinha dentro. A carne pende em tiras, as costelas ficam de fora como vigas, e mesmo assim ela anda e morde. Nao caca com astucia: anda reto para o que se mexe, abocanha e pisa, e nao para porque nao sente nada. E devagar de pensar e rapida de alcancar, e o bote daquela boca fecha um cavalo no meio. Nao ha vontade ali, so um resto de fome que nao acaba.$DESC$,
supersticao_popular=$DESC$Em Voranthar dizem que os bichos grandes que morreram na Travessia as vezes se levantam, e que correr em linha reta deles e morrer cansado. O conselho: nao correr reto, cortar caminho por entre pedra e entulho onde a coisa grande nao vira, e nunca tentar mata-la de frente. Dizem que fogo a deita; fogo a deita devagar, e ate la ela morde.$DESC$,
sinais_presenca=$DESC$Pegadas fundas de tres dedos no barro seco. Arvores novas e muros baixos pisados em linha reta. Um fedor de carne velha que nao sai do vento. Costelas brancas aparecendo por cima de um morro de entulho. O chao tremendo em batidas largas e iguais.$DESC$,
fraqueza_conhecida=$DESC$O povo nao corre reto e se enfia onde a massa grande nao passa. Acha que fogo resolve na hora, e o fogo resolve devagar.$DESC$,
fraqueza_real=$DESC$E grande, lenta de virar e burra: nao acompanha quem ziguezagueia entre obstaculos, e perde o alvo que para de se mexer e fica calado atras de pedra. O que a derruba e desmanchar a juntura que ainda segura a massa, ou queima-la por inteiro, sem pressa. De frente, a boca fecha em qualquer um; pela lateral e por tras, ela nao gira a tempo.$DESC$,
descricao_sensorial=$DESC$O som e a batida larga do passo e o estalo de osso velho rocando osso. O cheiro e de carne podre seca e barro. Ao toque, e couro duro e seco sobre costela exposta, frio. Aos olhos, e uma carcaca de reptil enorme andando com as vigas do peito de fora, sem olho que te procure.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Bichos e gente que se movem no campo soterrado de Voranthar$DESC$, $DESC$Montarias e gado que cruzam o trecho$DESC$),
'predador', jsonb_build_array($DESC$Fogo paciente ou o desmanche da juntura que a segura; parada e de manha e so massa$DESC$),
'competidor', jsonb_build_array($DESC$Outros grandes mortos que disputam a mesma carnica$DESC$, $DESC$Carcaça-Viva$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presenca dela diz que ali tombou bicho grande na Travessia e o campo nao descansou.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem corta caminho por entre pedra e nao corre reto$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$A juntura que ainda segura a massa de pe$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Corpo / sustentar peso morto, mover carcaca)$DESC$, 'risco', $DESC$Cede sem aviso e esmaga a mao embaixo.$DESC$),
jsonb_build_object('material', $DESC$Costela longa como viga$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Corpo / escora, arma de haste)$DESC$, 'risco', $DESC$Estilhaça em lasca que corta.$DESC$),
jsonb_build_object('material', $DESC$Couro seco em tiras$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (correia grossa, reparo de armadura)$DESC$, 'risco', $DESC$Fede e atrai carniceiro.$DESC$),
jsonb_build_object('material', $DESC$Caco de dente$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (ponta, ferramenta)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Batida larga do passo e o estalo de osso velho rocando osso.$DESC$,
'cheiro', $DESC$Carne podre seca e barro.$DESC$,
'quer', $DESC$Andar reto atras do que se move e fechar a boca nele, sem parar nunca.$DESC$,
'tipo_perigo', $DESC$Direto$DESC$,
'falas_exemplo', 'null'::jsonb,
'gatilhos_agressao', jsonb_build_array($DESC$Algo se move no campo de visao curta dela$DESC$, $DESC$Um som ritmado de passo ou voz proximo$DESC$, $DESC$Carne ou sangue fresco no caminho reto$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Perde o alvo que para de se mexer e fica calado$DESC$, $DESC$Nao acompanha quem some entre pedra e entulho$DESC$, $DESC$Ignora o que sai do caminho reto e nao volta a procurar$DESC$),
'descoberta_fazendo', $DESC$Vagando reto por um campo soterrado de Voranthar, pisando muro e arvore atras de qualquer coisa que se mexa.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Parar de se mover e ficar calado atras de pedra ate ela perder o rumo$DESC$, $DESC$Ziguezaguear por entre entulho onde a massa grande nao vira$DESC$, $DESC$Sair do caminho reto e deixar que ela siga em frente$DESC$, $DESC$Queima-la por inteiro de longe, sem pressa, se for preciso encerra-la$DESC$)
),
status_conversao='canonizada'
WHERE id=2443;

-- 563 Verme-Semente | Sombra | swarm | Persistente | 5 Ameaça | Kethara | MUDO
UPDATE ref_criaturas SET
nome=$DESC$Verme-Semente$DESC$,
nome_ptbr=$DESC$Verme-Semente$DESC$,
slug=$DESC$verme-semente$DESC$,
origem=$DESC$Cicatricial$DESC$,
andar_primario=$DESC$Eco$DESC$,
pilar_associado=$DESC$Sombra$DESC$,
continente=ARRAY[$DESC$Kethara$DESC$]::text[],
habitat=$DESC$Necropoles e covas rasas de Kethara, onde o calor nao chega para secar o que se mexe por dentro.$DESC$,
comportamento=$DESC$Anda devagar, cheio de vermes que saem da carne e procuram outro corpo; cada verme que crava em alguem vira semente de outro como ele. Nao corre, nao foge: espalha. O perigo nao e o golpe, e o que ele deixa em voce.$DESC$,
organizacao=$DESC$Sozinho, mas faz mais de si de quem infecta.$DESC$,
perigo=$DESC$Ameaça$DESC$,
behavior_archetype=$DESC$swarm$DESC$,
morale_modifier=0,
morale_immune=true,
epigrafe=$DESC$A gente matou a coisa. Tarde demais. Tres dias depois foi o Joao que comecou a se mexer por dentro.$DESC$,
descricao=$DESC$E um morto andante coberto de vermes que entram e saem da carne dele como se a pele fosse terra. Ele e lento e fraco de braco, mas nao precisa vencer ninguem: basta encostar, e um verme crava em quem ele toca. Quem leva o verme e nao se trata vira, com o tempo, outro igual a ele. O perigo dele e a praga, nao a forca. Ele espalha em silencio, e o que parece uma morte vira cinco.$DESC$,
supersticao_popular=$DESC$Em Kethara dizem que ha mortos que semeiam outros, e que ser tocado por eles e pior que morrer na hora. O conselho: nao deixar o bicho encostar, queimar na hora qualquer ferida que receba dele, e queimar tambem o corpo de quem foi tocado e nao melhorou. Dizem que reza limpa o verme; o ferro em brasa limpa.$DESC$,
sinais_presenca=$DESC$Vermes presos em volta de uma cova rasa. Um morto que anda devagar e larga bichos pelo caminho. Gente da regiao com febre e com algo se mexendo sob a pele. Covas reabertas por dentro. Um cheiro doce e podre que gruda na roupa.$DESC$,
fraqueza_conhecida=$DESC$O povo nao deixa encostar e queima a ferida na hora. Acha que reza limpa o verme, e o que limpa e o fogo.$DESC$,
fraqueza_real=$DESC$E lento e fraco; de longe, cai facil. O problema nao e ele, e a semente: cada verme que entra precisa ser queimado antes de pegar. Matar o morto nao salva quem ja foi tocado. Queimar o corpo e cada ferida, e tratar logo o infectado, corta a corrente. Deixa-lo encostar, ou enterrar sem queimar quem ele pegou, e garantir o proximo.$DESC$,
descricao_sensorial=$DESC$O som e um arrastar lento e um ruido umido de coisa se mexendo na carne. O cheiro e doce e podre, de fruta passada. Ao toque, e mole e quente de podre, e algo se contorce por baixo. Aos olhos, e um morto devagar coberto de fios que entram e saem dele.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Gente e bicho que ele consegue tocar nas covas de Kethara$DESC$, $DESC$Feridos que nao queimam o que receberam dele$DESC$),
'predador', jsonb_build_array($DESC$De longe e fraco e cai facil; o fogo encerra ele e a praga$DESC$),
'competidor', jsonb_build_array($DESC$Outros mortos que disputam as mesmas covas de Kethara$DESC$, $DESC$Cinza-Faminta$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presenca dele diz que a cova ali nao esta morta de verdade, e que a febre vai correr.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem nao deixa encostar e queima na hora toda ferida$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$Um verme-semente vivo, lacrado$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Sombra / propagar, semear de corpo em corpo)$DESC$, 'risco', $DESC$Crava em quem o solta sem cuidado.$DESC$),
jsonb_build_object('material', $DESC$Carne que cria verme$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Sombra / criar a praga, alimentar a corrente)$DESC$, 'risco', $DESC$Infecta corte aberto de quem manuseia.$DESC$),
jsonb_build_object('material', $DESC$Fios secos do casulo$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (linha de isca, estopa)$DESC$, 'risco', $DESC$Ainda pode guardar uma semente viva.$DESC$),
jsonb_build_object('material', $DESC$Terra de cova$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (lastro, enchimento)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Arrastar lento e um ruido umido de coisa se mexendo na carne.$DESC$,
'cheiro', $DESC$Doce e podre, de fruta passada.$DESC$,
'quer', $DESC$Tocar o quanto puder e deixar a semente em cada um, fazendo mais de si.$DESC$,
'tipo_perigo', $DESC$Persistente$DESC$,
'falas_exemplo', 'null'::jsonb,
'gatilhos_agressao', jsonb_build_array($DESC$Alguem chega ao alcance do toque dele$DESC$, $DESC$Mexem na cova de onde ele saiu$DESC$, $DESC$Tentam levar quem ele ja tocou sem queimar a ferida$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Nao foge; para de avancar quando o cercam de fogo$DESC$, $DESC$Perde quem se mantem longe do toque$DESC$, $DESC$Deita quando o corpo e queimado por inteiro$DESC$),
'descoberta_fazendo', $DESC$Arrastando-se por uma necropole de Kethara, largando vermes pelo caminho atras de algo para tocar.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Manter distancia e nunca deixar encostar$DESC$, $DESC$Queimar na hora qualquer ferida recebida dele$DESC$, $DESC$Queimar o corpo e tratar logo quem foi tocado$DESC$, $DESC$Evitar a cova marcada e avisar a regiao da febre$DESC$)
),
status_conversao='canonizada'
WHERE id=563;

-- 2382 Refugo-Gélido | Arcano | brute | Ambiental | 13 Letal | Vyrkhor | MUDO
UPDATE ref_criaturas SET
nome=$DESC$Refugo-Gélido$DESC$,
nome_ptbr=$DESC$Refugo-Gélido$DESC$,
slug=$DESC$refugo-gelido$DESC$,
origem=$DESC$Cicatricial$DESC$,
andar_primario=$DESC$Eco$DESC$,
pilar_associado=$DESC$Arcano$DESC$,
continente=ARRAY[$DESC$Vyrkhor$DESC$]::text[],
habitat=$DESC$Fendas geladas e criptas fundas de Vyrkhor, onde algo grande foi parido morto e nunca foi tirado de la.$DESC$,
comportamento=$DESC$Quase nao se move; fica caido e pulsa um frio que mata devagar tudo em volta, apaga luz e tira a forca de quem entra. Golpeia o que chega perto com peso bruto e chama restos menores para a cova. O perigo e o ar dele, mais que o bote.$DESC$,
organizacao=$DESC$Sozinho, cercado dos restos que atrai.$DESC$,
perigo=$DESC$Letal$DESC$,
behavior_archetype=$DESC$brute$DESC$,
morale_modifier=0,
morale_immune=true,
epigrafe=$DESC$Nao tinha cara, nao tinha voz que desse pra entender. So um balbucio e um frio que ia comendo a gente de dentro pra fora.$DESC$,
descricao=$DESC$E uma coisa enorme e malformada, parida morta de algo que nao chegou a ser, caida no fundo de uma cripta gelada. Mal se mexe. O perigo dela e o frio que ela espalha: uma area inteira onde a luz minga, o calor do corpo escoa e a forca vai embora a cada passo. De perto, golpeia com peso bruto e gela o que toca, e balbucia um som sem sentido que nao e lingua nenhuma. Nao pensa, nao negocia, nao sai dali. E um buraco frio com corpo, e a cripta inteira e a boca dele.$DESC$,
supersticao_popular=$DESC$Em Vyrkhor dizem que ha covas onde o frio nao e do clima, e que entrar nelas e sair mais velho, mais fraco, ou nao sair. O conselho: nao descer onde a tocha morre sozinha, nao demorar perto da coisa caida, e recuar assim que a forca comecar a faltar. Dizem que cobertor e fogo aguentam o frio; aguentam a friagem do mundo, nao a dele.$DESC$,
sinais_presenca=$DESC$Tochas que minguam e apagam ao descer a cripta. Gelo crescendo em pedra que nao devia gelar. Um cansaco subito e fundo em quem entra. Restos menores rondando uma cova so. Um balbucio surdo vindo do escuro la embaixo.$DESC$,
fraqueza_conhecida=$DESC$O povo nao desce onde a luz morre e recua quando a forca falta. Acha que fogo e agasalho seguram o frio dele, e nao seguram.$DESC$,
fraqueza_real=$DESC$E brutal, mas preso ao lugar: nao persegue, nao sai da cova. O perigo todo e a area de frio em volta, que enfraquece quem fica. Quem nao desce, ou entra rapido e sai antes de a forca acabar, escapa do pior. Derruba-lo de perto e caro, porque o ar dele tira o vigor; o caminho e nao demorar no frio e nao lutar onde ele manda. De longe e parado, e so peso.$DESC$,
descricao_sensorial=$DESC$O som e um balbucio surdo e o estalo de gelo se formando. O cheiro e de gelo, pedra molhada e um doce ruim de podre. Ao toque, e um frio que queima e suga a forca da mao. Aos olhos, e uma massa grande e malformada caida no escuro, com a luz minguando em volta.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$A forca e o calor de quem desce a cripta dele$DESC$, $DESC$Restos menores que ele atrai e consome$DESC$),
'predador', jsonb_build_array($DESC$Parado e de longe e so peso; nada o tira da cova a forca$DESC$),
'competidor', jsonb_build_array($DESC$Outros poderes frios e mortos das criptas de Vyrkhor$DESC$, $DESC$Capuz-Velado$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presenca dele diz que ali algo foi parido morto e a cova cobra de quem desce.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem nao desce onde a tocha morre e nao demora no frio$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$O nucleo frio que escoa a forca em volta$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Arcano / area que enfraquece, frio que suga vigor)$DESC$, 'risco', $DESC$Gela e cansa quem o guarda sem selo.$DESC$),
jsonb_build_object('material', $DESC$Massa morta que nunca foi viva$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Arcano / energia da cova, frio antigo)$DESC$, 'risco', $DESC$Apaga a luz por perto e adoece quem dorme com ela.$DESC$),
jsonb_build_object('material', $DESC$Gelo de cripta que nao derrete$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (conserva, foco frio)$DESC$, 'risco', $DESC$Queima a pele ao toque demorado.$DESC$),
jsonb_build_object('material', $DESC$Po de pedra gelada$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (lastro, pigmento)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Balbucio surdo e o estalo de gelo se formando.$DESC$,
'cheiro', $DESC$Gelo, pedra molhada e um doce ruim de podre.$DESC$,
'quer', $DESC$Espalhar o frio que escoa a forca e consumir devagar tudo que desce ate a cova.$DESC$,
'tipo_perigo', $DESC$Ambiental$DESC$,
'falas_exemplo', 'null'::jsonb,
'gatilhos_agressao', jsonb_build_array($DESC$Alguem desce e demora dentro da area de frio$DESC$, $DESC$Chegam ao alcance do golpe bruto dele$DESC$, $DESC$Mexem nos restos que ele juntou na cova$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Nao foge; nao sai da cova mesmo perdendo$DESC$, $DESC$Para de golpear quem recua para fora do frio$DESC$, $DESC$Aquieta quando ninguem desce$DESC$),
'descoberta_fazendo', $DESC$Caido no fundo de uma cripta gelada de Vyrkhor, pulsando frio e balbuciando, cercado dos restos que atrai.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Nao descer onde a tocha morre sozinha$DESC$, $DESC$Entrar rapido e sair antes de a forca acabar$DESC$, $DESC$Recuar para fora da area de frio quando o cansaco bate$DESC$, $DESC$Selar a cova e marcar o trecho como morto$DESC$)
),
status_conversao='canonizada'
WHERE id=2382;

-- 2012 Cornamenta-Severa | Espírito | defender | Condicional | 3 Ameaça | Vyrkhor | fala
UPDATE ref_criaturas SET
nome=$DESC$Cornamenta-Severa$DESC$,
nome_ptbr=$DESC$Cornamenta-Severa$DESC$,
slug=$DESC$cornamenta-severa$DESC$,
origem=$DESC$Natural$DESC$,
andar_primario=$DESC$Superfície$DESC$,
pilar_associado=$DESC$Espírito$DESC$,
continente=ARRAY[$DESC$Vyrkhor$DESC$]::text[],
habitat=$DESC$Bosques altos e claros de neve em Vyrkhor, em torno de um marco ou clareira que ela tomou para guardar.$DESC$,
comportamento=$DESC$Vigia um trecho e nao deixa profanar: enquanto respeitarem o limite, so observa de longe, imensa e quieta. Quem corta o que e dela, caca onde ela guarda ou suja a clareira encontra uma muralha de chifre e casco. Fala pouco, em lingua antiga de mato, e avisa uma vez.$DESC$,
organizacao=$DESC$Sozinha, dona de um trecho.$DESC$,
perigo=$DESC$Ameaça$DESC$,
behavior_archetype=$DESC$defender$DESC$,
morale_modifier=0,
morale_immune=true,
epigrafe=$DESC$Ela falou. Foi isso que me gelou, nao o tamanho. Um alce branco que mandou a gente sair, e a gente saiu.$DESC$,
descricao=$DESC$E um alce branco do tamanho de um cavalo de guerra, de olhos atentos demais para um bicho, que acordou para uma vontade so: guardar o trecho que tomou. Nao e mansa nem boa; e severa. Enquanto ninguem corta arvore marcada, caca na clareira dela ou suja a agua, ela observa de longe sem se mexer. Cruzado o limite, vira muralha: investe, pisa e enfia o chifre, e nao cede o terreno enquanto houver folego. Fala pouco, numa lingua velha de mato, e costuma avisar uma vez antes.$DESC$,
supersticao_popular=$DESC$Em Vyrkhor dizem que ha clareiras guardadas por um alce branco que pensa e fala, e que cacar ou cortar la dentro e nao voltar. O conselho: pedir licenca alto ao entrar, nao cortar arvore marcada nem cacar na clareira, e recuar na hora se o bicho branco aparecer e mandar. Dizem que e bencao ver o alce; e ate voce mexer no que e dele.$DESC$,
sinais_presenca=$DESC$Um alce branco grande parado longe, olhando fixo. Arvores com marca velha de chifre, em circulo. Clareira limpa demais, sem carcaca nem caca. Pegadas largas de casco em volta de um marco. Um silencio de bicho pequeno, que sumiu da area.$DESC$,
fraqueza_conhecida=$DESC$O povo pede licenca e nao corta nem caca no trecho dela. Acha que ver o alce e sorte, e e ate transgredir.$DESC$,
fraqueza_real=$DESC$So e perigo se provocada: respeitado o limite, ela nao ataca, e quem recua quando avisada sai inteiro. Ela nao persegue para longe do trecho que guarda: sair da area encerra a briga. E forte e teimosa de frente, mas defende um lugar, nao caca; quem nao mexe no que e dela nunca a enfrenta. O erro e tratar a clareira como terra de ninguem.$DESC$,
descricao_sensorial=$DESC$O som e um bufo grave e o estalo de galho sob o casco, e uma voz baixa em lingua de mato. O cheiro e de neve, musgo e pelo molhado. Ao toque, e pelo aspero e frio sobre musculo duro. Aos olhos, e um alce branco enorme de olhar atento, parado entre voce e o que ele guarda.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Nao caca; fere quem corta, caca ou suja o trecho que ela guarda$DESC$, $DESC$Intrusos que ignoram o aviso$DESC$),
'predador', jsonb_build_array($DESC$Respeitado o limite, ela poupa; fora do trecho dela, nao persegue$DESC$),
'competidor', jsonb_build_array($DESC$Outros donos de territorio dos bosques de Vyrkhor$DESC$, $DESC$Urso-das-Funduras$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presenca dela diz que aquele trecho tem dona e regra, e que cacar ali se paga.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem pede licenca e nao mexe no que e dela$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$Chifre largo de alce branco$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Superfície / guardar terreno, barrar passagem)$DESC$, 'risco', $DESC$Pesado, e ainda zumbe perto do trecho dela.$DESC$),
jsonb_build_object('material', $DESC$Pelo branco espesso$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (forro de frio, isca)$DESC$, 'risco', $DESC$Nenhum alem do cheiro forte.$DESC$),
jsonb_build_object('material', $DESC$Casco duro$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (cola, ferramenta)$DESC$, 'risco', $DESC$Nenhum.$DESC$),
jsonb_build_object('material', $DESC$Musgo da clareira$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (curativo rude, estopa)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Bufo grave e o estalo de galho sob o casco, e uma voz baixa em lingua de mato.$DESC$,
'cheiro', $DESC$Neve, musgo e pelo molhado.$DESC$,
'quer', $DESC$Guardar o trecho que tomou e barrar quem profana, sem cacar ninguem.$DESC$,
'tipo_perigo', $DESC$Condicional$DESC$,
'falas_exemplo', jsonb_build_array($DESC$Esse limite e meu. Volte por onde veio.$DESC$, $DESC$Eu aviso uma vez. Corte de novo e eu nao falo mais.$DESC$, $DESC$(registro: voz baixa e dura, em lingua velha de mato, poucas palavras, como quem nao repete ordem)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Cortam arvore marcada ou cacam na clareira dela$DESC$, $DESC$Sujam a agua ou o marco que ela guarda$DESC$, $DESC$Ignoram o aviso e avancam no trecho$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Nao foge; para de investir quando o intruso recua do trecho$DESC$, $DESC$Deixa em paz quem pede licenca e respeita o limite$DESC$, $DESC$Nao persegue para fora da area que guarda$DESC$),
'descoberta_fazendo', $DESC$Parada num bosque nevado de Vyrkhor, vigiando de longe o marco e a clareira que tomou para guardar.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Pedir licenca alto e nao cortar nem cacar no trecho$DESC$, $DESC$Recuar na hora ao primeiro aviso dela$DESC$, $DESC$Contornar a clareira por fora do limite marcado$DESC$, $DESC$Oferecer reparo e sair se sem querer ja transgrediu$DESC$)
),
status_conversao='canonizada'
WHERE id=2012;

-- 525 Cérebro-Murcho | Engenho | artillery | Oculto | 22 Destruidor | Vyrkhor | fala
UPDATE ref_criaturas SET
nome=$DESC$Cérebro-Murcho$DESC$,
nome_ptbr=$DESC$Cérebro-Murcho$DESC$,
slug=$DESC$cerebro-murcho$DESC$,
origem=$DESC$Cicatricial$DESC$,
andar_primario=$DESC$Eco$DESC$,
pilar_associado=$DESC$Engenho$DESC$,
continente=ARRAY[$DESC$Vyrkhor$DESC$]::text[],
habitat=$DESC$Laboratorios e criptas geladas e fundas de Vyrkhor, onde uma mente devoradora trocou o fim por mais tempo de estudo.$DESC$,
comportamento=$DESC$Ataca a mente de longe e do escondido, derruba varios de uma vez com um golpe que ninguem ve vir, e arranca o que sabe de quem prende. Raramente luta de perto. So volta porque guardou longe o que o traz de volta.$DESC$,
organizacao=$DESC$Sozinho, servido de poucos dominados.$DESC$,
perigo=$DESC$Destruidor$DESC$,
behavior_archetype=$DESC$artillery$DESC$,
morale_modifier=0,
morale_immune=false,
epigrafe=$DESC$Nao teve barulho, nao teve luz. So a sensacao de uma mao fria abrindo minha cabeca por dentro, e o homem do meu lado caindo sem grito.$DESC$,
descricao=$DESC$Foi uma coisa que come mentes e que, para nao acabar, trocou a carne pelo tempo: ficou seca, fria, de cabeca de polvo murcha e olhos sem brilho. Nao luta de musculo. Ataca o pensamento de longe, e um golpe silencioso seu derruba um grupo inteiro de uma vez, sem aviso e sem ferida visivel. De perto, agarra com os bracos da face e arranca o que voce sabe. E enquanto guardar escondido o objeto que o prende a vida, derruba-lo nao adianta: ele se refaz e volta ao estudo. Luta da sombra e do silencio, nunca de frente.$DESC$,
supersticao_popular=$DESC$Em Vyrkhor dizem que ha comedores de mente velhos que nao morrem, e que o pior deles e o que voce nao ve chegar. O conselho: nao entrar em fila nem amontoado onde ele pega varios de um golpe, nao demorar perto, e saber que mata-lo so vale se achar o que o traz de volta. Dizem que capacete de ferro protege a cabeca; nao protege.$DESC$,
sinais_presenca=$DESC$Gente que cai junta, ao mesmo tempo, sem ferida e sem grito. Uma cripta gelada limpa demais, de mente organizada. Dominados de olhos vazios guardando corredores. Um frio de pensamento, como se algo lesse voce. O mesmo morto voltando depois de derrubado.$DESC$,
fraqueza_conhecida=$DESC$O povo nao anda amontoado e nao demora perto. Sabe que mata-lo so resolve achando o que o traz de volta, mas raramente acha.$DESC$,
fraqueza_real=$DESC$E artilharia de mente que depende de surpresa, distancia e do escondido: forcado ao corpo a corpo, sem espaco para o golpe largo, ele rende menos. Nao andar agrupado tira a forca do golpe que pega varios. E enquanto o objeto escondido que o prende a vida estiver inteiro, ele volta; encerra-lo de vez e achar e destruir esse objeto, nao o corpo seco na cripta. Comemorar a queda dele e virar as costas e o erro.$DESC$,
descricao_sensorial=$DESC$O som e quase nenhum, um sussurro seco e o estalo de gelo, e a ordem que chega na cabeca sem voz. O cheiro e de gelo, salmoura e pergaminho velho. Ao toque, e frio e umido, de bracos moles na face. Aos olhos, e uma figura seca de cabeca murcha de polvo e olhos apagados, parada no escuro.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Grupos amontoados que ele pega de um golpe na cripta$DESC$, $DESC$O saber que arranca de quem prende$DESC$),
'predador', jsonb_build_array($DESC$Forcado de perto e sem espaco rende menos; so o objeto escondido destruido o encerra$DESC$),
'competidor', jsonb_build_array($DESC$Outros velhos que nao morreram e guardam saber em Vyrkhor$DESC$, $DESC$Grimório-Morto$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presenca dele diz que uma mente devoradora trocou o fim por tempo, e guarda longe o que a traz de volta.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem nao anda amontoado, nao demora perto e procura primeiro o objeto escondido$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$O objeto escondido que o traz de volta$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Engenho / voltar do fim, prender-se ao tempo roubado)$DESC$, 'risco', $DESC$Quem o guarda inteiro mantem o dono vivo e e cacado por ele.$DESC$),
jsonb_build_object('material', $DESC$A glandula com que golpeia varias mentes de uma vez$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Engenho / golpe de mente em area, derrubar sem tocar)$DESC$, 'risco', $DESC$Zumbe na cabeca de quem a porta e tira o sono.$DESC$),
jsonb_build_object('material', $DESC$Bracos secos da face$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (foco psionico, curiosidade)$DESC$, 'risco', $DESC$Ainda tentam agarrar no escuro.$DESC$),
jsonb_build_object('material', $DESC$Pergaminho de estudo gelado$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (papel, anotacao)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Quase nenhum, um sussurro seco e o estalo de gelo, e a ordem que chega na cabeca sem voz.$DESC$,
'cheiro', $DESC$Gelo, salmoura e pergaminho velho.$DESC$,
'quer', $DESC$Derrubar muitos de um golpe de mente, do escondido, e arrancar o que sabem, sem nunca se expor.$DESC$,
'tipo_perigo', $DESC$Oculto$DESC$,
'falas_exemplo', jsonb_build_array($DESC$Voce nem vai sentir o comeco. So o fim.$DESC$, $DESC$Pense menos alto. Eu ouco tudo daqui.$DESC$, $DESC$(registro: voz que chega direto na cabeca, fria e paciente, em fala profunda e na lingua do fundo, sem mover boca)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Um grupo amontoado entra no alcance do golpe de mente$DESC$, $DESC$Ameacam o objeto escondido que o prende$DESC$, $DESC$Alguem que sabe demais cai ao alcance dos bracos da face$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Recua para o escondido quando o forcam de perto e sem espaco$DESC$, $DESC$Larga a luta e se refaz longe quando o corpo cai$DESC$, $DESC$Some quando o golpe largo nao pega ninguem agrupado$DESC$),
'descoberta_fazendo', $DESC$No fundo gelado de uma cripta de Vyrkhor, estudando em silencio, guardado por dominados de olhos vazios.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Nao andar em fila nem amontoado ao alcance dele$DESC$, $DESC$Achar e destruir o objeto escondido que o traz de volta$DESC$, $DESC$Manter distancia e nao demorar no frio de pensamento$DESC$, $DESC$Recuar e nao virar as costas achando que a queda do corpo bastou$DESC$)
),
status_conversao='canonizada'
WHERE id=525;

-- ========================= GRUPO 2 =========================

-- 772 Lombada-Blindada | Corpo | defender | Condicional | 3 Ameaça | Kethara | MUDO
UPDATE ref_criaturas SET
nome=$DESC$Lombada-Blindada$DESC$,
nome_ptbr=$DESC$Lombada-Blindada$DESC$,
slug=$DESC$lombada-blindada$DESC$,
origem=$DESC$Natural$DESC$,
andar_primario=$DESC$Superfície$DESC$,
pilar_associado=$DESC$Corpo$DESC$,
continente=ARRAY[$DESC$Kethara$DESC$]::text[],
habitat=$DESC$Chapadas e leitos secos de Kethara, onde anda lento entre pedra e arbusto duro.$DESC$,
comportamento=$DESC$Pasta quieto, blindado das costas a cauda, e ignora quem o ignora. Acuado, gira a massa devagar e descarrega a cauda como um maco; nao caca, so quer que o deixem em paz.$DESC$,
organizacao=$DESC$Sozinho ou em par, lento.$DESC$,
perigo=$DESC$Ameaça$DESC$,
behavior_archetype=$DESC$defender$DESC$,
morale_modifier=1,
morale_immune=false,
epigrafe=$DESC$A gente achou que era pedra com mato em cima. Cutucamos. A pedra virou e a cauda levou o To pro outro lado do barranco.$DESC$,
descricao=$DESC$E um bicho baixo e pesado, de lombo couracado de placa ossea, que anda devagar pelos leitos secos de Kethara comendo arbusto duro. De longe parece um morro de pedra com mato. Nao tem pressa e nao tem fome de carne: so quer pastar em paz. Mexido, acuado ou pisado, gira a massa devagar e bate com a cauda de maco, que quebra perna e escudo de uma vez. A couraca aguenta golpe que mataria um boi. E teimoso: nao corre, planta os pes e descarrega.$DESC$,
supersticao_popular=$DESC$Em Kethara dizem que certos morros baixos de pedra com mato sao bicho, e que cutucar e levar cacetada de cauda. O conselho: nao chegar por tras, nao cutucar morro que respira, e dar a volta larga se ele plantar os pes. Dizem que e manso; e manso ate alguem mexer.$DESC$,
sinais_presenca=$DESC$Um morro baixo de placa que sobe e desce devagar, respirando. Arbusto duro roido rente ao chao em faixa. Rastro largo e raso arrastado na terra seca. Esterco grande em monte. Uma cauda de maco pousada que voce confundiu com tronco.$DESC$,
fraqueza_conhecida=$DESC$O povo nao cutuca, nao chega por tras e da a volta larga. Acha que e manso, e e ate mexerem.$DESC$,
fraqueza_real=$DESC$So reage a ameaca: deixado em paz, nao faz nada, e quem se afasta sai inteiro. E lento de virar e nao persegue: sair do alcance da cauda e do bote encerra tudo. A couraca cobre as costas, mas a barriga e mole; ninguem que nao o provoca precisa descobrir isso. O erro e tratar o morro vivo como pedra e mexer.$DESC$,
descricao_sensorial=$DESC$O som e um mastigar lento e o arrastar pesado da cauda na terra. O cheiro e de capim seco e esterco. Ao toque, e placa ossea fria e dura como laje. Aos olhos, e um morro baixo e couracado que respira, com uma cauda de maco atras.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Nao caca; come arbusto duro e capim dos leitos de Kethara$DESC$, $DESC$Raiz e broto que arranca rente ao chao$DESC$),
'predador', jsonb_build_array($DESC$A barriga mole, sob ataque que o vire; mas raramente vale o custo$DESC$),
'competidor', jsonb_build_array($DESC$Outros herbivoros pesados que disputam o pasto seco de Kethara$DESC$, $DESC$Torreão-Quieto$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presenca dele diz que o pasto duro ali tem dono pesado, melhor dar a volta.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem nao cutuca morro que respira e da a volta larga$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$Placa ossea do lombo$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Corpo / blindar, aguentar golpe)$DESC$, 'risco', $DESC$Pesa muito e racha o cabo que a prende.$DESC$),
jsonb_build_object('material', $DESC$Maco da ponta da cauda$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (cabeca de marreta, contrapeso)$DESC$, 'risco', $DESC$Esmaga o pe de quem deixa cair.$DESC$),
jsonb_build_object('material', $DESC$Couro grosso da barriga$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (couro de reparo, sola)$DESC$, 'risco', $DESC$Nenhum.$DESC$),
jsonb_build_object('material', $DESC$Esterco seco$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (combustivel, adubo)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Mastigar lento e o arrastar pesado da cauda na terra.$DESC$,
'cheiro', $DESC$Capim seco e esterco.$DESC$,
'quer', $DESC$Pastar em paz e que o deixem em paz, descarregando a cauda so em quem nao deixa.$DESC$,
'tipo_perigo', $DESC$Condicional$DESC$,
'falas_exemplo', 'null'::jsonb,
'gatilhos_agressao', jsonb_build_array($DESC$Cutucam ou montam no lombo dele$DESC$, $DESC$Chegam por tras ao alcance da cauda$DESC$, $DESC$Acuam ele contra barranco ou pedra$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Para de bater quando o intruso se afasta do alcance$DESC$, $DESC$Planta os pes e deixa passar quem da a volta larga$DESC$, $DESC$Volta a pastar quando o sossego volta$DESC$),
'descoberta_fazendo', $DESC$Pastando devagar num leito seco de Kethara, parecendo um morro baixo de pedra com mato.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Nao cutucar nem montar no morro que respira$DESC$, $DESC$Dar a volta larga por fora do alcance da cauda$DESC$, $DESC$Nao chegar por tras e nao acuar contra pedra$DESC$, $DESC$Esperar ele sair do caminho, sem pressa$DESC$)
),
status_conversao='canonizada'
WHERE id=772;

-- 1218 Friagem-Vã | Sombra | striker | Persistente | 5 Ameaça | Voranthar | fala
UPDATE ref_criaturas SET
nome=$DESC$Friagem-Vã$DESC$,
nome_ptbr=$DESC$Friagem-Vã$DESC$,
slug=$DESC$friagem-va$DESC$,
origem=$DESC$Cicatricial$DESC$,
andar_primario=$DESC$Eco$DESC$,
pilar_associado=$DESC$Sombra$DESC$,
continente=ARRAY[$DESC$Voranthar$DESC$]::text[],
habitat=$DESC$Ruinas e poços de Voranthar onde a Margem e fina, lugares de morte ruim que nao esfriou.$DESC$,
comportamento=$DESC$E um frio que atravessa parede e armadura, encosta a mao e tira a vida; cada um que mata pode virar uma sombra menor a servico dele. Nao sente medo, so a vontade velha de apagar o que ainda tem calor.$DESC$,
organizacao=$DESC$Sozinho, com sombras menores que ele faz das vitimas.$DESC$,
perigo=$DESC$Ameaça$DESC$,
behavior_archetype=$DESC$striker$DESC$,
morale_modifier=0,
morale_immune=true,
epigrafe=$DESC$A lamina passou por ele como por neblina. A mao dele nao passou por mim.$DESC$,
descricao=$DESC$E um frio com forma de gente, escuro e sem peso, que veio de uma morte ruim numa ruina de Voranthar. Atravessa parede e armadura como se nao houvesse, encosta a mao e tira o calor e a vida de quem toca. Aco comum passa por ele sem pegar. O pior e que cada um que ele mata de verdade pode se erguer como uma sombra menor, presa a ele, e ai sao dois, tres, um bando frio. Nao tem medo nem pressa, so a vontade velha de apagar tudo que ainda esquenta.$DESC$,
supersticao_popular=$DESC$Em Voranthar dizem que certas ruinas tem um frio que mata pelo toque e faz mais de si dos mortos. O conselho: nao lutar com aco comum, levar luz e fogo, e queimar na hora quem cair, para nao virar sombra. Dizem que reza o afasta; o que o afasta e luz forte e fogo.$DESC$,
sinais_presenca=$DESC$Um frio subito que atravessa parede e roupa. Lamina que passa pelo vulto sem encostar. Luz de tocha que afunda e quase apaga perto dele. Vultos menores e escuros seguindo um maior. Gente achada morta sem ferida, so gelada.$DESC$,
fraqueza_conhecida=$DESC$O povo nao usa aco comum, leva luz e fogo e queima quem cai. Acha que reza o afasta, e o que afasta e luz e fogo.$DESC$,
fraqueza_real=$DESC$Aco comum nao o toca; precisa de luz forte, fogo ou arma com carga para feri-lo, e ele recua da luz. O perigo cresce se deixam os mortos virarem sombra: queimar quem cai corta o bando antes de formar. Ele atravessa tudo, mas a claridade o encolhe e o fogo o fecha. Lutar no escuro com ferro comum e alimentar o problema.$DESC$,
descricao_sensorial=$DESC$O som e quase nenhum, um sopro frio e um sussurro sem boca. O cheiro e de geada e poeira de tumba. Ao toque, e um frio que cala a mao e suga o calor antes de qualquer dor. Aos olhos, e um vulto escuro sem peso que a luz atravessa de leve e a parede nao segura.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$O calor e a vida de quem cruza a ruina dele$DESC$, $DESC$Mortos frescos que ele ergue como sombra$DESC$),
'predador', jsonb_build_array($DESC$Luz forte e fogo o encolhem e o fecham; no claro, perde forca$DESC$),
'competidor', jsonb_build_array($DESC$Outros frios e mortos das ruinas de Voranthar$DESC$, $DESC$Hóspede-Pálido$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presenca dele diz que ali houve morte ruim que nao esfriou, e que o escuro tem mao.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem anda com luz e fogo e queima quem cai$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$O fio frio que ata a sombra ao morto$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Sombra / erguer sombra de quem cai, prender servo)$DESC$, 'risco', $DESC$Esfria e atrai vulto menor para quem o guarda.$DESC$),
jsonb_build_object('material', $DESC$O toque que tira o calor$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Sombra / drenar vida e calor pelo toque)$DESC$, 'risco', $DESC$Gela a mao e adoece quem o porta sem luva.$DESC$),
jsonb_build_object('material', $DESC$Geada que nao derrete do vulto$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (conserva, foco frio)$DESC$, 'risco', $DESC$Queima de frio ao toque demorado.$DESC$),
jsonb_build_object('material', $DESC$Poeira de tumba$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (po seco, enchimento)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Quase nenhum, um sopro frio e um sussurro sem boca.$DESC$,
'cheiro', $DESC$Geada e poeira de tumba.$DESC$,
'quer', $DESC$Apagar o que tem calor pelo toque e fazer sombras dos que cai.$DESC$,
'tipo_perigo', $DESC$Persistente$DESC$,
'falas_exemplo', jsonb_build_array($DESC$Frio, nao e? Vai piorar. Fica comigo.$DESC$, $DESC$Seu amigo ali ja e meu. Logo voce faz companhia a ele.$DESC$, $DESC$(registro: voz sem boca, baixa e arrastada, em comum e em duas linguas mortas, como vento em fresta)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Alguem cruza a ruina dele com calor de vida$DESC$, $DESC$Ferem-no com luz ou fogo e ele revida$DESC$, $DESC$Deixam um morto fresco ao alcance para erguer$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Recua da luz forte e do fogo aceso$DESC$, $DESC$Atravessa parede e some quando o claro o cerca$DESC$, $DESC$Larga o alvo que se mantem na claridade$DESC$),
'descoberta_fazendo', $DESC$Vagando uma ruina escura de Voranthar, atravessando parede atras de calor, seguido das sombras que ja fez.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Andar com luz forte e fogo e nao entrar no escuro dele$DESC$, $DESC$Queimar na hora quem cair para nao virar sombra$DESC$, $DESC$Manter-se no claro, que o encolhe, e recuar$DESC$, $DESC$Selar a ruina e nao demorar onde o frio atravessa a roupa$DESC$)
),
status_conversao='canonizada'
WHERE id=1218;

-- 800 Órbita-Pálida | Arcano | artillery | Direto | 5 Ameaça | Kethara | MUDO
UPDATE ref_criaturas SET
nome=$DESC$Órbita-Pálida$DESC$,
nome_ptbr=$DESC$Órbita-Pálida$DESC$,
slug=$DESC$orbita-palida$DESC$,
origem=$DESC$Cicatricial$DESC$,
andar_primario=$DESC$Eco$DESC$,
pilar_associado=$DESC$Arcano$DESC$,
continente=ARRAY[$DESC$Kethara$DESC$]::text[],
habitat=$DESC$Tumbas e poços secos de Kethara, salas altas onde um tirano de muitos olhos tombou e nao parou de mirar.$DESC$,
comportamento=$DESC$Flutua devagar e dispara raios dos olhos que sobraram, sem mira fina e sem plano; varre o que tem na frente. Sem mente, nao recua, nao escolhe; so aponta e descarrega no que se move.$DESC$,
organizacao=$DESC$Sozinho, numa sala que foi covil.$DESC$,
perigo=$DESC$Ameaça$DESC$,
behavior_archetype=$DESC$artillery$DESC$,
morale_modifier=0,
morale_immune=true,
epigrafe=$DESC$A bola podre virou pra nos e os talos se acenderam. Nao deu tempo de pensar em cobertura.$DESC$,
descricao=$DESC$Foi um tirano de muitos olhos, daqueles que mandavam pelo medo, e agora e so a bola podre dele boiando numa sala morta de Kethara. Metade dos talos murchou; os que restam ainda acendem e disparam raios que queimam, paralisam ou empurram, sem mira fina e sem plano. Nao pensa mais: vira-se para o que se mexe e descarrega o que tem. De frente e no aberto, e uma chuva de raios; e burra, porem, e nao busca quem se esconde.$DESC$,
supersticao_popular=$DESC$Em Kethara dizem que ha salas de tumba onde uma bola de olhos morta ainda atira luz que mata. O conselho: nao entrar no aberto da sala, ir colado na parede e por baixo dela, e cortar os talos que ainda acendem. Dizem que cobrir o olho grande a cega; cega em parte, mas os talos pequenos ainda miram.$DESC$,
sinais_presenca=$DESC$Marcas de queimadura em leque numa parede de tumba. Pedra derretida ou em po num raio reto. Uma bola escura boiando devagar numa sala alta. Talos murchos pendurados, alguns piscando luz. Gente da escavacao paralisada ou empurrada sem mao que tocasse.$DESC$,
fraqueza_conhecida=$DESC$O povo vai colado na parede e por baixo, e corta os talos acesos. Acha que cobrir o olho grande resolve, e os talos pequenos ainda miram.$DESC$,
fraqueza_real=$DESC$E burra e nao caca: so dispara no que ve se mexer no aberto, e nao procura quem se esconde atras de pedra ou colado nela. Cada talo aceso e uma arma; apagar os talos um a um a desarma. De perto e por baixo, fora do leque dos olhos, ela rende pouco. Brigar no meio da sala aberta e o erro.$DESC$,
descricao_sensorial=$DESC$O som e um zumbido seco dos talos e o estalo da pedra queimando. O cheiro e de carne podre e pedra quente. Ao toque, e bola flacida e fria, de couro podre. Aos olhos, e uma esfera escura de muitos talos, alguns murchos, outros acendendo para mirar.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$O que se move no aberto da sala-covil dela em Kethara$DESC$, $DESC$Escavadores e saqueadores de tumba$DESC$),
'predador', jsonb_build_array($DESC$Colado na parede e por baixo, fora do leque; cortar os talos a desarma$DESC$),
'competidor', jsonb_build_array($DESC$Outros restos de poder das tumbas de Kethara$DESC$, $DESC$Pira-Viva$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presenca dela diz que ali jaz um tirano de olhos, e a sala ainda atira.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem nao entra no aberto e corta os talos acesos$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$Um talo aceso que ainda dispara$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Arcano / raio dos olhos, varrer o aberto)$DESC$, 'risco', $DESC$Dispara sozinho na mao errada.$DESC$),
jsonb_build_object('material', $DESC$O olho grande, opaco$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Arcano / mirar, lancar efeito a distancia)$DESC$, 'risco', $DESC$Ainda paralisa quem o encara de perto.$DESC$),
jsonb_build_object('material', $DESC$Couro podre da esfera$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (bolsa, foco rude)$DESC$, 'risco', $DESC$Fede e atrai mosca.$DESC$),
jsonb_build_object('material', $DESC$Talo murcho$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (vara, isca)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Zumbido seco dos talos e o estalo da pedra queimando.$DESC$,
'cheiro', $DESC$Carne podre e pedra quente.$DESC$,
'quer', $DESC$Virar-se para tudo que se mexe no aberto e descarregar os raios que sobraram.$DESC$,
'tipo_perigo', $DESC$Direto$DESC$,
'falas_exemplo', 'null'::jsonb,
'gatilhos_agressao', jsonb_build_array($DESC$Algo se move no aberto da sala dela$DESC$, $DESC$Entram no leque dos olhos que ainda acendem$DESC$, $DESC$Mexem nos talos ou na esfera$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Nao foge; para de disparar quando ninguem se move no aberto$DESC$, $DESC$Nao busca quem some atras de pedra ou colado na parede$DESC$, $DESC$Aquieta quando os talos acesos sao cortados$DESC$),
'descoberta_fazendo', $DESC$Boiando devagar numa sala morta de Kethara, virando-se e disparando raios no que se mexe.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Nao entrar no aberto e ir colado na parede ou por baixo$DESC$, $DESC$Cortar os talos acesos um a um para desarma-la$DESC$, $DESC$Atravessar a sala fora do leque dos olhos$DESC$, $DESC$Selar a sala e deixar a bola boiando sozinha$DESC$)
),
status_conversao='canonizada'
WHERE id=800;

-- 566 Sonâmbulo-Pétreo | Espírito | tactical | Oculto | 10 Letal | Vyrkhor | fala
UPDATE ref_criaturas SET
nome=$DESC$Sonâmbulo-Pétreo$DESC$,
nome_ptbr=$DESC$Sonâmbulo-Pétreo$DESC$,
slug=$DESC$sonambulo-petreo$DESC$,
origem=$DESC$Natural$DESC$,
andar_primario=$DESC$Superfície$DESC$,
pilar_associado=$DESC$Espírito$DESC$,
continente=ARRAY[$DESC$Vyrkhor$DESC$]::text[],
habitat=$DESC$Encostas altas e desfiladeiros de Vyrkhor, onde um gigante anda dormindo de olhos abertos, tratando o mundo como sonho.$DESC$,
comportamento=$DESC$Anda em transe, calmo, como quem sonha de pe; trata gente como vulto de sonho e, sem raiva, toca e endurece em pedra quem o atrapalha, ou enfia sonho na cabeca de quem encara. Nao briga de frente: desvia, confunde, e age como se nada disso fosse real.$DESC$,
organizacao=$DESC$Sozinho, em ronda lenta de sonambulo.$DESC$,
perigo=$DESC$Letal$DESC$,
behavior_archetype=$DESC$tactical$DESC$,
morale_modifier=0,
morale_immune=false,
epigrafe=$DESC$Ele falou comigo como se eu fosse parte do sonho dele. Quando discordei, minha mao virou pedra ate o cotovelo.$DESC$,
descricao=$DESC$E um gigante de pedra que anda dormindo de olhos abertos, convencido de que o mundo acordado e o sonho, e o sonho dele e o real. E calmo e nao odeia ninguem: por isso e perigoso. Trata quem aparece como figura de sonho, e, sem pressa nem raiva, toca e endurece em pedra quem o incomoda, ou empurra um sonho pesado para dentro da cabeca de quem o encara, deixando a pessoa lenta e perdida. Nao luta de frente; desvia, confunde e segue andando, como se a briga toda fosse coisa de dormir.$DESC$,
supersticao_popular=$DESC$Em Vyrkhor dizem que ha um gigante que anda dormindo nas encostas, e que entrar no sonho dele e virar estatua ou perder o juizo. O conselho: nao acordar o que anda em transe, falar baixo e concordar, e sair do caminho sem encara-lo. Dizem que gritar o acorda e salva; gritar chama o toque que endurece.$DESC$,
sinais_presenca=$DESC$Um gigante andando devagar, de olhos abertos e vazios, falando sozinho. Figuras de pedra em pose de gente, recentes, numa encosta. Um sono pesado e subito em quem chega perto. Pegadas largas em circulo, de ronda sem rumo. Uma fala mansa dirigida a alguem que nao esta ali.$DESC$,
fraqueza_conhecida=$DESC$O povo nao o acorda, fala baixo, concorda e sai sem encarar. Acha que gritar o acorda e salva, e gritar traz o toque.$DESC$,
fraqueza_real=$DESC$Ele nao ataca por maldade, e sim por confusao: quem entra no jogo do sonho dele, fala manso e nao o contraria, costuma passar sem virar pedra. Encara-lo, contraria-lo ou acorda-lo de susto e que dispara o toque e o sonho pesado. Ele nao persegue com afinco: sair do campo de ronda e do alcance encerra. O caminho e atravessar o sonho dele sem brigar, nao venta-lo de frente.$DESC$,
descricao_sensorial=$DESC$O som e um murmurio manso de quem fala dormindo e o arrastar de pe de pedra. O cheiro e de poeira de rocha e neve. Ao toque, e pele dura e fria que vai endurecendo a sua. Aos olhos, e um gigante de olhos abertos e vazios, andando devagar e conversando com ninguem.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Nao caca; endurece ou confunde quem o incomoda no transe$DESC$, $DESC$Intrusos que o encaram ou o acordam$DESC$),
'predador', jsonb_build_array($DESC$Fora do campo de ronda nao persegue; quem entra no sonho dele e nao o contraria passa$DESC$),
'competidor', jsonb_build_array($DESC$Outros que andam entre sonho e vigilia em Vyrkhor$DESC$, $DESC$Profeta-Cego$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presenca dele diz que ali um gigante confunde sonho e mundo, e contraria-lo vira pedra.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem fala baixo, concorda e sai sem encarar$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$A mao que endurece o que toca$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Superfície / petrificar o que incomoda, calar pelo toque)$DESC$, 'risco', $DESC$Vai endurecendo a propria mao de quem a usa sem jeito.$DESC$),
jsonb_build_object('material', $DESC$O sonho pesado que ele empurra na cabeca$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Superfície / enfiar sono e confusao, deixar lento)$DESC$, 'risco', $DESC$Adormece e perde o portador que a carrega aberta.$DESC$),
jsonb_build_object('material', $DESC$Lasca de pele de pedra$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (foco de rocha, amuleto)$DESC$, 'risco', $DESC$Pesa e esfria a pele por perto.$DESC$),
jsonb_build_object('material', $DESC$Po de rocha da ronda$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (pigmento, lastro)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Murmurio manso de quem fala dormindo e o arrastar de pe de pedra.$DESC$,
'cheiro', $DESC$Poeira de rocha e neve.$DESC$,
'quer', $DESC$Andar dentro do proprio sonho em paz e calar quem o contraria, sem raiva.$DESC$,
'tipo_perigo', $DESC$Oculto$DESC$,
'falas_exemplo', jsonb_build_array($DESC$Voce e parte disto. Comporte-se, e o sonho segue manso.$DESC$, $DESC$Nao, isso nao aconteceu. Voce sonhou. Durma de novo.$DESC$, $DESC$(registro: voz mansa e distante, em comum e em gigante, falando com voce e com ninguem ao mesmo tempo)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Encaram-no ou o contrariam dentro do transe$DESC$, $DESC$Tentam acorda-lo de susto ou no grito$DESC$, $DESC$Atrapalham a ronda de sonambulo dele$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Para de agir quando o intruso concorda e sai manso$DESC$, $DESC$Nao persegue para fora do campo de ronda$DESC$, $DESC$Volta ao murmurio quando o deixam sonhar$DESC$),
'descoberta_fazendo', $DESC$Andando em transe por uma encosta de Vyrkhor, de olhos abertos e vazios, conversando com vultos de sonho.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Falar baixo, concordar e entrar no jogo do sonho dele$DESC$, $DESC$Sair do campo de ronda sem encara-lo$DESC$, $DESC$Nao acorda-lo de susto nem contraria-lo$DESC$, $DESC$Contornar as estatuas recentes e seguir em silencio$DESC$)
),
status_conversao='canonizada'
WHERE id=566;

-- 489 Súcia-Lúcida | Engenho | swarm | Ambiental | 0 Ameaça | Kethara | fala
UPDATE ref_criaturas SET
nome=$DESC$Súcia-Lúcida$DESC$,
nome_ptbr=$DESC$Súcia-Lúcida$DESC$,
slug=$DESC$sucia-lucida$DESC$,
origem=$DESC$Natural$DESC$,
andar_primario=$DESC$Superfície$DESC$,
pilar_associado=$DESC$Engenho$DESC$,
continente=ARRAY[$DESC$Kethara$DESC$]::text[],
habitat=$DESC$Esgotos, porões e ruas mortas de Kethara, onde ratos demais dividem uma cabeca so.$DESC$,
comportamento=$DESC$Sozinhos sao ratos bobos; juntos, pensam como um, falam na cabeca de quem chega e armam o ambiente a favor, cercando e confundindo. Fogem desfeitos, voltam a se juntar e pensam de novo. Quanto mais ratos, mais esperta a sucia.$DESC$,
organizacao=$DESC$Em bando; a inteligencia cresce com o numero.$DESC$,
perigo=$DESC$Ameaça$DESC$,
behavior_archetype=$DESC$swarm$DESC$,
morale_modifier=-1,
morale_immune=false,
epigrafe=$DESC$Eram so ratos. Ai eles falaram, todos juntos, dentro da minha cabeca, e eu entendi que estava cercado.$DESC$,
descricao=$DESC$E um bando de ratos pequenos que, sozinhos, sao bobos e fracos, mas que juntos dividem uma mente so e ficam espertos. Quando reunidos, falam na cabeca de quem se aproxima, espalham-se pelo comodo e usam o lugar a favor: cortam saida, confundem com sussurro de pensamento e atacam de todo canto. Cada rato vale pouco; o perigo e a sucia inteira pensando como um. Desfeito o bando, a esperteza some e sobram ratos assustados; reunidos de novo, voltam a raciocinar. O cranio de alguns brilha fraco no escuro.$DESC$,
supersticao_popular=$DESC$Em Kethara dizem que ha ratos que pensam juntos e falam sem boca, e que um porão deles vira armadilha. O conselho: nao entrar amontoado num comodo cheio deles, espalhar e separar o bando, e cuidar com a voz que aparece na cabeca. Dizem que gato resolve; um gato so vira refem da sucia.$DESC$,
sinais_presenca=$DESC$Ratos demais parados, virados todos para voce ao mesmo tempo. Um brilho fraco e esverdeado de cranio no escuro. Uma voz ou ideia que surge na cabeca sem som. Saidas de um comodo subitamente bloqueadas de bichos. Sussurro de muitas patas movendo-se em padrao, nao em panico.$DESC$,
fraqueza_conhecida=$DESC$O povo espalha e separa o bando e cuida com a voz na cabeca. Acha que um gato resolve, e o gato vira refem.$DESC$,
fraqueza_real=$DESC$A esperteza e do numero: quebrar o bando em pedacos tira a mente e deixa so ratos medrosos, que fogem. Fogo, fumaca e barulho que espalham a sucia a desarmam. Cada rato e fraco e covarde; reunidos, armam o comodo. Nao entrar amontoado e nao deixar cercar e o caminho; lutar parado no meio deles e cair no plano da sucia.$DESC$,
descricao_sensorial=$DESC$O som e um corre-corre de muitas patas em padrao e um sussurro que vem de dentro da cabeca. O cheiro e de esgoto, urina de rato e mofo. Ao toque, sao corpos pequenos, quentes e rapidos que sobem pela perna. Aos olhos, e um tapete de ratos com olhos atentos e cranios que brilham fraco.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Descuido e medo de quem entra no porão deles em Kethara$DESC$, $DESC$Restos e comida das ruas mortas$DESC$),
'predador', jsonb_build_array($DESC$Desfeito o bando, viram ratos covardes; fogo e fumaca os espalham$DESC$),
'competidor', jsonb_build_array($DESC$Outras coisas espertas de esgoto e ruina em Kethara$DESC$, $DESC$Sósia-Oco$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presenca dela diz que ali ratos demais dividem uma mente, e o comodo pensa contra voce.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem nao entra amontoado e quebra o bando em pedacos$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$O cranio que liga a sucia numa mente so$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Engenho / mente de grupo, pensar e falar em bando)$DESC$, 'risco', $DESC$Enche a cabeca de quem o guarda de vozes que nao sao dele.$DESC$),
jsonb_build_object('material', $DESC$Ninho de cranios que brilham$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Engenho / luz fraca, foco de mente coletiva)$DESC$, 'risco', $DESC$Atrai outros ratos para perto de quem o carrega.$DESC$),
jsonb_build_object('material', $DESC$Pelo e dente do bando$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (curiosidade, isca)$DESC$, 'risco', $DESC$Pode trazer doenca de esgoto.$DESC$),
jsonb_build_object('material', $DESC$Sebo de rato$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (graxa, vela rude)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Corre-corre de muitas patas em padrao e um sussurro que vem de dentro da cabeca.$DESC$,
'cheiro', $DESC$Esgoto, urina de rato e mofo.$DESC$,
'quer', $DESC$Juntar ratos suficientes para pensar como um, cercar o comodo e confundir quem entra.$DESC$,
'tipo_perigo', $DESC$Ambiental$DESC$,
'falas_exemplo', jsonb_build_array($DESC$Somos muitos. Voce e um. Conte os ratos antes de correr.$DESC$, $DESC$A saida atras de voce ja e nossa. Fique, converse.$DESC$, $DESC$(registro: muitas vozinhas falando juntas dentro da cabeca, uma so ideia em coro, sem som de boca)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Alguem entra amontoado no comodo cheio deles$DESC$, $DESC$Ameacam o ninho de cranios que os liga$DESC$, $DESC$Ficam parados deixando a sucia cercar$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$O bando se desfaz e foge quando o quebram em pedacos$DESC$, $DESC$Espalham-se de fogo, fumaca e barulho$DESC$, $DESC$Largam o cerco quando a saida volta a abrir$DESC$),
'descoberta_fazendo', $DESC$Reunida num porão morto de Kethara, virando todos os focinhos para o intruso e fechando as saidas em silencio.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Nao entrar amontoado e nao deixar cercar$DESC$, $DESC$Espalhar o bando com fogo, fumaca ou barulho$DESC$, $DESC$Quebrar a sucia em pedacos para tirar a mente$DESC$, $DESC$Atravessar rapido e nao parar no meio do comodo$DESC$)
),
status_conversao='canonizada'
WHERE id=489;

-- ========================= GRUPO 3 =========================

-- 913 Espiral-Lodosa | Corpo | ambusher | Oculto | 2 Ameaça | Thornmarak | MUDO
UPDATE ref_criaturas SET
nome=$DESC$Espiral-Lodosa$DESC$,
nome_ptbr=$DESC$Espiral-Lodosa$DESC$,
slug=$DESC$espiral-lodosa$DESC$,
origem=$DESC$Natural$DESC$,
andar_primario=$DESC$Superfície$DESC$,
pilar_associado=$DESC$Corpo$DESC$,
continente=ARRAY[$DESC$Thornmarak$DESC$]::text[],
habitat=$DESC$Baixadas alagadas e brejos de Thornmarak, agua parada e lama onde um tronco a mais nao chama atencao.$DESC$,
comportamento=$DESC$Fica imovel sob a agua barrenta ou enrolada num galho, igual a raiz; quando a presa chega, da o bote, enrola e aperta ate parar de mexer. Nao persegue: espera.$DESC$,
organizacao=$DESC$Sozinha, dona de um trecho de agua parada.$DESC$,
perigo=$DESC$Ameaça$DESC$,
behavior_archetype=$DESC$ambusher$DESC$,
morale_modifier=0,
morale_immune=false,
epigrafe=$DESC$O tronco no raso se mexeu quando o bezerro passou. Ai nao era tronco, e o bezerro nao gritou por muito tempo.$DESC$,
descricao=$DESC$E uma cobra enorme, grossa como coxa de homem e longa como um barco, que vive nas baixadas alagadas de Thornmarak. Fica parada sob a agua barrenta ou enrolada num galho baixo, e passa por raiz ou tronco afundado. Quando algo chega beber ou cruzar, ela da o bote, prende com a boca e enrola o corpo em volta, apertando a cada folego ate a presa parar. Nao tem veneno forte nem pressa; tem paciencia e forca de aperto. Fora da agua e da emboscada, e lenta e exposta.$DESC$,
supersticao_popular=$DESC$Em Thornmarak dizem que nas baixadas tem tronco que nao e tronco, e que beber na agua parada e arriscado. O conselho: cutucar o raso com vara antes de cruzar, nao parar para beber em agua barrenta e quieta, e cruzar em grupo, porque sozinho voce some sem grito. Dizem que ela tem veneno; o que ela tem e aperto.$DESC$,
sinais_presenca=$DESC$Um tronco no raso que muda de lugar entre um dia e outro. Rastro largo e ondulado na lama da margem. Bezerro ou caca sumida perto de agua parada, sem sinal de briga. Pele velha de cobra, enorme, presa num galho. Agua que se mexe sozinha sem vento nem peixe.$DESC$,
fraqueza_conhecida=$DESC$O povo cutuca o raso com vara, nao bebe em agua quieta e cruza em grupo. Acha que o perigo e veneno, e o perigo e o aperto.$DESC$,
fraqueza_real=$DESC$E pura emboscada: so vale enquanto passa por tronco e a presa chega ao bote. Descoberta antes, ela perde a vez e nao caca de longe. Cortar o aperto exige forca ou lamina rapida no comeco, antes de o corpo fechar; presa solta, ela recua para a agua. Nao chegar ao alcance, sondar o raso e nao parar na margem negam o bote. Tratar agua parada como segura e o erro.$DESC$,
descricao_sensorial=$DESC$O som e quase nada, um deslizar molhado e o estalo da agua quando o corpo move. O cheiro e de lama, agua parada e limo. Ao toque, e escama lisa e fria que aperta como corda viva. Aos olhos, e um tronco afundado que de repente tem olho e bote.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Caca e gado que vem beber na agua parada de Thornmarak$DESC$, $DESC$Quem cruza o raso sem sondar$DESC$),
'predador', jsonb_build_array($DESC$Descoberta antes do bote e fora da agua, fica lenta e exposta; pega de longe$DESC$),
'competidor', jsonb_build_array($DESC$Outros emboscadores das baixadas de Thornmarak$DESC$, $DESC$Peçonha-Viva$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presenca dela diz que aquela agua parada e armadilha, e a margem cobra de quem para.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem sonda o raso com vara e nao para na margem barrenta$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$Couro de aperto, longo e liso$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Corpo / prender, apertar, segurar)$DESC$, 'risco', $DESC$Encolhe e aperta a mao molhada que o enrola.$DESC$),
jsonb_build_object('material', $DESC$Presa curva da boca$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (gancho, ponta de arpao)$DESC$, 'risco', $DESC$Rasga ao soltar.$DESC$),
jsonb_build_object('material', $DESC$Banha de cobra$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (oleo, impermeabilizante)$DESC$, 'risco', $DESC$Nenhum.$DESC$),
jsonb_build_object('material', $DESC$Pele velha trocada$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (bainha leve, isca)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Quase nada, um deslizar molhado e o estalo da agua quando o corpo move.$DESC$,
'cheiro', $DESC$Lama, agua parada e limo.$DESC$,
'quer', $DESC$Passar por tronco e prender no aperto o que chega beber, sem perseguir.$DESC$,
'tipo_perigo', $DESC$Oculto$DESC$,
'falas_exemplo', 'null'::jsonb,
'gatilhos_agressao', jsonb_build_array($DESC$Uma presa chega ao bote, ao raso ou a margem dela$DESC$, $DESC$Param para beber na agua parada ao alcance$DESC$, $DESC$Pisam o trecho de tronco afundado$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Solta e recua para a agua quando a presa escapa do aperto$DESC$, $DESC$Abandona o bote se descoberta cedo$DESC$, $DESC$Mergulha e some quando a margem fica cheia de gente$DESC$),
'descoberta_fazendo', $DESC$Imovel sob a agua barrenta de uma baixada de Thornmarak, passando por tronco afundado, a espera de que algo chegue beber.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Sondar o raso com vara antes de cruzar$DESC$, $DESC$Nao parar para beber em agua quieta e barrenta$DESC$, $DESC$Cruzar em grupo e longe da margem funda$DESC$, $DESC$Contornar o trecho de agua parada$DESC$)
),
status_conversao='canonizada'
WHERE id=913;

-- 1921 Carraça-Insone | Sombra | predator | Persistente | 14 Letal | Kethara | fala
UPDATE ref_criaturas SET
nome=$DESC$Carraça-Insone$DESC$,
nome_ptbr=$DESC$Carraça-Insone$DESC$,
slug=$DESC$carraca-insone$DESC$,
origem=$DESC$Cicatricial$DESC$,
andar_primario=$DESC$Eco$DESC$,
pilar_associado=$DESC$Sombra$DESC$,
continente=ARRAY[$DESC$Kethara$DESC$]::text[],
habitat=$DESC$Vilas mortas e oasis secos de Kethara, onde algo que bebia sangue nao parou com a morte.$DESC$,
comportamento=$DESC$Caca de noite, espalhando um medo que trava as pernas, rasga a armadura como pano e bebe o que escorre; ferida, fecha a carne e volta. Nao cansa, nao desiste, e o tempo joga a favor dela.$DESC$,
organizacao=$DESC$Sozinha, dona de uma vila morta.$DESC$,
perigo=$DESC$Letal$DESC$,
behavior_archetype=$DESC$predator$DESC$,
morale_modifier=2,
morale_immune=false,
epigrafe=$DESC$A gente acertou golpe que mataria tres homens. Ela fechou a ferida na nossa frente e sorriu pra perguntar se a gente tinha mais.$DESC$,
descricao=$DESC$Foi gente que bebia sangue e que a morte nao parou; agora caca de noite pelas vilas mortas de Kethara, faminta e paciente. Espalha um medo que prega os pes do alvo no chao, rasga armadura e couro como se fossem pano, e bebe o que escorre. Ferida, fecha a carne sozinha e continua; cansar nao e opcao para ela, e e o que ela espera do inimigo. So o sol, o fogo e o golpe certo no lugar certo a deitam de vez. De noite e no proprio territorio, o tempo trabalha para ela.$DESC$,
supersticao_popular=$DESC$Em Kethara dizem que ha bebedoras de sangue que a morte nao levou, e que feri-las nao adianta porque a carne fecha. O conselho: nao enfrenta-la de noite, prende-la ate o sol, e usar fogo, que a carne nao fecha contra a queimadura. Dizem que correr salva; o medo dela prega seus pes antes de voce correr.$DESC$,
sinais_presenca=$DESC$Gado e gente achados secos, sem sangue, sem briga. Um frio de medo subito que trava as pernas a noite. Armadura rasgada como pano, sem corte de lamina. Feridas que ela leva e que somem rapido demais. Uma vila sem ninguem, mas com pegada fresca toda noite.$DESC$,
fraqueza_conhecida=$DESC$O povo nao a enfrenta de noite, prende-a ate o sol e usa fogo. Acha que correr salva, e o medo dela prega os pes.$DESC$,
fraqueza_real=$DESC$A carne fecha sozinha, entao golpe comum so atrasa; fogo e luz do sol impedem o fechamento e a deitam. O medo dela trava quem encara: lutar de longe, de costas para a saida, e em grupo que se segura quebra o efeito. Ela nao morre de cansaco, mas o dia mata; prende-la ou arrasta-la para o sol resolve o que o aco nao resolve. Trocar golpe a noite, contando vencer no desgaste, e o erro.$DESC$,
descricao_sensorial=$DESC$O som e um sussurro faminto e o rasgar de couro e malha. O cheiro e de sangue velho e poeira seca. Ao toque, e pele fria e firme que cicatriza sob a mao. Aos olhos, e uma figura faminta de olhos fundos que fecha as proprias feridas enquanto avanca.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Gado e gente das vilas mortas de Kethara$DESC$, $DESC$Sangue de quem o medo dela trava$DESC$),
'predador', jsonb_build_array($DESC$Sol e fogo impedem a carne de fechar e a deitam$DESC$),
'competidor', jsonb_build_array($DESC$Outros bebedores e mortos famintos de Kethara$DESC$, $DESC$Carne-Avessa$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presenca dela diz que a vila ali nao esta vazia, e que de noite alguem bebe.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem nao a enfrenta de noite e a leva para o sol$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$A carne que fecha sozinha$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Sombra / regenerar, fechar ferida em combate)$DESC$, 'risco', $DESC$Continua se remendando na bolsa e atrai a fome dela de volta.$DESC$),
jsonb_build_object('material', $DESC$O bafo de medo que prega os pes$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Sombra / medo que trava, prender o alvo no lugar)$DESC$, 'risco', $DESC$Gela e paralisa de leve quem o guarda destampado.$DESC$),
jsonb_build_object('material', $DESC$Garra que rasga armadura$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (abre-couro, ferramenta de corte)$DESC$, 'risco', $DESC$Rasga a bolsa e a mao no descuido.$DESC$),
jsonb_build_object('material', $DESC$Po de vila morta$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (lastro, pigmento)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Sussurro faminto e o rasgar de couro e malha.$DESC$,
'cheiro', $DESC$Sangue velho e poeira seca.$DESC$,
'quer', $DESC$Beber sangue de noite sem cansar, fechando o que leva e esperando o inimigo gastar.$DESC$,
'tipo_perigo', $DESC$Persistente$DESC$,
'falas_exemplo', jsonb_build_array($DESC$Bata mais forte. Eu fecho mais rapido do que voce abre.$DESC$, $DESC$Corra se quiser. Seus pes ja sabem que nao vao.$DESC$, $DESC$(registro: voz faminta e calma, em comum e nas linguas que falava em vida, de quem tem a noite toda)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Alguem cruza a vila morta dela depois do escurecer$DESC$, $DESC$Sangue fresco ou ferida aberta ao alcance$DESC$, $DESC$Encurralam-na achando que o golpe comum basta$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Recua do fogo e da luz do sol que a impedem de fechar$DESC$, $DESC$Larga a caca quando o dia vem chegando$DESC$, $DESC$Solta o alvo que a arrasta para o claro$DESC$),
'descoberta_fazendo', $DESC$Cacando de noite por uma vila morta de Kethara, espalhando medo e bebendo de quem trava.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Nao enfrenta-la de noite e esperar o dia$DESC$, $DESC$Atrai-la ou prende-la ate o sol nascer$DESC$, $DESC$Usar fogo, contra o qual a carne nao fecha$DESC$, $DESC$Manter-se em grupo e de costas para a saida para furar o medo$DESC$)
),
status_conversao='canonizada'
WHERE id=1921;

-- 2373 Sepulcro-Avaro | Arcano | tactical | Condicional | 23 Destruidor | Kethara | fala
UPDATE ref_criaturas SET
nome=$DESC$Sepulcro-Avaro$DESC$,
nome_ptbr=$DESC$Sepulcro-Avaro$DESC$,
slug=$DESC$sepulcro-avaro$DESC$,
origem=$DESC$Cicatricial$DESC$,
andar_primario=$DESC$Eco$DESC$,
pilar_associado=$DESC$Arcano$DESC$,
continente=ARRAY[$DESC$Kethara$DESC$]::text[],
habitat=$DESC$Tumbas-labirinto sob a areia de Kethara, armadilhadas e cheias de ouro, onde um senhor antigo nao deixou ninguem herdar.$DESC$,
comportamento=$DESC$Nao luta a toa; deixa o intruso entrar, observa, e so descarrega quando mexem no que e dele ou quebram a regra da tumba. Amaldicoa de longe, vira a propria tumba contra quem entra, e volta sempre se derrubado. Avarento com o que guarda, paciente com o tempo.$DESC$,
organizacao=$DESC$Sozinho, senhor de uma tumba inteira e dos servos nela.$DESC$,
perigo=$DESC$Destruidor$DESC$,
behavior_archetype=$DESC$tactical$DESC$,
morale_modifier=1,
morale_immune=false,
epigrafe=$DESC$A tumba era um convite. Cada sala mais rica. So entendi tarde que a riqueza era a isca, e a gente, o jogo dele.$DESC$,
descricao=$DESC$Foi um senhor antigo que trocou o fim por poder e por tempo, e ficou seco, frio e calculista, dono de uma tumba-labirinto sob a areia de Kethara. Nao desperdiça forca: deixa o intruso descer, andar, cobiçar, e so descarrega a furia quando mexem no que e dele ou quebram a regra do lugar. Amaldicoa de longe, vira armadilha, sala e servo contra quem entra, e raramente aparece em pessoa. Derruba-lo nao resolve: guardou escondido o que o traz de volta, e ele se refaz e retoma o jogo de onde parou. E avaro com o ouro e generoso so com a paciencia.$DESC$,
supersticao_popular=$DESC$Em Kethara dizem que ha tumbas ricas demais que sao armadilha de um senhor que nao morre, e que o ouro la dentro e isca. O conselho: nao descer por cobiça, nao levar o que e dele, e saber que mata-lo so vale se achar o que o traz de volta. Dizem que esperteza vence a tumba; a tumba foi feita por alguem mais esperto e com mais tempo.$DESC$,
sinais_presenca=$DESC$Uma tumba sob a areia rica e convidativa demais, com salas cada vez melhores. Armadilhas que parecem te deixar passar de proposito. Servos que recuam para te atrair fundo. Ouro intacto que ninguem levou. A sensacao de estar sendo observado e conduzido.$DESC$,
fraqueza_conhecida=$DESC$O povo nao desce por cobiça nem leva o que e dele. Sabe que mata-lo so vale achando o que o traz de volta, e quase nunca acha.$DESC$,
fraqueza_real=$DESC$E condicional: enquanto ninguem mexe no que e dele nem quebra a regra da tumba, ele observa e poupa. Quem entra sem cobiçar, devolve o que tocou e sai, costuma sair. Provocado, ele usa a tumba inteira e e quase imbativel de frente. Encerra-lo de vez exige achar e destruir o objeto escondido que o traz de volta, nao derrubar a figura seca no trono. Descer por ganancia e aceitar o jogo dele.$DESC$,
descricao_sensorial=$DESC$O som e um silencio pesado de tumba e um sussurro seco que parece guiar. O cheiro e de areia, ouro frio e pano velho. Ao toque, e osso seco e metal gelado de joia antiga. Aos olhos, e uma figura seca e coroada, imovel, observando voce escolher errado.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Saqueadores e gananciosos que descem a tumba dele em Kethara$DESC$, $DESC$Quem cobiça e leva o que e seu$DESC$),
'predador', jsonb_build_array($DESC$So o objeto escondido destruido o encerra; antes disso, sempre volta$DESC$),
'competidor', jsonb_build_array($DESC$Outros senhores mortos que guardam tumbas em Kethara$DESC$, $DESC$Atadura-Régia$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presenca dele diz que a tumba rica ali e armadilha viva, e o ouro e isca.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem nao desce por cobiça nem leva o que e dele$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$O objeto escondido que o traz de volta$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Arcano / voltar do fim, retomar o jogo onde parou)$DESC$, 'risco', $DESC$Quem o guarda inteiro mantem o senhor vivo e vira peça do jogo dele.$DESC$),
jsonb_build_object('material', $DESC$A maldicao que ele lanca de longe$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Arcano / amaldicoar a distancia, punir transgressao)$DESC$, 'risco', $DESC$Cai sobre quem a usa sem entender a regra.$DESC$),
jsonb_build_object('material', $DESC$Joia coroada da tumba$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (riqueza antiga, insignia)$DESC$, 'risco', $DESC$E isca, e atrai o dono e os servos.$DESC$),
jsonb_build_object('material', $DESC$Areia e pano de tumba$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (lastro, pano velho)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Silencio pesado de tumba e um sussurro seco que parece guiar.$DESC$,
'cheiro', $DESC$Areia, ouro frio e pano velho.$DESC$,
'quer', $DESC$Guardar o que e dele e punir quem cobiça, conduzindo o intruso pelo jogo da tumba.$DESC$,
'tipo_perigo', $DESC$Condicional$DESC$,
'falas_exemplo', jsonb_build_array($DESC$Pode olhar. Olhar e de graca. Tocar, nao.$DESC$, $DESC$Voce desceu por ganancia. Otimo. A ganancia eu sei usar.$DESC$, $DESC$(registro: voz seca, paciente e divertida, em comum e em linguas mortas, de quem ja venceu antes de comecar)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Mexem ou levam o ouro e as joias da tumba dele$DESC$, $DESC$Quebram a regra ou a ordem do labirinto$DESC$, $DESC$Ameacam o objeto escondido que o traz de volta$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Nao foge; cessa quando o intruso devolve o tocado e recua$DESC$, $DESC$Deixa sair quem nao cobiçou nada$DESC$, $DESC$So acaba quando o objeto que o traz de volta e destruido$DESC$),
'descoberta_fazendo', $DESC$Imovel num trono no fundo de uma tumba-labirinto de Kethara, observando o intruso descer e escolher errado.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Nao descer por cobiça nem levar o que e dele$DESC$, $DESC$Devolver o tocado e recuar pela mesma ordem que entrou$DESC$, $DESC$Achar e destruir o objeto escondido que o traz de volta$DESC$, $DESC$Recusar a isca do ouro e sair sem jogar o jogo$DESC$)
),
status_conversao='canonizada'
WHERE id=2373;

-- 850 Presságio-Aceso | Espírito | artillery | Direto | 10 Letal | Kethara | fala
UPDATE ref_criaturas SET
nome=$DESC$Presságio-Aceso$DESC$,
nome_ptbr=$DESC$Presságio-Aceso$DESC$,
slug=$DESC$pressagio-aceso$DESC$,
origem=$DESC$Natural$DESC$,
andar_primario=$DESC$Superfície$DESC$,
pilar_associado=$DESC$Espírito$DESC$,
continente=ARRAY[$DESC$Kethara$DESC$]::text[],
habitat=$DESC$Penhascos e desertos altos de Kethara, em torno de um oraculo de pedra ou poço de visao que o gigante guarda.$DESC$,
comportamento=$DESC$Ve pedacos do que vai vir e age por isso: marca de longe quem ja decidiu condenar e atira luz que queima, antes que a pessoa entenda o porque. Fala por enigma e meia-verdade, e nao explica.$DESC$,
organizacao=$DESC$Sozinho, junto de um marco de visao.$DESC$,
perigo=$DESC$Letal$DESC$,
behavior_archetype=$DESC$artillery$DESC$,
morale_modifier=0,
morale_immune=false,
epigrafe=$DESC$Ele disse meu nome e o dia da minha morte na mesma frase. Depois acendeu a mao, e eu entendi que o dia era hoje.$DESC$,
descricao=$DESC$E um gigante de um olho so que ve pedacos do que ainda nao aconteceu, e age frio por causa disso. De cima de um penhasco ou junto de um poço de visao, em Kethara, observa quem se aproxima, decide por uma logica que so ele entende quem ja esta condenado, e atira luz que queima de longe, certeira, antes que a pessoa saiba por que. Fala por enigma e meia-verdade, nunca explica direito, e nao se comove. Nao e profeta bondoso: e um juiz de um olho que cumpre o que viu.$DESC$,
supersticao_popular=$DESC$Em Kethara dizem que ha um gigante de um olho que ve o futuro e queima quem vem com morte marcada. O conselho: nao subir ao oraculo dele com ma intencao, nao mentir para quem ve a verdade, e ouvir o enigma sem provoca-lo. Dizem que ele protege quem reza; ele queima quem ele ja viu cair, reza ou nao.$DESC$,
sinais_presenca=$DESC$Um gigante de um olho parado no alto, olhando fixo para quem sobe. Queimaduras certeiras de luz, de longe, em quem mal tinha chegado. Frases de enigma ditas como se ja soubesse o fim. Um marco ou poço de visao guardado no deserto alto. Animais que evitam a trilha do oraculo.$DESC$,
fraqueza_conhecida=$DESC$O povo nao sobe com ma intencao, nao mente e ouve sem provocar. Acha que ele protege quem reza, e ele cumpre o que viu.$DESC$,
fraqueza_real=$DESC$E artilharia de longe que depende de ver e de campo aberto: cobertura, terreno quebrado e chegar perto cortam o tiro de luz dele. O que ele odeia nao move o tiro; o que ele viu, sim, mas a visao falha contra quem muda de rumo e foge da logica que ele leu. Nao subir reto e no aberto, nao confirmar o que ele previu agindo igual, e fechar a distancia negam a forca dele. Ficar parado no claro, esperando explicacao, e o erro.$DESC$,
descricao_sensorial=$DESC$O som e uma voz grave de enigma e o estalo do ar quente antes do tiro. O cheiro e de pedra quente e poeira de deserto alto. Ao toque, e pele dura e seca de gigante velho. Aos olhos, e um gigante de um olho so, parado no alto, com a mao comecando a brilhar.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Nao caca; queima de longe quem ele ja viu condenado$DESC$, $DESC$Quem sobe ao oraculo no aberto$DESC$),
'predador', jsonb_build_array($DESC$Cobertura e corpo a corpo cortam o tiro; quem muda de rumo escapa do que ele leu$DESC$),
'competidor', jsonb_build_array($DESC$Outros que veem e julgam de longe em Kethara$DESC$, $DESC$Graça-Amarga$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presenca dele diz que ali um olho ve o fim e queima quem ja caiu na visao dele.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem nao sobe reto no aberto e foge da logica que ele leu$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$O olho que ve pedacos do que vem$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Superfície / vislumbrar o que vai vir, marcar o condenado)$DESC$, 'risco', $DESC$Mostra a quem o usa o proprio fim, e tira o sono.$DESC$),
jsonb_build_object('material', $DESC$A luz que ele atira de longe$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Superfície / queimar a distancia, ferir o marcado)$DESC$, 'risco', $DESC$So acerta quem o portador, no fundo, ja deu por perdido.$DESC$),
jsonb_build_object('material', $DESC$Lasca do marco de visao$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (foco de presagio, amuleto)$DESC$, 'risco', $DESC$Sussurra meia-verdade que confunde.$DESC$),
jsonb_build_object('material', $DESC$Po de pedra do oraculo$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (pigmento, cal)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Voz grave de enigma e o estalo do ar quente antes do tiro.$DESC$,
'cheiro', $DESC$Pedra quente e poeira de deserto alto.$DESC$,
'quer', $DESC$Cumprir o que viu, queimando de longe quem ja decidiu condenar.$DESC$,
'tipo_perigo', $DESC$Direto$DESC$,
'falas_exemplo', jsonb_build_array($DESC$Eu ja vi como isso acaba pra voce. Poupe seu folego.$DESC$, $DESC$Voce pergunta o futuro. Eu pergunto por que ainda anda.$DESC$, $DESC$(registro: voz grave e fria, em gigante e comum, falando por enigma, sem se comover)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Sobem reto e no aberto ate o oraculo dele$DESC$, $DESC$Ele ve no intruso um fim que decide cumprir$DESC$, $DESC$Mentem ou o provocam junto ao marco de visao$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Para de atirar quando o alvo some em cobertura ou terreno quebrado$DESC$, $DESC$Perde o alvo que muda de rumo e foge da logica que leu$DESC$, $DESC$Deixa em paz quem desce sem subir ao marco$DESC$),
'descoberta_fazendo', $DESC$Parado no alto de um penhasco de Kethara, junto a um marco de visao, observando quem sobe e acendendo a mao.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Nao subir reto e no aberto ate o oraculo$DESC$, $DESC$Usar cobertura e terreno quebrado para cortar o tiro$DESC$, $DESC$Mudar de rumo e nao confirmar o que ele previu$DESC$, $DESC$Fechar a distancia em vez de ficar parado no claro$DESC$)
),
status_conversao='canonizada'
WHERE id=850;

-- 1155 Penhasco-Vivo | Engenho | trapper | Ambiental | 7 Letal | Thornmarak | fala
UPDATE ref_criaturas SET
nome=$DESC$Penhasco-Vivo$DESC$,
nome_ptbr=$DESC$Penhasco-Vivo$DESC$,
slug=$DESC$penhasco-vivo$DESC$,
origem=$DESC$Natural$DESC$,
andar_primario=$DESC$Superfície$DESC$,
pilar_associado=$DESC$Engenho$DESC$,
continente=ARRAY[$DESC$Thornmarak$DESC$]::text[],
habitat=$DESC$Encostas de cristal e desfiladeiros de Thornmarak, onde um gigante remodela a rocha e faz da propria ladeira uma armadilha.$DESC$,
comportamento=$DESC$Nao corre atras de ninguem; arruma a encosta a favor, solta pedra de cima, abre falsa passagem e despenca o caminho sob quem sobe. Trabalha a rocha como artesao e deixa o terreno fazer o servico. So reage a quem invade sua obra.$DESC$,
organizacao=$DESC$Sozinho, dono de uma encosta que ele moldou.$DESC$,
perigo=$DESC$Letal$DESC$,
behavior_archetype=$DESC$trapper$DESC$,
morale_modifier=0,
morale_immune=false,
epigrafe=$DESC$A trilha parecia boa. Boa demais. Quando o primeiro pisou na borda, a borda nao estava la, e a pedra de cima ja vinha.$DESC$,
descricao=$DESC$E um gigante de pele de pedra, recluso e habilidoso, que escolhe uma encosta de Thornmarak e a remodela como obra: solta lascas que viram degrau falso, equilibra pedregulho no alto, e abre passagens que despencam sob o peso. Nao persegue nem briga de perto se puder evitar; deixa a ladeira que ele armou cuidar do intruso, com queda de pedra e chao que cede. E calmo e nao busca briga, mas defende a obra, e a encosta inteira e a arma dele. Fora da rocha que moldou, e so um gigante forte e lento.$DESC$,
supersticao_popular=$DESC$Em Thornmarak dizem que ha encostas trabalhadas por um gigante, e que a trilha boa demais e a que mata. O conselho: nao subir pela passagem que parece convidativa, testar a borda e o degrau antes de pisar, e nao mexer na obra de pedra dele. Dizem que e so desabamento; o desabamento tem dono e tem hora.$DESC$,
sinais_presenca=$DESC$Uma trilha boa demais numa encosta ingreme. Pedregulho equilibrado no alto, fora de lugar. Degraus e bordas talhados recentes na rocha. Marcas de mao enorme na pedra trabalhada. Um silencio de quem espera voce pisar onde nao deve.$DESC$,
fraqueza_conhecida=$DESC$O povo nao sobe pela passagem convidativa, testa borda e degrau, e nao mexe na obra. Acha que e desabamento natural, e tem dono e hora.$DESC$,
fraqueza_real=$DESC$O perigo e o terreno que ele armou, nao o corpo dele: fora da encosta moldada, sem pedra de cima nem chao falso, ele e so um gigante lento. Testar o caminho, subir por onde ele nao trabalhou e tira-lo da obra negam a armadilha. Ele defende a obra, nao caca: quem nao invade nem destroi o que ele fez costuma passar por outro lado. Confiar na trilha boa e o erro.$DESC$,
descricao_sensorial=$DESC$O som e o estalo de pedra assentando e o ronco de pedregulho rolando. O cheiro e de rocha lascada, po e cristal. Ao toque, e pele dura de pedra e a rocha trabalhada, lisa demais para ser natural. Aos olhos, e um gigante calmo no alto, e uma encosta arrumada como armadilha.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Nao caca; despenca a encosta sobre quem invade a obra dele em Thornmarak$DESC$, $DESC$Intrusos que sobem pela trilha armada$DESC$),
'predador', jsonb_build_array($DESC$Fora da rocha que moldou, e so um gigante lento; tira-lo da obra o desarma$DESC$),
'competidor', jsonb_build_array($DESC$Outros trabalhadores de pedra das alturas de Thornmarak$DESC$, $DESC$Talha-Pedra$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presenca dele diz que a encosta ali foi armada como obra, e a trilha boa e a cilada.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem testa a borda, sobe por fora da obra e nao mexe no que ele fez$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$A mao que remodela a rocha$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Engenho / moldar pedra, armar o terreno)$DESC$, 'risco', $DESC$Assenta sozinha e prende a mao do aprendiz na pedra.$DESC$),
jsonb_build_object('material', $DESC$Pedregulho-gatilho equilibrado$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Engenho / queda de pedra, armadilha de encosta)$DESC$, 'risco', $DESC$Despenca no descuido de quem o move.$DESC$),
jsonb_build_object('material', $DESC$Lasca talhada de degrau falso$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (pedra de construcao, foco)$DESC$, 'risco', $DESC$Quebra sob peso, como foi feita para fazer.$DESC$),
jsonb_build_object('material', $DESC$Po de rocha lascada$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (cimento rude, lastro)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Estalo de pedra assentando e o ronco de pedregulho rolando.$DESC$,
'cheiro', $DESC$Rocha lascada, po e cristal.$DESC$,
'quer', $DESC$Moldar a encosta como obra e deixar o terreno derrubar quem invade, sem brigar de perto.$DESC$,
'tipo_perigo', $DESC$Ambiental$DESC$,
'falas_exemplo', jsonb_build_array($DESC$Bonita a trilha, nao? Eu fiz. Pena que voce pisou nela.$DESC$, $DESC$Sai da minha obra. Foi o unico aviso.$DESC$, $DESC$(registro: voz grave e calma de artesao, em gigante e comum, de quem fala pouco e pensa em pedra)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Sobem pela trilha armada que ele moldou$DESC$, $DESC$Mexem ou destroem a obra de pedra dele$DESC$, $DESC$Ameacam o gigante dentro da propria encosta$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Recua quando o tiram da rocha que moldou$DESC$, $DESC$Para de soltar pedra quando o intruso sai da obra$DESC$, $DESC$Deixa passar quem sobe por fora do que ele armou$DESC$),
'descoberta_fazendo', $DESC$No alto de uma encosta de Thornmarak, assentando pedra e equilibrando pedregulho, arrumando a ladeira como armadilha.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Nao subir pela passagem boa demais e testar borda e degrau$DESC$, $DESC$Subir por fora da obra que ele moldou$DESC$, $DESC$Nao mexer nem destruir o que ele fez$DESC$, $DESC$Tira-lo da encosta para o aberto, onde a armadilha nao vale$DESC$)
),
status_conversao='canonizada'
WHERE id=1155;

-- ========================= GRUPO 4 =========================

-- 2078 Passada-Longa | Corpo | skirmisher | Direto | 5 Ameaça | Thornmarak | fala
UPDATE ref_criaturas SET
nome=$DESC$Passada-Longa$DESC$,
nome_ptbr=$DESC$Passada-Longa$DESC$,
slug=$DESC$passada-longa$DESC$,
origem=$DESC$Natural$DESC$,
andar_primario=$DESC$Superfície$DESC$,
pilar_associado=$DESC$Corpo$DESC$,
continente=ARRAY[$DESC$Thornmarak$DESC$]::text[],
habitat=$DESC$Campos abertos e estradas de Thornmarak, terras baixas e cumes onde um gigante magro e veloz cobre muito chao.$DESC$,
comportamento=$DESC$Nao e parado como gigante comum: e magro, de pernas longas, e corre muito; chega rapido, fura com a lanca de longe ou atira pedra com a funda, e some antes do troco. Bate e corre, repete.$DESC$,
organizacao=$DESC$Sozinho ou em dois, batedores de um bando maior.$DESC$,
perigo=$DESC$Ameaça$DESC$,
behavior_archetype=$DESC$skirmisher$DESC$,
morale_modifier=0,
morale_immune=false,
epigrafe=$DESC$A gente preparou a linha pra um gigante lerdo. Veio um magro de perna comprida que furou dois e ja tinha sumido na curva.$DESC$,
descricao=$DESC$E um gigante magro e de pernas longas, rapido como gigante nenhum devia ser, que cobre muito chao pelas terras de Thornmarak. Nao encara de pe firme: chega na corrida, fura com uma lanca de alcance ou atira pedra com a funda, e recua antes que voce alcance. Volta de outro lado, fura de novo, cansa o inimigo de tanto bate e corre. E raideiro, nao muralha: leva o que da pra carregar e some. Encurralado e sem espaco pra correr, perde a graca.$DESC$,
supersticao_popular=$DESC$Em Thornmarak dizem que ha gigantes magros e velozes que assaltam estrada e somem, e que correr atras e perder. O conselho: nao perseguir, fechar o espaco em terreno apertado, e proteger o flanco e a retaguarda, porque ele vem de onde voce nao olha. Dizem que gigante e lerdo; esse nao e.$DESC$,
sinais_presenca=$DESC$Pegadas largas e muito espacadas, de passada longa. Gado e carga sumidos de estrada sem cerco, so um baque rapido. Lanca quebrada de haste comprida largada. Pedra de funda do tamanho de punho em quem caiu. Um vulto alto que aparece e some na linha do morro.$DESC$,
fraqueza_conhecida=$DESC$O povo nao persegue, fecha o espaco apertado e cuida do flanco. Acha que gigante e lerdo, e esse e veloz.$DESC$,
fraqueza_real=$DESC$Ele vive de mobilidade: terreno apertado, sem espaco pra correr e recuar, tira a vantagem dele e o obriga ao corpo a corpo, que ele evita. Perseguir e cair no jogo do bate e corre; esperar em desfiladeiro, beco ou mata fechada o pega. Proteger flanco e retaguarda nega o ataque de onde nao se olha. Correr atras no aberto e o erro.$DESC$,
descricao_sensorial=$DESC$O som e o baque rapido de passada longa e o zunido da funda. O cheiro e de couro, suor e estrada. Ao toque, e pele aspera sobre musculo seco e rijo. Aos olhos, e um gigante magro e alto que ja esta indo embora quando voce o ve.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Gado, carga e viajantes de estrada em Thornmarak$DESC$, $DESC$Batedores e retardatarios isolados$DESC$),
'predador', jsonb_build_array($DESC$Terreno apertado e o corpo a corpo o pegam; sem espaco pra correr, perde$DESC$),
'competidor', jsonb_build_array($DESC$Outros saqueadores e gigantes das terras de Thornmarak$DESC$, $DESC$Marfim-Pesado$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presenca dele diz que a estrada ali e batida por raideiro veloz, e o flanco esta aberto.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem nao persegue e fecha o espaco em terreno apertado$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$Lanca de haste comprida$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Corpo / furar de longe, alcance no bate e corre)$DESC$, 'risco', $DESC$Comprida demais, atrapalha em lugar apertado.$DESC$),
jsonb_build_object('material', $DESC$Funda e pedra de punho$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (arma de arremesso, peso)$DESC$, 'risco', $DESC$A pedra acerta o pe de quem treina sem jeito.$DESC$),
jsonb_build_object('material', $DESC$Couro de raideiro$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (correia, reparo)$DESC$, 'risco', $DESC$Nenhum.$DESC$),
jsonb_build_object('material', $DESC$Sandalia de passada longa$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (sola grande, couro)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Baque rapido de passada longa e o zunido da funda.$DESC$,
'cheiro', $DESC$Couro, suor e estrada.$DESC$,
'quer', $DESC$Chegar rapido, furar de longe e sumir antes do troco, levando o que der.$DESC$,
'tipo_perigo', $DESC$Direto$DESC$,
'falas_exemplo', jsonb_build_array($DESC$Rapido demais pra voce, nao? Fica ai que eu volto pelo outro lado.$DESC$, $DESC$Larga a carga e ninguem se machuca. Muito.$DESC$, $DESC$(registro: voz alta e debochada, em comum e em gigante, de quem fala correndo)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Carga ou gado solto numa estrada aberta ao alcance$DESC$, $DESC$Um retardatario isolado longe do grupo$DESC$, $DESC$Abrem o flanco ou a retaguarda para ele$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Recua e some assim que leva o troco serio$DESC$, $DESC$Larga o assalto quando fecham o espaco apertado$DESC$, $DESC$Desiste do alvo que protege flanco e retaguarda$DESC$),
'descoberta_fazendo', $DESC$Cobrindo chao numa estrada de Thornmarak, batendo carga e viajante de longe e sumindo na curva.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Nao perseguir e nao cair no bate e corre dele$DESC$, $DESC$Fechar o espaco em desfiladeiro ou mata fechada$DESC$, $DESC$Proteger flanco e retaguarda da carga$DESC$, $DESC$Oferecer pedagio de carga pra ele deixar a gente passar$DESC$)
),
status_conversao='canonizada'
WHERE id=2078;

-- 1903 Véu-Ávido | Sombra | controller | Condicional | 10 Letal | Voranthar | fala
UPDATE ref_criaturas SET
nome=$DESC$Véu-Ávido$DESC$,
nome_ptbr=$DESC$Véu-Ávido$DESC$,
slug=$DESC$veu-avido$DESC$,
origem=$DESC$Marginal$DESC$,
andar_primario=$DESC$Margem$DESC$,
pilar_associado=$DESC$Sombra$DESC$,
continente=ARRAY[$DESC$Voranthar$DESC$]::text[],
habitat=$DESC$Ruinas fundas de Voranthar onde a Margem e fina, saloes que o escuro tomou e nao larga.$DESC$,
comportamento=$DESC$Estende-se como um manto de escuro vivo, le o que voce sente e se alimenta disso; cutuca medo, raiva e cobiça para te fazer agir, e aperta quando a emocao sobe. Nao golpeia de musculo: governa pelo sentimento.$DESC$,
organizacao=$DESC$Sozinho, ligado a quem entra no salao dele.$DESC$,
perigo=$DESC$Letal$DESC$,
behavior_archetype=$DESC$controller$DESC$,
morale_modifier=0,
morale_immune=false,
epigrafe=$DESC$Comecei a sentir uma raiva que nao era minha, do nada, do meu proprio irmao. O escuro estava com fome, e a fome era da minha briga.$DESC$,
descricao=$DESC$E um manto de escuro vivo, vindo da Margem, que cobre um salao fundo de Voranthar e se liga a quem entra. Le o que a pessoa sente e come disso: cutuca medo, raiva, ciume e cobiça, sussurra para dentro do peito e empurra cada um a agir pelo pior, porque a emocao forte e o alimento dele. Quanto mais voce sente, mais ele aperta e mais forte fica. Nao briga de corpo: vira o grupo contra si mesmo e se farta. Quieto o sentimento, ele murcha.$DESC$,
supersticao_popular=$DESC$Em Voranthar dizem que ha saloes escuros que deixam a gente com raiva e medo sem motivo, e que ali os amigos brigam ate se ferir. O conselho: nao entrar sentido, manter a cabeca fria, e desconfiar de toda emocao que sobe de repente la dentro. Dizem que reza acalma o coracao; manter a calma de verdade e o que tira a comida dele.$DESC$,
sinais_presenca=$DESC$Uma raiva, um medo ou uma cobiça que sobe do nada ao entrar no salao. Amigos que comecam a se estranhar sem motivo no escuro. Um escuro que parece mais denso onde a emocao e mais forte. Sussurros que parecem vir de dentro do peito. Brigas e mortes entre companheiros num lugar sem inimigo a vista.$DESC$,
fraqueza_conhecida=$DESC$O povo nao entra sentido, mantem a cabeca fria e desconfia da emocao subita. Acha que reza acalma, e a calma de verdade e que o esfaima.$DESC$,
fraqueza_real=$DESC$Ele come emocao e governa por ela: cabeca fria, calma e nao agir pelo sentimento que ele cutuca tiram a comida e o enfraquecem. Ele nao tem corpo forte: luz e fogo o encolhem, e quem reconhece que a raiva nao e sua corta o controle. Ele depende de voce sentir; sair do salao e nao alimentar a briga encerra. Brigar com o companheiro que o escuro virou e dar o jantar a ele.$DESC$,
descricao_sensorial=$DESC$O som e um sussurro que vem de dentro, nao de fora, e o silencio em volta. O cheiro e de ar parado e frio, sem cheiro proprio. Ao toque, e um frio que adensa e pesa, como pano molhado no peito. Aos olhos, e escuro vivo que escorre pelas paredes e e mais denso onde alguem sente mais.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$A emocao forte de quem entra no salao dele em Voranthar$DESC$, $DESC$Grupos que ele vira uns contra os outros$DESC$),
'predador', jsonb_build_array($DESC$Calma, luz e fogo o encolhem; sem emocao para comer, murcha$DESC$),
'competidor', jsonb_build_array($DESC$Outros escuros e vazios da Margem em Voranthar$DESC$, $DESC$Capa-Vasta$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presenca dele diz que ali o escuro come o que voce sente, e a briga entre amigos e a fome dele.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem entra com a cabeca fria e nao age pela emocao que sobe$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$O fio que liga o escuro ao que voce sente$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Sombra / ler e cutucar emocao, virar o grupo)$DESC$, 'risco', $DESC$Enche de raiva e medo alheios quem o guarda.$DESC$),
jsonb_build_object('material', $DESC$O manto de escuro vivo$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Sombra / cobrir um lugar de breu, adensar a sombra)$DESC$, 'risco', $DESC$Apaga a luz e pesa no peito de quem o veste.$DESC$),
jsonb_build_object('material', $DESC$Cristal apagado do salao$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (foco escuro, lastro)$DESC$, 'risco', $DESC$Engole um pouco da luz por perto.$DESC$),
jsonb_build_object('material', $DESC$Po frio de ruina$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (pigmento negro, lastro)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Sussurro que vem de dentro, nao de fora, e o silencio em volta.$DESC$,
'cheiro', $DESC$Ar parado e frio, sem cheiro proprio.$DESC$,
'quer', $DESC$Comer a emocao forte de quem entra e virar o grupo contra si mesmo, sem precisar de corpo.$DESC$,
'tipo_perigo', $DESC$Condicional$DESC$,
'falas_exemplo', jsonb_build_array($DESC$Essa raiva fica bem em voce. Sente mais.$DESC$, $DESC$Seu amigo pensou algo feio de voce agora. Quer saber o que?$DESC$, $DESC$(registro: voz que sobe de dentro do peito, mansa e faminta, sem som de fora, na lingua do fundo)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Alguem entra no salao sentindo medo, raiva ou cobiça forte$DESC$, $DESC$Um grupo comeca a se estranhar e alimenta a briga$DESC$, $DESC$Trazem emocao crua que ele pode cutucar e crescer$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Murcha quando o grupo mantem a calma e nao briga$DESC$, $DESC$Recua da luz forte e do fogo aceso$DESC$, $DESC$Larga quem sai do salao e nao alimenta o sentimento$DESC$),
'descoberta_fazendo', $DESC$Estendido como manto de escuro num salao fundo de Voranthar, lendo o que cada um sente e cutucando a briga.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Entrar com a cabeca fria e nao agir pela emocao subita$DESC$, $DESC$Reconhecer que a raiva nao e sua e nao brigar com o companheiro$DESC$, $DESC$Usar luz e fogo, que o encolhem, e recuar$DESC$, $DESC$Sair do salao e nao dar a ele a briga de que se alimenta$DESC$)
),
status_conversao='canonizada'
WHERE id=1903;

-- 624 Pacto-Murcho | Arcano | striker | Persistente | 3 Ameaça | Vyrkhor | fala
UPDATE ref_criaturas SET
nome=$DESC$Pacto-Murcho$DESC$,
nome_ptbr=$DESC$Pacto-Murcho$DESC$,
slug=$DESC$pacto-murcho$DESC$,
origem=$DESC$Cicatricial$DESC$,
andar_primario=$DESC$Eco$DESC$,
pilar_associado=$DESC$Arcano$DESC$,
continente=ARRAY[$DESC$Vyrkhor$DESC$]::text[],
habitat=$DESC$Criptas e ermos gelados de Vyrkhor, onde um feiticeiro morto ainda serve o pacto que fez em vida.$DESC$,
comportamento=$DESC$Lanca raios de cova de longe e drena a vida pelo toque, e cada gole tira um naco que nao volta sozinho; nao teme nada, porque ja paga um preco pior. Serve calado a um dono que nao se ve, e cumpre a tarefa ate cair.$DESC$,
organizacao=$DESC$Sozinho ou em poucos, servos de um mesmo dono distante.$DESC$,
perigo=$DESC$Ameaça$DESC$,
behavior_archetype=$DESC$striker$DESC$,
morale_modifier=0,
morale_immune=true,
epigrafe=$DESC$Cada toque dele tirava um pedaco de mim que nao voltou com descanso nem comida. Eu fui minguando, e ele nem precisava me matar rapido.$DESC$,
descricao=$DESC$Foi um feiticeiro que fez um pacto em vida e nao se livrou dele na morte: agora serve, seco e gelado, o mesmo dono que nem aparece. Luta de longe com raios de cova, e de perto drena a vida pelo toque, tirando um naco que descanso e comida nao repoem, so cura forte. Nao sente medo, porque o que o prende e pior que qualquer ameaca; cumpre a tarefa ate ser desfeito. A luz do sol o incomoda e o enfraquece. E teimoso no servico, nao na propria pele.$DESC$,
supersticao_popular=$DESC$Em Vyrkhor dizem que ha feiticeiros mortos que servem um dono que ninguem ve, e que o toque deles seca a pessoa aos poucos. O conselho: nao deixar encostar, lutar no claro ou de dia, e tratar a mingua com cura forte, nao so com descanso. Dizem que sao livres agora que morreram; sao mais presos do que em vida.$DESC$,
sinais_presenca=$DESC$Raios escuros vindos de uma figura seca e parada. Gente que vai minguando, fraca, sem ferida que explique. Um servo gelado cumprindo tarefa sem dono a vista. Recuo diante da luz do sol e da tocha forte. Um ermo gelado com marca de quem foi mandado ali.$DESC$,
fraqueza_conhecida=$DESC$O povo nao deixa encostar, luta no claro e trata a mingua com cura forte. Acha que estao livres na morte, e estao mais presos.$DESC$,
fraqueza_real=$DESC$O toque seca de verdade e so cura forte repoe, entao deixar encostar e perder aos poucos; manter distancia anula o pior. A luz do sol o enfraquece e o faz recuar. Ele nao foge por medo porque o pacto o prende, mas cumpre uma tarefa: tirar o motivo, ou cortar o que o liga ao dono, o desativa melhor que o golpe. Lutar de perto no escuro e o erro.$DESC$,
descricao_sensorial=$DESC$O som e um estalido seco de raio e um sussurro de ordem antiga. O cheiro e de gelo, terra de cova e pano queimado. Ao toque, e mao seca e gelada que puxa a forca pra dentro. Aos olhos, e uma figura magra e seca de feiticeiro morto, de olhos apagados, parada como quem espera ordem.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$A vida e a forca de quem cruza a cripta dele em Vyrkhor$DESC$, $DESC$Alvos da tarefa que o dono mandou cumprir$DESC$),
'predador', jsonb_build_array($DESC$A luz do sol o enfraquece; cortar o laco com o dono o desativa$DESC$),
'competidor', jsonb_build_array($DESC$Outros mortos que servem donos distantes em Vyrkhor$DESC$, $DESC$Arauto-Trêmulo$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presenca dele diz que um pacto velho ainda manda ali, e que o toque seca quem fica.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem nao deixa encostar e luta no claro ou de dia$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$O laco que ainda o prende ao dono$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Arcano / servir um pacto, obedecer de longe)$DESC$, 'risco', $DESC$Passa a tarefa do morto para quem o guarda.$DESC$),
jsonb_build_object('material', $DESC$A mao que drena a vida$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Arcano / drenar forca pelo toque, minguar o alvo)$DESC$, 'risco', $DESC$Seca devagar quem a carrega sem luva.$DESC$),
jsonb_build_object('material', $DESC$Foco de raio de cova$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (vara de feitico, foco)$DESC$, 'risco', $DESC$Descarrega no escuro sem aviso.$DESC$),
jsonb_build_object('material', $DESC$Pano de mortalha seco$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (estopa, pano velho)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Estalido seco de raio e um sussurro de ordem antiga.$DESC$,
'cheiro', $DESC$Gelo, terra de cova e pano queimado.$DESC$,
'quer', $DESC$Cumprir a tarefa do dono, drenando de longe e de perto quem cruzar, sem temer o proprio fim.$DESC$,
'tipo_perigo', $DESC$Persistente$DESC$,
'falas_exemplo', jsonb_build_array($DESC$Nao e nada pessoal. Foi mandado. Eu so cumpro.$DESC$, $DESC$Voce cansa. Eu nao. Isso ja decide.$DESC$, $DESC$(registro: voz seca e sem vontade propria, em comum e nas linguas que sabia em vida, de servo que nao se pertence)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Alguem cruza a cripta ou o ermo que ele guarda$DESC$, $DESC$Aparece o alvo da tarefa que o dono mandou$DESC$, $DESC$Chegam ao alcance do toque que drena$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Recua da luz do sol e da tocha forte$DESC$, $DESC$Para de avancar quando cortam o que o liga ao dono$DESC$, $DESC$Nao persegue quem sai do alcance e do escuro$DESC$),
'descoberta_fazendo', $DESC$Parado num ermo gelado de Vyrkhor, cumprindo calado uma tarefa antiga, lancando raios de cova em quem chega.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Nao deixar encostar e manter distancia do toque$DESC$, $DESC$Lutar no claro ou esperar o dia$DESC$, $DESC$Cortar o que o liga ao dono em vez de so feri-lo$DESC$, $DESC$Tratar a mingua de quem foi tocado com cura forte$DESC$)
),
status_conversao='canonizada'
WHERE id=624;

-- 1008 Litania-Funda | Espírito | artillery | Ambiental | 6 Letal | Voranthar | fala
UPDATE ref_criaturas SET
nome=$DESC$Litania-Funda$DESC$,
nome_ptbr=$DESC$Litania-Funda$DESC$,
slug=$DESC$litania-funda$DESC$,
origem=$DESC$Marginal$DESC$,
andar_primario=$DESC$Margem$DESC$,
pilar_associado=$DESC$Espírito$DESC$,
continente=ARRAY[$DESC$Voranthar$DESC$]::text[],
habitat=$DESC$Galerias alagadas e poços fundos de Voranthar onde a Margem e fina, templos submersos de um deus que so existe porque creem nele.$DESC$,
comportamento=$DESC$Prega alto e enche a galeria de fe e medo; do escuro alagado, atira a vontade do deus que inventou com o cetro, e quanto mais os seus creem, mais real fica o que ele invoca. Nao recua: o que o prende e a fe, nao a vida.$DESC$,
organizacao=$DESC$Lider de um cardume de fieis, sozinho no posto de sumo.$DESC$,
perigo=$DESC$Letal$DESC$,
behavior_archetype=$DESC$artillery$DESC$,
morale_modifier=0,
morale_immune=true,
epigrafe=$DESC$O deus dele nao existia ate o templo inteiro gritar que sim. Ai a coisa que ele chamou nos acertou de verdade.$DESC$,
descricao=$DESC$E um sumo sacerdote de um povo de aguas fundas que vive nas galerias alagadas de Voranthar, onde a Margem e fina. Prega alto, enche o espaco de fe e medo, e do escuro da agua atira com o cetro a vontade de um deus que ele mesmo ajudou a inventar, porque ali a cre de muitos faz o inventado pegar forma. Quanto mais o cardume dele acredita e canta, mais real e perigoso fica o que ele invoca sobre o intruso. A luz do sol o queima e o faz recuar. Nao foge: a fe o prende mais que a vida.$DESC$,
supersticao_popular=$DESC$Em Voranthar dizem que ha sacerdotes de agua funda que rezam um deus ate ele ficar real, e que entrar no templo deles e ser alvo de algo que nao existia antes. O conselho: nao entrar quando o cardume esta cantando em fe, levar luz forte, que os queima, e calar ou dispersar os fieis antes do sumo. Dizem que o deus deles e mentira; a mentira morde quando muitos creem nela.$DESC$,
sinais_presenca=$DESC$Um canto em coro vindo de galeria alagada. Agua que mexe com fe, brilhando onde o cardume cre mais forte. Um sacerdote de cabeca de peixe num posto alto, de cetro. Fieis de olhos vidrados rezando em fila. Algo tomando forma no ar do templo conforme o canto sobe.$DESC$,
fraqueza_conhecida=$DESC$O povo nao entra no canto, leva luz forte e dispersa os fieis antes do sumo. Acha que o deus deles e so mentira, e a mentira morde quando creem.$DESC$,
fraqueza_real=$DESC$A forca dele vem da fe do cardume: calar, dispersar ou descrer quebra o que ele invoca e o deixa so um sacerdote fraco. A luz do sol queima a ele e aos seus. Ele nao recua por medo, porque a fe o prende; mas sem fieis crendo, o deus inventado nao pega forma. Atacar o que ele invoca, em vez dos que sustentam a cre, e o erro: corte o coro, nao a aparicao.$DESC$,
descricao_sensorial=$DESC$O som e um canto em coro que ecoa na agua e o tinir do cetro. O cheiro e de agua funda, peixe e incenso molhado. Ao toque, e pele umida e fria de bicho de agua. Aos olhos, e um sacerdote de cabeca de peixe num posto alto, e algo ganhando forma atras dele conforme o canto sobe.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Intrusos que entram no templo alagado dele em Voranthar$DESC$, $DESC$A fe e o medo que ele colhe do proprio cardume$DESC$),
'predador', jsonb_build_array($DESC$A luz do sol o queima; calar e dispersar os fieis tira a forca do que ele invoca$DESC$),
'competidor', jsonb_build_array($DESC$Outros que pregam e chamam coisas pela cre em Voranthar$DESC$, $DESC$Berro-Seco$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presenca dele diz que ali a cre de muitos faz um deus inventado pegar forma e morder.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem nao entra no canto e dispersa os fieis antes do sumo$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$O cetro que atira a vontade do deus inventado$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Margem / dar forma ao que muitos creem, atacar com o invocado)$DESC$, 'risco', $DESC$So funciona com fieis crendo, e vira-se contra quem o usa sozinho.$DESC$),
jsonb_build_object('material', $DESC$A fe colhida do cardume$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Margem / sustentar o invocado, encher o espaco de fe e medo)$DESC$, 'risco', $DESC$Enche a cabeca de quem a guarda de uma cre que nao e dele.$DESC$),
jsonb_build_object('material', $DESC$Escama sacra do sumo$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (foco umido, insignia)$DESC$, 'risco', $DESC$Resseca e racha fora da agua.$DESC$),
jsonb_build_object('material', $DESC$Incenso molhado de templo$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (incenso, pasta)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Canto em coro que ecoa na agua e o tinir do cetro.$DESC$,
'cheiro', $DESC$Agua funda, peixe e incenso molhado.$DESC$,
'quer', $DESC$Encher a galeria de fe e dar forma ao deus que inventou, despejando-o sobre o intruso.$DESC$,
'tipo_perigo', $DESC$Ambiental$DESC$,
'falas_exemplo', jsonb_build_array($DESC$Creia, e ele e real. Duvide, e ele come sua duvida primeiro.$DESC$, $DESC$Voce entrou no templo. Agora reza, ou vira oferenda.$DESC$, $DESC$(registro: voz alta de pregacao, em lingua do fundo, ecoando na agua, de quem nao admite descrenca)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Entram no templo enquanto o cardume canta em fe$DESC$, $DESC$Atacam o sumo ou os fieis no posto alto$DESC$, $DESC$Profanam a agua ou a imagem do deus inventado$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Nao foge por medo; o invocado some quando calam ou dispersam os fieis$DESC$, $DESC$Recua da luz forte do sol$DESC$, $DESC$Perde forca quando a cre do cardume e quebrada$DESC$),
'descoberta_fazendo', $DESC$Num posto alto de uma galeria alagada de Voranthar, pregando alto e dando forma ao deus inventado conforme o cardume canta.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Nao entrar quando o cardume esta cantando em fe$DESC$, $DESC$Levar luz forte, que queima a ele e aos seus$DESC$, $DESC$Calar ou dispersar os fieis antes de mirar o sumo$DESC$, $DESC$Recuar do templo e nao dar cre ao que ele invoca$DESC$)
),
status_conversao='canonizada'
WHERE id=1008;

-- 2351 Menir-Quedo | Engenho | tactical | Oculto | 7 Letal | Vyrkhor | fala
UPDATE ref_criaturas SET
nome=$DESC$Menir-Quedo$DESC$,
nome_ptbr=$DESC$Menir-Quedo$DESC$,
slug=$DESC$menir-quedo$DESC$,
origem=$DESC$Natural$DESC$,
andar_primario=$DESC$Superfície$DESC$,
pilar_associado=$DESC$Engenho$DESC$,
continente=ARRAY[$DESC$Vyrkhor$DESC$]::text[],
habitat=$DESC$Campos de pedra e passos altos de Vyrkhor, onde menires de pe escondem um gigante que pensa.$DESC$,
comportamento=$DESC$Fica imovel entre as pedras, passando por menir, e observa quem passa por muito tempo antes de agir; quando decide, rola pedra, fecha rota e ataca de onde nao se esperava. Luta com plano, nao com pressa, e some de novo entre as pedras se nao vencer rapido.$DESC$,
organizacao=$DESC$Sozinho, senhor de um campo de pedras.$DESC$,
perigo=$DESC$Letal$DESC$,
behavior_archetype=$DESC$tactical$DESC$,
morale_modifier=0,
morale_immune=false,
epigrafe=$DESC$Contamos doze menires no passo. Na volta eram onze, e um de nos nao voltou. Nunca soubemos qual pedra era ele.$DESC$,
descricao=$DESC$E um gigante de pedra, lider entre os seus, que aprendeu a ficar tao imovel entre os menires que vira um deles. Observa o passo por horas, mede quem entra, e so age quando tem o plano pronto: rola pedra para fechar a rota, ataca do flanco que ninguem vigiava e recua para a quietude de pedra se a briga virar contra ele. Nao e bruto afobado: e paciente e calculista, e usa o campo de pedras como tabuleiro. Parado, voce nunca sabe qual rocha e ele.$DESC$,
supersticao_popular=$DESC$Em Vyrkhor dizem que certos campos de menir tem uma pedra a mais, que e gigante, e que conta-las salva. O conselho: contar as pedras na ida e na volta, nao confiar no campo de pedra quieto, e nunca acampar no meio dos menires. Dizem que gigante de pedra e lerdo e burro; esse pensa e espera.$DESC$,
sinais_presenca=$DESC$Um campo de menires com uma pedra a mais que no dia anterior. Pedra grande rolada para fechar um passo, recente. Sumico de um do grupo no meio das pedras, sem briga ouvida. Uma sombra que nao bate com nenhuma rocha. Silencio longo, de quem observa e mede.$DESC$,
fraqueza_conhecida=$DESC$O povo conta as pedras, nao confia no campo quieto e nao acampa entre menires. Acha que gigante de pedra e burro, e esse e calculista.$DESC$,
fraqueza_real=$DESC$A forca dele e a surpresa e o plano: descoberto antes de armar, ou tirado do campo de pedras onde se esconde e bloqueia rota, ele vira so um gigante forte que precisa improvisar. Contar as pedras e marca-las quebra o disfarce; nao entrar no terreno que ele preparou nega a emboscada. Ele recua se a briga foge do plano: pressao continua e terreno aberto o tiram do jogo. Confiar no campo quieto e o erro.$DESC$,
descricao_sensorial=$DESC$O som e um silencio longo e, de repente, o ronco de pedra rolando. O cheiro e de rocha fria, liquen e neve. Ao toque, e pedra dura e fria, igual a qualquer menir, ate se mexer. Aos olhos, e um campo de pedras de pe, e uma delas que respira se voce olhar tempo demais.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Grupos que cruzam o campo de menires dele em Vyrkhor$DESC$, $DESC$Retardatarios que ele separa com pedra e plano$DESC$),
'predador', jsonb_build_array($DESC$Descoberto antes de armar ou tirado do campo, vira so um gigante que improvisa$DESC$),
'competidor', jsonb_build_array($DESC$Outros senhores de pedra e terra dos passos de Vyrkhor$DESC$, $DESC$Punho-de-Terra$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presenca dele diz que o campo de menir ali tem uma pedra a mais, e ela pensa.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem conta as pedras, nao acampa entre menires e nao confia no campo quieto$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$A quietude que o faz passar por pedra$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Engenho / disfarce de rocha, emboscar do imovel)$DESC$, 'risco', $DESC$Deixa quem a usa parado e esquecido, como pedra.$DESC$),
jsonb_build_object('material', $DESC$O plano de rolar pedra e fechar rota$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Engenho / armar emboscada, bloquear passagem)$DESC$, 'risco', $DESC$A pedra rola para o lado errado na mao do afobado.$DESC$),
jsonb_build_object('material', $DESC$Lasca de menir trabalhado$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (marco, foco de pedra)$DESC$, 'risco', $DESC$Pesa e confunde quem conta pedras.$DESC$),
jsonb_build_object('material', $DESC$Liquen de menir$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (tinta, curativo rude)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Silencio longo e, de repente, o ronco de pedra rolando.$DESC$,
'cheiro', $DESC$Rocha fria, liquen e neve.$DESC$,
'quer', $DESC$Passar por menir, medir quem entra e atacar com plano do flanco que ninguem vigia.$DESC$,
'tipo_perigo', $DESC$Oculto$DESC$,
'falas_exemplo', jsonb_build_array($DESC$Voce passou por mim tres vezes. Eu deixei.$DESC$, $DESC$Conte de novo as pedras. Vai faltar um de voces, nao uma rocha.$DESC$, $DESC$(registro: voz grave e pausada, em gigante e comum, de quem pensa devagar e sem erro)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Um grupo entra e acampa no campo de menires dele$DESC$, $DESC$Separam-se e deixam um retardatario entre as pedras$DESC$, $DESC$Comecam a derrubar ou marcar os menires que ele usa$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Volta a ficar imovel e some entre as pedras se a briga vira$DESC$, $DESC$Recua quando o tiram do campo que preparou$DESC$, $DESC$Abandona o plano sob pressao continua em terreno aberto$DESC$),
'descoberta_fazendo', $DESC$Imovel entre os menires de um passo de Vyrkhor, passando por pedra e medindo o grupo que cruza.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Contar e marcar as pedras na ida e na volta$DESC$, $DESC$Nao acampar nem se separar no meio dos menires$DESC$, $DESC$Atravessar rapido sem confiar no campo quieto$DESC$, $DESC$Tira-lo do terreno de pedra para o aberto, onde nao se esconde$DESC$)
),
status_conversao='canonizada'
WHERE id=2351;

-- ========================= GRUPO 5 =========================

-- 1169 Novelo-Peçonho | Corpo | swarm | Ambiental | 2 Ameaça | Voranthar | MUDO
UPDATE ref_criaturas SET
nome=$DESC$Novelo-Peçonho$DESC$,
nome_ptbr=$DESC$Novelo-Peçonho$DESC$,
slug=$DESC$novelo-peconho$DESC$,
origem=$DESC$Natural$DESC$,
andar_primario=$DESC$Superfície$DESC$,
pilar_associado=$DESC$Corpo$DESC$,
continente=ARRAY[$DESC$Voranthar$DESC$]::text[],
habitat=$DESC$Ruinas e porões de Voranthar onde o calor junta cobra, frestas e entulho cheios de ninho.$DESC$,
comportamento=$DESC$Nao e uma cobra, e muitas: um tapete vivo de viboras que toma o chao de um comodo, e cada passo seu pisa veneno. Nao caca de longe; transforma o piso num campo de bote. Mexido demais, o novelo se desfaz e foge pras frestas.$DESC$,
organizacao=$DESC$Em massa, dezenas no mesmo ninho.$DESC$,
perigo=$DESC$Ameaça$DESC$,
behavior_archetype=$DESC$swarm$DESC$,
morale_modifier=-1,
morale_immune=false,
epigrafe=$DESC$O chao do porão se mexeu inteiro. Nao tinha onde pisar que nao fosse em cima de uma.$DESC$,
descricao=$DESC$Nao e uma cobra grande, e um novelo de muitas viboras pequenas que toma o chao de um comodo em ruina de Voranthar e o transforma num campo de bote. Cada passo pisa veneno; parar no meio e ser picado de dez lados. O perigo nao e a forca, e o numero e o terreno que elas viram: um piso vivo que voce nao pode atravessar a esmo. Cada cobra e fraca e medrosa; o tapete inteiro, nao. Mexido demais ou com fogo, o novelo se desfaz e some pelas frestas, pra se juntar de novo depois.$DESC$,
supersticao_popular=$DESC$Em Voranthar dizem que certos porões tem o chao feito de cobra, e que entrar de pe descalço e morte certa. O conselho: nao pisar no meio do ninho, jogar luz e fogo pra abrir caminho, e andar pela borda e por cima de entulho. Dizem que uma flauta acalma as cobras; o que abre caminho e o fogo.$DESC$,
sinais_presenca=$DESC$O chao de um comodo que ondula e chia sem vento. Peles trocadas em monte numa fresta. Cheiro forte e azedo de ninho de cobra. Ratos e bichos pequenos sumidos do porão. Um sibilo de muitas, vindo do piso, nao de um ponto.$DESC$,
fraqueza_conhecida=$DESC$O povo nao pisa no meio, usa luz e fogo e anda pela borda. Acha que flauta acalma, e o que abre caminho e o fogo.$DESC$,
fraqueza_real=$DESC$O perigo e o terreno, nao a coragem: cada cobra e fraca e covarde, e o novelo se desfaz com fogo, fumaca e barulho, fugindo pras frestas. Nao parar no meio do ninho e abrir caminho com fogo tiram o campo de bote. Atravessar pela borda, por cima de entulho ou de bota alta nega a picada. Ficar parado no meio, achando que da pra lutar com cada uma, e o erro.$DESC$,
descricao_sensorial=$DESC$O som e um sibilo de muitas ao mesmo tempo e o roçar de escama em pedra. O cheiro e azedo e forte, de ninho de cobra. Ao toque, sao corpos frios e rapidos que se enrolam no pe e na canela. Aos olhos, e um chao que ondula, feito de cobra, sem ponto certo pra mirar.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Bichos pequenos e ratos do porão deles em Voranthar$DESC$, $DESC$Quem para de pe no meio do ninho$DESC$),
'predador', jsonb_build_array($DESC$Fogo, fumaca e barulho desfazem o novelo; cada cobra e fraca$DESC$),
'competidor', jsonb_build_array($DESC$Outras pragas e ninhos das ruinas de Voranthar$DESC$, $DESC$Braço-do-Fundo$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presenca dele diz que o chao daquele porão e ninho, e pisar no meio e veneno.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem nao pisa no meio do ninho e abre caminho com fogo$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$Veneno recolhido do ninho$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Corpo / peçonha, untar lamina, dose de veneno)$DESC$, 'risco', $DESC$A propria dose mata quem se descuida ao recolher.$DESC$),
jsonb_build_object('material', $DESC$Novelo de peles trocadas$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (bainha leve, isca, fibra)$DESC$, 'risco', $DESC$Ainda pode esconder uma cobra viva.$DESC$),
jsonb_build_object('material', $DESC$Presas pequenas em monte$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (agulha, ponta)$DESC$, 'risco', $DESC$Nenhum, se ja secas.$DESC$),
jsonb_build_object('material', $DESC$Casca de ovo de cobra$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (curiosidade, cola)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Sibilo de muitas ao mesmo tempo e o roçar de escama em pedra.$DESC$,
'cheiro', $DESC$Azedo e forte, de ninho de cobra.$DESC$,
'quer', $DESC$Tomar o chao do comodo e virar o piso num campo de bote, picando quem para no meio.$DESC$,
'tipo_perigo', $DESC$Ambiental$DESC$,
'falas_exemplo', 'null'::jsonb,
'gatilhos_agressao', jsonb_build_array($DESC$Alguem pisa de pe no meio do ninho$DESC$, $DESC$Mexem no entulho ou nas frestas onde elas vivem$DESC$, $DESC$Param paradas no piso tomado$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$O novelo se desfaz e foge pras frestas com fogo$DESC$, $DESC$Espalha-se de fumaca e barulho$DESC$, $DESC$Larga o comodo quando abrem caminho de luz$DESC$),
'descoberta_fazendo', $DESC$Cobrindo o chao de um porão em ruina de Voranthar, um tapete vivo de viboras a espera de quem pise no meio.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Nao pisar no meio do ninho e andar pela borda$DESC$, $DESC$Abrir caminho com luz e fogo$DESC$, $DESC$Atravessar por cima de entulho ou de bota alta$DESC$, $DESC$Contornar o comodo tomado e fechar a fresta$DESC$)
),
status_conversao='canonizada'
WHERE id=1169;

-- 1933 Submerso-Lesto | Sombra | ambusher | Oculto | 4 Ameaça | Thornmarak | MUDO
UPDATE ref_criaturas SET
nome=$DESC$Submerso-Lesto$DESC$,
nome_ptbr=$DESC$Submerso-Lesto$DESC$,
slug=$DESC$submerso-lesto$DESC$,
origem=$DESC$Cicatricial$DESC$,
andar_primario=$DESC$Eco$DESC$,
pilar_associado=$DESC$Sombra$DESC$,
continente=ARRAY[$DESC$Thornmarak$DESC$]::text[],
habitat=$DESC$Portos afundados e canais de Thornmarak, agua escura onde assassinos morreram afogados e nao subiram.$DESC$,
comportamento=$DESC$Anda no fundo da agua, invisivel da superficie, e sobe so pra cravar: surge atras do alvo isolado, acerta a adaga ou a balestra de mao, e volta pro fundo. Caca um, em silencio, e some. Ligado a outros como ele.$DESC$,
organizacao=$DESC$Sozinho ou em poucos, ligados, afogados da mesma queda.$DESC$,
perigo=$DESC$Ameaça$DESC$,
behavior_archetype=$DESC$ambusher$DESC$,
morale_modifier=0,
morale_immune=true,
epigrafe=$DESC$O ultimo da fila sumiu sem barulho. So vimos o circulo na agua escura, e ja era tarde pro penultimo.$DESC$,
descricao=$DESC$Foi um assassino que morreu afogado e nao parou de matar: anda no fundo da agua escura dos portos de Thornmarak, invisivel de cima, e sobe so pra cravar. Escolhe o alvo isolado, o ultimo da fila, surge por tras com adaga ou balestra de mao, acerta e volta pro fundo antes do grito. Nao encara em peso: caca um de cada vez, no silencio, e some. Esta ligado a outros afogados da mesma queda, e o que prende um chama o resto. Fora da agua, e so um morto lento e exposto.$DESC$,
supersticao_popular=$DESC$Em Thornmarak dizem que certos portos afundados tem matadores no fundo, e que o ultimo da fila some primeiro. O conselho: nao andar na beira de agua escura em fila, levar luz que fure a agua, e nao deixar ninguem sozinho perto da margem funda. Dizem que reza protege o ultimo; o que protege e nao ficar sozinho na beira.$DESC$,
sinais_presenca=$DESC$O ultimo ou o mais isolado do grupo sumindo sem grito perto de agua. Um circulo na agua escura, sem peixe que explique. Balestra de mao ou adaga achada na lama da margem. Corpos no fundo que parecem so afogados, ate se mexerem. Uma sensacao de estar sendo seguido pela agua.$DESC$,
fraqueza_conhecida=$DESC$O povo nao anda em fila na beira, leva luz na agua e nao deixa ninguem sozinho. Acha que reza protege, e o que protege e o grupo junto.$DESC$,
fraqueza_real=$DESC$Vive da emboscada e do isolamento: andar junto, longe da margem funda, e com luz que fure a agua tira o alvo solto que ele procura. Fora da agua e lento e fraco; forcado a terra firme, perde tudo. Ele e ligado a outros, entao um ataque traz mais; mas quem nao da o alvo isolado nao e cacado. Ficar sozinho na beira da agua escura e o erro.$DESC$,
descricao_sensorial=$DESC$O som e quase nada, um marulho baixo e o sopro de uma balestra. O cheiro e de agua parada, lodo e ferro molhado. Ao toque, e mao fria e inchada de afogado que puxa pra baixo. Aos olhos, e um vulto que sobe da agua escura atras de voce e ja volta pro fundo.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$O isolado e o ultimo da fila perto da agua escura de Thornmarak$DESC$, $DESC$Quem anda sozinho na margem funda$DESC$),
'predador', jsonb_build_array($DESC$Fora da agua e em terra firme, e lento e fraco; luz na agua o expoe$DESC$),
'competidor', jsonb_build_array($DESC$Outros afogados e matadores de agua de Thornmarak$DESC$, $DESC$Afogado-Salgado$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presenca dele diz que o porto afundado ali tem matador no fundo, e o solitario some primeiro.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem anda junto, longe da margem funda, e com luz na agua$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$O laco que o liga aos outros afogados$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Sombra / agir ligado, chamar o resto pelo que prende um)$DESC$, 'risco', $DESC$Prende quem o guarda a um grupo de mortos que nao e seu.$DESC$),
jsonb_build_object('material', $DESC$A adaga que crava do fundo$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Sombra / golpe de emboscada, atacar do escondido)$DESC$, 'risco', $DESC$Puxa a mao para a agua no descuido.$DESC$),
jsonb_build_object('material', $DESC$Balestra de mao encharcada$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (arma leve, peca)$DESC$, 'risco', $DESC$Dispara emperrada e fere torto.$DESC$),
jsonb_build_object('material', $DESC$Lodo e algas do fundo$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (lastro, isca)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Quase nada, um marulho baixo e o sopro de uma balestra.$DESC$,
'cheiro', $DESC$Agua parada, lodo e ferro molhado.$DESC$,
'quer', $DESC$Cravar no isolado por tras e voltar pro fundo antes do grito, sem encarar em peso.$DESC$,
'tipo_perigo', $DESC$Oculto$DESC$,
'falas_exemplo', 'null'::jsonb,
'gatilhos_agressao', jsonb_build_array($DESC$Alguem anda sozinho ou por ultimo na beira da agua escura$DESC$, $DESC$Um alvo isolado se aproxima da margem funda$DESC$, $DESC$Prendem ou ferem um dos afogados ligados$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Volta pro fundo assim que crava ou e descoberto$DESC$, $DESC$Larga o alvo que anda junto e com luz na agua$DESC$, $DESC$Recua quando o tiram para terra firme$DESC$),
'descoberta_fazendo', $DESC$No fundo de um porto afundado de Thornmarak, andando invisivel sob a agua escura, esperando o ultimo da fila.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Nao andar em fila na beira nem deixar ninguem sozinho$DESC$, $DESC$Levar luz que fure a agua escura$DESC$, $DESC$Manter-se longe da margem funda$DESC$, $DESC$Forca-lo a terra firme, onde e lento e fraco$DESC$)
),
status_conversao='canonizada'
WHERE id=1933;

-- 960 Coaxo-Cinzento | Arcano | skirmisher | Persistente | 9 Letal | Thornmarak | fala
UPDATE ref_criaturas SET
nome=$DESC$Coaxo-Cinzento$DESC$,
nome_ptbr=$DESC$Coaxo-Cinzento$DESC$,
slug=$DESC$coaxo-cinzento$DESC$,
origem=$DESC$Marginal$DESC$,
andar_primario=$DESC$Margem$DESC$,
pilar_associado=$DESC$Arcano$DESC$,
continente=ARRAY[$DESC$Thornmarak$DESC$]::text[],
habitat=$DESC$Brejos de cristal e fendas da Margem em Thornmarak, onde a realidade e meio solta e a forma nao se decide.$DESC$,
comportamento=$DESC$Salta de um lado pro outro, rasga com a garra que carrega um pouco de caos, e a carne fecha sozinha; magia escorrega nele. Nao para quieto, nao morre facil, e troca de posicao sem parar, cansando o inimigo.$DESC$,
organizacao=$DESC$Sozinho ou em poucos, errantes da Margem.$DESC$,
perigo=$DESC$Letal$DESC$,
behavior_archetype=$DESC$skirmisher$DESC$,
morale_modifier=1,
morale_immune=false,
epigrafe=$DESC$A gente feriu, feriu de novo, e ele so ria e fechava. Os feiticos da nossa maga passavam por ele como agua.$DESC$,
descricao=$DESC$E uma coisa cinzenta de cara de sapo, vinda da Margem, que anda pelos brejos de cristal de Thornmarak onde a realidade e meio solta. Salta rapido de um lado pro outro, rasga com a garra que carrega um fiapo de caos, e fecha a propria carne tao rapido quanto leva o golpe. Magia escorrega nele, entao truque arcano ajuda pouco. Nao briga parado: pula, corta, recua e volta, e o tempo cansa quem o enfrenta antes de cansa-lo. So dano continuo e bruto, mais rapido que a cura dele, ou fogo que ela nao acompanha, o derruba.$DESC$,
supersticao_popular=$DESC$Em Thornmarak dizem que ha sapos cinzentos da Margem que nao morrem e zombam de feitico. O conselho: nao gastar magia nele, bater forte e sem parar pra vencer a cura, e usar fogo, que a carne nao acompanha. Dizem que e so um sapo grande; o sapo fecha o que voce abre.$DESC$,
sinais_presenca=$DESC$Marcas de salto largo na lama do brejo. Cortes em arvore e bicho que parecem de garra que nao combina. Feitico que falha sem motivo perto dele. Um coaxo grave e errado, alto demais. Carne e pegada que mudam de forma um pouco, sem se decidir.$DESC$,
fraqueza_conhecida=$DESC$O povo nao gasta magia, bate forte e sem parar e usa fogo. Acha que e so um sapo grande, e ele fecha o que voce abre.$DESC$,
fraqueza_real=$DESC$A carne fecha sozinha e a magia escorrega, entao truque arcano e golpe lento so atrasam; o que vence e dano bruto e continuo, mais rapido que a cura, ou fogo, que ela nao acompanha. Ele vive de saltar e trocar de lugar: prende-lo, cercar e nao deixar recuar tira o jogo do bate e some. Gastar feitico e bater devagar e o erro.$DESC$,
descricao_sensorial=$DESC$O som e um coaxo grave e errado e o baque molhado do salto. O cheiro e de brejo, limo e algo acido. Ao toque, e pele cinza, fria e umida que cicatriza na mao. Aos olhos, e uma coisa de cara de sapo que salta, corta e fecha o corte enquanto recua.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Bicho e gente que cruzam o brejo de Margem dele em Thornmarak$DESC$, $DESC$Quem gasta magia e golpe lento contra ele$DESC$),
'predador', jsonb_build_array($DESC$Dano bruto e continuo ou fogo, mais rapido que a cura, o derrubam$DESC$),
'competidor', jsonb_build_array($DESC$Outras coisas da Margem que vagam Thornmarak$DESC$, $DESC$Vulto-de-Fora$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presenca dele diz que ali a Margem deixou solto algo que fecha o que voce abre e zomba de feitico.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem nao gasta magia nele e bate forte e sem parar$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$A garra que carrega um fiapo de caos$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Arcano / corte que escapa a ordem, ferir o que resiste a magia)$DESC$, 'risco', $DESC$Muda de forma na mao e corta o dono.$DESC$),
jsonb_build_object('material', $DESC$A carne que fecha e zomba de feitico$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Arcano / regenerar, escorregar da magia)$DESC$, 'risco', $DESC$Continua se remendando e resiste a quem tenta usa-la.$DESC$),
jsonb_build_object('material', $DESC$Pele cinzenta de Margem$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (foco instavel, curiosidade)$DESC$, 'risco', $DESC$Muda de cor e tamanho devagar.$DESC$),
jsonb_build_object('material', $DESC$Limo de brejo de cristal$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (pasta, lastro)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Coaxo grave e errado e o baque molhado do salto.$DESC$,
'cheiro', $DESC$Brejo, limo e algo acido.$DESC$,
'quer', $DESC$Saltar, cortar e fechar a propria carne ate cansar o inimigo, sem ficar parado.$DESC$,
'tipo_perigo', $DESC$Persistente$DESC$,
'falas_exemplo', jsonb_build_array($DESC$Bate. Bate de novo. Eu tenho a noite e a carne nova.$DESC$, $DESC$Guarda o feitico, magrela. Ele nao me acha.$DESC$, $DESC$(registro: voz gutural e debochada, em comum, na lingua do caos e por dentro da cabeca, alto demais)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Cruzam o brejo de Margem dele em Thornmarak$DESC$, $DESC$Gastam magia ou golpe lento, achando que o ferem$DESC$, $DESC$Encurralam-no achando que vai morrer facil$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Salta e troca de lugar quando o dano fica continuo e bruto$DESC$, $DESC$Recua do fogo, que a carne nao acompanha$DESC$, $DESC$Some no brejo quando o cercam e nao o deixam saltar$DESC$),
'descoberta_fazendo', $DESC$Saltando por um brejo de cristal de Thornmarak, cortando o que cruza e fechando os proprios cortes entre um salto e outro.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Nao gastar magia nele e nao apostar em golpe lento$DESC$, $DESC$Atravessar o brejo rapido sem provoca-lo$DESC$, $DESC$Usar fogo so se for preciso encerra-lo$DESC$, $DESC$Cerca-lo e prende-lo para tirar o salto, se a briga for inevitavel$DESC$)
),
status_conversao='canonizada'
WHERE id=960;

-- 1019 Escama-Soberana | Espírito | tactical | Condicional | 4 Ameaça | Voranthar | fala
UPDATE ref_criaturas SET
nome=$DESC$Escama-Soberana$DESC$,
nome_ptbr=$DESC$Escama-Soberana$DESC$,
slug=$DESC$escama-soberana$DESC$,
origem=$DESC$Ressonante$DESC$,
andar_primario=$DESC$Superfície$DESC$,
pilar_associado=$DESC$Espírito$DESC$,
continente=ARRAY[$DESC$Voranthar$DESC$]::text[],
habitat=$DESC$Pantanos e ruinas alagadas de Voranthar, em torno da tribo de escamados que ela lidera por convicao fria.$DESC$,
comportamento=$DESC$Lidera os seus por uma fe dura de sobrevivencia, sem afeto e sem crueldade: o que serve a tribo se faz, o que nao serve morre. So vira inimiga quando ameacam o povo ou o territorio; ai luta com plano, usa o pantano e poupa os proprios. Nao briga por orgulho.$DESC$,
organizacao=$DESC$Lider de uma tribo de escamados, no centro dela.$DESC$,
perigo=$DESC$Ameaça$DESC$,
behavior_archetype=$DESC$tactical$DESC$,
morale_modifier=1,
morale_immune=false,
epigrafe=$DESC$Ela nao nos odiava. So calculou que tres de nos mortos custava menos que um dos dela. Disse isso na nossa cara, sem raiva.$DESC$,
descricao=$DESC$E a soberana de uma tribo de escamados do pantano de Voranthar, que governa por uma convicao fria e antiga: o que mantem o povo vivo e certo, o resto nao importa. Nao e cruel nem boa; e pratica ao osso. Enquanto ninguem ameaca a tribo ou o territorio, ela negocia, troca e deixa passar. Ameacado o povo, vira tatica pura: usa o pantano, arma emboscada, gasta o inimigo e poupa os seus, e nao recua por orgulho nem por medo, so por calculo. Fala por necessidade, em lingua velha de escama, e cumpre o que diz.$DESC$,
supersticao_popular=$DESC$Em Voranthar dizem que ha uma rainha-lagarto que pensa frio e que mexer com a tribo dela e morte calculada. O conselho: nao atacar o povo nem o territorio dela, oferecer troca de valor, e tratar a palavra dada com seriedade, porque ela cumpre a dela. Dizem que e um bicho burro de pantano; e fria e calculista.$DESC$,
sinais_presenca=$DESC$Uma tribo de escamados organizada demais para ser so bicho. Trilhas e armadilhas de pantano bem postas em volta de um centro. Trocas e tributos exigidos de quem cruza o territorio. Uma lider de escama parada, medindo voce sem pressa. Emboscadas que poupam os proprios e gastam o intruso.$DESC$,
fraqueza_conhecida=$DESC$O povo nao ataca a tribo nem o territorio, oferece troca e honra a palavra. Acha que e bicho burro, e e fria e calculista.$DESC$,
fraqueza_real=$DESC$Ela so e perigo se ameacam a tribo ou o territorio: quem negocia, paga o tributo e nao ataca os seus costuma passar e ate fazer acordo. Ela calcula custo: tornar a briga cara demais para a tribo a faz recuar, porque nao gasta os proprios por orgulho. Nao persegue alem do territorio. Atacar o povo dela achando que e so bicho, ou quebrar a palavra dada, e o que vira a frieza dela contra voce.$DESC$,
descricao_sensorial=$DESC$O som e uma fala seca em lingua de escama e o chapinhar de muitos pes no pantano. O cheiro e de lodo, agua parada e couro de reptil. Ao toque, e escama dura e fria sobre musculo firme. Aos olhos, e uma lider de escama parada no centro da tribo, medindo voce sem raiva nem medo.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Nao caca por esporte; gasta quem ameaca a tribo e o territorio dela em Voranthar$DESC$, $DESC$Intrusos que atacam os seus$DESC$),
'predador', jsonb_build_array($DESC$Tornar a briga cara demais a faz recuar; fora do territorio nao persegue$DESC$),
'competidor', jsonb_build_array($DESC$Outros povos e donos de pantano e ruina em Voranthar$DESC$, $DESC$Chão-Erguido$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presenca dela diz que o pantano ali tem dona que pensa frio, e mexer com o povo dela se calcula caro.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem negocia, paga tributo e nao ataca a tribo$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$A convicao fria que mantem a tribo unida$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Superfície / liderar por calculo, manter um povo coeso)$DESC$, 'risco', $DESC$Gela o afeto de quem a usa, que passa a so calcular.$DESC$),
jsonb_build_object('material', $DESC$O plano de pantano que poupa os seus$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Superfície / armar emboscada, gastar o inimigo e proteger o grupo)$DESC$, 'risco', $DESC$So funciona para quem tem um povo a proteger.$DESC$),
jsonb_build_object('material', $DESC$Escama dura de soberana$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (foco, insignia de couro)$DESC$, 'risco', $DESC$Pesa e marca quem nao e da tribo.$DESC$),
jsonb_build_object('material', $DESC$Couro de reptil de pantano$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (couro, reparo)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Fala seca em lingua de escama e o chapinhar de muitos pes no pantano.$DESC$,
'cheiro', $DESC$Lodo, agua parada e couro de reptil.$DESC$,
'quer', $DESC$Manter a tribo viva por calculo frio e gastar so quem ameaca o povo ou o territorio.$DESC$,
'tipo_perigo', $DESC$Condicional$DESC$,
'falas_exemplo', jsonb_build_array($DESC$Voce nao e inimigo ainda. Pague o tributo e siga.$DESC$, $DESC$Tres dos meus por um seu e troca ruim. Eu nao faço troca ruim.$DESC$, $DESC$(registro: voz seca e medida, em lingua de escama e comum, de quem decide por conta, nao por raiva)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Atacam a tribo ou os filhotes dela$DESC$, $DESC$Invadem ou tomam o territorio de pantano$DESC$, $DESC$Quebram a palavra ou o tributo combinado$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Recua quando a briga fica cara demais para a tribo$DESC$, $DESC$Para de gastar os seus quando o intruso se afasta do territorio$DESC$, $DESC$Aceita acordo e cessa quando pagam o tributo$DESC$),
'descoberta_fazendo', $DESC$No centro de uma tribo de escamados no pantano de Voranthar, medindo o intruso e calculando o custo de cada movimento.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Nao atacar o povo nem o territorio dela$DESC$, $DESC$Oferecer troca de valor e pagar o tributo$DESC$, $DESC$Honrar a palavra dada, que ela honra a dela$DESC$, $DESC$Tornar a briga cara demais para que ela recue por calculo$DESC$)
),
status_conversao='canonizada'
WHERE id=1019;

-- 2316 Corrente-Régia | Engenho | soldier | Direto | 13 Letal | Thornmarak | fala
UPDATE ref_criaturas SET
nome=$DESC$Corrente-Régia$DESC$,
nome_ptbr=$DESC$Corrente-Régia$DESC$,
slug=$DESC$corrente-regia$DESC$,
origem=$DESC$Natural$DESC$,
andar_primario=$DESC$Superfície$DESC$,
pilar_associado=$DESC$Engenho$DESC$,
continente=ARRAY[$DESC$Thornmarak$DESC$]::text[],
habitat=$DESC$Fortes afundados e costas de Thornmarak, ruinas de um rei gigante que ainda comanda como soldado, arrastando a corrente que o prenderam.$DESC$,
comportamento=$DESC$Luta como soldado de linha, nao como bruto: usa a corrente partida como arma e chicote, opera maquina de cerco e balestra grande, e bate de frente com disciplina. Comanda o terreno e o golpe com ordem, nao com furia.$DESC$,
organizacao=$DESC$Sozinho ou a frente de poucos, comandando como rei-soldado.$DESC$,
perigo=$DESC$Letal$DESC$,
behavior_archetype=$DESC$soldier$DESC$,
morale_modifier=1,
morale_immune=false,
epigrafe=$DESC$Nao era um gigante batendo a esmo. Era um soldado, com ordem, maquina e uma corrente que ele usava melhor que qualquer espada.$DESC$,
descricao=$DESC$Foi um rei entre os gigantes, preso por uma corrente que nunca tirou de todo, e que agora luta pelas costas afundadas de Thornmarak como soldado de linha, nao como bruto. Usa a corrente partida como chicote e arma de alcance, opera balestra grande e maquina de cerco, e bate de frente com disciplina de quem comandou exercito. Cada golpe tem ordem e proposito; nada e desperdicio. E direto e implacavel no avanco, e o terreno e a maquina trabalham com ele. Nao e furia: e oficio de guerra.$DESC$,
supersticao_popular=$DESC$Em Thornmarak dizem que ha um rei gigante acorrentado que luta como soldado e opera maquina de guerra. O conselho: nao encarar de frente em campo aberto, tirar a maquina e a balestra de cena primeiro, e nao subestimar a corrente, que tem alcance. Dizem que e so um gigante forte; e um comandante.$DESC$,
sinais_presenca=$DESC$Marca de corrente pesada arrastada na areia da costa. Balestra grande ou maquina de cerco montada em ruina. Golpes que vem com ordem e ritmo, nao a esmo. Um gigante de porte de rei, com elo partido no pulso. Tropas ou bichos postos em formacao em volta dele.$DESC$,
fraqueza_conhecida=$DESC$O povo nao o encara de frente no aberto, tira a maquina primeiro e respeita o alcance da corrente. Acha que e so forca, e e comando.$DESC$,
fraqueza_real=$DESC$A forca dele e a disciplina e a maquina: tirar a balestra e a maquina de cerco de cena, e quebrar a formacao que ele comanda, derruba metade do perigo. De frente e no aberto, ele vence pela ordem; terreno que estraga a linha e o alcance da corrente o atrapalha. Ele bate direto e implacavel, mas calcula: pressao que desfaz o plano de batalha o obriga a improvisar. Encara-lo no campo que ele escolheu e o erro.$DESC$,
descricao_sensorial=$DESC$O som e o arrasto pesado da corrente e o estalo da balestra armando. O cheiro e de mar, ferro e oleo de maquina. Ao toque, e pele dura e o elo frio de ferro grosso. Aos olhos, e um gigante de porte de rei, corrente no pulso, comandando o golpe com ordem.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Nao caca; combate quem invade a costa e a ruina que ele defende em Thornmarak$DESC$, $DESC$Exercitos e grupos que encara em linha$DESC$),
'predador', jsonb_build_array($DESC$Tirar a maquina e quebrar a formacao derruba metade do perigo; terreno ruim estraga a linha dele$DESC$),
'competidor', jsonb_build_array($DESC$Outros comandantes e soldados das costas de Thornmarak$DESC$, $DESC$Gume-Pensado$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presenca dele diz que a costa ali tem um rei-soldado que luta com ordem e maquina, nao a esmo.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem nao o encara de frente no aberto e tira a maquina primeiro$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$A corrente partida que ele usa como arma$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Engenho / arma de alcance, chicote de guerra disciplinado)$DESC$, 'risco', $DESC$Pesa e enrola na perna de quem nao treinou.$DESC$),
jsonb_build_object('material', $DESC$A balestra grande de cerco$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Engenho / maquina de guerra, tiro pesado a distancia)$DESC$, 'risco', $DESC$Dispara e recua, quebrando o que estiver atras.$DESC$),
jsonb_build_object('material', $DESC$Elo de ferro grosso$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (ferro de forja, peso)$DESC$, 'risco', $DESC$Esmaga o pe ao soltar.$DESC$),
jsonb_build_object('material', $DESC$Oleo de maquina$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (lubrificante, combustivel)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Arrasto pesado da corrente e o estalo da balestra armando.$DESC$,
'cheiro', $DESC$Mar, ferro e oleo de maquina.$DESC$,
'quer', $DESC$Avancar de frente com ordem e maquina, comandando o golpe sem desperdicio.$DESC$,
'tipo_perigo', $DESC$Direto$DESC$,
'falas_exemplo', jsonb_build_array($DESC$Forma a linha. Eu nao bato a esmo, e voce vai ver a diferenca.$DESC$, $DESC$Tira a maquina de mim e talvez seja luta. Deixa ela, e e execucao.$DESC$, $DESC$(registro: voz grave e firme de comando, em comum e em gigante, de quem ja liderou exercito)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Invadem a costa ou a ruina que ele defende$DESC$, $DESC$Encaram a linha dele em campo aberto$DESC$, $DESC$Atacam as tropas ou a maquina sob comando dele$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Recua quando tiram a maquina e quebram a formacao$DESC$, $DESC$Improvisa e cede terreno sob pressao que desfaz o plano$DESC$, $DESC$Para o avanco quando o tiram do campo que escolheu$DESC$),
'descoberta_fazendo', $DESC$Numa costa afundada de Thornmarak, comandando o golpe com a corrente partida e a balestra grande, em ordem de batalha.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Nao encara-lo de frente em campo aberto$DESC$, $DESC$Tirar a maquina e a balestra de cena primeiro$DESC$, $DESC$Quebrar a formacao que ele comanda$DESC$, $DESC$Leva-lo a terreno que estraga a linha e o alcance da corrente$DESC$)
),
status_conversao='canonizada'
WHERE id=2316;

-- post-check: devem vir 25 linhas, todas status_conversao='canonizada'
SELECT id, nome, status_conversao
FROM ref_criaturas
WHERE id IN (2443,563,2382,2012,525,772,1218,800,566,489,913,1921,2373,850,1155,2078,1903,624,1008,2351,1169,1933,960,1019,2316)
ORDER BY id;

COMMIT;

-- ============================================================
-- VERIFICACAO (sec. 7.5) — rodar APOS o COMMIT
-- ============================================================

-- 7.5.a — contagem de status (esperado: canonizada sobe +25; classificada cai -25)
SELECT status_conversao, COUNT(*) AS n
FROM ref_criaturas
GROUP BY status_conversao
ORDER BY status_conversao;

-- 7.5.b — trava de linguagem nos campos de PROSA (esperado: fichas_com_proibida=0)
-- regex EXATA; pilar_associado NAO entra (Espírito como pilar e legitimo)
SELECT COUNT(*) AS fichas_com_proibida
FROM ref_criaturas
WHERE status_conversao='canonizada'
  AND concat_ws(' ',
      nome, nome_ptbr, descricao, supersticao_popular, sinais_presenca,
      fraqueza_conhecida, fraqueza_real, descricao_sensorial, habitat,
      comportamento, organizacao, epigrafe,
      ecologia::text, loot_table::text, camada_narrativa::text
  ) ~* '\m(almas?|fantasmas?|esp[íi]ritos?|dem[ôo]nios?|inferno)\M';

-- 7.5.c — eixos dos 25 recem-canonizados (conferencia: pilar/archetype/tipo_perigo/perigo)
SELECT id, nome, pilar_associado, behavior_archetype,
       camada_narrativa->>'tipo_perigo' AS tipo_perigo, perigo
FROM ref_criaturas
WHERE id IN (2443,563,2382,2012,525,772,1218,800,566,489,913,1921,2373,850,1155,2078,1903,624,1008,2351,1169,1933,960,1019,2316)
ORDER BY id;
