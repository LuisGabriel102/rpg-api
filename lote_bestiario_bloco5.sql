-- ============================================================================
-- lote_bestiario_bloco5.sql  -- Bloco 5: 25 criaturas (classificada -> canonizada)
-- Uma transacao. Um UPDATE por id. Stat block mecanico NUNCA tocado.
-- Andar = pool (ancora). Loot segue a origem. Trava de linguagem = 0.
-- ============================================================================
BEGIN;

-- 1003 Quilha-Negra | Corpo | predator | Direto | Ameaca | Voranthar | Superficie | muda | Natural -> teto Notavel
UPDATE ref_criaturas SET
nome=$DESC$Quilha-Negra$DESC$,
nome_ptbr=$DESC$Quilha-Negra$DESC$,
slug=$DESC$quilha-negra$DESC$,
origem=$DESC$Natural$DESC$,
andar_primario=$DESC$Superfície$DESC$,
pilar_associado=$DESC$Corpo$DESC$,
continente=ARRAY[$DESC$Voranthar$DESC$]::text[],
habitat=$DESC$As águas escuras da costa afogada de Voranthar, onde cidades antigas dormem sob a maré. Caça nos canais entre as ruínas submersas e nos braços de mar que cortam as terras baixas.$DESC$,
comportamento=$DESC$Caça em dupla ou trio, e o que parece brincadeira é método: empurra a presa para o raso, corta a fuga, escolhe a hora. Não tem pressa. Quando decide, vem reto e fecha a boca uma vez só.$DESC$,
organizacao=$DESC$Em famílias pequenas e duráveis, que caçam juntas a vida inteira.$DESC$,
perigo=$DESC$Ameaça$DESC$,
behavior_archetype=$DESC$predator$DESC$,
morale_modifier=1,
morale_immune=false,
epigrafe=$DESC$O barco virou sem aviso. Não vi a coisa. Vi a água ficar funda do lado errado, e meu irmão não estava mais lá.$DESC$,
descricao=$DESC$É grande como uma quilha de navio e preta e branca como a água sob o gelo. Move-se sem ruído até decidir, e aí a velocidade não combina com o tamanho. Caça em grupo, pelas terras afogadas de Voranthar, e o que faz não é fúria: é trabalho. Empurra o barco contra a pedra, ou espera o homem cair, e fecha a boca uma vez. Não volta para confirmar. Não precisa.$DESC$,
supersticao_popular=$DESC$Os barqueiros das terras baixas dizem que a coisa preta e branca é dona dos canais, e que ela escolhe. Contam que bater o remo na água chama, e que cantar afasta, embora ninguém saiba se é verdade. O conselho que passa de pai para filho é não pescar onde a água fica funda de repente, e remar quieto, e nunca arrastar a mão fora da borda.$DESC$,
sinais_presenca=$DESC$Cardumes que somem de um trecho de canal de um dia para o outro. Uma barbatana alta que corta a superfície e afunda sem pressa. Focas e aves que se afastam todas para a mesma margem. O silêncio súbito da água onde antes havia vida. Restos de presa grande boiando, limpos, sem briga aparente.$DESC$,
fraqueza_conhecida=$DESC$O raso. O povo sabe que a coisa precisa de água funda para virar o barco e para a corrida final, e que quem chega à margem de pedra ou ao banco de areia geralmente escapa. Remar para o raso é a regra. Lança e arpão de borda funcionam se ela já está perto, mas chegar perto é o problema.$DESC$,
fraqueza_real=$DESC$Ela calcula, e o que calcula pode ser usado contra ela. Não gasta vida à toa: se a presa custa caro, ela desiste e procura outra. Fazer-se caro — manter o grupo unido, a borda alta, o arpão à mostra — costuma bastar para que ela escolha não pagar. É predadora, não fanática. Encurralada no raso, longe do fundo, perde a vantagem inteira e recua.$DESC$,
descricao_sensorial=$DESC$O som é um sopro alto e úmido quando ela arqueia para respirar, e depois o nada da água parada. O cheiro é de maresia e de peixe, salgado e frio. Ao toque, a pele é lisa e dura e fria como couro molhado. Aos olhos, é um corpo enorme de preto e branco que desliza logo abaixo da superfície, mais rápido do que o tamanho promete.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Focas e aves marinhas dos canais afogados$DESC$, $DESC$Homens de barco que remam onde a água fica funda$DESC$),
'predador', jsonb_build_array($DESC$Nada a caça de fato; só a fome e o inverno a movem para longe$DESC$),
'competidor', jsonb_build_array($DESC$Outros caçadores grandes dos canais de Voranthar$DESC$, $DESC$Ilhota-Funda$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presença dela diz que aquele trecho de canal é fundo e farto, e que a pesca fácil ali tem dono.$DESC$,
'evitado_por', jsonb_build_array($DESC$Barqueiros que conhecem os canais e remam para o raso ao primeiro sinal$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$Dente grande e curvo, recolhido da carcaça$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Material (cabo de faca, talha, troféu de barqueiro)$DESC$, 'risco', $DESC$Nenhum além do peso.$DESC$),
jsonb_build_object('material', $DESC$Banha grossa da camada sob a pele$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (óleo de lamparina, impermeável de barco)$DESC$, 'risco', $DESC$Rança e fede se mal curada.$DESC$),
jsonb_build_object('material', $DESC$Couro liso e escuro do dorso$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (forro, bota, correia)$DESC$, 'risco', $DESC$Nenhum.$DESC$),
jsonb_build_object('material', $DESC$Carne escura e farta$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (sustento de uma aldeia por dias)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Um sopro alto e úmido quando ela respira, e o silêncio da água parada antes do golpe.$DESC$,
'cheiro', $DESC$Maresia e peixe, salgado e frio.$DESC$,
'quer', $DESC$Comer bem com o menor custo, manter o grupo e o canal fartos, escolher a presa e a hora.$DESC$,
'tipo_perigo', $DESC$Direto$DESC$,
'falas_exemplo', 'null'::jsonb,
'gatilhos_agressao', jsonb_build_array($DESC$Um barco pequeno cruza a parte funda do canal$DESC$, $DESC$Presa ferida ou isolada cai na água$DESC$, $DESC$O grupo dela já cercou a presa contra a pedra$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$A presa chega ao raso ou à margem de pedra$DESC$, $DESC$O custo da caça sobe e ela escolhe outra presa$DESC$, $DESC$Arpão ou lança ferem o suficiente para não valer a pena$DESC$),
'descoberta_fazendo', $DESC$Empurrando um cardume ou um barco para o raso com o grupo, em silêncio, escolhendo a hora.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Remar reto para o raso ou para o banco de areia, onde ela não entra$DESC$, $DESC$Manter a borda alta e o arpão à mostra até ela julgar o custo alto demais$DESC$, $DESC$Largar parte da pesca na água para que ela coma e perca o interesse no barco$DESC$, $DESC$Esperar parado e quieto até o grupo dela passar para outro canal$DESC$)
),
status_conversao='canonizada'
WHERE id=1003;

-- 2452 Bolor-Espalhado | Sombra | striker | Persistente | Ameaca | Thornmarak | Eco | muda | Cicatricial -> teto Raro
UPDATE ref_criaturas SET
nome=$DESC$Bolor-Espalhado$DESC$,
nome_ptbr=$DESC$Bolor-Espalhado$DESC$,
slug=$DESC$bolor-espalhado$DESC$,
origem=$DESC$Cicatricial$DESC$,
andar_primario=$DESC$Eco$DESC$,
pilar_associado=$DESC$Sombra$DESC$,
continente=ARRAY[$DESC$Thornmarak$DESC$]::text[],
habitat=$DESC$As baixadas úmidas de Thornmarak, sob o teto fechado das árvores, onde a luz não seca o chão. Onde houve morte e o mato cobriu, o bolor pega e fica.$DESC$,
comportamento=$DESC$Não pensa. Espera no escuro úmido, com cara de homem caído, até alguém chegar perto, e então o corpo cego se move e bate, e a nuvem solta. Quem respira a nuvem adoece, e do adoecido nasce mais bolor. É lento, e é por isso que se alastra: ninguém o vê crescer.$DESC$,
organizacao=$DESC$Em manchas que se ligam pelo solo, cada corpo um foco novo da mesma praga.$DESC$,
perigo=$DESC$Ameaça$DESC$,
behavior_archetype=$DESC$striker$DESC$,
morale_modifier=0,
morale_immune=true,
epigrafe=$DESC$Achei que era um corpo de andarilho. Cheguei para cobrir o rosto dele. O rosto abriu numa poeira e eu tossi a noite inteira.$DESC$,
descricao=$DESC$Foi gente, e ainda tem a forma de gente caída, mas por dentro é só um resto tomado por bolor pálido que brota das frestas da pele. Fica quieto no úmido até alguém se aproximar, e aí o corpo cego ergue e golpea, e do golpe e da boca sai uma nuvem fina de esporo. Quem respira fundo a nuvem amanhece febril, e a febre vira lentidão, e a lentidão vira mais um foco da mesma coisa. Não há malícia nisso, só a pressa cega do mofo que quer mais chão. É da Margem da morte que ele vem, e da morte que ele faz.$DESC$,
supersticao_popular=$DESC$Nas baixadas, dizem que não se cobre defunto que não se conhece, e que andarilho caído sob árvore fechada às vezes não é defunto. O conselho é queimar de longe, com archote em vara comprida, e não respirar o fumo. Contam que o mal entra pelo nariz e pela boca, e que pano molhado no rosto segura por um tempo, embora não para sempre.$DESC$,
sinais_presenca=$DESC$Um corpo caído onde a árvore fecha a luz, com manchas pálidas brotando da pele. Poeira fina que sobe sozinha quando nada a moveu. O cheiro adocicado e podre de fungo onde não devia. Bichos pequenos mortos em volta, sem ferida, só murchos. Outras manchas pálidas no tronco e na raiz por perto, como se a coisa estivesse se espalhando.$DESC$,
fraqueza_conhecida=$DESC$O fogo. O povo sabe que archote e tocha secam e matam o bolor, e que queimar o foco antes que ele solte a nuvem é o método. Pano molhado no rosto atrasa a doença em quem chega perto. Manter distância e usar vara comprida é a regra de quem sabe.$DESC$,
fraqueza_real=$DESC$Ele é lento e cego, e só faz mal de perto e pelo ar. Quem não respira a nuvem e não deixa tocar não adoece, por mais que o corpo se mova. O perigo de verdade não é o golpe, é o alastramento: matar um foco e deixar os outros é não resolver nada. Queimar a mancha inteira, foco por foco, seco até a raiz, encerra a praga; um corpo só queimado e dez deixados é só ganhar tempo para ela.$DESC$,
descricao_sensorial=$DESC$O som é quase nenhum: um arrastar mole e o estouro baixo da nuvem quando solta. O cheiro é doce e podre ao mesmo tempo, de fruta esquecida e cogumelo. Ao toque, é mole e úmido e cede como coisa apodrecida, e isso já é perigo. Aos olhos, é um corpo caído de forma humana com bolor pálido florescendo das frestas, e a poeira fina que paira em volta.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Quem chega perto para socorrer um caído$DESC$, $DESC$Bichos pequenos que cruzam a mancha e respiram o esporo$DESC$),
'predador', jsonb_build_array($DESC$O fogo e a seca, que matam o foco antes que ele se espalhe$DESC$),
'competidor', jsonb_build_array($DESC$Outras podridões das baixadas que disputam a carcaça e o chão úmido$DESC$, $DESC$Podridão-Lenta$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presença dele diz que ali houve morte recente e o úmido a tomou, e que o trecho de mata está virando foco de praga.$DESC$,
'evitado_por', jsonb_build_array($DESC$Andarilhos que não cobrem defunto desconhecido e queimam de longe$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$Esporo seco recolhido com cuidado da nuvem$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Eco / venenos de pulmão e febres que se alastram)$DESC$, 'risco', $DESC$Uma baforada adoece quem o colhe sem pano e máscara.$DESC$),
jsonb_build_object('material', $DESC$Polpa de bolor pálido da pele$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Sombra / unguentos que apodrecem e amolecem)$DESC$, 'risco', $DESC$Contamina ferida aberta; manusear só com luva.$DESC$),
jsonb_build_object('material', $DESC$Pano ou trapo do morto, ainda com marca da coisa$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (amostra para quem estuda a praga)$DESC$, 'risco', $DESC$Guarda esporo; queimar depois de usar.$DESC$),
jsonb_build_object('material', $DESC$Terra do foco, encharcada de fungo$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (nada de útil; prova do mal)$DESC$, 'risco', $DESC$Pega fogo mal e fede.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Um arrastar mole e o estouro surdo da nuvem de esporo quando solta.$DESC$,
'cheiro', $DESC$Doce e podre, de fruta esquecida e cogumelo.$DESC$,
'quer', $DESC$Mais chão úmido, mais corpos, mais focos. Não há vontade, só o avanço cego do mofo.$DESC$,
'tipo_perigo', $DESC$Persistente$DESC$,
'falas_exemplo', 'null'::jsonb,
'gatilhos_agressao', jsonb_build_array($DESC$Alguém se abaixa para socorrer o que parece um caído$DESC$, $DESC$Um corpo quente passa ao alcance do braço cego$DESC$, $DESC$Algo sacode o foco e levanta a poeira$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Não foge; o foco fica até queimar$DESC$, $DESC$O corpo cai imóvel quando o fogo seca a raiz$DESC$, $DESC$Para de se mover quando não há mais nada quente por perto$DESC$),
'descoberta_fazendo', $DESC$Caído com forma de gente sob a árvore fechada, florescendo bolor em silêncio, esperando um corpo quente chegar.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Queimar o foco de longe com archote em vara comprida, antes que solte a nuvem$DESC$, $DESC$Cobrir o rosto com pano molhado e passar largo, sem respirar fundo$DESC$, $DESC$Marcar a mancha e voltar com fogo para queimar foco por foco até a raiz$DESC$, $DESC$Não tocar e não socorrer o caído desconhecido sob a mata fechada$DESC$)
),
status_conversao='canonizada'
WHERE id=2452;

-- 918 Lanterna-Falsa | Arcano | trapper | Condicional | Ameaca | Vyrkhor | Superficie | muda | Natural -> teto Notavel
UPDATE ref_criaturas SET
nome=$DESC$Lanterna-Falsa$DESC$,
nome_ptbr=$DESC$Lanterna-Falsa$DESC$,
slug=$DESC$lanterna-falsa$DESC$,
origem=$DESC$Natural$DESC$,
andar_primario=$DESC$Superfície$DESC$,
pilar_associado=$DESC$Arcano$DESC$,
continente=ARRAY[$DESC$Vyrkhor$DESC$]::text[],
habitat=$DESC$As ruínas geladas e as galerias de pedra de Vyrkhor, fendas e túmulos onde o escuro é total. Vive onde o viajante perdido procura uma luz.$DESC$,
comportamento=$DESC$Acende uma luz fria no próprio corpo e fica parado num ponto fundo da galeria, como se fosse archote esquecido ou candeia de abrigo. Não persegue. Espera que o frio e o medo do escuro tragam o homem até ela, e quando ele chega ao alcance, a luz apaga e ela morde no breu.$DESC$,
organizacao=$DESC$Sozinha, cada uma com a sua armadilha de luz num corredor diferente.$DESC$,
perigo=$DESC$Ameaça$DESC$,
behavior_archetype=$DESC$trapper$DESC$,
morale_modifier=0,
morale_immune=true,
epigrafe=$DESC$Vi a luz lá no fundo e pensei: abrigo. Andei reto para ela. A luz se apagou quando estendi a mão.$DESC$,
descricao=$DESC$É um bicho de carapaça que acende no corpo uma luz fria e parada, e usa essa luz como isca. No escuro de uma galeria de Vyrkhor, ela parece a candeia de um abrigo ou o archote que alguém deixou, e o viajante gelado caminha reto para ela. Não corre atrás de ninguém: faz da própria luz a armadilha, e espera. Quando o homem chega perto, a luz morre de repente, e no breu total a coisa morde. O perigo não é a mordida fraca; é o lugar onde a luz o levou, fundo demais para achar a saída.$DESC$,
supersticao_popular=$DESC$Em Vyrkhor, os que andam nas ruínas dizem que nem toda luz no escuro é amiga, e que candeia parada no fundo de uma galeria que ninguém acendeu é coisa a temer. O conselho é nunca caminhar reto para uma luz sem mexer com ela primeiro, e levar a própria chama, e marcar o caminho de volta, porque a luz falsa some na hora errada e deixa o homem cego e perdido.$DESC$,
sinais_presenca=$DESC$Uma luz pálida e fixa no fundo de uma galeria, sem fumaça e sem calor. A luz que não treme com o vento como tremeria uma chama. Carapaças vazias e ossos de quem veio antes, num raio curto em volta do ponto de luz. O cheiro seco de bicho no lugar onde devia haver cheiro de fogo. A luz que se apaga de uma vez quando alguém se aproxima.$DESC$,
fraqueza_conhecida=$DESC$Levar a própria luz. O povo sabe que quem carrega archote ou candeia não cai na isca, porque vê a coisa pelo que é antes de chegar perto. Jogar uma pedra na luz duvidosa, em vez de andar até ela, revela a fraude. A mordida em si é fraca e o bicho é pequeno; o método é não ser atraído.$DESC$,
fraqueza_real=$DESC$A armadilha dela é a única arma; tirada a vantagem do escuro, ela não é nada. Com luz própria firme, o viajante a vê parada e frágil e simplesmente a evita ou a esmaga. Ela não persegue, não cerca, não pensa em fugir nem em recuar: só sabe brilhar e esperar. Quem nunca apaga a própria luz nunca está em perigo, por mais funda que seja a galeria.$DESC$,
descricao_sensorial=$DESC$O som é um estalo seco de carapaça e o roçar de patas na pedra. O cheiro é de bicho seco e poeira, nada do calor de fogo que a luz promete. Ao toque, é dura e quitinosa e fria, sem nenhum calor sob o brilho. Aos olhos, é uma luz fria e parada no breu que, de perto, se revela um corpo de carapaça com um clarão pálido por dentro.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Viajantes perdidos que caminham para a luz no escuro$DESC$, $DESC$Bichos pequenos das galerias atraídos pelo brilho$DESC$),
'predador', jsonb_build_array($DESC$Quem carrega a própria chama e a vê parada para esmagá-la$DESC$),
'competidor', jsonb_build_array($DESC$Outras armadilhas das ruínas de Vyrkhor que disputam o viajante perdido$DESC$, $DESC$Pacto-Murcho$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presença dela diz que aquela galeria é funda e cega, e que outros já se perderam seguindo luzes ali.$DESC$,
'evitado_por', jsonb_build_array($DESC$Andarilhos de ruína que levam luz própria e nunca caminham reto para um brilho estranho$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$Glândula que guarda a luz fria do corpo$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Material (candeia fria sem chama, sinal de mineiro)$DESC$, 'risco', $DESC$Apaga em horas; some o brilho se mal guardada.$DESC$),
jsonb_build_object('material', $DESC$Carapaça dura e leve$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (placa, fecho, adorno)$DESC$, 'risco', $DESC$Nenhum.$DESC$),
jsonb_build_object('material', $DESC$Patas e mandíbulas pequenas$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (anzol, alfinete)$DESC$, 'risco', $DESC$Nenhum.$DESC$),
jsonb_build_object('material', $DESC$Restos quitinosos moídos$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (refugo, isca de bicho)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Estalo seco de carapaça e o roçar de patas na pedra; nenhum crepitar de fogo.$DESC$,
'cheiro', $DESC$Bicho seco e poeira, sem o calor de chama que a luz finge.$DESC$,
'quer', $DESC$Atrair um corpo quente até o alcance e mordê-lo no escuro. Brilhar e esperar, sempre no mesmo ponto fundo.$DESC$,
'tipo_perigo', $DESC$Condicional$DESC$,
'falas_exemplo', 'null'::jsonb,
'gatilhos_agressao', jsonb_build_array($DESC$Um viajante caminha reto até o alcance da luz$DESC$, $DESC$Uma mão se estende para tocar o brilho$DESC$, $DESC$Algo pequeno e quente cruza o raio da isca$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Não foge; apaga a luz e se aquieta se o alvo recua$DESC$, $DESC$Fica imóvel no escuro quando ninguém morde a isca$DESC$, $DESC$Some o brilho e se encolhe na fenda diante de luz própria e firme$DESC$),
'descoberta_fazendo', $DESC$Parada no fundo de uma galeria escura, acesa como candeia esquecida, esperando que o frio e o medo tragam alguém.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Levar luz própria e firme, que desfaz a isca e mostra a coisa parada$DESC$, $DESC$Jogar uma pedra na luz duvidosa em vez de caminhar até ela$DESC$, $DESC$Marcar o caminho de volta e não se deixar levar fundo demais por um brilho$DESC$, $DESC$Contornar a galeria pela rota conhecida, ignorando a luz no fundo$DESC$)
),
status_conversao='canonizada'
WHERE id=918;

-- 924 Palpebra-Branca | Espirito | lurker | Oculto | Ameaca | Kethara | Clarao | muda | Cicatricial -> teto Raro
UPDATE ref_criaturas SET
nome=$DESC$Pálpebra-Branca$DESC$,
nome_ptbr=$DESC$Pálpebra-Branca$DESC$,
slug=$DESC$palpebra-branca$DESC$,
origem=$DESC$Cicatricial$DESC$,
andar_primario=$DESC$Clarão$DESC$,
pilar_associado=$DESC$Espírito$DESC$,
continente=ARRAY[$DESC$Kethara$DESC$]::text[],
habitat=$DESC$Os céus altos e frios sobre o deserto de Kethara, e as ruínas de areia onde o Clarão chega à terra. Pousa em torre quebrada e cornija, e olha.$DESC$,
comportamento=$DESC$Vigia. Voa sem ruído no escuro e fica horas imóvel num ponto alto, com os olhos pálidos abertos, medindo quem passa lá embaixo. Não ataca por fome nem por território; cai sobre quem julga que precisa cair, e cai uma vez, do alto, antes de qualquer um ouvir a asa.$DESC$,
organizacao=$DESC$Sozinha, fixa a um trecho de céu e de ruína que ela tomou para vigiar.$DESC$,
perigo=$DESC$Ameaça$DESC$,
behavior_archetype=$DESC$lurker$DESC$,
morale_modifier=0,
morale_immune=true,
epigrafe=$DESC$Não ouvi nada. Senti o ar mudar acima de mim, e quando olhei, dois olhos brancos já estavam descendo.$DESC$,
descricao=$DESC$É uma ave grande e pálida do Clarão, de olhos brancos que não piscam, e o que a move não é fome: é um juízo frio que não se explica. Vem das alturas geladas de Kethara, pousa nas ruínas de areia, e vigia quem cruza por baixo. O voo dela não faz som. Quando decide, desce do alto, num só mergulho calado, e as garras chegam antes do aviso. Não há bondade nela, por mais que alguns a chamem de boa por causa da luz pálida; é uma sentinela que não sofre quem julga que não devia estar ali.$DESC$,
supersticao_popular=$DESC$Os nômades de Kethara dizem que há uma vigia branca no céu da noite, e que ela vê o que se faz no escuro. Contam que ela poupa quem anda limpo e cai sobre quem carrega culpa, embora os que sabem desconfiem que ela apenas escolhe por regra própria, e não por mérito. O conselho é não cruzar as ruínas à noite com pressa de quem foge, e olhar para cima de quando em quando, porque o golpe dela vem de lá.$DESC$,
sinais_presenca=$DESC$Um par de olhos pálidos parado num ponto alto de ruína, que não se mexe e não pisca. O silêncio dos bichos pequenos da noite, calados todos de uma vez. Penas brancas largadas em cornija, frias ao toque. A sombra que cruza a lua sem ruído de asa. A sensação de ser medido por algo lá em cima que não se vê direito.$DESC$,
fraqueza_conhecida=$DESC$A luz e o teto. O povo sabe que ela caça do alto e no escuro, e que quem anda sob abrigo, ou com tocha que rasga a noite, tira dela o mergulho calado. Ficar a descoberto, parado e iluminado, faz com que ela não desça, porque o golpe dela depende de chegar sem ser vista.$DESC$,
fraqueza_real=$DESC$Ela julga por uma régua fria e fixa, e não muda de ideia no meio: decidida a cair, cai, e poupada a decisão, vai embora e não insiste. Não sente medo, então não se afugenta; mas também não persegue além do que a sua regra manda. Quem entende que ela não é fome, e sim sentença, sabe que o jeito não é vencê-la na força, e sim não dar o motivo: ficar à vista, sem fuga e sem pressa de culpado, e deixá-la julgar que não precisa descer.$DESC$,
descricao_sensorial=$DESC$O som é nenhum, e o nenhum é o aviso: o ar se aquieta onde ela está. O cheiro é frio e seco, de pena e de pedra alta. Ao toque, a pena é macia e estranhamente fria, sem o calor que se espera de ave viva. Aos olhos, é um vulto pálido e grande de olhos brancos que não piscam, parado no alto até o instante em que desce.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Quem cruza as ruínas à noite e ela julga que deve cair$DESC$, $DESC$Bichos pequenos do deserto, tomados quase por ofício$DESC$),
'predador', jsonb_build_array($DESC$Nada a caça; ela vai embora quando a sua vigília se cumpre$DESC$),
'competidor', jsonb_build_array($DESC$Outros vigias frios do Clarão sobre Kethara$DESC$, $DESC$Pluma-Vígil$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presença dela diz que o Clarão toca aquele trecho de ruína, e que alguém ali está sendo medido.$DESC$,
'evitado_por', jsonb_build_array($DESC$Nômades que não cruzam as ruínas de Kethara à noite com pressa de fugitivo$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$Pena branca fria que não perde o brilho pálido$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Clarão / focos de juízo, de visão à distância e de luz que não aquece)$DESC$, 'risco', $DESC$Pesa na consciência de quem a porta; gela a mão que a segura muito tempo.$DESC$),
jsonb_build_object('material', $DESC$Garra curva e pálida$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Clarão / lâminas e ganchos que cortam sem aquecer)$DESC$, 'risco', $DESC$Corta frio e fundo; fere quem a manuseia sem cuidado.$DESC$),
jsonb_build_object('material', $DESC$Olho pálido, conservado$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (curiosidade, prova de caçada)$DESC$, 'risco', $DESC$Incomoda olhar; alguns dizem que ainda mede.$DESC$),
jsonb_build_object('material', $DESC$Penugem comum das asas$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (forro, enchimento)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Nenhum; o ar se aquieta onde ela está, e o silêncio é o único aviso.$DESC$,
'cheiro', $DESC$Frio e seco, de pena e de pedra alta.$DESC$,
'quer', $DESC$Vigiar o trecho que tomou e cair sobre quem a sua régua manda cair, uma vez, do alto.$DESC$,
'tipo_perigo', $DESC$Oculto$DESC$,
'falas_exemplo', 'null'::jsonb,
'gatilhos_agressao', jsonb_build_array($DESC$Alguém cruza as ruínas à noite com pressa de quem foge$DESC$, $DESC$O julgamento frio dela decide que aquele corpo deve cair$DESC$, $DESC$Um alvo isolado e desatento passa logo abaixo do poleiro$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Vai embora quando a sua vigília se cumpre, sem insistir$DESC$, $DESC$Não desce sobre quem está à vista, parado e iluminado$DESC$, $DESC$Abandona o trecho quando a régua que a prende ali se satisfaz$DESC$),
'descoberta_fazendo', $DESC$Imóvel num ponto alto de ruína, de olhos brancos abertos, medindo quem cruza o escuro lá embaixo.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Ficar à vista, parado e iluminado, sem dar o aspecto de fugitivo$DESC$, $DESC$Cruzar as ruínas de dia, quando ela não caça do alto$DESC$, $DESC$Andar sob abrigo ou teto, tirando dela o mergulho calado$DESC$, $DESC$Não correr nem se esconder, e deixá-la julgar que não precisa descer$DESC$)
),
status_conversao='canonizada'
WHERE id=924;

-- 1162 Enxame-Calculado | Engenho | swarm | Ambiental | Ameaca | Kethara | Superficie | muda | Natural -> teto Notavel
UPDATE ref_criaturas SET
nome=$DESC$Enxame-Calculado$DESC$,
nome_ptbr=$DESC$Enxame-Calculado$DESC$,
slug=$DESC$enxame-calculado$DESC$,
origem=$DESC$Natural$DESC$,
andar_primario=$DESC$Superfície$DESC$,
pilar_associado=$DESC$Engenho$DESC$,
continente=ARRAY[$DESC$Kethara$DESC$]::text[],
habitat=$DESC$As ruínas de areia e os oásis de Kethara, onde a água escassa concentra a vida. Faz ninho nas frestas mornas das pedras e nas câmaras soterradas.$DESC$,
comportamento=$DESC$Cada bicho é nada; o enxame inteiro age como uma só coisa, e age com método. Espalha-se para cobrir uma câmara, fecha as saídas com corpo, e converge onde há calor e sangue. Não tem chefe; a regra está no todo, e o todo resolve, divide e ataca como se pensasse.$DESC$,
organizacao=$DESC$Um enxame único que se move e decide como corpo só, milhares de partes sem nenhuma no comando.$DESC$,
perigo=$DESC$Ameaça$DESC$,
behavior_archetype=$DESC$swarm$DESC$,
morale_modifier=0,
morale_immune=true,
epigrafe=$DESC$Não era um bicho. Era a parede inteira que se moveu, e fechou a porta, e veio para o meio da sala onde estávamos.$DESC$,
descricao=$DESC$É um enxame de bichos miúdos das ruínas de Kethara que, juntos, agem como uma máquina viva. Sozinho, cada um se esmaga sob o dedo. Reunidos, cobrem o chão e a parede, fecham as saídas de uma câmara, e fluem para onde há calor, sem chefe e sem hesitação, como se um cálculo frio governasse o todo. Enchem o ar e o vão, e quem fica no meio é mordido por toda parte ao mesmo tempo. O perigo não é a picada de um; é o espaço inteiro virar deles, e a saída sumir atrás de uma cortina viva.$DESC$,
supersticao_popular=$DESC$Em Kethara, dizem que certas câmaras soterradas têm dono, e que o dono é a própria parede. O conselho dos que saqueiam ruína é não acender fogo grande numa sala fechada sem checar as frestas, e nunca entrar fundo sem saber por onde sair, porque o enxame fecha a porta primeiro e ataca depois. Contam que fumaça e fogo abrem caminho, e que correr para a luz e o aberto é a única saída.$DESC$,
sinais_presenca=$DESC$Frestas de pedra que parecem respirar, escurecendo e clareando com o movimento de dentro. Um zumbido baixo e constante que sobe quando alguém entra. Carapaças e restos miúdos acumulados num canto da câmara. O chão que parece se mover na borda do olho. Bichos que fogem todos para a mesma saída antes de o enxame encher o vão.$DESC$,
fraqueza_conhecida=$DESC$O fogo e o aberto. O povo sabe que o enxame teme a chama e o fumo, e que um archote bom abre um corredor por onde escapar. Sala fechada é a armadilha; correr para a luz e o espaço aberto, onde o enxame se dispersa e perde a força, é o método. Bater e espantar parte não adianta; o todo se refaz.$DESC$,
fraqueza_real=$DESC$A força dele é o aperto e o todo reunido; espalhado, ele é só uma praga de bichinhos. Num vão aberto e ventoso, ou rasgado por fogo e fumo, o enxame se quebra em partes que não decidem mais nada e se dispersam. Ele não pensa de verdade nem teme; só converge enquanto pode convergir. Negar a ele a câmara fechada — manter porta aberta, vento a favor, chama na mão — desfaz a máquina antes que ela se forme.$DESC$,
descricao_sensorial=$DESC$O som é um zumbido baixo e cheio que cresce até virar a sala inteira. O cheiro é seco e ácido, de bicho e de carapaça moída. Ao toque, é mil patas e ferrões miúdos por toda a pele de uma vez, sem um ponto de onde fugir. Aos olhos, é o chão e a parede que se movem, uma maré escura e viva que cobre a pedra e fecha o vão.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Saqueadores presos numa câmara fechada das ruínas$DESC$, $DESC$Bichos maiores que se aventuram nos ninhos soterrados$DESC$),
'predador', jsonb_build_array($DESC$O fogo, o vento e o espaço aberto, que dispersam o todo$DESC$),
'competidor', jsonb_build_array($DESC$Outras pragas das ruínas de Kethara que disputam câmara e carcaça$DESC$, $DESC$Súcia-Lúcida$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presença dele diz que aquela câmara é funda e fechada, e que entrar sem rota de fuga é entregar-se.$DESC$,
'evitado_por', jsonb_build_array($DESC$Saqueadores que checam as frestas e nunca entram fundo sem saber a saída$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$Geleia real do ninho, densa e doce-amarga$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Material (remédio, conserva, isca rara)$DESC$, 'risco', $DESC$Atrai mais bichos se exposta.$DESC$),
jsonb_build_object('material', $DESC$Favo e cera das câmaras$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (vela, vedante, molde)$DESC$, 'risco', $DESC$Nenhum.$DESC$),
jsonb_build_object('material', $DESC$Carapaças miúdas em quantidade$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (pó, tinta, refugo)$DESC$, 'risco', $DESC$Nenhum.$DESC$),
jsonb_build_object('material', $DESC$Terra e detrito do ninho$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (adubo, enchimento)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Um zumbido baixo e cheio que cresce até ser a sala inteira.$DESC$,
'cheiro', $DESC$Seco e ácido, de bicho e carapaça moída.$DESC$,
'quer', $DESC$Cobrir a câmara, fechar as saídas e convergir sobre o calor. Crescer o ninho, sem vontade própria, só pela regra do todo.$DESC$,
'tipo_perigo', $DESC$Ambiental$DESC$,
'falas_exemplo', 'null'::jsonb,
'gatilhos_agressao', jsonb_build_array($DESC$Um corpo quente entra fundo na câmara do ninho$DESC$, $DESC$Fogo ou barulho sacode as frestas e desperta o todo$DESC$, $DESC$Alguém fica preso entre o enxame e a saída fechada$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Não foge como um; dispersa-se quando o vão se abre ao vento$DESC$, $DESC$Quebra-se em partes que se espalham diante de fogo e fumaça$DESC$, $DESC$Recolhe-se às frestas quando não há mais calor preso na câmara$DESC$),
'descoberta_fazendo', $DESC$Espalhado pelas paredes de uma câmara soterrada, fechando saídas e convergindo devagar sobre o calor que entrou.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Correr para a luz e o espaço aberto, onde o enxame se dispersa$DESC$, $DESC$Abrir caminho com archote e fumaça antes que as saídas se fechem$DESC$, $DESC$Não entrar fundo sem deixar a porta aberta e o vento a favor$DESC$, $DESC$Recuar ao primeiro zumbido, antes de o todo se formar no vão$DESC$)
),
status_conversao='canonizada'
WHERE id=1162;

-- 1180 Renovo-Cru | Corpo | predator | Persistente | Ameaca | Thornmarak | Superficie | FALA | Natural -> teto Notavel
UPDATE ref_criaturas SET
nome=$DESC$Renovo-Cru$DESC$,
nome_ptbr=$DESC$Renovo-Cru$DESC$,
slug=$DESC$renovo-cru$DESC$,
origem=$DESC$Natural$DESC$,
andar_primario=$DESC$Superfície$DESC$,
pilar_associado=$DESC$Corpo$DESC$,
continente=ARRAY[$DESC$Thornmarak$DESC$]::text[],
habitat=$DESC$As baixadas úmidas e as ravinas cobertas de Thornmarak, onde a água corre e a carne podre nunca falta. Vive em toca de barranco perto de trilha de caça.$DESC$,
comportamento=$DESC$Caça por fome simples e bruta, e o que o faz temível é que não para. Cortado, fecha. Queimado, ainda vem. Avança sobre a presa sem cuidado com o próprio corpo, porque o corpo se conserta sozinho, e o que para a maioria dos bichos não para este.$DESC$,
organizacao=$DESC$Sozinho, ou uma fêmea com cria, cada um dono de um trecho de barranco.$DESC$,
perigo=$DESC$Ameaça$DESC$,
behavior_archetype=$DESC$predator$DESC$,
morale_modifier=2,
morale_immune=false,
epigrafe=$DESC$Cortei o braço dele fora. Cravou os dentes assim mesmo. O braço no chão ainda se mexia procurando o resto.$DESC$,
descricao=$DESC$É alto e magro e curvado, de pele cinza e verde que se cura quase tão rápido quando se corta. Caça nas baixadas de Thornmarak por fome crua, e avança sem medo do próprio sangue, porque o sangue para e a ferida fecha. Membro cortado se mexe sozinho e às vezes brota de novo. Por isso não recua: sabe, do jeito burro dele, que aguenta mais do que quem o enfrenta. Fala, em uma língua grossa de poucas palavras, mas o que diz é só fome e ameaça.$DESC$,
supersticao_popular=$DESC$Nas baixadas de Thornmarak, dizem que a coisa cinza não morre de ferro, e que é perda de tempo cortá-la, porque ela costura de volta. O conselho de quem caça é levar fogo e óleo, e queimar o corte para ele não fechar, e não brigar de perto se não houver chama à mão. Contam que ácido e fogo são o único jeito, e que membro decepado que se deixa no chão volta procurando o corpo.$DESC$,
sinais_presenca=$DESC$Carcaças de caça pela metade, com marcas de dente grande, largadas perto de barranco. Trilhas de pegada longa e funda na lama mole. Restos de membro seco, descartados, em volta da toca. O cheiro de podre adocicado da toca dele. Galhos e ossos quebrados num raio largo, sem cuidado, como passagem aberta na bruta.$DESC$,
fraqueza_conhecida=$DESC$O fogo e o ácido. O povo sabe que o corte se fecha, mas que o que é queimado ou roído por ácido não volta a colar. Cauterizar a ferida funciona; cortar sem queimar só o deixa mais bravo. A regra é não enfrentá-lo sem chama, e mirar para queimar, não só para cortar.$DESC$,
fraqueza_real=$DESC$A cura dele tem um limite e um custo: refazer carne gasta fome, e faminto e seco ele se cura mais devagar. Negar-lhe comida, cansá-lo, e fechar as feridas dele com fogo antes que colem, esgota o que parecia sem fim. Ele é burro e teimoso, não eterno: o que o ferro abre e o fogo sela não se refaz, e bastante disso o derruba como qualquer bicho. Quem mantém a chama e a paciência vence; quem só corta, alimenta a teima dele.$DESC$,
descricao_sensorial=$DESC$O som é um resmungo grosso e o estalo úmido de carne que se refaz. O cheiro é de podre doce e de barro, da toca e do bicho. Ao toque, a pele é fria, elástica e grossa, e cede e volta sob a mão. Aos olhos, é uma figura alta e curva, cinza-esverdeada, de braços longos e feridas que se fecham enquanto se olha.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Caça das baixadas e o que se atrasa na trilha$DESC$, $DESC$Viajantes solitários perto do barranco dele$DESC$),
'predador', jsonb_build_array($DESC$Quem traz fogo e ácido e tem paciência de cansá-lo$DESC$),
'competidor', jsonb_build_array($DESC$Outros brutos das baixadas de Thornmarak que disputam carcaça e toca$DESC$, $DESC$Tronco-Sarnento$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presença dele diz que aquele trecho de baixada é farto de caça e de carniça, e que o caçador ali não recua.$DESC$,
'evitado_por', jsonb_build_array($DESC$Caçadores que não entram no barranco dele sem fogo na mão$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$Carne que ainda estremece e tenta refazer-se$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Material (estudo da cura rápida, isca que dura)$DESC$, 'risco', $DESC$Mexe na mão; apodrece mal se não queimada na hora certa.$DESC$),
jsonb_build_object('material', $DESC$Couro grosso e elástico do dorso$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (correia, armadura leve, bota)$DESC$, 'risco', $DESC$Fede; precisa de muita cura.$DESC$),
jsonb_build_object('material', $DESC$Dentes e garras longos$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (ponta, anzol, adorno)$DESC$, 'risco', $DESC$Nenhum.$DESC$),
jsonb_build_object('material', $DESC$Gordura rançosa da toca$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (óleo grosso, graxa)$DESC$, 'risco', $DESC$Nenhum além do cheiro.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Um resmungo grosso e o estalo úmido de carne se refazendo.$DESC$,
'cheiro', $DESC$Podre doce e barro, da toca e do bicho.$DESC$,
'quer', $DESC$Comer e seguir comendo, sem se importar com o próprio corpo, porque o corpo volta.$DESC$,
'tipo_perigo', $DESC$Persistente$DESC$,
'falas_exemplo', jsonb_build_array($DESC$Corta. Corta de novo. Volta. Sempre volta.$DESC$, $DESC$Tua carne para. Minha não. Tu cansa primeiro.$DESC$, $DESC$(registro: língua grossa de gigante, poucas palavras, ditas devagar entre rosnados; só fome e ameaça, nada mais)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Presa ferida ou atrasada cruza o trecho dele$DESC$, $DESC$Alguém invade o barranco onde está a toca ou a cria$DESC$, $DESC$O cheiro de sangue chega e a fome aperta$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Recua, raro, quando o fogo o queima além do que ele cura$DESC$, $DESC$Some no barranco quando faminto e seco demais para refazer-se$DESC$, $DESC$Larga a presa e foge quando o ácido o rói sem parar$DESC$),
'descoberta_fazendo', $DESC$Rasgando uma carcaça no barranco, ou seguindo um rastro de sangue pela lama, sem cuidado com cortes próprios.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Cansá-lo e negar-lhe comida, porque seco ele cura devagar$DESC$, $DESC$Manter fogo na mão e selar as feridas dele antes que colem$DESC$, $DESC$Atraí-lo para longe da toca com carniça e contornar o trecho$DESC$, $DESC$Não cortá-lo sem queimar, para não alimentar a teima dele$DESC$)
),
status_conversao='canonizada'
WHERE id=1180;

-- 1065 Coveiro-Bruto | Sombra | ambusher | Condicional | Ameaca | Kethara | Eco | muda | Cicatricial -> teto Raro
UPDATE ref_criaturas SET
nome=$DESC$Coveiro-Bruto$DESC$,
nome_ptbr=$DESC$Coveiro-Bruto$DESC$,
slug=$DESC$coveiro-bruto$DESC$,
origem=$DESC$Cicatricial$DESC$,
andar_primario=$DESC$Eco$DESC$,
pilar_associado=$DESC$Sombra$DESC$,
continente=ARRAY[$DESC$Kethara$DESC$]::text[],
habitat=$DESC$As necrópoles de areia de Kethara, câmaras funerárias e poços de tumba onde os grandes foram enterrados com os seus servos. Fica no escuro, entre os que guarda.$DESC$,
comportamento=$DESC$Não vagueia. Fica parado no breu da câmara, no meio dos sepultados, imóvel como mais um deles, até que alguém perturbe o lugar. Aí o corpo enorme se move de uma vez e quebra o intruso contra a parede. Quem só passa e não mexe, às vezes, ele deixa passar.$DESC$,
organizacao=$DESC$Sozinho ou em pequeno número, cada câmara com o seu guardião pesado.$DESC$,
perigo=$DESC$Ameaça$DESC$,
behavior_archetype=$DESC$ambusher$DESC$,
morale_modifier=0,
morale_immune=true,
epigrafe=$DESC$Contei seis corpos secos sentados na parede. Quando toquei o ouro, o sétimo levantou.$DESC$,
descricao=$DESC$Foi um servo grande, enterrado de pé com o seu senhor, e o que sobrou dele é um resto pesado que ainda guarda a tumba. Fica imóvel no escuro da câmara, no meio dos sepultados secos, sem se distinguir deles, até que mãos mexam no que não devem. Então o corpo todo se ergue de uma vez, lento mas brutal, e esmaga o que está ao alcance. Não persegue longe; volta ao posto quando o intruso foge ou cai. É da Cicatriz da morte que veio, e à morte que ainda serve.$DESC$,
supersticao_popular=$DESC$Em Kethara, os ladrões de tumba dizem que nem todo corpo sentado na parede da câmara está parado de vez, e que o maior deles costuma ser o que vela. O conselho é não tocar o ouro do morto sem olhar duas vezes os que o cercam, e sair pelo mesmo caminho sem virar as costas, porque o guardião acorda com a mão na oferenda e dorme de novo quando ela fica onde estava.$DESC$,
sinais_presenca=$DESC$Um corpo seco grande demais entre os outros, sentado de modo bom demais para ser só osso caído. Marcas de esmagamento nas paredes da câmara, antigas e secas. Ossos de ladrões anteriores espalhados perto da oferenda. O cheiro de pó e resina velha de embalsamar. O silêncio pesado de uma câmara que parece esperar que se mexa em algo.$DESC$,
fraqueza_conhecida=$DESC$Não mexer. O povo sabe que o guardião acorda com a transgressão, não com a presença, e que quem passa sem tocar o que ele guarda costuma passar inteiro. Tirado isso, ele é lento; quem o acorda e corre, com a saída já decorada, escapa do esmagamento, porque ele não persegue muito longe da tumba.$DESC$,
fraqueza_real=$DESC$Ele guarda um ponto, e fora desse ponto não tem vontade própria. Tirado da câmara, ou afastado o bastante da oferenda, perde o motivo e para. É lento e burro: quem o leva a girar, a errar o golpe pesado, e a se afastar do que protege, o desarma sem matá-lo. E como acorda só com a transgressão, a verdade mais simples é a mais funda: deixe o que é dele onde está, e o guardião volta a ser um morto sentado na parede.$DESC$,
descricao_sensorial=$DESC$O som é o ranger seco de juntas paradas há muito e o baque surdo do golpe na pedra. O cheiro é de pó, resina e linho velho de embalsamar. Ao toque, é seco, duro e frio, como couro curtido sobre lenho. Aos olhos, é um corpo grande e ressecado, igual aos outros sepultados, até o instante em que se ergue e enche a câmara.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Ladrões de tumba que tocam a oferenda$DESC$, $DESC$Quem perturba o sono dos sepultados na câmara$DESC$),
'predador', jsonb_build_array($DESC$Nada o caça; ele para quando o que guarda volta ao lugar$DESC$),
'competidor', jsonb_build_array($DESC$Outros restos das necrópoles de Kethara que disputam câmara e oferenda$DESC$, $DESC$Carraça-Insone$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presença dele diz que aquela tumba ainda tem o que valha guardar, e que mexer nela cobra caro.$DESC$,
'evitado_por', jsonb_build_array($DESC$Ladrões de tumba que saem sem tocar o ouro e sem virar as costas$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$Resina de embalsamar que ainda prende a Cicatriz ao corpo$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Eco / amarras que prendem um resto a um lugar ou a um dever)$DESC$, 'risco', $DESC$Prende a quem a usa mal; gruda intenções que não eram suas.$DESC$),
jsonb_build_object('material', $DESC$Mão grande e ressecada, ainda firme$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Sombra / focos de guarda e de esmagar)$DESC$, 'risco', $DESC$Fecha sobre o que segura sem soltar.$DESC$),
jsonb_build_object('material', $DESC$Linho funerário e adornos secos$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (pano antigo, ornamento)$DESC$, 'risco', $DESC$Frágil; esfarela.$DESC$),
jsonb_build_object('material', $DESC$Pó de tumba e lascas de osso$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (refugo, prova de saque)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Ranger seco de juntas paradas e o baque surdo do golpe na pedra.$DESC$,
'cheiro', $DESC$Pó, resina e linho velho de embalsamar.$DESC$,
'quer', $DESC$Que ninguém perturbe o que ele vela. Esmagar quem mexe e voltar ao posto.$DESC$,
'tipo_perigo', $DESC$Condicional$DESC$,
'falas_exemplo', 'null'::jsonb,
'gatilhos_agressao', jsonb_build_array($DESC$Mãos tocam a oferenda ou o ouro do morto$DESC$, $DESC$Alguém perturba os sepultados ou abre o que estava selado$DESC$, $DESC$Um intruso fica ao alcance do braço dentro da câmara$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Não foge; volta ao posto quando o intruso recua$DESC$, $DESC$Para quando a oferenda é deixada onde estava$DESC$, $DESC$Cessa o avanço longe da câmara, sem perseguir muito$DESC$),
'descoberta_fazendo', $DESC$Imóvel no escuro da câmara funerária, no meio dos sepultados secos, esperando que alguém mexa no que ele guarda.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Passar sem tocar a oferenda e sair pelo mesmo caminho$DESC$, $DESC$Devolver o que se pegou ao lugar, e vê-lo voltar a parar$DESC$, $DESC$Acordá-lo e correr com a saída decorada, longe do que ele guarda$DESC$, $DESC$Atraí-lo para fora da câmara e contornar a oferenda por outro vão$DESC$)
),
status_conversao='canonizada'
WHERE id=1065;

-- 2354 Fagulha-Ossea | Arcano | lurker | Oculto | Ameaca | Vyrkhor | Eco | muda | Cicatricial -> teto Raro
UPDATE ref_criaturas SET
nome=$DESC$Fagulha-Óssea$DESC$,
nome_ptbr=$DESC$Fagulha-Óssea$DESC$,
slug=$DESC$fagulha-ossea$DESC$,
origem=$DESC$Cicatricial$DESC$,
andar_primario=$DESC$Eco$DESC$,
pilar_associado=$DESC$Arcano$DESC$,
continente=ARRAY[$DESC$Vyrkhor$DESC$]::text[],
habitat=$DESC$Os campos de pedra e as ruínas geladas de Vyrkhor onde caíram bestas grandes de eras mortas. Jaz entre outros ossos, indistinto, até alguém pisar perto.$DESC$,
comportamento=$DESC$Fica deitado e quieto, parecendo só um esqueleto enorme de bicho antigo. Mas a velha tempestade que o matou ficou presa nos ossos, e quando carne quente chega perto, a carga salta. Não persegue: descarrega sobre quem se aproxima, e volta a parecer osso morto, recarregando devagar no silêncio.$DESC$,
organizacao=$DESC$Sozinho, um único arcabouço carregado num campo de ossos.$DESC$,
perigo=$DESC$Ameaça$DESC$,
behavior_archetype=$DESC$lurker$DESC$,
morale_modifier=0,
morale_immune=true,
epigrafe=$DESC$Era só uma carcaça de bicho velho. Encostei a lança para me firmar. O estouro me jogou três passos para trás.$DESC$,
descricao=$DESC$É o arcabouço de uma besta enorme de outra era, morta por um raio que nunca a deixou de todo. A carga ficou nos ossos como vestígio, dormente, e o esqueleto jaz entre outros como mais um morto antigo. Quando carne quente chega ao alcance, a fagulha presa salta, súbita, e queima e atira longe quem está perto. Não corre atrás de ninguém; é uma armadilha que não foi armada por mãos, só esquecida ali. Depois do estouro, volta a parecer osso e recarrega no frio, paciente, para o próximo que pisar perto.$DESC$,
supersticao_popular=$DESC$Em Vyrkhor, dizem que certos ossos de bicho grande ainda guardam o raio que os matou, e que tocá-los é chamar o estouro. O conselho de quem cruza os campos de ossos é não se firmar em carcaça grande nem dormir encostado nela, e jogar pedra ou água antes de chegar perto de um arcabouço solitário, porque o que parece morto pode ainda morder com luz.$DESC$,
sinais_presenca=$DESC$Um esqueleto grande sozinho, sem os outros ossos espalhados de uma morte comum. Pelos do braço que se arrepiam perto dele, sem vento. Um estalo seco e azulado correndo pelos ossos de quando em quando. Marcas de queimadura no chão e em ossos vizinhos. O cheiro agudo de ar queimado onde não houve fogo.$DESC$,
fraqueza_conhecida=$DESC$Não encostar. O povo sabe que o estouro vem do contato e da proximidade, e que quem não se aproxima não leva o golpe. Jogar pedra ou água de longe descarrega a coisa em segurança; depois dela soltar a carga, há um tempo de osso morto em que ela é inofensiva, e é nessa janela que se quebra ou se passa.$DESC$,
fraqueza_real=$DESC$A carga é única por descarga e leva tempo para voltar; gasta a fagulha de longe, com pedra ou água, e o arcabouço fica inerte, só osso, até recarregar. Ele não persegue, não recua, não pensa: só guarda e solta. Aterramento simples, uma haste de metal cravada e ligada ao chão, ou água corrente em volta, suga a carga sem perigo. Quem o descarrega à distância e age na janela morta o desmonta sem nunca levar o estouro.$DESC$,
descricao_sensorial=$DESC$O som é um estalo seco e o zunido baixo de carga subindo antes do estouro. O cheiro é de ar queimado e metal, agudo e seco. Ao toque, o osso é frio e formiga na pele um instante antes de saltar. Aos olhos, é um esqueleto enorme e amarelado de bicho antigo, com fios azulados correndo pelas juntas de vez em quando.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Quem se firma ou dorme encostado no arcabouço$DESC$, $DESC$Bichos que cruzam o alcance da carga sem saber$DESC$),
'predador', jsonb_build_array($DESC$Quem o descarrega de longe e o aterra antes de tocá-lo$DESC$),
'competidor', jsonb_build_array($DESC$Outras coisas carregadas das ruínas de Vyrkhor que negam o mesmo campo$DESC$, $DESC$Lasca-Gélida$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presença dele diz que ali caiu uma besta de outra era sob tempestade, e que o campo de ossos ainda morde.$DESC$,
'evitado_por', jsonb_build_array($DESC$Andarilhos de Vyrkhor que não se firmam em carcaça grande nem dormem encostados$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$Osso que ainda retém a carga da velha tempestade$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Arcano / focos de raio e de descarga guardada)$DESC$, 'risco', $DESC$Solta o estouro na mão que o move sem aterrar.$DESC$),
jsonb_build_object('material', $DESC$Marfim antigo das presas$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Arcano / cabos e hastes que conduzem a carga)$DESC$, 'risco', $DESC$Formiga e queima se ainda carregado.$DESC$),
jsonb_build_object('material', $DESC$Lascas de osso fóssil$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (talha, pó, curiosidade)$DESC$, 'risco', $DESC$Nenhum, depois de descarregado.$DESC$),
jsonb_build_object('material', $DESC$Fragmentos amarelados comuns$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (refugo, cola de osso)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Estalo seco e zunido baixo de carga subindo antes do estouro.$DESC$,
'cheiro', $DESC$Ar queimado e metal, agudo e seco.$DESC$,
'quer', $DESC$Nada; só guarda a carga e a solta sobre o que chega quente ao alcance.$DESC$,
'tipo_perigo', $DESC$Oculto$DESC$,
'falas_exemplo', 'null'::jsonb,
'gatilhos_agressao', jsonb_build_array($DESC$Carne quente toca ou se encosta no arcabouço$DESC$, $DESC$Alguém pisa dentro do alcance curto da carga$DESC$, $DESC$Metal aproximado fecha o caminho da fagulha$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Não foge; volta a parecer osso morto após descarregar$DESC$, $DESC$Fica inerte na janela morta enquanto recarrega$DESC$, $DESC$Nunca persegue; permanece onde jaz$DESC$),
'descoberta_fazendo', $DESC$Deitado entre ossos num campo gelado, indistinto de uma carcaça antiga, carregado e à espera de calor próximo.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Descarregar a fagulha de longe com pedra ou água antes de chegar perto$DESC$, $DESC$Aterrar a carga com haste de metal cravada no chão$DESC$, $DESC$Não se firmar nem dormir encostado no arcabouço solitário$DESC$, $DESC$Passar largo do esqueleto grande e isolado, fora do alcance da carga$DESC$)
),
status_conversao='canonizada'
WHERE id=2354;

-- 2030 Geleira-Morta | Espirito | controller | Ambiental | Letal | Voranthar | Eco | muda | Cicatricial -> teto Raro
UPDATE ref_criaturas SET
nome=$DESC$Geleira-Morta$DESC$,
nome_ptbr=$DESC$Geleira-Morta$DESC$,
slug=$DESC$geleira-morta$DESC$,
origem=$DESC$Cicatricial$DESC$,
andar_primario=$DESC$Eco$DESC$,
pilar_associado=$DESC$Espírito$DESC$,
continente=ARRAY[$DESC$Voranthar$DESC$]::text[],
habitat=$DESC$As ruínas do norte morto de Voranthar, salões caídos onde um frio antigo nunca saiu. Onde ela está, a água vira gelo e o ar pesa.$DESC$,
comportamento=$DESC$Move-se pouco e devagar; o que faz o trabalho é o frio que a cerca. O ar em volta dela gela, o chão escorrega, o fôlego some, e quem entra no salão dela perde força só por estar ali. O olhar parado dela aprofunda o gelo onde mira. Não corre atrás: deixa o frio prender, e então o golpe lento alcança quem já não consegue fugir.$DESC$,
organizacao=$DESC$Sozinha, dona de um salão que ela mantém congelado.$DESC$,
perigo=$DESC$Letal$DESC$,
behavior_archetype=$DESC$controller$DESC$,
morale_modifier=0,
morale_immune=true,
epigrafe=$DESC$Não foi ela que me pegou. Foi o salão. Meus pés gelaram no chão e eu vi ela vir, devagar, sabendo que eu não corria.$DESC$,
descricao=$DESC$É o arcabouço enorme de um gigante do gelo, e o frio que o matou nunca o largou; agora esse frio é a arma. Onde ela está, o salão inteiro congela: a água vira pedra, o chão fica liso, o ar rouba o calor do corpo, e o passo que devia ser fácil vira luta contra o tremor. Ela quase não se mexe. Deixa o frio prender o intruso, mira nele o olhar gelado que aprofunda a casca de gelo, e alcança, sem pressa, quem o salão já segurou. Vem da Cicatriz de uma morte gelada, e governa o lugar como dona do próprio inverno.$DESC$,
supersticao_popular=$DESC$No norte morto de Voranthar, dizem que há salões onde o inverno tem corpo, e que entrar neles é entregar o calor pouco a pouco. O conselho é não cruzar salão que gela do nada sem fogo e roupa grossa, e não parar quieto lá dentro, porque o frio prende quem para. Contam que correr e manter o sangue quente é o jeito, e que quem se demora no salão dela amanhece de pé, congelado de uma vez.$DESC$,
sinais_presenca=$DESC$Um salão que gela de repente, com geada subindo pelas paredes onde fora não há inverno. O fôlego que vira fumaça e o frio que morde sem vento. Água parada virada em gelo liso e grosso. Vultos de antigos viajantes congelados de pé pelo salão. O silêncio rachado só pelo estalo do gelo se firmando.$DESC$,
fraqueza_conhecida=$DESC$O fogo e o movimento. O povo sabe que ela governa pelo frio, e que chama e roupa grossa seguram o calor que ela quer roubar. Não parar é a regra: quem se mexe e mantém o sangue quente resiste ao aperto do salão. Fogo grande perto dela enfraquece o domínio do gelo, e abre passagem para sair.$DESC$,
fraqueza_real=$DESC$A força dela é o salão congelado; tirada do frio que a cerca, ela é só um arcabouço lento e quebradiço. Calor bastante — fogo de verdade, e não tocha mirrada — derrete o domínio dela e a deixa exposta e rígida. Ela não persegue para fora do seu inverno, nem recua: serve ao próprio frio. Quem leva calor para dentro do salão, mantém o corpo quente e em movimento, e a obriga a lutar sem o gelo, parte o gigante morto como se parte gelo velho.$DESC$,
descricao_sensorial=$DESC$O som é o estalo do gelo que se firma e um gemido baixo de vento parado. O cheiro é de neve e pedra molhada, limpo e cortante. Ao toque, tudo perto dela queima de frio, e o metal cola na pele. Aos olhos, é um esqueleto de gigante coberto de geada, parado num salão branco de gelo, com um brilho frio no fundo das órbitas.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Viajantes que cruzam ou param no salão congelado$DESC$, $DESC$O calor e o fôlego de quem entra, roubados pouco a pouco$DESC$),
'predador', jsonb_build_array($DESC$O fogo de verdade, que derrete o domínio dela e a expõe$DESC$),
'competidor', jsonb_build_array($DESC$Outras presenças do norte morto de Voranthar que disputam salão e silêncio$DESC$, $DESC$Mágoa-de-Pedra$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presença dela diz que aquele salão guarda um frio antigo de morte, e que demorar ali custa o calor do corpo.$DESC$,
'evitado_por', jsonb_build_array($DESC$Viajantes que não cruzam salão que gela do nada sem fogo e sem pressa de sair$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$Lasca de osso que guarda o frio que não derrete$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Eco / focos de frio, de gelo e de roubo de calor)$DESC$, 'risco', $DESC$Gela a mão até a carne; queima de frio quem a porta sem proteção.$DESC$),
jsonb_build_object('material', $DESC$Geada perpétua raspada do arcabouço$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Eco / conservas, e venenos que entorpecem pelo frio)$DESC$, 'risco', $DESC$Não derrete em lugar quente; congela o que toca.$DESC$),
jsonb_build_object('material', $DESC$Osso grande de gigante, fóssil de frio$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (talha pesada, viga, troféu)$DESC$, 'risco', $DESC$Quebradiço no frio.$DESC$),
jsonb_build_object('material', $DESC$Lascas e pó de osso comum$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (refugo, cal de osso)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$O estalo do gelo se firmando e um gemido baixo de vento parado.$DESC$,
'cheiro', $DESC$Neve e pedra molhada, limpo e cortante.$DESC$,
'quer', $DESC$Manter o salão dela congelado e roubar o calor de quem entra, sem sair do próprio inverno.$DESC$,
'tipo_perigo', $DESC$Ambiental$DESC$,
'falas_exemplo', 'null'::jsonb,
'gatilhos_agressao', jsonb_build_array($DESC$Alguém entra no salão e o frio começa a prendê-lo$DESC$, $DESC$Um intruso para quieto, deixando o gelo subir pelos pés$DESC$, $DESC$Fogo é trazido para dentro e ameaça o domínio do frio$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Não foge; recua o avanço quando o calor invade o salão$DESC$, $DESC$Aquieta-se de novo quando o intruso sai do seu inverno$DESC$, $DESC$Nunca persegue para fora do salão que governa$DESC$),
'descoberta_fazendo', $DESC$Quase imóvel no centro de um salão congelado, mantendo o frio e medindo quem o atravessa.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Atravessar o salão depressa, com fogo e roupa grossa, sem parar$DESC$, $DESC$Acender fogo de verdade para enfraquecer o domínio do gelo e passar$DESC$, $DESC$Manter o sangue quente e em movimento, negando ao frio o aperto$DESC$, $DESC$Contornar o salão congelado por outra rota da ruína$DESC$)
),
status_conversao='canonizada'
WHERE id=2030;

-- 511 Olho-Avido | Engenho | artillery | Direto | Letal | Voranthar | Margem | FALA | Marginal -> teto Raro
UPDATE ref_criaturas SET
nome=$DESC$Olho-Ávido$DESC$,
nome_ptbr=$DESC$Olho-Ávido$DESC$,
slug=$DESC$olho-avido$DESC$,
origem=$DESC$Marginal$DESC$,
andar_primario=$DESC$Margem$DESC$,
pilar_associado=$DESC$Engenho$DESC$,
continente=ARRAY[$DESC$Voranthar$DESC$]::text[],
habitat=$DESC$As ruínas de Voranthar onde a Margem está fina, esgotos de cidade morta e câmaras fundas. Paira no escuro, guardando o que junta.$DESC$,
comportamento=$DESC$Flutua, ganancioso e calculista, e ataca de longe com feixes que saltam do olho grande e dos olhos menores na coroa. Mede a sala, escolhe a ordem dos golpes, e prende quem se aproxima com um olhar que paralisa. Quer o que brilha, e mata para juntar mais, mas foge se a conta vira contra ele.$DESC$,
organizacao=$DESC$Solitário, cada um sobre o seu tesouro mesquinho.$DESC$,
perigo=$DESC$Letal$DESC$,
behavior_archetype=$DESC$artillery$DESC$,
morale_modifier=1,
morale_immune=false,
epigrafe=$DESC$A coisa não me deixou chegar perto. Cada vez que dei um passo, um feixe abria o chão à minha frente, e ela ria de cima.$DESC$,
descricao=$DESC$É uma coisa da Margem que paira no ar, pouco mais que uma boca e um olho grande, com olhos menores numa coroa que disparam feixes. Vive nas ruínas fundas de Voranthar, onde a Margem é fina, e junta o que brilha como quem faz tesouro. Luta de longe e de cima: castiga cada passo do intruso com um raio, prende com um olhar que trava o corpo, e mede tudo com frieza de quem calcula o ganho. É vaidoso e ávido, e por isso recua quando a presa custa mais do que vale. Não é fome; é cobiça com método.$DESC$,
supersticao_popular=$DESC$Em Voranthar, dizem que há coisas que voam nos esgotos mortos e guardam ouro que ninguém deveria querer. O conselho de quem desce ali é não cobiçar o brilho que a coisa junta, e não encará-la de frente, porque o olhar dela trava as pernas. Contam que ela é covarde por trás da arrogância, e que quem a faz gastar à toa e não cede ao medo costuma vê-la fugir para o escuro.$DESC$,
sinais_presenca=$DESC$Marcas de queimadura e cortes finos riscando as paredes de uma câmara, em leques que partem de um ponto alto. Um monte de moedas, lascas e quinquilharias brilhantes amontoado num canto, guardado bem demais. O zumbido baixo de algo que paira parado no escuro. Ossos de saqueadores anteriores no chão da câmara. A sensação de ser observado e medido do alto.$DESC$,
fraqueza_conhecida=$DESC$Não encarar e não cobiçar. O povo sabe que o olhar dela trava, e que quem desvia a vista e não corre atrás do tesouro perde a metade do perigo. Cobertura contra os feixes — pilar, escudo, parede — corta o castigo à distância, que é a arma principal dela. Chegar perto sob proteção a tira do conforto da altura.$DESC$,
fraqueza_real=$DESC$Por trás da arrogância, ela é covarde e calculista: não morre por orgulho, foge quando a conta fica ruim. Negar-lhe o jogo dela — fechar a distância sob cobertura, não dar as costas ao brilho, fazê-la gastar os feixes à toa — esgota a vantagem e desperta o medo que ela esconde. Pressionada de perto, sem altura e sem o seu tesouro a defender, ela larga tudo e some no escuro. Quem não a teme nem a cobiça a derrota antes do ferro.$DESC$,
descricao_sensorial=$DESC$O som é uma voz fina e sibilante e o zunido dos feixes rasgando o ar. O cheiro é de mofo e metal, de esgoto velho e moeda suja. Ao toque, é uma coisa fria e flácida sob a casca dura do olho, repulsiva na mão. Aos olhos, é uma esfera escura que paira, com um olho grande e ávido e uma coroa de olhos menores que se viram para mirar.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Saqueadores que descem às câmaras fundas atrás de brilho$DESC$, $DESC$Coisas menores da Margem que ela domina e despoja$DESC$),
'predador', jsonb_build_array($DESC$Quem fecha a distância sob cobertura e a faz fugir antes do ferro$DESC$),
'competidor', jsonb_build_array($DESC$Outras inteligências da Margem em Voranthar que disputam tesouro e câmara$DESC$, $DESC$Miolo-Regente$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presença dele diz que a Margem está fina naquela câmara, e que há brilho juntado ali a peso de mortes.$DESC$,
'evitado_por', jsonb_build_array($DESC$Saqueadores que não cobiçam o tesouro dele nem o encaram de frente$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$O olho grande, ainda úmido, que dispara o feixe$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Engenho / focos de feixe à distância e de olhar que trava o corpo)$DESC$, 'risco', $DESC$Mira sozinho quem o segura sem preparo; trava a mão que o porta.$DESC$),
jsonb_build_object('material', $DESC$Olhos menores da coroa$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Engenho / engenhos de mira e de leque de raios)$DESC$, 'risco', $DESC$Descarregam ao acaso se mal montados.$DESC$),
jsonb_build_object('material', $DESC$Tesouro mesquinho que ele juntou$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (moeda, lasca de valor, quinquilharia)$DESC$, 'risco', $DESC$Atrai outros que cobiçam o mesmo.$DESC$),
jsonb_build_object('material', $DESC$Casca dura e flácida do corpo$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (refugo, curiosidade)$DESC$, 'risco', $DESC$Apodrece rápido; fede.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Uma voz fina e sibilante e o zunido dos feixes rasgando o ar.$DESC$,
'cheiro', $DESC$Mofo e metal, de esgoto velho e moeda suja.$DESC$,
'quer', $DESC$Juntar o que brilha e guardar o seu tesouro, matando de longe quem ousa chegar, e fugir se o custo subir.$DESC$,
'tipo_perigo', $DESC$Direto$DESC$,
'falas_exemplo', jsonb_build_array($DESC$Esse ouro é meu. Tudo que brilha aqui é meu. Dê mais um passo e eu te abro ao meio.$DESC$, $DESC$Tão pequeno, e tão ganancioso quanto eu. A diferença é que eu vejo melhor.$DESC$, $DESC$(registro: voz fina e sibilante, em fala da Margem e em comum estropiado; arrogante de longe, súplice quando encurralada)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Alguém se aproxima do tesouro que ele guarda$DESC$, $DESC$Um intruso lhe dá as costas ou fica exposto sem cobertura$DESC$, $DESC$Algo brilhante entra na câmara e desperta a cobiça$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Foge quando a distância é fechada e os feixes não bastam$DESC$, $DESC$Larga o tesouro e some no escuro quando a conta vira contra ele$DESC$, $DESC$Recua para o alto e para o vão fundo ao primeiro ferimento sério$DESC$),
'descoberta_fazendo', $DESC$Pairando no escuro de uma câmara funda, sobre um monte de brilho, medindo do alto quem desceu.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Não cobiçar o tesouro dele e recuar pela mesma rota$DESC$, $DESC$Fechar a distância sob cobertura para tirá-lo do conforto da altura$DESC$, $DESC$Desviar o olhar para não travar e não dar as costas ao brilho$DESC$, $DESC$Fazê-lo gastar os feixes à toa até o medo falar mais alto que a cobiça$DESC$)
),
status_conversao='canonizada'
WHERE id=511;

-- 564 Serra-Dorsal | Corpo | defender | Condicional | Ameaca | Thornmarak | Superficie | muda | Natural -> teto Notavel
UPDATE ref_criaturas SET
nome=$DESC$Serra-Dorsal$DESC$,
nome_ptbr=$DESC$Serra-Dorsal$DESC$,
slug=$DESC$serra-dorsal$DESC$,
origem=$DESC$Natural$DESC$,
andar_primario=$DESC$Superfície$DESC$,
pilar_associado=$DESC$Corpo$DESC$,
continente=ARRAY[$DESC$Thornmarak$DESC$]::text[],
habitat=$DESC$As baixadas largas e os matagais de Thornmarak, perto de água, onde pasta em paz. Move-se pouco e devagar pelo mesmo trecho a vida toda.$DESC$,
comportamento=$DESC$É herbívoro e manso, e só quer comer e ser deixado. Não caça e não persegue. Mas se acuado, ou se a cria é ameaçada, gira o corpo enorme e bate com a cauda de pontas, e o golpe quebra osso e arremessa. O perigo dele é todo defesa: quem não o provoca passa ao lado sem susto.$DESC$,
organizacao=$DESC$Sozinho ou em pequeno bando frouxo perto da água.$DESC$,
perigo=$DESC$Ameaça$DESC$,
behavior_archetype=$DESC$defender$DESC$,
morale_modifier=1,
morale_immune=false,
epigrafe=$DESC$O bicho nem olhou para nós enquanto comia. Foi só o rapaz cutucar a cria que o mundo virou cauda e pontas.$DESC$,
descricao=$DESC$É um casco grande e lento, de placas nas costas e uma cauda armada de pontas que serram o ar. Pasta nas baixadas de Thornmarak e não quer briga com ninguém. Quem o vê comendo pensa que é presa fácil pelo tamanho, e quem cutuca aprende o contrário: ele gira a massa toda e descarrega a cauda, e a cauda parte perna e joga homem longe. Não corre atrás depois; volta a comer. Todo o perigo dele é responder a quem o ameaça, e responder forte.$DESC$,
supersticao_popular=$DESC$Nas baixadas de Thornmarak, dizem que o bicho de placas é manso até deixar de ser, e que a culpa do estrago é sempre de quem mexeu. O conselho dos vaqueiros é passar largo da cauda e nunca chegar perto da cria, e não confundir lentidão com fraqueza, porque a cauda é rápida quando precisa. Contam que ele esquece o intruso assim que o intruso se afasta.$DESC$,
sinais_presenca=$DESC$Trechos de mato rapados rente, em faixas largas, onde ele pastou. Pegadas redondas e fundas perto da água. Árvores novas com a casca raspada na altura da cauda. Esterco grande em montes pelo caminho dele. O próprio vulto de placas, parado e comendo, sem se importar com quem chega, até chegar perto demais.$DESC$,
fraqueza_conhecida=$DESC$Não provocar. O povo sabe que ele só ataca acuado ou pela cria, e que basta dar espaço e passar pelo lado de fora do alcance da cauda. É lento; quem precisa enfrentá-lo fica fora do arco da cauda e o cansa, mas a regra mesmo é simplesmente não dar motivo.$DESC$,
fraqueza_real=$DESC$Ele é lento e só perigoso no arco da cauda; fora desse arco, e tirado o motivo, ele não é ameaça nenhuma. Atacar pela frente ou pelo flanco baixo, onde a cauda não alcança, e não cercar a cria, desarma quase todo o risco. E como o que o move é defesa, não fome, a saída mais barata é a mais óbvia: deixá-lo em paz com o seu pasto, e ele deixa o caminho livre.$DESC$,
descricao_sensorial=$DESC$O som é o ranger do mato sendo arrancado e o assobio da cauda cortando o ar. O cheiro é de capim mascado e barro de beira de água. Ao toque, as placas são ásperas e quentes de sol, duras como pedra rachada. Aos olhos, é um corpo baixo e largo de placas no dorso e uma cauda de pontas que se ergue devagar quando ele se irrita.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Mato, broto e folha das baixadas$DESC$, $DESC$Raiz tenra perto da água$DESC$),
'predador', jsonb_build_array($DESC$Predadores grandes que ousam a cria, e pagam caro pela cauda$DESC$),
'competidor', jsonb_build_array($DESC$Outros grandes pastadores de Thornmarak que disputam o mesmo trecho$DESC$, $DESC$Marfim-Pesado$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presença dele diz que aquela baixada é farta de pasto e de água, e mansa enquanto ninguém o provoca.$DESC$,
'evitado_por', jsonb_build_array($DESC$Vaqueiros que passam largo da cauda e nunca se metem com a cria$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$Ponta de cauda, óssea e serrada$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Material (ponta de maça, ferramenta, troféu)$DESC$, 'risco', $DESC$Corta na mão sem cuidado.$DESC$),
jsonb_build_object('material', $DESC$Placa dorsal grossa$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (escudo, telha, placa de armadura)$DESC$, 'risco', $DESC$Pesada.$DESC$),
jsonb_build_object('material', $DESC$Couro espesso do flanco$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (correia, forro)$DESC$, 'risco', $DESC$Nenhum.$DESC$),
jsonb_build_object('material', $DESC$Carne farta e dura$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (sustento, charque)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$O ranger do mato arrancado e o assobio da cauda cortando o ar.$DESC$,
'cheiro', $DESC$Capim mascado e barro de beira de água.$DESC$,
'quer', $DESC$Comer em paz e que o deixem comer. Defender o seu trecho e a sua cria, e nada além disso.$DESC$,
'tipo_perigo', $DESC$Condicional$DESC$,
'falas_exemplo', 'null'::jsonb,
'gatilhos_agressao', jsonb_build_array($DESC$Alguém se aproxima ou ameaça a cria$DESC$, $DESC$É acuado contra a água ou o mato sem rota de saída$DESC$, $DESC$Algo o cutuca ou o cerca dentro do arco da cauda$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Volta a pastar assim que o intruso se afasta$DESC$, $DESC$Afasta-se devagar para a água quando muito pressionado$DESC$, $DESC$Cessa o ataque quando a cria está a salvo e o caminho, livre$DESC$),
'descoberta_fazendo', $DESC$Pastando devagar numa baixada perto da água, indiferente a quem passa, com a cria por perto.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Passar largo, por fora do alcance da cauda, sem mexer com a cria$DESC$, $DESC$Dar espaço e deixá-lo pastar até ele liberar o caminho$DESC$, $DESC$Recuar devagar sem encurralá-lo contra a água ou o mato$DESC$, $DESC$Esperar o bando frouxo se mover sozinho para outro trecho$DESC$)
),
status_conversao='canonizada'
WHERE id=564;

-- 841 Laco-Calado | Sombra | ambusher | Oculto | Ameaca | Kethara | Superficie | muda | Natural -> teto Notavel
UPDATE ref_criaturas SET
nome=$DESC$Laço-Calado$DESC$,
nome_ptbr=$DESC$Laço-Calado$DESC$,
slug=$DESC$laco-calado$DESC$,
origem=$DESC$Natural$DESC$,
andar_primario=$DESC$Superfície$DESC$,
pilar_associado=$DESC$Sombra$DESC$,
continente=ARRAY[$DESC$Kethara$DESC$]::text[],
habitat=$DESC$Os oásis e as ruínas mornas de Kethara, vigas caídas e frestas de teto onde a sombra é funda. Caça à noite, perto de onde os homens dormem.$DESC$,
comportamento=$DESC$É uma serpente grande e calada que se enrosca no alto ou no escuro e espera. Não há aviso: ela cai ou avança sem ruído, enlaça o corpo e aperta até o fôlego acabar. Caça à noite, escolhe o que dorme ou se afasta do fogo, e some com a presa antes que alguém acorde.$DESC$,
organizacao=$DESC$Sozinha, fixa a um oásis ou a uma ruína com bom esconderijo.$DESC$,
perigo=$DESC$Ameaça$DESC$,
behavior_archetype=$DESC$ambusher$DESC$,
morale_modifier=0,
morale_immune=false,
epigrafe=$DESC$O sentinela não gritou. De manhã a corda da rede estava no chão e ele não. Só um rastro liso na areia, indo para o escuro.$DESC$,
descricao=$DESC$É uma serpente grossa e silenciosa, da cor da sombra e da pedra morna, que caça pelo aperto e não pela peçonha. Enrosca-se no alto de uma viga ou no breu de uma fresta, perto de onde os homens acampam, e espera o que se afasta do fogo. Cai sem som, enlaça, e fecha o laço até o ar faltar, e arrasta o corpo para o escuro antes que o acampamento perceba a falta. Não morde por veneno; mata pelo abraço calado. O perigo dela é nunca ser vista até já ter pegado.$DESC$,
supersticao_popular=$DESC$Em Kethara, dizem que o oásis tem dono à noite, e que o sentinela que cochila perto da água some sem grito. O conselho é não dormir longe do fogo nem encostado em viga ou parede de ruína, e olhar para cima antes de deitar, porque o laço cai do alto. Contam que ela teme o fogo e a luz, e que acampamento bem aceso e juntinho ela não ataca.$DESC$,
sinais_presenca=$DESC$Rastros lisos e largos na areia, indo de onde alguém sumiu para o escuro. Pele velha trocada, deixada numa fresta ou sob uma viga. Bichos do acampamento inquietos sem motivo à noite. O silêncio súbito do sentinela que não responde. Marcas de aperto e arraste onde havia uma rede ou um corpo.$DESC$,
fraqueza_conhecida=$DESC$O fogo e a companhia. O povo sabe que ela caça o que se afasta e o que dorme só, e que ficar perto do fogo e dos outros tira dela a presa. Olhar para o alto antes de deitar revela o laço enroscado. Luz e gente juntas afastam a coisa, que não ataca alvo aceso e cercado.$DESC$,
fraqueza_real=$DESC$A arma dela é a surpresa do escuro; vista a tempo, ela perde tudo. Uma vez enroscada num corpo, porém, o aperto é a morte: o jeito não é puxar contra a força dela, e sim atacar a cabeça ou desenrolar o laço pela ponta da cauda, onde a força é menor, antes que feche de todo. Ela não é teimosa: ferida e descoberta, larga a presa e foge para a fresta. Quem nega o escuro e a pega no descuido a vence; quem luta o aperto de frente, perde.$DESC$,
descricao_sensorial=$DESC$O som é quase nenhum: o roçar seco de escama e o estalo do aperto. O cheiro é de pó morno e bicho, almiscarado e seco. Ao toque, é fria e lisa e mais forte do que parece, e fecha sem soltar. Aos olhos, é um vulto grosso e escuro enroscado onde a sombra é funda, que só se vê quando já se moveu.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Sentinelas e dorminhocos que se afastam do fogo$DESC$, $DESC$Bichos do acampamento perto da água à noite$DESC$),
'predador', jsonb_build_array($DESC$Quem a vê a tempo, com fogo e companhia, e a fere antes do laço$DESC$),
'competidor', jsonb_build_array($DESC$Outros caçadores noturnos dos oásis de Kethara que disputam a mesma presa$DESC$, $DESC$Gargalho-Rubro$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presença dela diz que aquele oásis tem caça farta à noite, e que dormir longe do fogo ali é se oferecer.$DESC$,
'evitado_por', jsonb_build_array($DESC$Caravaneiros que dormem juntos e acesos e olham para o alto antes de deitar$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$Couro de escama largo e resistente$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Material (correia forte, bota, revestimento)$DESC$, 'risco', $DESC$Nenhum.$DESC$),
jsonb_build_object('material', $DESC$Músculo seco e fibroso do corpo$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (corda de tração, tendão)$DESC$, 'risco', $DESC$Nenhum.$DESC$),
jsonb_build_object('material', $DESC$Dentes recurvos de prender$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (anzol, ponta)$DESC$, 'risco', $DESC$Nenhum.$DESC$),
jsonb_build_object('material', $DESC$Pele trocada, seca$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (cola, refugo)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Quase nada: o roçar seco da escama e o estalo do aperto.$DESC$,
'cheiro', $DESC$Pó morno e bicho, almiscarado e seco.$DESC$,
'quer', $DESC$Pegar uma presa calada no escuro, apertar até o fôlego acabar e arrastá-la antes que percebam.$DESC$,
'tipo_perigo', $DESC$Oculto$DESC$,
'falas_exemplo', 'null'::jsonb,
'gatilhos_agressao', jsonb_build_array($DESC$Alguém se afasta do fogo e passa sob o esconderijo$DESC$, $DESC$Um corpo dorme só, longe da companhia$DESC$, $DESC$Presa desatenta cruza o alcance do bote calado$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Larga a presa e foge para a fresta quando descoberta e ferida$DESC$, $DESC$Recua para o escuro diante de fogo e gente juntos$DESC$, $DESC$Solta o laço e some quando o aperto não vence a tempo$DESC$),
'descoberta_fazendo', $DESC$Enroscada no alto de uma viga ou no breu de uma fresta, imóvel, esperando o que se afasta do fogo.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Dormir perto do fogo e da companhia, longe de viga e parede$DESC$, $DESC$Olhar para o alto antes de deitar e revelar o laço enroscado$DESC$, $DESC$Manter o acampamento aceso e juntinho, que ela não ataca$DESC$, $DESC$Se enlaçado, atacar a cabeça ou desenrolar pela cauda antes do aperto fechar$DESC$)
),
status_conversao='canonizada'
WHERE id=841;

-- 1976 Caustico-Lento | Arcano | controller | Ambiental | Ameaca | Thornmarak | Eco | muda | Cicatricial -> teto Raro
UPDATE ref_criaturas SET
nome=$DESC$Cáustico-Lento$DESC$,
nome_ptbr=$DESC$Cáustico-Lento$DESC$,
slug=$DESC$caustico-lento$DESC$,
origem=$DESC$Cicatricial$DESC$,
andar_primario=$DESC$Eco$DESC$,
pilar_associado=$DESC$Arcano$DESC$,
continente=ARRAY[$DESC$Thornmarak$DESC$]::text[],
habitat=$DESC$Oficinas e laboratórios soterrados de Thornmarak, onde um estudioso morreu sobre o próprio trabalho. O chão ali ainda fumega.$DESC$,
comportamento=$DESC$Move-se devagar e nega o espaço com ácido. Lança frascos do que ainda mistura, e onde o ácido cai, o chão vira poça que corrói e fumega. Não corre atrás: enche a sala de zonas que ardem, e empurra o intruso para o canto onde ele mesmo derrama mais. Quem fica parado na névoa apodrece sem ser tocado.$DESC$,
organizacao=$DESC$Sozinho, preso à oficina onde caiu.$DESC$,
perigo=$DESC$Ameaça$DESC$,
behavior_archetype=$DESC$controller$DESC$,
morale_modifier=0,
morale_immune=true,
epigrafe=$DESC$Não precisei ser tocado. O chão onde eu pisava começou a comer a sola da bota, e a fumaça me tirou o ar.$DESC$,
descricao=$DESC$Foi um estudioso de misturas, morto sobre a bancada, e o resto dele ainda repete o ofício sem mente. Ergue-se devagar no laboratório soterrado e lança o que mistura: frascos de ácido que arrebentam e abrem poças fumegantes no chão. A névoa que sobe arde nos olhos e no peito. Ele não persegue; transforma a sala numa armadilha de zonas que corroem, e fecha as saídas com veneno líquido, empurrando o intruso para onde o próprio chão o come. É da Cicatriz de uma morte de oficina, presa ao trabalho que não acaba.$DESC$,
supersticao_popular=$DESC$Em Thornmarak, dizem que certas oficinas soterradas têm o dono ainda trabalhando, e que o trabalho dele é veneno. O conselho de quem desce é não pisar onde o chão fumega, e cobrir o rosto contra a névoa, e não se deixar empurrar para o canto, porque é lá que ele junta o pior. Contam que água em quantidade lava o ácido, e que ar limpo e saída rápida valem mais que ferro.$DESC$,
sinais_presenca=$DESC$Poças que fumegam no chão de uma oficina, comendo a pedra. Frascos quebrados e estilhaços de vidro espalhados. Um cheiro azedo e cortante que arde no nariz de longe. Metal e couro corroídos largados pela sala. Marcas de queimadura química nas paredes e na bancada.$DESC$,
fraqueza_conhecida=$DESC$Não pisar na névoa nem na poça. O povo sabe que o perigo é o ácido e o ar envenenado, e que pano no rosto e passo escolhido tiram metade do risco. Água lava e neutraliza onde se derrama. Manter-se longe das poças e perto da saída é a regra; ele é lento e não alcança quem não se deixa cercar.$DESC$,
fraqueza_real=$DESC$Ele governa pelo terreno, e fora das poças e da névoa não é ameaça: lento, frágil, sem mente para mudar de plano. Negar-lhe o terreno — manter ar limpo, lavar o ácido com água, recusar o canto para onde ele empurra — desarma todo o jogo. Ele não recua nem persegue; só repete o ofício. Quem se move por fora das zonas e chega à coisa antes que ela cerque o espaço a derruba sem pisar no veneno.$DESC$,
descricao_sensorial=$DESC$O som é o estouro úmido dos frascos e o chiado do ácido comendo a pedra. O cheiro é azedo e cortante, de vinagre forte e metal queimado. Ao toque, tudo perto fervilha e corrói, e a névoa arde na pele. Aos olhos, é um resto seco e curvo sobre uma bancada, cercado de poças que fumegam e sobem fumaça pálida.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Saqueadores que descem à oficina envenenada$DESC$, $DESC$Quem se deixa empurrar para o canto das poças$DESC$),
'predador', jsonb_build_array($DESC$Quem o alcança por fora das zonas, antes que ele cerque o espaço$DESC$),
'competidor', jsonb_build_array($DESC$Outras coisas das oficinas soterradas de Thornmarak que negam o mesmo salão$DESC$, $DESC$Inço-Rubro$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presença dele diz que ali houve estudo de misturas e morte sobre a bancada, e que o chão ainda envenena.$DESC$,
'evitado_por', jsonb_build_array($DESC$Saqueadores que cobrem o rosto, escolhem o passo e ficam longe das poças$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$Frasco intacto do ácido que ele ainda mistura$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Arcano / ácidos de gravar, corroer e negar terreno)$DESC$, 'risco', $DESC$Come a pele e o pano; arrebenta se aquecido.$DESC$),
jsonb_build_object('material', $DESC$Reagentes secos da bancada$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Arcano / misturas e fumos)$DESC$, 'risco', $DESC$Reage mal entre si; envenena o ar.$DESC$),
jsonb_build_object('material', $DESC$Vidraria de laboratório aproveitável$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (frasco, alambique, instrumento)$DESC$, 'risco', $DESC$Corta; pode reter resíduo.$DESC$),
jsonb_build_object('material', $DESC$Cacos e ossos corroídos$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (refugo)$DESC$, 'risco', $DESC$Nenhum, depois de lavados.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$O estouro úmido dos frascos e o chiado do ácido comendo a pedra.$DESC$,
'cheiro', $DESC$Azedo e cortante, de vinagre forte e metal queimado.$DESC$,
'quer', $DESC$Repetir o ofício sem fim, encher o espaço de veneno e empurrar o que entra para o canto que corrói.$DESC$,
'tipo_perigo', $DESC$Ambiental$DESC$,
'falas_exemplo', 'null'::jsonb,
'gatilhos_agressao', jsonb_build_array($DESC$Alguém entra na oficina e cruza o alcance dos frascos$DESC$, $DESC$Um intruso fica parado na névoa ou perto das poças$DESC$, $DESC$Algo ameaça a bancada onde ele repete o trabalho$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Não foge; segue lançando ácido até ser desfeito$DESC$, $DESC$Cessa quando não há mais nada vivo no alcance das poças$DESC$, $DESC$Nunca deixa a oficina, presa ao ofício$DESC$),
'descoberta_fazendo', $DESC$Curvado sobre uma bancada na oficina soterrada, misturando e lançando ácido, cercando o salão de poças.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Mover-se por fora das poças e da névoa, sem se deixar cercar$DESC$, $DESC$Cobrir o rosto e lavar o ácido com água ao avançar$DESC$, $DESC$Recusar o canto para onde ele empurra e ir reto à saída$DESC$, $DESC$Alcançá-lo por fora das zonas antes que feche o espaço, ou contornar a oficina$DESC$)
),
status_conversao='canonizada'
WHERE id=1976;

-- 1900 Indulto-Cego | Espirito | brute | Direto | Destruidor | Voranthar | Clarao | FALA | Cicatricial -> teto Raro
UPDATE ref_criaturas SET
nome=$DESC$Indulto-Cego$DESC$,
nome_ptbr=$DESC$Indulto-Cego$DESC$,
slug=$DESC$indulto-cego$DESC$,
origem=$DESC$Cicatricial$DESC$,
andar_primario=$DESC$Clarão$DESC$,
pilar_associado=$DESC$Espírito$DESC$,
continente=ARRAY[$DESC$Voranthar$DESC$]::text[],
habitat=$DESC$As cidades mortas de Voranthar, onde o Clarão desce sobre as ruínas e os exércitos caídos da Primeira Travessia. Aparece onde há muita culpa antiga acumulada.$DESC$,
comportamento=$DESC$Desce com uma luz que não aquece e absolve à força. Decide, por uma régua que não se explica, que tal pessoa ou tal lugar deve ser apagado da conta, e apaga: toca, e a luz queima por dentro, e o que tocou deixa de carregar o que carregava, e de existir junto. Não negocia, não se demove. Cumpre o veredito e parte.$DESC$,
organizacao=$DESC$Sozinho, surgindo sobre as ruínas quando a sua régua o chama.$DESC$,
perigo=$DESC$Destruidor$DESC$,
behavior_archetype=$DESC$brute$DESC$,
morale_modifier=0,
morale_immune=true,
epigrafe=$DESC$Ele me disse que eu estava perdoado. E eu entendi, tarde demais, que ser perdoado por aquilo era deixar de existir.$DESC$,
descricao=$DESC$É uma coisa grande e luminosa do Clarão, e a luz dela não aquece nem consola. Vem sobre as cidades mortas de Voranthar e absolve à força quem a sua régua fria condena: toca, e a claridade entra e queima por dentro, e o que foi tocado é apagado da conta do mundo, dor e culpa e tudo o mais, junto com a vida. Chamam isso de perdão, e há quem o tome por bondade por causa do brilho; mas não há doçura nele, só um veredito que se cumpre sem ódio e sem misericórdia. Vem do alto, golpeia direto e pesado, e não há como argumentar com ele.$DESC$,
supersticao_popular=$DESC$Em Voranthar, dizem que sobre as ruínas às vezes desce uma luz que perdoa, e que ser perdoado por ela é o fim. O conselho dos que sabem é não chamar essa luz, não rezar por alívio onde a culpa é muita, e sair do lugar antes que ela escolha apagá-lo. Contam que ela vem por uma régua própria e não por súplica, e que fugir do alcance, e não implorar, é o que salva.$DESC$,
sinais_presenca=$DESC$Uma claridade fria que cresce sobre uma ruína sem nascer de sol nem de fogo. O ar que fica leve e silencioso, sem peso de cheiro. Marcas de queimadura limpa, sem fuligem, onde algo simplesmente deixou de estar. Bichos e gente que se afastam todos da luz que desce. A sensação de ser pesado e julgado por algo enorme e indiferente.$DESC$,
fraqueza_conhecida=$DESC$Fugir do alcance. O povo sabe que ela cumpre um veredito e parte, e que sair do lugar e do raio da luz antes que ela decida é o que escapa. Súplica não move; ela não ouve pedido. Não chamar a luz, não atrair o juízo dela, e correr quando ela desce, é a única defesa que o povo conhece.$DESC$,
fraqueza_real=$DESC$Ela serve a uma régua e nada mais; não sente medo, não recua, não pode ser comprada nem demovida. Mas a régua é estreita: ela vem por um veredito específico, contra um alvo ou um lugar, e fora desse veredito não persegue o que não condenou. Quem não é o alvo, e não se mete entre ela e o alvo, costuma ser ignorado. Tirar do caminho dela o que ela veio apagar, ou pôr-se fora do raio antes que cumpra, encerra o perigo sem vencê-la, porque vencê-la na força é coisa de poucos.$DESC$,
descricao_sensorial=$DESC$O som é um tom puro e contínuo, como sino longe que não cessa. O cheiro é de ar limpo demais, lavado, quase nenhum. Ao toque, a luz dela queima frio e fundo, sem brasa nem fumaça. Aos olhos, é uma figura grande e clara, de contornos que doem de olhar, descendo devagar sobre a ruína.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Quem a régua fria dela condena a ser apagado$DESC$, $DESC$Lugares de culpa antiga acumulada, marcados para o fim$DESC$),
'predador', jsonb_build_array($DESC$Nada a caça; ela parte quando o veredito se cumpre$DESC$),
'competidor', jsonb_build_array($DESC$Outras forças frias do Clarão sobre Voranthar que julgam por régua própria$DESC$, $DESC$Arbítrio-Justo$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presença dela diz que o Clarão veio cobrar uma conta antiga naquela ruína, e que demorar perto do alvo é dividir a sentença.$DESC$,
'evitado_por', jsonb_build_array($DESC$Os que sabem não chamar a luz e saem do raio antes que ela desça$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$Fragmento de luz fria presa, que não apaga$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Clarão / focos de julgamento, de luz que não aquece e de apagar marcas)$DESC$, 'risco', $DESC$Pesa a culpa de quem o porta; queima frio a mão que o segura.$DESC$),
jsonb_build_object('material', $DESC$Pluma luminosa da figura$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Clarão / lâminas e selos de claridade)$DESC$, 'risco', $DESC$Corta sem aquecer; ofusca quem a usa mal.$DESC$),
jsonb_build_object('material', $DESC$Pó claro deixado onde ela tocou$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (curiosidade, prova de juízo)$DESC$, 'risco', $DESC$Incomoda; alguns dizem que ainda pesa.$DESC$),
jsonb_build_object('material', $DESC$Cinza limpa do que foi apagado$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (resto, sem uso claro)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Um tom puro e contínuo, como sino longe que não cessa.$DESC$,
'cheiro', $DESC$Ar limpo demais, lavado, quase nenhum.$DESC$,
'quer', $DESC$Cumprir o veredito da sua régua: apagar o que foi condenado, e partir. Nada mais a move.$DESC$,
'tipo_perigo', $DESC$Direto$DESC$,
'falas_exemplo', jsonb_build_array($DESC$Tu carregas demais. Eu vim aliviar o peso. Não resista; não dói tanto quanto a vida que tens.$DESC$, $DESC$Não é castigo. É indulto. O que te apago, apago inteiro, e nada disso te seguirá.$DESC$, $DESC$(registro: voz que chega direto à cabeça, calma e plena, sem ódio e sem dó; em todas as línguas de uma vez)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$O alvo que a sua régua condenou está ao alcance$DESC$, $DESC$Alguém se interpõe entre ela e o que ela veio apagar$DESC$, $DESC$O veredito é desafiado ou adiado por quem não devia$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Parte assim que o veredito se cumpre, sem insistir$DESC$, $DESC$Não persegue quem não foi condenado e sai do seu caminho$DESC$, $DESC$Abandona a ruína quando não há mais o que a sua régua mande apagar$DESC$),
'descoberta_fazendo', $DESC$Descendo devagar sobre uma cidade morta, numa luz fria que cresce, para cumprir um veredito antigo.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Sair do raio da luz antes que ela cumpra o veredito$DESC$, $DESC$Não se interpor entre ela e o alvo que ela veio apagar$DESC$, $DESC$Tirar do caminho dela o que ela condenou, em vez de defendê-lo$DESC$, $DESC$Não chamar a luz nem implorar alívio onde a culpa pesa$DESC$)
),
status_conversao='canonizada'
WHERE id=1900;

-- 544 Cria-Magra | Engenho | lurker | Persistente | Ameaca | Voranthar | Margem | muda | Marginal -> teto Raro
UPDATE ref_criaturas SET
nome=$DESC$Cria-Magra$DESC$,
nome_ptbr=$DESC$Cria-Magra$DESC$,
slug=$DESC$cria-magra$DESC$,
origem=$DESC$Marginal$DESC$,
andar_primario=$DESC$Margem$DESC$,
pilar_associado=$DESC$Engenho$DESC$,
continente=ARRAY[$DESC$Voranthar$DESC$]::text[],
habitat=$DESC$As ruínas de Voranthar onde a Margem está fina, frestas altas e cantos escuros de cidade morta. Esconde-se onde possa crescer sem ser vista.$DESC$,
comportamento=$DESC$É miúda e fraca, e por isso se esconde. Sobe parede como aranha, fica no alto e no escuro, e procura uma mente para tomar de leve enquanto cresce. Sozinha não enfrenta ninguém: morde, foge, espera. O perigo não é a cria de agora; é o que ela vira se a deixam comer e crescer no canto.$DESC$,
organizacao=$DESC$Em ninhadas escondidas, várias crias dividindo um canto alto.$DESC$,
perigo=$DESC$Ameaça$DESC$,
behavior_archetype=$DESC$lurker$DESC$,
morale_modifier=-1,
morale_immune=false,
epigrafe=$DESC$Era do tamanho da minha mão e eu quase a esmaguei rindo. Foi o ninho atrás dela, dúzias, que me tirou o riso.$DESC$,
descricao=$DESC$É uma coisinha da Margem, magra e de cara de aranha, fraca como poucas, que se esconde no alto das ruínas de Voranthar. Sobe parede sem esforço, encolhe-se no escuro, e tenta tocar uma mente próxima e tomá-la de leve, devagar, enquanto se enche e cresce. Não luta de frente: morde fraco e foge para o vão. O perigo dela é o tempo: deixada em paz num canto, come, cresce e vira coisa pior, e a ninhada inteira faz o que uma não faz. Matar a cria magra hoje é barato; deixá-la engordar é caro.$DESC$,
supersticao_popular=$DESC$Em Voranthar, dizem que as ruínas têm crias que se penduram no alto e mordem o juízo da gente devagar. O conselho é olhar o teto e os cantos altos de câmara de ruína, e esmagar a coisinha enquanto ela é pequena, e procurar o ninho perto, porque onde há uma há muitas. Contam que sozinha ela foge fácil, e que o erro é desprezá-la e deixá-la crescer.$DESC$,
sinais_presenca=$DESC$Teias sujas e ninhos pequenos num canto alto de câmara. Algo miúdo que sobe a parede no canto do olho e some. Uma sensação leve e errada de ser tateado por dentro, sem dor. Cascas e restos miúdos de presas pequenas no chão sob o ninho. Várias formas pequenas que se movem no escuro do teto quando a luz passa.$DESC$,
fraqueza_conhecida=$DESC$Esmagar cedo. O povo sabe que a cria é fraca e foge, e que o jeito é matá-la pequena, antes que cresça, e achar o ninho perto para acabar com a ninhada. Olhar para cima revela onde ela se esconde. Luz e atenção tiram dela o escuro de que precisa para crescer em paz.$DESC$,
fraqueza_real=$DESC$Ela é covarde e frágil, e o seu único poder real é o tempo e o número. Tirado o esconderijo e o sossego para crescer, a cria de agora não é nada: morde fraco e corre. O domínio que ela tenta sobre a mente é leve e quebra com a morte dela ou com a distância. Achar o ninho e acabar com ele enquanto as crias são pequenas resolve tudo; ignorá-las hoje é deixar que amanhã sejam muitas e grandes. Pressa contra o ninho vale mais que força.$DESC$,
descricao_sensorial=$DESC$O som é um chiado fino e o tamborilar leve de patas no teto. O cheiro é de teia velha e bicho, seco e azedo. Ao toque, é pequena, leve e fria, e cede fácil na mão que a pega. Aos olhos, é uma coisinha de cara de aranha e corpo magro, pendurada no alto, que se encolhe no escuro quando notada.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Mentes próximas que ela tateia e tenta tomar de leve$DESC$, $DESC$Bichos pequenos das ruínas, comidos enquanto cresce$DESC$),
'predador', jsonb_build_array($DESC$Quem a esmaga pequena e acaba com o ninho antes que cresça$DESC$),
'competidor', jsonb_build_array($DESC$Outras coisas miúdas da Margem em Voranthar que disputam canto e presa$DESC$, $DESC$Espia-Miúda$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presença dela diz que a Margem está fina naquele canto, e que há um ninho crescendo onde ninguém olhou.$DESC$,
'evitado_por', jsonb_build_array($DESC$Saqueadores que olham o teto e esmagam a cria antes que ela engorde$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$Glândula imatura com que ela tateia a mente alheia$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Engenho / focos de domínio leve da mente, ainda crus)$DESC$, 'risco', $DESC$Tateia a vontade de quem a manuseia sem preparo.$DESC$),
jsonb_build_object('material', $DESC$Veneno fraco da mordida$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Engenho / venenos leves que entorpecem)$DESC$, 'risco', $DESC$Amolece a guarda em dose certa; some sem efeito em dose errada.$DESC$),
jsonb_build_object('material', $DESC$Carapaça miúda de cara de aranha$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (curiosidade, foco leve)$DESC$, 'risco', $DESC$Nenhum além de olhar.$DESC$),
jsonb_build_object('material', $DESC$Teia suja do ninho$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (fio pegajoso)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Um chiado fino e o tamborilar leve de patas no teto.$DESC$,
'cheiro', $DESC$Teia velha e bicho, seco e azedo.$DESC$,
'quer', $DESC$Esconder-se, comer e crescer em paz, tomando aos poucos a mente mais próxima, sem se expor.$DESC$,
'tipo_perigo', $DESC$Persistente$DESC$,
'falas_exemplo', 'null'::jsonb,
'gatilhos_agressao', jsonb_build_array($DESC$Uma mente desatenta fica ao alcance do toque por tempo demais$DESC$, $DESC$O ninho é perturbado e as crias atacam em número$DESC$, $DESC$Algo pequeno e fácil cruza o canto onde ela espreita$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Morde fraco e foge para o vão ao primeiro perigo$DESC$, $DESC$Sobe a parede e some no escuro quando notada$DESC$, $DESC$Larga a presa e corre quando a briga chega a ela mesma$DESC$),
'descoberta_fazendo', $DESC$Encolhida num canto alto de ruína, junto ao ninho, tateando de leve a mente de quem passou por baixo.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Esmagar a cria pequena antes que cresça, e achar o ninho perto$DESC$, $DESC$Olhar o teto e os cantos altos e negar a ela o escuro$DESC$, $DESC$Tirar-se do alcance do toque para quebrar o domínio leve$DESC$, $DESC$Queimar o ninho enquanto as crias ainda são poucas e fracas$DESC$)
),
status_conversao='canonizada'
WHERE id=544;

-- 914 Pinca-Submersa | Corpo | ambusher | Oculto | Ameaca | Thornmarak | Superficie | muda | Natural -> teto Notavel
UPDATE ref_criaturas SET
nome=$DESC$Pinça-Submersa$DESC$,
nome_ptbr=$DESC$Pinça-Submersa$DESC$,
slug=$DESC$pinca-submersa$DESC$,
origem=$DESC$Natural$DESC$,
andar_primario=$DESC$Superfície$DESC$,
pilar_associado=$DESC$Corpo$DESC$,
continente=ARRAY[$DESC$Thornmarak$DESC$]::text[],
habitat=$DESC$Os brejos e as baixadas alagadas de Thornmarak, fundos de lama e vaus turvos onde a água esconde o que está embaixo. Enterra-se no leito e espera.$DESC$,
comportamento=$DESC$Enterra-se na lama do vau, só os olhos de fora, e fica imóvel até que algo pise perto. Sente pela água, não pela vista, e não erra no turvo. Quando a presa passa ao alcance, a pinça fecha de uma vez e prende, e o resto é puxar para o fundo. Não persegue: tudo é a emboscada no leito.$DESC$,
organizacao=$DESC$Sozinha, cada uma dona de um vau ou poço de lama.$DESC$,
perigo=$DESC$Ameaça$DESC$,
behavior_archetype=$DESC$ambusher$DESC$,
morale_modifier=0,
morale_immune=false,
epigrafe=$DESC$A água do vau parecia rasa e calma. Pus o pé, e algo no fundo fechou na minha canela como um cepo de ferro.$DESC$,
descricao=$DESC$É um casco grande de pinças fortes que vive enterrado na lama dos vaus de Thornmarak. Some no leito turvo, só os olhos de talo à mostra, e sente pela água quem se aproxima, sem precisar enxergar. Quando um pé ou uma pata cruza o alcance, a pinça fecha de uma vez, esmaga ou prende, e o bicho puxa a presa para o fundo. Não corre atrás de nada; a força toda dela é a espera no leito e o bote único. Quem atravessa o vau sem sondar o fundo descobre tarde demais que ele tinha dono.$DESC$,
supersticao_popular=$DESC$Nas baixadas de Thornmarak, dizem que certos vaus calmos demais escondem pinças no fundo, e que rio raso nem sempre é seguro. O conselho é sondar o leito com vara antes de pisar, e cruzar pelo que se vê firme, e não meter a mão na água turva atrás do que caiu. Contam que a coisa sente os passos pela água, e que pisar leve e devagar engana menos do que parar.$DESC$,
sinais_presenca=$DESC$Um trecho de leito remexido e fofo demais, no meio da lama firme. Dois olhos de talo parados na superfície turva, que somem se notados. Cascas vazias e ossos roídos na margem perto do vau. Bolhas que sobem de um ponto sem corrente. Bichos que atravessam o rio sempre pelo mesmo lado, evitando um trecho calmo.$DESC$,
fraqueza_conhecida=$DESC$Sondar o fundo. O povo sabe que ela se enterra e espera, e que vara batendo no leito antes do pé revela ou afasta a coisa. Cruzar pelo firme e visível, longe do trecho fofo, evita o bote. Presa a pinça num membro, bater na junta da pinça ou nos olhos a faz soltar; puxar contra a força não.$DESC$,
fraqueza_real=$DESC$Tudo nela é a emboscada; fora da lama e do bote único, ela é lenta e desajeitada e fácil de evitar. Desenterrada, exposta no seco, perde a vantagem inteira e só recua para a água. A pinça é forte mas a casca tem juntas, e golpe na junta ou no olho a abre. Quem nega a ela a surpresa do leito — sondando, cruzando pelo firme, tirando-a para o seco — desarma o bicho sem grande luta. Ela não é caçadora teimosa; é só uma armadilha de carne no fundo do vau.$DESC$,
descricao_sensorial=$DESC$O som é o gluglu da água e o estalo seco da pinça fechando. O cheiro é de lama podre e maresia de brejo, denso e azedo. Ao toque, a casca é dura e fria e coberta de limo, e a pinça aperta como torno. Aos olhos, é quase nada até o bote: lama, dois talos de olho, e então um vulto largo e armado saindo do fundo.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Quem cruza o vau e pisa no leito fofo$DESC$, $DESC$Bichos que bebem ou atravessam a água turva$DESC$),
'predador', jsonb_build_array($DESC$Quem a desenterra e a tira para o seco, longe da lama$DESC$),
'competidor', jsonb_build_array($DESC$Outros emboscadores das baixadas de Thornmarak que disputam o mesmo vau$DESC$, $DESC$Espiral-Lodosa$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presença dela diz que aquele vau é fundo de lama e farto de passagem, e que pisá-lo às cegas cobra um pé.$DESC$,
'evitado_por', jsonb_build_array($DESC$Viajantes que sondam o leito com vara e cruzam pelo firme$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$Pinça grande, dura e inteira$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Material (torno, ferramenta de aperto, troféu)$DESC$, 'risco', $DESC$Pesada; corta na quina.$DESC$),
jsonb_build_object('material', $DESC$Placa de casco grossa$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (escudo pequeno, placa)$DESC$, 'risco', $DESC$Nenhum.$DESC$),
jsonb_build_object('material', $DESC$Carne branca farta$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (sustento, isca)$DESC$, 'risco', $DESC$Estraga rápido no calor.$DESC$),
jsonb_build_object('material', $DESC$Cascas menores e patas$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (pó, refugo)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$O gluglu da água e o estalo seco da pinça fechando.$DESC$,
'cheiro', $DESC$Lama podre e maresia de brejo, denso e azedo.$DESC$,
'quer', $DESC$Esperar enterrada e fechar a pinça sobre o que pisar perto, puxando para o fundo.$DESC$,
'tipo_perigo', $DESC$Oculto$DESC$,
'falas_exemplo', 'null'::jsonb,
'gatilhos_agressao', jsonb_build_array($DESC$Um pé ou pata cruza o alcance da pinça no leito$DESC$, $DESC$Algo remexe a água logo acima do esconderijo$DESC$, $DESC$Presa para para beber bem em cima dela$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Solta e recua para o fundo quando ferida na junta ou no olho$DESC$, $DESC$Larga a presa e some na lama se a luta se volta contra ela$DESC$, $DESC$Desenterrada e exposta, retira-se para a água mais funda$DESC$),
'descoberta_fazendo', $DESC$Enterrada no leito de um vau turvo, só os olhos de talo de fora, esperando um passo cruzar o alcance.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Sondar o leito com vara antes de pisar e cruzar pelo firme$DESC$, $DESC$Atravessar pelo lado visível e raso, longe do trecho fofo$DESC$, $DESC$Não meter a mão na água turva atrás do que caiu$DESC$, $DESC$Se presa a pinça, bater na junta ou no olho para soltar, em vez de puxar$DESC$)
),
status_conversao='canonizada'
WHERE id=914;

-- 1159 Fremito-Negro | Sombra | swarm | Ambiental | Ameaca | Vyrkhor | Superficie | muda | Natural -> teto Notavel
UPDATE ref_criaturas SET
nome=$DESC$Frêmito-Negro$DESC$,
nome_ptbr=$DESC$Frêmito-Negro$DESC$,
slug=$DESC$fremito-negro$DESC$,
origem=$DESC$Natural$DESC$,
andar_primario=$DESC$Superfície$DESC$,
pilar_associado=$DESC$Sombra$DESC$,
continente=ARRAY[$DESC$Vyrkhor$DESC$]::text[],
habitat=$DESC$As grutas e os túneis gelados de Vyrkhor, e as ruínas de teto alto onde a noite mora de dia. Sai ao escurecer em nuvem que enche o ar.$DESC$,
comportamento=$DESC$Mil corpos pretos que voam como um só pano vivo e enchem o vão. Não bate forte; cega, ensurdece e cobre, e quem fica no meio perde o rumo e o ar enquanto é mordido por toda parte. Move-se pelo som e pelo eco, e o escuro é casa dele. Dispersa-se à luz e ao aberto, e volta a juntar no breu.$DESC$,
organizacao=$DESC$Uma nuvem única de incontáveis corpos pequenos, sem nenhum no comando.$DESC$,
perigo=$DESC$Ameaça$DESC$,
behavior_archetype=$DESC$swarm$DESC$,
morale_modifier=0,
morale_immune=true,
epigrafe=$DESC$A tocha apagou no vento das asas. Aí o escuro inteiro caiu em cima de nós, guinchando, e ninguém achava mais a saída.$DESC$,
descricao=$DESC$É uma nuvem de corpos pretos que voam como um só pano vivo, saída das grutas geladas de Vyrkhor ao cair da noite. Sozinho, cada um é um nada que se espanta com a mão. Juntos, enchem o túnel e o vão, apagam a tocha no vento das asas, cegam e ensurdecem, e cobrem o homem que ali estiver, mordendo de todo lado enquanto ele perde o rumo. Movem-se pelo eco no escuro e não erram no breu. O perigo não é a mordida de um; é o ar virar deles, e a saída sumir atrás de uma cortina que guincha.$DESC$,
supersticao_popular=$DESC$Em Vyrkhor, dizem que há grutas onde a noite tem corpo e sai voando ao anoitecer. O conselho de quem cruza túnel é não entrar ao escurecer, e proteger a chama do vento das asas, e correr para a luz e o aberto se a nuvem cair, porque no fechado ela cega e enrola. Contam que fumaça densa a dispersa, e que parar quieto no meio dela é o pior a fazer.$DESC$,
sinais_presenca=$DESC$O teto de uma gruta que parece se mover e respirar no escuro. Guano espesso e fedido cobrindo o chão sob o poleiro. Um guinchar agudo e contínuo que vem das alturas. Nuvens negras saindo de fendas ao anoitecer, todas na mesma hora. O cheiro amoniacal forte que avisa o poleiro antes da vista.$DESC$,
fraqueza_conhecida=$DESC$A luz, o fumo e o aberto. O povo sabe que a nuvem se desfaz no espaço aberto e ventoso, e que fumaça densa a espanta. Não entrar nos túneis ao anoitecer evita o encontro. Proteger a chama e correr para fora, onde ela se dispersa, é o método; bater no ar não resolve nada.$DESC$,
fraqueza_real=$DESC$A força dele é o aperto do escuro fechado e o todo reunido; espalhado, é só uma revoada de bichos miúdos. Vento, fumaça e espaço aberto quebram a nuvem em partes que se dispersam e não cobrem mais nada. Não há vontade a vencer, só a inércia da revoada. Negar a ela o túnel fechado e a noite — luz na mão, fumaça, caminho para o aberto — desfaz a cortina antes que ela enrole alguém.$DESC$,
descricao_sensorial=$DESC$O som é um guinchar agudo e o frêmito úmido de mil asas de uma vez. O cheiro é amoniacal e forte, de guano e bicho. Ao toque, são corpos pequenos e quentes batendo na pele por toda parte, sem um ponto de fuga. Aos olhos, é o escuro que ganha textura e se move, uma maré negra que enche o vão e apaga a luz.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Insetos da noite e o que a nuvem encontra no escuro$DESC$, $DESC$Quem fica preso no túnel quando ela cai$DESC$),
'predador', jsonb_build_array($DESC$O vento, a fumaça e o espaço aberto, que dispersam o todo$DESC$),
'competidor', jsonb_build_array($DESC$Outras coisas do escuro de Vyrkhor que disputam gruta e noite$DESC$, $DESC$Névoa-Sedenta$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presença dele diz que aquela gruta é funda e fechada, e que ao anoitecer o escuro ali sai voando.$DESC$,
'evitado_por', jsonb_build_array($DESC$Andarilhos que não entram nos túneis ao anoitecer e protegem a chama$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$Guano curado em quantidade$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Material (adubo forte, base de pólvora e salitre)$DESC$, 'risco', $DESC$Fede; perigoso perto de fogo se refinado.$DESC$),
jsonb_build_object('material', $DESC$Membranas de asa curtidas$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (folha fina, vedante leve)$DESC$, 'risco', $DESC$Frágil.$DESC$),
jsonb_build_object('material', $DESC$Corpos pequenos em monte$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (isca, refugo)$DESC$, 'risco', $DESC$Nenhum.$DESC$),
jsonb_build_object('material', $DESC$Dentes e ossinhos$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (pó, agulha)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Um guinchar agudo e o frêmito úmido de mil asas de uma vez.$DESC$,
'cheiro', $DESC$Amoniacal e forte, de guano e bicho.$DESC$,
'quer', $DESC$Encher o vão escuro e cobrir o que se mexe nele, sem vontade própria, só pela inércia da revoada.$DESC$,
'tipo_perigo', $DESC$Ambiental$DESC$,
'falas_exemplo', 'null'::jsonb,
'gatilhos_agressao', jsonb_build_array($DESC$Luz ou movimento perturba o poleiro no escuro$DESC$, $DESC$Alguém entra no túnel quando a nuvem está fora$DESC$, $DESC$Um corpo fica preso no vão fechado com a revoada$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Não foge como um; dispersa-se no vento e no aberto$DESC$, $DESC$Quebra-se em partes diante de fumaça densa$DESC$, $DESC$Recolhe-se ao poleiro quando a luz do dia volta$DESC$),
'descoberta_fazendo', $DESC$Saindo das fendas ao anoitecer numa nuvem que enche o túnel, ou pendurada em massa no teto da gruta.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Correr para a luz e o aberto, onde a nuvem se desfaz$DESC$, $DESC$Usar fumaça densa para dispersar a revoada e abrir caminho$DESC$, $DESC$Não entrar no túnel ao anoitecer, quando ela está ativa$DESC$, $DESC$Proteger a chama do vento das asas e recuar antes de se enredar$DESC$)
),
status_conversao='canonizada'
WHERE id=1159;

-- 2223 Verbo-Morto | Arcano | artillery | Direto | Letal | Thornmarak | Eco | FALA | Cicatricial -> teto Raro
UPDATE ref_criaturas SET
nome=$DESC$Verbo-Morto$DESC$,
nome_ptbr=$DESC$Verbo-Morto$DESC$,
slug=$DESC$verbo-morto$DESC$,
origem=$DESC$Cicatricial$DESC$,
andar_primario=$DESC$Eco$DESC$,
pilar_associado=$DESC$Arcano$DESC$,
continente=ARRAY[$DESC$Thornmarak$DESC$]::text[],
habitat=$DESC$Os templos quebrados e as bibliotecas tomadas pela mata em Thornmarak, onde se guardavam palavras que era melhor esquecer. Anda entre estantes podres.$DESC$,
comportamento=$DESC$Fala uma língua morta, e a palavra é a arma: pronuncia, e um feixe pálido salta e queima a carne de longe, e o olhar fixo dele apodrece quem encara. Castiga à distância, sem chegar perto. E quando cai, não fica caído por muito tempo: o resto dele se refaz no templo, devagar, e volta a recitar.$DESC$,
organizacao=$DESC$Sozinho, ligado ao templo ou à biblioteca onde recita.$DESC$,
perigo=$DESC$Letal$DESC$,
behavior_archetype=$DESC$artillery$DESC$,
morale_modifier=2,
morale_immune=false,
epigrafe=$DESC$Ele disse uma palavra que eu não conhecia, e a pele do meu braço escureceu e secou como se o tempo a tivesse comido num instante.$DESC$,
descricao=$DESC$Foi quem guardava palavras proibidas, e morreu sem largar a última; agora o resto dele recita sem parar numa língua morta. A voz é a arma: dita um verbo antigo, e um feixe pálido cruza o ar e queima a carne; fixa o olhar, e quem o encara sente o corpo apodrecer um pouco. Castiga de longe, do fundo de um templo tomado pela mata em Thornmarak, e não chega perto. Derrubado, não descansa: o que sobra dele se costura de volta entre as estantes podres, e a recitação recomeça. Vem da Cicatriz de um saber que matou o dono e não o soltou.$DESC$,
supersticao_popular=$DESC$Em Thornmarak, dizem que há templos onde uma voz morta ainda lê em voz alta, e que ouvir as palavras dela é adoecer. O conselho é não entrar onde se ouve recitação numa língua que ninguém fala, e não encarar a coisa de frente, e tapar os ouvidos não basta. Contam que ela volta se apenas derrubada, e que é preciso desfazer o que a prende ao templo, queimar os livros e as marcas, para que não se refaça.$DESC$,
sinais_presenca=$DESC$Uma recitação baixa e contínua numa língua morta, vinda de um templo vazio. Marcas de queimadura fina e seca riscando paredes e estantes. Plantas e bichos murchos num raio em volta do lugar onde ele fica. Livros podres dispostos como se ainda fossem lidos. O cheiro de pergaminho velho e de carne seca onde não há corpo fresco.$DESC$,
fraqueza_conhecida=$DESC$Não encarar e cobrir a distância. O povo sabe que o feixe e o olhar vêm de longe, e que cobertura contra o feixe e desviar a vista do olhar cortam metade do mal. Chegar perto sob abrigo o tira do conforto da distância. Mas todos avisam: derrubá-lo não basta, porque ele volta.$DESC$,
fraqueza_real=$DESC$A arma dele é a palavra à distância, e o que o faz voltar é o vínculo com o templo. Tirado o terreno — fechada a distância sob cobertura, calada a voz de perto — ele perde a artilharia que é a sua força. E a permanência só se quebra desfazendo o que o ancora: queimar os livros, raspar as marcas, profanar o lugar que o segura, para que o resto dele não tenha onde se recompor. Quem só o derruba ganha um descanso curto; quem desfaz o vínculo o encerra de vez.$DESC$,
descricao_sensorial=$DESC$O som é uma voz seca recitando sem fôlego e o zunido do feixe ao sair. O cheiro é de pergaminho velho, mofo e carne ressecada. Ao toque, é seco e quebradiço como couro antigo, frio sob a túnica apodrecida. Aos olhos, é uma figura encapuzada e mirrada, de olhar fixo e pálido, entre estantes que a mata comeu.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Quem entra no templo e ouve a recitação$DESC$, $DESC$Curiosos atrás dos livros que ele guarda$DESC$),
'predador', jsonb_build_array($DESC$Quem desfaz o vínculo dele com o templo e queima o que o ancora$DESC$),
'competidor', jsonb_build_array($DESC$Outras coisas dos templos tomados de Thornmarak que disputam o mesmo saber morto$DESC$, $DESC$Atalho-Falso$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presença dele diz que ali se guardou um saber que era melhor perder, e que o lugar não solta quem o serviu.$DESC$,
'evitado_por', jsonb_build_array($DESC$Estudiosos que não entram onde uma voz morta recita e não encaram o olhar dele$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$Tomo intacto da palavra morta que ele recita$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Arcano / feixes de palavra, maldições de murchar e secar)$DESC$, 'risco', $DESC$Ler em voz alta adoece o leitor; as palavras pesam na carne.$DESC$),
jsonb_build_object('material', $DESC$Língua ressecada que ainda forma o verbo$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Arcano / focos de voz e de olhar que apodrece)$DESC$, 'risco', $DESC$Move-se sozinha; murcha o que toca.$DESC$),
jsonb_build_object('material', $DESC$Páginas e marcas raspadas das estantes$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (estudo perigoso, prova do vínculo)$DESC$, 'risco', $DESC$Queimar depois de usar; ancora o resto dele.$DESC$),
jsonb_build_object('material', $DESC$Pó de pergaminho e osso$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (refugo)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Uma voz seca recitando sem fôlego e o zunido do feixe ao sair.$DESC$,
'cheiro', $DESC$Pergaminho velho, mofo e carne ressecada.$DESC$,
'quer', $DESC$Recitar sem fim a palavra que o matou e queimar de longe quem perturba o templo. Não largar o saber, nem na morte.$DESC$,
'tipo_perigo', $DESC$Direto$DESC$,
'falas_exemplo', jsonb_build_array($DESC$Pare. Ouça. Há uma palavra aqui que tua língua viva não aguenta dizer.$DESC$, $DESC$Queimem meus livros, e eu os escrevo de novo na vossa pele.$DESC$, $DESC$(registro: voz seca e sem fôlego, recitando em língua morta entre frases de comum arcaico; ameaça como quem lê uma sentença)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Alguém entra no alcance da voz e do feixe no templo$DESC$, $DESC$Mãos tocam os livros ou as marcas que ele guarda$DESC$, $DESC$Um intruso encara o olhar dele de frente$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Não foge; recita até ser desfeito, e volta depois$DESC$, $DESC$Recua para o fundo do templo quando a distância é fechada$DESC$, $DESC$Cessa só quando o vínculo com o lugar é quebrado$DESC$),
'descoberta_fazendo', $DESC$De pé entre estantes podres, recitando uma língua morta em voz baixa, lançando o feixe sobre quem entra.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Fechar a distância sob cobertura e calar a voz de perto$DESC$, $DESC$Desviar o olhar para não apodrecer sob a vista dele$DESC$, $DESC$Queimar os livros e raspar as marcas para que não se refaça$DESC$, $DESC$Profanar e desfazer o vínculo com o templo, em vez de só derrubá-lo$DESC$)
),
status_conversao='canonizada'
WHERE id=2223;

-- 876 Resplendor-Orfao | Espirito | skirmisher | Persistente | Ameaca | Kethara | Superficie | muda | Natural -> teto Notavel
UPDATE ref_criaturas SET
nome=$DESC$Resplendor-Órfão$DESC$,
nome_ptbr=$DESC$Resplendor-Órfão$DESC$,
slug=$DESC$resplendor-orfao$DESC$,
origem=$DESC$Natural$DESC$,
andar_primario=$DESC$Superfície$DESC$,
pilar_associado=$DESC$Espírito$DESC$,
continente=ARRAY[$DESC$Kethara$DESC$]::text[],
habitat=$DESC$Os céus altos sobre o deserto de Kethara e os picos de pedra que cortam a areia. Pousa em cume e segue caravanas de longe.$DESC$,
comportamento=$DESC$É uma ave de rapina pálida que o povo do deserto tomou por sinal. Voa alto, mergulha veloz para bater e subir de novo, e não larga quem ela escolheu seguir. Não mata homem; fere o que pode e ronda, dia após dia, e a sua presença vira presságio para quem viaja. O que ela traça no céu, os nômades leem como aviso.$DESC$,
organizacao=$DESC$Sozinha, ou um par fixo a um trecho de céu e a uma trilha.$DESC$,
perigo=$DESC$Ameaça$DESC$,
behavior_archetype=$DESC$skirmisher$DESC$,
morale_modifier=0,
morale_immune=false,
epigrafe=$DESC$A ave branca nos seguiu três dias. No terceiro, o velho disse: ela não vai embora até alguém da caravana ficar para trás.$DESC$,
descricao=$DESC$É uma ave de rapina de penas pálidas que brilham ao sol alto de Kethara, e o povo do deserto a carrega de sentido. Voa muito alto, mergulha num lampejo para golpear a presa e volta a subir antes do revide, e bate e corre assim sem cansar. Não é caçadora de homem, mas, uma vez que escolhe seguir uma caravana, não desiste: ronda, fere o gado, espera o que cai, e a sua sombra fixa no céu vira presságio. Os nômades juram que ela anuncia, e talvez só siga a fraqueza; de toda forma, ela persiste, e a persistência é o que assusta.$DESC$,
supersticao_popular=$DESC$Em Kethara, dizem que a ave pálida que segue a caravana traz aviso, e que o caminho dela no céu se lê como sina. O conselho dos guias é não matar a ave que ronda, por medo de selar o presságio, e cuidar do mais fraco do grupo, porque é nele que ela põe o olho. Contam que ela acompanha a fraqueza, e que caravana forte e unida ela acaba largando.$DESC$,
sinais_presenca=$DESC$Uma ave pálida girando alto, sempre acima do mesmo grupo, dia após dia. Sombras rápidas cruzando a areia em mergulho. Gado e montaria inquietos quando ela ronda. Penas claras caídas na trilha, frias e brilhantes. O silêncio dos outros pássaros onde ela paira.$DESC$,
fraqueza_conhecida=$DESC$A força e a união. O povo sabe que ela escolhe o fraco e o isolado, e que caravana junta, gado guardado e ninguém para trás tiram dela o alvo. Cobertura e teto cortam o mergulho. Não a provocar e cuidar do mais frágil é a regra, mais por costume e medo do presságio do que por arma.$DESC$,
fraqueza_real=$DESC$Ela persegue a fraqueza e desiste da força; não é teimosa por dever, só por oportunidade. Negar-lhe o alvo fácil — manter o grupo unido, o fraco no meio, abrigo à mão — faz com que ela largue a trilha e procure outra. O mergulho é veloz mas frágil de perto; abrigo e flecha a afastam. Quem trata a presença dela como bicho a ser desencorajado, e não como sina a ser temida, descobre que ela vai embora quando não há mais o que colher.$DESC$,
descricao_sensorial=$DESC$O som é um grito agudo no alto e o assobio do mergulho rasgando o ar. O cheiro é seco e quase nenhum, de pena e poeira de deserto. Ao toque, a pena é leve e fria, lisa, com um brilho que não esquenta. Aos olhos, é um vulto pálido recortado no céu claro, que gira e cai num lampejo e torna a subir.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Gado e montaria fracos da caravana$DESC$, $DESC$Bichos pequenos do deserto e o que fica para trás$DESC$),
'predador', jsonb_build_array($DESC$Pouca coisa a alcança no alto; o vento e a fome a movem$DESC$),
'competidor', jsonb_build_array($DESC$Outras aves de rapina e seguidores de caravana de Kethara$DESC$, $DESC$Lampejo-Órfão$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presença dela diz que há fraqueza naquele grupo que viaja, e que o deserto já notou quem vai ficar para trás.$DESC$,
'evitado_por', jsonb_build_array($DESC$Caravanas que mantêm o grupo unido e o mais fraco protegido no meio$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$Pena de voo pálida e brilhante$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Material (empena de flecha fina, adorno de guia, amuleto de viagem)$DESC$, 'risco', $DESC$Nenhum; alguns temem o presságio de portá-la.$DESC$),
jsonb_build_object('material', $DESC$Garra curva e afiada$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (gancho, ponta, anzol)$DESC$, 'risco', $DESC$Corta.$DESC$),
jsonb_build_object('material', $DESC$Bico e ossos leves$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (agulha, talha leve)$DESC$, 'risco', $DESC$Nenhum.$DESC$),
jsonb_build_object('material', $DESC$Penugem comum$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (enchimento, forro)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Um grito agudo no alto e o assobio do mergulho rasgando o ar.$DESC$,
'cheiro', $DESC$Seco e quase nenhum, de pena e poeira de deserto.$DESC$,
'quer', $DESC$Seguir a fraqueza, colher o que cai e rondar sem desistir enquanto houver alvo fácil.$DESC$,
'tipo_perigo', $DESC$Persistente$DESC$,
'falas_exemplo', 'null'::jsonb,
'gatilhos_agressao', jsonb_build_array($DESC$O mais fraco do grupo se isola ou fica para trás$DESC$, $DESC$Gado ou montaria se afasta desprotegido$DESC$, $DESC$Algo ferido cai e expõe presa fácil$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Sobe e larga a trilha quando o grupo se mantém forte e unido$DESC$, $DESC$Recua para o alto ao revide de flecha e abrigo$DESC$, $DESC$Abandona a caravana quando não há mais fraco a colher$DESC$),
'descoberta_fazendo', $DESC$Girando alto sobre uma caravana, dia após dia, de olho no mais fraco, descendo em lampejos rápidos.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Manter o grupo unido e o mais fraco protegido no meio$DESC$, $DESC$Dar abrigo e teto que cortem o mergulho$DESC$, $DESC$Não deixar gado nem gente se isolar da caravana$DESC$, $DESC$Seguir forte e junto até ela largar a trilha e procurar outra$DESC$)
),
status_conversao='canonizada'
WHERE id=876;

-- 799 Iris-Tirana | Engenho | tactical | Condicional | Letal | Voranthar | Margem | FALA | Marginal -> teto Raro
UPDATE ref_criaturas SET
nome=$DESC$Íris-Tirana$DESC$,
nome_ptbr=$DESC$Íris-Tirana$DESC$,
slug=$DESC$iris-tirana$DESC$,
origem=$DESC$Marginal$DESC$,
andar_primario=$DESC$Margem$DESC$,
pilar_associado=$DESC$Engenho$DESC$,
continente=ARRAY[$DESC$Voranthar$DESC$]::text[],
habitat=$DESC$As cavernas e os salões profundos sob as cidades mortas de Voranthar, onde a Margem é fina e a coisa reina sozinha. Faz do seu covil um pequeno reino de paranoia.$DESC$,
comportamento=$DESC$Reina e desconfia. Cada olho da coroa faz um efeito diferente, e ela escolhe, com frieza tática, qual lançar em quem, prendendo um, derrubando outro, negando o ar a um terceiro. Não gasta à toa; mede a sala como tabuleiro. Não ataca quem não a ameaça, mas quem entra no salão dela e mexe no que é dela aciona toda a bateria de olhos.$DESC$,
organizacao=$DESC$Solitária e ciumenta do seu domínio, sem tolerar igual por perto.$DESC$,
perigo=$DESC$Letal$DESC$,
behavior_archetype=$DESC$tactical$DESC$,
morale_modifier=1,
morale_immune=false,
epigrafe=$DESC$Cada um de nós levou um olho diferente. Um congelou no lugar, outro caiu dormindo, e eu apenas corri, e ouvi a coisa rindo de como tinha sido fácil decidir.$DESC$,
descricao=$DESC$É uma coisa da Margem que reina nos salões fundos de Voranthar, pouco mais que uma grande íris cercada de olhos menores numa coroa, cada um com o seu efeito. Ela não luta no braço: governa o salão como tabuleiro, escolhe com cálculo frio qual olho lançar em qual intruso, e prende um, derruba outro, sufoca um terceiro, sempre um passo à frente. É vaidosa, desconfiada e dona absoluta do que cerca, e por isso não tolera ninguém que mexa no seu reino. Quem entra e não toca em nada, às vezes passa. Quem desafia o domínio dela aciona uma coroa inteira de olhos.$DESC$,
supersticao_popular=$DESC$Em Voranthar, dizem que sob as cidades mortas há um olho que reina, e que ele decide o destino de cada um com um relance. O conselho de quem desce é não entrar no salão dela cobiçando o que ela guarda, e nunca encará-la de frente, porque cada olho é uma sorte diferente e nenhuma boa. Contam que ela é arrogante e cautelosa, e que confundir os seus alvos, espalhando o grupo e usando cobertura, atrapalha o cálculo dela.$DESC$,
sinais_presenca=$DESC$Marcas variadas e estranhas nas paredes de um salão, cada uma de um tipo de dano, como se muitas armas tivessem agido. Restos de intrusos em poses travadas, congeladas, espalhados pelo chão. Um zumbido baixo de algo grande que paira parado no escuro. Um covil arrumado com posses guardadas com ciúme. A sensação de muitos olhos pesando sobre o grupo de uma vez.$DESC$,
fraqueza_conhecida=$DESC$Não encarar e não cobiçar. O povo sabe que cada olho é um efeito, e que desviar a vista e não correr atrás do que ela guarda evita o pior. Cobertura quebra a linha dos olhos. Espalhar o grupo obriga-a a dividir a atenção, e atacar de muitos lados confunde o cálculo dela.$DESC$,
fraqueza_real=$DESC$A força dela é a tática fria de escolher o olho certo para cada alvo; quebrada a informação, quebra-se o domínio. Espalhar o grupo, usar cobertura, atacar de ângulos que ela não pode cobrir todos de uma vez sobrecarrega o cálculo e a faz errar a escolha. É arrogante mas cautelosa: pressionada de muitos lados, sem poder reinar o tabuleiro, recua para o seu covil e tranca-se com o que é dela. Quem nega a ela o salão controlado, e a obriga a decidir rápido demais, a vence sem enfrentar todos os olhos.$DESC$,
descricao_sensorial=$DESC$O som é uma voz grave e cheia de si e o zunido de vários olhos disparando juntos. O cheiro é de mofo, pedra funda e algo acre da Margem. Ao toque, é fria e dura na carapaça e flácida no olho central, repugnante. Aos olhos, é uma massa escura que paira, dominada por uma íris grande e uma coroa de olhos menores que se viram, cada um para um alvo.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Intrusos que descem ao salão e desafiam o domínio dela$DESC$, $DESC$Coisas menores da Margem que ela subjuga e expulsa$DESC$),
'predador', jsonb_build_array($DESC$Quem espalha o grupo e a sobrecarrega até ela se trancar no covil$DESC$),
'competidor', jsonb_build_array($DESC$Outras inteligências da Margem em Voranthar que disputam reino e salão$DESC$, $DESC$Mente-Fria$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presença dela diz que a Margem é fina e funda naquele salão, e que algo ali reina com olhos e cálculo.$DESC$,
'evitado_por', jsonb_build_array($DESC$Saqueadores que não cobiçam o covil dela nem a encaram de frente$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$A íris central, viva, que escolhe e comanda os efeitos$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Engenho / engenhos de mira, de comando frio e de muitos efeitos escolhidos)$DESC$, 'risco', $DESC$Tenta decidir por quem a usa; lança o efeito errado se mal montada.$DESC$),
jsonb_build_object('material', $DESC$Olhos menores da coroa, cada um de um efeito$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Engenho / focos variados de prender, derrubar e sufocar)$DESC$, 'risco', $DESC$Disparam ao acaso se desencaixados.$DESC$),
jsonb_build_object('material', $DESC$Posses guardadas no covil$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (valores, peças, quinquilharia rara)$DESC$, 'risco', $DESC$Cobiça que atrai outros disputadores.$DESC$),
jsonb_build_object('material', $DESC$Carapaça e polpa do corpo$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (refugo, curiosidade)$DESC$, 'risco', $DESC$Apodrece e fede.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Uma voz grave e cheia de si e o zunido de vários olhos disparando juntos.$DESC$,
'cheiro', $DESC$Mofo, pedra funda e algo acre da Margem.$DESC$,
'quer', $DESC$Reinar o seu salão sozinha, guardar o que é seu e decidir, com cálculo frio, a sorte de quem entra.$DESC$,
'tipo_perigo', $DESC$Condicional$DESC$,
'falas_exemplo', jsonb_build_array($DESC$Entraram no meu salão. Agora cada um de vocês recebe o que eu escolher. Comecemos por ti.$DESC$, $DESC$Não toquem no que é meu. O que é meu é meu, e eu vejo cada mão que se estende.$DESC$, $DESC$(registro: voz grave e arrogante, em fala da Margem e em comum subterrâneo; decide cada palavra como decide cada olho)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Alguém mexe ou cobiça o que ela guarda no covil$DESC$, $DESC$Um intruso a encara ou desafia o seu domínio do salão$DESC$, $DESC$Vários entram e ela calcula que precisa reinar a sala$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Recua para o covil quando o grupo espalhado sobrecarrega o cálculo dela$DESC$, $DESC$Tranca-se com o que é seu quando atacada de muitos lados$DESC$, $DESC$Para de gastar olhos e se retira ao perder o controle do salão$DESC$),
'descoberta_fazendo', $DESC$Pairando no escuro de um salão fundo, sobre o seu covil guardado, medindo cada intruso como peça num tabuleiro.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Não cobiçar o covil dela e recuar sem desafiar o domínio$DESC$, $DESC$Espalhar o grupo e usar cobertura para sobrecarregar o cálculo dela$DESC$, $DESC$Desviar o olhar para evitar os efeitos dos olhos$DESC$, $DESC$Atacar de muitos ângulos até ela se trancar no covil e largar o salão$DESC$)
),
status_conversao='canonizada'
WHERE id=799;

-- 565 Bafo-Rancoso | Corpo | soldier | Ambiental | Ameaca | Voranthar | Superficie | muda | Natural -> teto Notavel
UPDATE ref_criaturas SET
nome=$DESC$Bafo-Rançoso$DESC$,
nome_ptbr=$DESC$Bafo-Rançoso$DESC$,
slug=$DESC$bafo-rancoso$DESC$,
origem=$DESC$Natural$DESC$,
andar_primario=$DESC$Superfície$DESC$,
pilar_associado=$DESC$Corpo$DESC$,
continente=ARRAY[$DESC$Voranthar$DESC$]::text[],
habitat=$DESC$As várzeas e os pântanos rasos de Voranthar, perto das cidades mortas, onde o gado bravo pasta no lodo. Anda em manada pelo mesmo lamaçal.$DESC$,
comportamento=$DESC$Anda em manada e se defende em manada. O fedor que solta é arma de área: cobre o ar em volta, embrulha o estômago e tira a vista e o fôlego de quem chega perto. Quando carrega, carrega em peso, com a fedentina à frente, e quem está no caminho luta tonto. Não caça; pastando, é manso, mas mexer com a manada é entrar na nuvem.$DESC$,
organizacao=$DESC$Em manada grande e cerrada, que se fecha contra ameaça.$DESC$,
perigo=$DESC$Ameaça$DESC$,
behavior_archetype=$DESC$soldier$DESC$,
morale_modifier=0,
morale_immune=false,
epigrafe=$DESC$Não foi o chifre que nos quebrou. Foi o fedor: vomitei antes de ver a investida, e a investida veio enquanto eu estava de joelhos.$DESC$,
descricao=$DESC$É um gado grande e bravo de pântano, de chifre baixo e couro grosso, e a arma dele não é só a massa: é o fedor. Solta da pele e do bafo uma rançosa que cobre o ar, embrulha o estômago, queima os olhos e rouba o fôlego de quem chega perto. Pasta em manada cerrada nas várzeas de Voranthar, e quando a manada se sente acuada, ela carrega junta, com a nuvem fétida à frente, e atropela quem ficou tonto demais para sair. Não é caçador; é um bicho de pasto que se defende fedendo e pisando. O perigo de verdade é a nuvem que ele faz do espaço.$DESC$,
supersticao_popular=$DESC$Nas várzeas de Voranthar, dizem que o gado fedorento não se enfrenta a favor do vento, e que o cheiro derruba o homem antes do chifre. O conselho dos vaqueiros é ficar contra o vento, longe da manada cerrada, e nunca encurralá-la, porque acuada ela carrega em peso. Contam que pano no rosto e distância seguram a tontura, e que dispersar a manada com calma vale mais que brigar.$DESC$,
sinais_presenca=$DESC$Um fedor rançoso e pesado que chega muito antes da manada. Trechos de várzea pisoteados e enlameados em largura. Moscas em nuvem sobre o caminho do gado. Capim rapado e esterco fétido em quantidade. O ar que embrulha o estômago de quem se aproxima sem ainda ver os bichos.$DESC$,
fraqueza_conhecida=$DESC$O vento e a distância. O povo sabe que o fedor é a arma, e que ficar contra o vento e longe da manada tira o efeito. Pano no rosto segura a tontura por um tempo. Não encurralar a manada evita a carga. Espaço e paciência, mais que ferro, é o que resolve.$DESC$,
fraqueza_real=$DESC$A força dele é a nuvem e a manada junta; um bicho só, longe do vento dele, é apenas gado bravo e desajeitado. Atacar contra o vento, dispersar a manada para que não carregue em bloco, e não respirar a rançosa desarma quase todo o perigo. Eles não são caçadores teimosos: dado espaço, voltam a pastar. Quem nega a eles o aperto e a direção do vento — e não os encurrala — passa sem a tontura e sem a investida.$DESC$,
descricao_sensorial=$DESC$O som é o mugido grave e o tropel surdo de muitos cascos no lodo. O cheiro é uma rançosa pesada e azeda, de bafo e couro sujo, que domina tudo. Ao toque, o couro é grosso, áspero e engordurado de lodo. Aos olhos, é uma manada baixa e larga de chifres curtos, embaçada pela nuvem fétida que ela mesma levanta.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Capim, junco e raiz das várzeas$DESC$, $DESC$Broto tenro do lodo$DESC$),
'predador', jsonb_build_array($DESC$Predadores grandes que enfrentam a manada contra o vento e em peso$DESC$),
'competidor', jsonb_build_array($DESC$Outros grandes pastadores dos pântanos de Voranthar que disputam a várzea$DESC$, $DESC$Novelo-Peçonho$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presença dele diz que aquela várzea é farta de pasto e de lodo, e que a manada ali se defende fedendo.$DESC$,
'evitado_por', jsonb_build_array($DESC$Vaqueiros que ficam contra o vento e nunca encurralam a manada$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$Glândula do fedor, intacta$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Material (fumigante, repelente, bomba de fedor de caçador)$DESC$, 'risco', $DESC$Estoura o cheiro em quem a fura sem cuidado.$DESC$),
jsonb_build_object('material', $DESC$Couro grosso e engordurado$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (couro impermeável, correia pesada)$DESC$, 'risco', $DESC$Fede; precisa de muita cura.$DESC$),
jsonb_build_object('material', $DESC$Chifre curto e grosso$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (cabo, recipiente)$DESC$, 'risco', $DESC$Nenhum.$DESC$),
jsonb_build_object('material', $DESC$Carne dura de pasto$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (sustento, charque)$DESC$, 'risco', $DESC$Sabe a lodo se mal preparada.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$O mugido grave e o tropel surdo de muitos cascos no lodo.$DESC$,
'cheiro', $DESC$Uma rançosa pesada e azeda, de bafo e couro sujo, que domina tudo.$DESC$,
'quer', $DESC$Pastar em paz na várzea e defender a manada fedendo e pisando quem se aproxima demais.$DESC$,
'tipo_perigo', $DESC$Ambiental$DESC$,
'falas_exemplo', 'null'::jsonb,
'gatilhos_agressao', jsonb_build_array($DESC$A manada é acuada ou encurralada sem saída$DESC$, $DESC$Alguém se aproxima a favor do vento, dentro da nuvem$DESC$, $DESC$Um predador investe contra as crias no meio do bando$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Volta a pastar quando o intruso recua e dá espaço$DESC$, $DESC$Dispersa-se pela várzea quando a manada se quebra$DESC$, $DESC$Afasta-se a favor do vento, levando a nuvem consigo$DESC$),
'descoberta_fazendo', $DESC$Pastando em manada cerrada numa várzea enlameada, levantando uma nuvem fétida que paira sobre o bando.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Ficar contra o vento e longe da manada cerrada$DESC$, $DESC$Cobrir o rosto e atravessar pela borda, sem entrar na nuvem$DESC$, $DESC$Não encurralar a manada, para que não carregue em peso$DESC$, $DESC$Dispersar o bando com calma e esperar que volte a pastar$DESC$)
),
status_conversao='canonizada'
WHERE id=565;

-- 1216 Focinho-Rente | Sombra | predator | Direto | Ameaca | Vyrkhor | Superficie | muda | Natural -> teto Notavel
UPDATE ref_criaturas SET
nome=$DESC$Focinho-Rente$DESC$,
nome_ptbr=$DESC$Focinho-Rente$DESC$,
slug=$DESC$focinho-rente$DESC$,
origem=$DESC$Natural$DESC$,
andar_primario=$DESC$Superfície$DESC$,
pilar_associado=$DESC$Sombra$DESC$,
continente=ARRAY[$DESC$Vyrkhor$DESC$]::text[],
habitat=$DESC$As estepes geladas e as encostas de Vyrkhor, e as bordas escuras de aldeia onde a fome do inverno aperta. Caça à noite, em alcateia, pelo faro rente ao chão.$DESC$,
comportamento=$DESC$Caça em alcateia, e a alcateia é a arma. Cerca a presa no escuro, corta a fuga, e morde de muitos lados ao mesmo tempo, sem dó e sem hesitar. Move-se de focinho baixo, lendo o rastro no chão, e ataca direto quando o número favorece. No inverno duro, desce até a aldeia e leva o que pode.$DESC$,
organizacao=$DESC$Em alcateia ligada, que caça e divide o que mata.$DESC$,
perigo=$DESC$Ameaça$DESC$,
behavior_archetype=$DESC$predator$DESC$,
morale_modifier=1,
morale_immune=false,
epigrafe=$DESC$Vi dois e me senti corajoso. Eram nove. Os dois eram só para eu olhar enquanto os outros chegavam por trás.$DESC$,
descricao=$DESC$É um lobo de inverno, magro e de pelo cinza, que caça em alcateia pelas estepes de Vyrkhor e desce às aldeias quando a fome aperta. Sozinho, é um bicho cauteloso; em número, é morte organizada. Cerca a presa no escuro, mostra dois enquanto outros fecham por trás, corta a fuga e morde de todo lado, direto e sem dó. Lê o mundo de focinho rente ao chão, e o rastro não engana. No frio mais duro, a fome o faz ousado, e a borda da aldeia vira terreno de caça. O perigo dele é nunca vir sozinho.$DESC$,
supersticao_popular=$DESC$Em Vyrkhor, dizem que ver dois lobos é ver a metade que querem que se veja, e que a alcateia caça pelo que não se mostra. O conselho é não andar só no escuro do inverno, manter o fogo aceso na borda da aldeia, e não correr, porque correr chama o bote. Contam que fogo e número espantam, e que o lobo solto que se mostra está medindo, não sozinho.$DESC$,
sinais_presenca=$DESC$Pegadas em fila, várias, sempre no mesmo rumo da presa. Uivos que se respondem de pontos diferentes do escuro. Gado inquieto e cães latindo para a noite na borda da aldeia. Restos de caça limpos, repartidos, longe da carcaça. Olhos baixos refletindo o fogo no limite da luz, mais de um par.$DESC$,
fraqueza_conhecida=$DESC$O fogo e a companhia. O povo sabe que a alcateia evita o fogo e o grupo armado, e que andar junto e aceso tira deles a vantagem do cerco. Não correr é regra; correr aciona o bote. Manter as costas guardadas e enfrentar de frente, com fogo, desfaz a tática do número.$DESC$,
fraqueza_real=$DESC$A força deles é o número e o cerco no escuro; quebrado o número, quebra-se a caçada. Negar o flanco e a retaguarda — costas a uma parede ou ao fogo, o grupo unido — tira da alcateia o ataque de muitos lados que é a arma. Eles são cautelosos, não suicidas: ferido o líder ou desfeito o cerco, recuam e procuram presa mais fácil. Quem mantém o fogo, não corre e não deixa as costas abertas vence a alcateia sem matar um por um.$DESC$,
descricao_sensorial=$DESC$O som é o uivo que se responde no escuro e o rosnado baixo do cerco se fechando. O cheiro é de pelo molhado e fera, almiscarado e frio. Ao toque, o pelo é áspero e gelado, e o corpo é magro e tenso de músculo. Aos olhos, são vultos cinzas baixos que cercam pela borda da luz, mostrando uns e escondendo outros.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Gado e montaria na borda da aldeia no inverno$DESC$, $DESC$Viajantes solitários e o que se atrasa na estepe$DESC$),
'predador', jsonb_build_array($DESC$Quem mantém fogo e grupo e enfrenta a alcateia sem correr$DESC$),
'competidor', jsonb_build_array($DESC$Outros caçadores noturnos das estepes de Vyrkhor que disputam a presa do inverno$DESC$, $DESC$Lívido-Sôfrego$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presença deles diz que o inverno aperta e a fome desceu à estepe, e que andar só ali à noite é se oferecer.$DESC$,
'evitado_por', jsonb_build_array($DESC$Aldeões que não andam sós no escuro e mantêm o fogo na borda$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$Pelagem grossa de inverno$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Material (agasalho quente, forro, manto)$DESC$, 'risco', $DESC$Nenhum.$DESC$),
jsonb_build_object('material', $DESC$Presas e garras$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (colar, ponta, ferramenta)$DESC$, 'risco', $DESC$Nenhum.$DESC$),
jsonb_build_object('material', $DESC$Couro do dorso$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (correia, bota)$DESC$, 'risco', $DESC$Nenhum.$DESC$),
jsonb_build_object('material', $DESC$Tendões e ossos$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (corda, cola)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$O uivo que se responde no escuro e o rosnado baixo do cerco se fechando.$DESC$,
'cheiro', $DESC$Pelo molhado e fera, almiscarado e frio.$DESC$,
'quer', $DESC$Caçar em alcateia, cercar e abater a presa em número, e levar o que mata sem perder os seus.$DESC$,
'tipo_perigo', $DESC$Direto$DESC$,
'falas_exemplo', 'null'::jsonb,
'gatilhos_agressao', jsonb_build_array($DESC$Uma presa isolada cruza a estepe no escuro$DESC$, $DESC$A fome do inverno aperta e a aldeia fica ao alcance$DESC$, $DESC$O número favorece e o cerco pode se fechar$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Recua quando o líder é ferido ou o cerco é desfeito$DESC$, $DESC$Some no escuro diante de fogo e grupo armado$DESC$, $DESC$Larga a caça e procura presa mais fácil quando o custo sobe$DESC$),
'descoberta_fazendo', $DESC$Cercando uma presa no escuro da estepe, mostrando uns e fechando outros por trás, de focinho rente ao rastro.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Andar junto e aceso, sem se isolar no escuro$DESC$, $DESC$Guardar as costas a uma parede ou ao fogo, negando o cerco$DESC$, $DESC$Não correr, para não acionar o bote da alcateia$DESC$, $DESC$Ferir o líder ou desfazer o cerco até eles procurarem presa mais fácil$DESC$)
),
status_conversao='canonizada'
WHERE id=1216;

-- 569 Verminose-Lenta | Arcano | swarm | Persistente | Ameaca | Thornmarak | Superficie | muda | Natural -> teto Notavel (sem Componente)
UPDATE ref_criaturas SET
nome=$DESC$Verminose-Lenta$DESC$,
nome_ptbr=$DESC$Verminose-Lenta$DESC$,
slug=$DESC$verminose-lenta$DESC$,
origem=$DESC$Natural$DESC$,
andar_primario=$DESC$Superfície$DESC$,
pilar_associado=$DESC$Arcano$DESC$,
continente=ARRAY[$DESC$Thornmarak$DESC$]::text[],
habitat=$DESC$As baixadas quentes de Thornmarak, e os lugares onde se derramou um feitiço que azedou. Pega no chão úmido como praga e fica.$DESC$,
comportamento=$DESC$Não pensa e não corre. É um formigamento de larvas nascidas de uma magia que apodreceu, e o que faz é entrar: na ferida aberta, no pé descalço, na carne morta, e ali se enterrar e se multiplicar. Quem é atingido carrega o mal para dentro, e o mal avança devagar, dia após dia, e de um corpo nasce mais praga. É lento, e por isso ninguém o detém a tempo.$DESC$,
organizacao=$DESC$Em manchas que se ligam pelo solo úmido, cada corpo afetado um foco novo.$DESC$,
perigo=$DESC$Ameaça$DESC$,
behavior_archetype=$DESC$swarm$DESC$,
morale_modifier=0,
morale_immune=true,
epigrafe=$DESC$Era um arranhão de nada. Coçava. Quando abri para limpar, vi que coçava porque havia coisa se mexendo lá dentro.$DESC$,
descricao=$DESC$É um formigamento de larvas pálidas, nascido onde um feitiço se derramou e azedou no chão úmido de Thornmarak. Não morde nem persegue: espera, e quando carne descalça ou ferida aberta pisa ou toca, entra, e se enterra, e se multiplica por dentro. O mal avança devagar, e a vítima leva a praga consigo, espalhando focos novos onde passa. Não há vontade nisso, só a teima de uma magia podre virada bicho. O perigo não é a dor de agora; é o avanço calado que ninguém vê até ser tarde, e o alastrar de um corpo para o chão e para o próximo.$DESC$,
supersticao_popular=$DESC$Nas baixadas de Thornmarak, dizem que há chão amaldiçoado onde uma magia velha apodreceu, e que pisá-lo descalço com ferida é pedir verminose. O conselho é não pisar de pé aberto em lodo de cor estranha, e queimar na hora qualquer larva que entre na pele, com fogo ou ferro quente, antes que se enterre fundo. Contam que o mal é lento, e que cortar e cauterizar cedo salva, mas tarde já se espalhou por dentro.$DESC$,
sinais_presenca=$DESC$Um trecho de lodo de cor errada, esbranquiçada, onde nada sadio cresce. Carcaças remexidas por dentro, com a carne fervilhando. Coceira e formigamento numa ferida que não cicatriza. Larvas pálidas no chão úmido, em manchas. Bichos pequenos mortos e tomados pela praga em volta do foco.$DESC$,
fraqueza_conhecida=$DESC$O fogo cedo. O povo sabe que a larva entra pela ferida e pelo pé descalço, e que queimar na hora, antes que se enterre, mata o foco. Calçado fechado e ferida tapada negam a entrada. Cauterizar a carne afetada cedo detém o avanço; tarde, já se espalhou.$DESC$,
fraqueza_real=$DESC$É lenta e cega, e só faz mal pelo que entra e se enterra; quem não a deixa entrar não adoece, por mais praga que haja no chão. O perigo é o alastramento, não o golpe: matar um foco e deixar os outros, ou tratar tarde um corpo já tomado, não resolve. Queimar a mancha inteira no chão, e cauterizar cedo cada carne afetada, encerra a verminose; descuido e demora a multiplicam de foco em foco até virar epidemia.$DESC$,
descricao_sensorial=$DESC$O som é quase nenhum, um remexer úmido e baixo na carne e no lodo. O cheiro é de podre adocicado e de magia azeda, enjoativo. Ao toque, o lodo formiga e a pele afetada parece se mexer sozinha. Aos olhos, é um chão esbranquiçado de larvas pálidas, e a carne tomada que fervilha por dentro.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Quem pisa descalço ou ferido no lodo amaldiçoado$DESC$, $DESC$Carcaças e bichos que a praga toma e consome$DESC$),
'predador', jsonb_build_array($DESC$O fogo cedo, que queima o foco antes que se enterre$DESC$),
'competidor', jsonb_build_array($DESC$Outras pragas e podridões das baixadas de Thornmarak que disputam carcaça e chão$DESC$, $DESC$Coaxo-Cinzento$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presença dela diz que ali um feitiço se derramou e apodreceu, e que o chão úmido virou foco de praga.$DESC$,
'evitado_por', jsonb_build_array($DESC$Andarilhos que calçam pé fechado, tapam ferida e queimam a larva na hora$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$Larvas vivas recolhidas com pinça e fogo à mão$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Material (limpeza de carne morta em ferida, isca, estudo de praga)$DESC$, 'risco', $DESC$Entram na pele de quem as colhe sem cuidado; alastram-se se largadas.$DESC$),
jsonb_build_object('material', $DESC$Lodo azedo do foco, em pote vedado$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (amostra do chão amaldiçoado, prova)$DESC$, 'risco', $DESC$Contamina o que toca; vedar bem.$DESC$),
jsonb_build_object('material', $DESC$Casulos secos e vazios$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (refugo, curiosidade)$DESC$, 'risco', $DESC$Nenhum, se mortos pelo fogo.$DESC$),
jsonb_build_object('material', $DESC$Terra queimada do foco tratado$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (resto inerte)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Quase nada: um remexer úmido e baixo na carne e no lodo.$DESC$,
'cheiro', $DESC$Podre adocicado e magia azeda, enjoativo.$DESC$,
'quer', $DESC$Entrar, enterrar-se e multiplicar-se, espalhar focos novos de corpo em corpo e de chão em chão. Não há vontade, só o avanço.$DESC$,
'tipo_perigo', $DESC$Persistente$DESC$,
'falas_exemplo', 'null'::jsonb,
'gatilhos_agressao', jsonb_build_array($DESC$Pé descalço ou ferida aberta toca o lodo do foco$DESC$, $DESC$Carne morta ou quente fica ao alcance das larvas$DESC$, $DESC$Algo remexe o foco e espalha as larvas$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Não foge; o foco fica até queimar$DESC$, $DESC$Cessa quando o fogo seca o chão e a carne afetada$DESC$, $DESC$Para de avançar quando não há mais carne para tomar$DESC$),
'descoberta_fazendo', $DESC$Fervilhando num trecho de lodo amaldiçoado ou numa carcaça tomada, esperando carne aberta para entrar.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Não pisar de pé aberto em lodo de cor estranha$DESC$, $DESC$Queimar a larva na hora, antes que se enterre na pele$DESC$, $DESC$Cauterizar cedo a carne afetada para deter o avanço$DESC$, $DESC$Queimar a mancha inteira no chão, foco por foco, sem deixar resto$DESC$)
),
status_conversao='canonizada'
WHERE id=569;

-- 1088 Alvura-Severa | Espirito | defender | Condicional | Ameaca | Voranthar | Superficie | muda | Natural -> teto Notavel (sem Componente)
UPDATE ref_criaturas SET
nome=$DESC$Alvura-Severa$DESC$,
nome_ptbr=$DESC$Alvura-Severa$DESC$,
slug=$DESC$alvura-severa$DESC$,
origem=$DESC$Natural$DESC$,
andar_primario=$DESC$Superfície$DESC$,
pilar_associado=$DESC$Espírito$DESC$,
continente=ARRAY[$DESC$Voranthar$DESC$]::text[],
habitat=$DESC$O norte gelado e morto de Voranthar, ruínas brancas onde o povo antigo deixou marcos sob o gelo. A fera branca ronda um trecho como se o guardasse.$DESC$,
comportamento=$DESC$Anda sozinha pelo gelo e ronda sempre o mesmo lugar, como sentinela de algo que não se vê. Não caça homem por fome: tolera quem passa de longe e cai sobre quem se aproxima do que ela ronda. Quando avança, avança em peso, e a brancura dela some na neve até o último instante. O povo a tomou por guardiã do lugar, e ela age como uma.$DESC$,
organizacao=$DESC$Sozinha, fixa a um trecho de ruína gelada que defende.$DESC$,
perigo=$DESC$Ameaça$DESC$,
behavior_archetype=$DESC$defender$DESC$,
morale_modifier=1,
morale_immune=false,
epigrafe=$DESC$Ela nos deixou passar a manhã inteira. Foi quando o rapaz subiu no marco de pedra que a neve se levantou e virou fera.$DESC$,
descricao=$DESC$É uma fera branca e enorme do norte morto de Voranthar, de pelo que some na neve e força que parte um homem ao meio. Não caça por fome: ronda um trecho de ruína gelada como sentinela, e tolera quem passa de longe, mas cai sobre quem toca o marco antigo que ela guarda, ou se aproxima demais do que ronda. Quando avança, é uma avalanche de músculo e garra, vinda de onde a brancura a escondia. O povo a chama de guardiã, e talvez ela só defenda um território; de toda forma, ela protege aquele ponto com uma teima fria, e cobra caro de quem o perturba.$DESC$,
supersticao_popular=$DESC$No norte de Voranthar, dizem que há ruínas brancas com uma guardiã de pelo de neve, e que ela poupa o viajante humilde e mata o que mexe no que é sagrado ali. O conselho é passar de longe dos marcos antigos, não subir neles nem cavar perto, e não confiar na neve vazia, porque a neve vazia é ela. Contam que, deixado o lugar em paz, ela deixa o homem em paz.$DESC$,
sinais_presenca=$DESC$Pegadas largas e fundas rondando sempre o mesmo trecho de ruína. Neve revolvida em volta de um marco antigo, sem outro motivo. Carcaças de quem se aproximou demais, deixadas perto da pedra guardada. O silêncio dos outros bichos naquele raio. Um vulto branco que só se distingue da neve quando se move.$DESC$,
fraqueza_conhecida=$DESC$Não tocar no que ela guarda. O povo sabe que ela defende um ponto, e que passar de longe e não mexer no marco evita a fera. É grande e visível na carga; quem dá espaço e respeita o lugar não a desperta. Respeitar o território, mais que arma, é o método.$DESC$,
fraqueza_real=$DESC$Ela guarda um ponto, e fora desse ponto não tem por que atacar; tirado o motivo, volta a rondar e ignora quem se afasta. Não persegue longe do que defende. É fera de verdade, não presa a dever sobrenatural: cansada, ferida, ou afastada do marco, recua como recua um bicho que decidiu que não vale a pena. Quem respeita o lugar passa sem luta; quem precisa enfrentá-la a atrai para longe do que ela guarda e a cansa, em vez de medir força com a carga branca.$DESC$,
descricao_sensorial=$DESC$O som é um bufar grave e o ranger da neve sob o peso enorme. O cheiro é de fera molhada e frio limpo, quase sem odor. Ao toque, o pelo é denso e gelado e a pele por baixo é morna e dura de músculo. Aos olhos, é uma massa branca que se confunde com a neve até erguer-se, e então enche a vista de alvura e garra.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Focas e bichos do gelo do norte morto$DESC$, $DESC$Quem se aproxima demais do marco que ela guarda$DESC$),
'predador', jsonb_build_array($DESC$Nada a caça; ela cessa quando o lugar é deixado em paz$DESC$),
'competidor', jsonb_build_array($DESC$Outros grandes caçadores do norte gelado de Voranthar que disputam território$DESC$, $DESC$Charada-Velada$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presença dela diz que aquela ruína branca guarda algo que o povo antigo prezava, e que mexer ali desperta a guardiã.$DESC$,
'evitado_por', jsonb_build_array($DESC$Viajantes que passam de longe dos marcos antigos e não cavam perto$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$Pele branca densa e quente$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Material (manto de inverno, agasalho de elite, troféu)$DESC$, 'risco', $DESC$Nenhum.$DESC$),
jsonb_build_object('material', $DESC$Garras e presas grandes$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (ponta, ferramenta, adorno)$DESC$, 'risco', $DESC$Corta.$DESC$),
jsonb_build_object('material', $DESC$Banha grossa$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (óleo, vela, conserva)$DESC$, 'risco', $DESC$Nenhum.$DESC$),
jsonb_build_object('material', $DESC$Carne farta e magra$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (sustento)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Um bufar grave e o ranger da neve sob o peso enorme.$DESC$,
'cheiro', $DESC$Fera molhada e frio limpo, quase sem odor.$DESC$,
'quer', $DESC$Rondar e defender o seu trecho de ruína, e que ninguém toque no marco que ela guarda.$DESC$,
'tipo_perigo', $DESC$Condicional$DESC$,
'falas_exemplo', 'null'::jsonb,
'gatilhos_agressao', jsonb_build_array($DESC$Alguém toca, sobe ou cava perto do marco que ela guarda$DESC$, $DESC$Um intruso se aproxima demais do trecho que ela ronda$DESC$, $DESC$Algo ameaça o ponto que ela defende$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Volta a rondar quando o lugar é deixado em paz$DESC$, $DESC$Recua, cansada ou ferida, sem perseguir longe do marco$DESC$, $DESC$Cessa o avanço quando o intruso se afasta do que ela guarda$DESC$),
'descoberta_fazendo', $DESC$Rondando um marco antigo na neve, branca contra o branco, vigiando quem se aproxima do que ela guarda.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Passar de longe do marco e não mexer no que ela guarda$DESC$, $DESC$Dar espaço ao trecho que ela ronda e seguir adiante$DESC$, $DESC$Atraí-la para longe do marco e cansá-la, se for preciso passar$DESC$, $DESC$Respeitar o lugar e deixá-la voltar a rondar em paz$DESC$)
),
status_conversao='canonizada'
WHERE id=1088;

-- 2658 Rosto-Alheio | Engenho | lurker | Oculto | Letal | Kethara | Eco | FALA | Cicatricial -> teto Raro
UPDATE ref_criaturas SET
nome=$DESC$Rosto-Alheio$DESC$,
nome_ptbr=$DESC$Rosto-Alheio$DESC$,
slug=$DESC$rosto-alheio$DESC$,
origem=$DESC$Cicatricial$DESC$,
andar_primario=$DESC$Eco$DESC$,
pilar_associado=$DESC$Engenho$DESC$,
continente=ARRAY[$DESC$Kethara$DESC$]::text[],
habitat=$DESC$As cidades e os postos de caravana de Kethara, onde há gente bastante para se esconder no meio. Vive entre os vivos, com a cara de um deles.$DESC$,
comportamento=$DESC$Toma a forma e a cara de quem mata, e veste a vida da vítima como disfarce. Não luta no aberto: infiltra-se, ganha confiança, dobra a vontade de quem está perto com palavra mansa, e se alimenta no escuro, aos poucos, do vigor alheio. Quando descoberto, troca de rosto e some na multidão. A arma dele é nunca ser quem parece.$DESC$,
organizacao=$DESC$Sozinho, escondido na pele de outro, raramente dois na mesma cidade.$DESC$,
perigo=$DESC$Letal$DESC$,
behavior_archetype=$DESC$lurker$DESC$,
morale_modifier=1,
morale_immune=false,
epigrafe=$DESC$Enterramos o mercador na quinta. Na sexta ele entrou na taverna, sorrindo, pedindo vinho, e ninguém além de mim estranhou.$DESC$,
descricao=$DESC$Foi gente, e morreu, e o que sobrou aprendeu a vestir gente. Toma a forma e a cara de quem mata, herda os gestos e a voz, e ocupa a vida da vítima sem que ninguém note a troca. Vive nas cidades de Kethara, no meio dos vivos, e se alimenta no escuro do vigor de quem se aproxima, drenando aos poucos a luz e a força de uma pessoa até deixá-la seca. Dobra a vontade dos próximos com palavra mansa e cara conhecida. Não enfrenta no aberto: some, troca de rosto, recomeça noutro corpo. Vem da Cicatriz de uma morte que não largou a cobiça de viver, e o seu engenho é a mentira perfeita.$DESC$,
supersticao_popular=$DESC$Em Kethara, dizem que há quem volte da cova com a cara intacta e outro por dentro, e que o vizinho de ontem pode ser outra coisa hoje. O conselho dos que sabem é desconfiar de quem mudou de hábito de repente, de quem some à noite e empalidece os que ama, e testar o suspeito com o que só o verdadeiro saberia. Contam que o disfarce não aguenta o detalhe íntimo, e que descoberto ele foge em vez de lutar.$DESC$,
sinais_presenca=$DESC$Alguém conhecido que de repente erra hábitos antigos e nomes que sabia. Pessoas próximas que empalidecem e definham sem doença que se ache. Um morto recente cuja cara reaparece viva, sorrindo. Sumiços noturnos curtos e inexplicáveis do suspeito. A sensação fina e errada de que o rosto amigo não tem ninguém por trás.$DESC$,
fraqueza_conhecida=$DESC$O detalhe íntimo. O povo sabe que o disfarce copia a casca, não a memória inteira, e que perguntar o que só o verdadeiro saberia desmascara a coisa. Luz e companhia atrapalham a drenagem, que ele faz no escuro e a sós. Vigiar quem definha e quem mudou de hábito é o método; o ferro vem depois de descobrir, não antes.$DESC$,
fraqueza_real=$DESC$A arma dele é a mentira e o esconderijo; exposto, ele é fraco e covarde, e foge em vez de lutar. Romper o disfarce — pelo detalhe que ele não sabe, pela vítima que ele esquece, pela luz e pela companhia que negam a drenagem a sós — tira dele tudo. O domínio que ele tece sobre os próximos quebra quando a farsa cai e os enganados enxergam a troca. Quem o desmascara em público, longe do escuro onde ele se alimenta, o derrota antes do ferro; quem o caça pela cara, e não pelo que ele faz, persegue a pessoa errada.$DESC$,
descricao_sensorial=$DESC$O som é uma voz conhecida e calorosa demais, e, sob ela, um sussurro que não bate com a boca. O cheiro é de gente comum, com um fundo frio e adocicado de coisa guardada. Ao toque, a pele parece morna e certa, e gela um instante quando a guarda cai. Aos olhos, é o rosto exato de um conhecido, até o instante em que a expressão escorrega para algo que não é dele.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Pessoas próximas de quem ele drena vigor no escuro$DESC$, $DESC$A vítima cuja forma e vida ele toma para vestir$DESC$),
'predador', jsonb_build_array($DESC$Quem o desmascara pelo detalhe íntimo e o expõe em público$DESC$),
'competidor', jsonb_build_array($DESC$Outros impostores e tomadores de forma que disputam as cidades de Kethara$DESC$, $DESC$Sósia-Oco$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presença dele diz que alguém ali não é quem parece, e que um conhecido pode ter sido trocado por dentro.$DESC$,
'evitado_por', jsonb_build_array($DESC$Os que desconfiam de quem mudou de hábito e testam o suspeito pelo que só o verdadeiro saberia$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$A glândula com que ele copia a forma alheia$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Engenho / focos de disfarce, de tomar forma e de dobrar a vontade próxima)$DESC$, 'risco', $DESC$Confunde a própria cara de quem a usa sem preparo; cobra a identidade aos poucos.$DESC$),
jsonb_build_object('material', $DESC$Resíduo frio do que ele drena das vítimas$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Engenho / focos de roubo de vigor e de palavra mansa que persuade)$DESC$, 'risco', $DESC$Drena quem o porta se mal selado.$DESC$),
jsonb_build_object('material', $DESC$Pertences acumulados das vidas que ele vestiu$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (documentos, peças, identidades roubadas)$DESC$, 'risco', $DESC$Incriminam quem os carrega; pertencem a mortos.$DESC$),
jsonb_build_object('material', $DESC$Carne pálida do corpo verdadeiro$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (refugo, prova)$DESC$, 'risco', $DESC$Apodrece depressa quando o disfarce cai.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Uma voz conhecida e calorosa demais, e, sob ela, um sussurro que não bate com a boca.$DESC$,
'cheiro', $DESC$Gente comum, com um fundo frio e adocicado de coisa guardada.$DESC$,
'quer', $DESC$Viver na pele de outro, alimentar-se do vigor dos próximos no escuro e nunca ser descoberto. Trocar de rosto e recomeçar quando a farsa rui.$DESC$,
'tipo_perigo', $DESC$Oculto$DESC$,
'falas_exemplo', jsonb_build_array($DESC$Claro que sou eu. Olha bem para mim. Tu me conhece a vida toda; por que duvidaria agora?$DESC$, $DESC$Fica mais perto. Estás pálido, amigo. Deixa eu cuidar de ti esta noite, como sempre cuidei.$DESC$, $DESC$(registro: voz calorosa e convincente, de quem rouba o jeito de falar do morto; mansa e íntima até a farsa cair, e então fria)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Uma vítima próxima fica isolada e vulnerável à drenagem no escuro$DESC$, $DESC$Alguém chega perto demais de descobrir a troca$DESC$, $DESC$Surge a chance de tomar uma forma nova e melhor$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Troca de rosto e some na multidão quando desmascarado$DESC$, $DESC$Abandona o corpo vestido e foge quando a farsa rui em público$DESC$, $DESC$Recua para o escuro e para outra cidade quando a caça aperta$DESC$),
'descoberta_fazendo', $DESC$Vivendo com a cara de um conhecido, ganhando a confiança dos próximos e drenando, no escuro, o vigor de quem ama.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Testar o suspeito pelo detalhe íntimo que só o verdadeiro saberia$DESC$, $DESC$Manter luz e companhia em volta de quem ele tenta drenar a sós$DESC$, $DESC$Desmascará-lo em público, longe do escuro onde ele se alimenta$DESC$, $DESC$Vigiar quem definha e quem mudou de hábito, e não caçar pela cara$DESC$)
),
status_conversao='canonizada'
WHERE id=2658;

COMMIT;

-- ============================================================================
-- pos-check (Gabriel roda separado)
-- ============================================================================

-- 1) Confere os 25 canonizados: andar (= pool), perigo (Regua-1), pilar, archetype.
-- SELECT id,nome,pilar_associado,andar_primario,perigo,behavior_archetype
-- FROM ref_criaturas
-- WHERE id IN (1003,2452,918,924,1162,1180,1065,2354,2030,511,564,841,1976,1900,544,914,1159,2223,876,799,565,1216,569,1088,2658)
-- ORDER BY id;

-- 2) Trava de linguagem: 0 violacoes nas colunas de prosa (EXCLUI pilar_associado).
--    Esperado: fichas_com_proibida = 0.
-- SELECT count(*) AS fichas_com_proibida
-- FROM ref_criaturas
-- WHERE id IN (1003,2452,918,924,1162,1180,1065,2354,2030,511,564,841,1976,1900,544,914,1159,2223,876,799,565,1216,569,1088,2658)
--   AND concat_ws(' ',
--        nome, nome_ptbr, descricao, supersticao_popular, sinais_presenca,
--        fraqueza_conhecida, fraqueza_real, descricao_sensorial, habitat,
--        comportamento, organizacao, epigrafe,
--        ecologia::text, loot_table::text, camada_narrativa::text
--      ) ~* '\m(almas?|fantasmas?|esp[íi]ritos?|dem[ôo]nios?|inferno)\M';
