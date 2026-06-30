-- ============================================================
-- lote_bestiario_bloco2.sql  —  Bestiario Alderyn, Bloco 2 (40 fichas, 8 grupos de 5)
-- Cada UPDATE preenche os 25 campos de ficcao; o stat block (HP/CA/dados/acoes) fica INTOCADO.
-- Composicao fechada + colisao (sec. 7.2) = 0. Caminho B: rodar no pgAdmin.
-- Esperado apos COMMIT: canonizada=148, classificada=351, fichas_com_proibida=0.
-- ============================================================
BEGIN;

-- pre-check: devem vir 40 linhas, todas status_conversao='classificada'
SELECT id, nome, cr, origem, status_conversao
FROM ref_criaturas
WHERE id IN (907,1109,783,1877,1833,915,1190,1106,2024,2135,851,1130,891,1932,501,698,717,1842,958,457,926,1189,810,2449,1958,928,1934,1049,1870,512,2304,1160,2444,1140,2086,629,1920,1015,1145,2034)
ORDER BY id;

-- ========================= GRUPO 1 =========================

-- 907 Pedrada-Surda | Corpo | brute | Direto | 7 Letal | Thornmarak | MUDO
UPDATE ref_criaturas SET
nome=$DESC$Pedrada-Surda$DESC$,
nome_ptbr=$DESC$Pedrada-Surda$DESC$,
slug=$DESC$pedrada-surda$DESC$,
origem=$DESC$Natural$DESC$,
andar_primario=$DESC$Superfície$DESC$,
pilar_associado=$DESC$Corpo$DESC$,
continente=ARRAY[$DESC$Thornmarak$DESC$]::text[],
habitat=$DESC$As encostas de mata fechada e os desfiladeiros de Thornmarak, onde sobra pedra solta e a copa alta esconde o tamanho dela.$DESC$,
comportamento=$DESC$Territorial e pesada. Arranca uma laje do chao e a arremessa de longe antes de fechar no soco, e nao recua de intruso: defende o trecho ate o invasor cair ou correr. Marca o limite com galho quebrado e pedra virada.$DESC$,
organizacao=$DESC$Solitaria, as vezes uma femea com um filhote a tiracolo.$DESC$,
perigo=$DESC$Letal$DESC$,
behavior_archetype=$DESC$brute$DESC$,
morale_modifier=1,
morale_immune=false,
epigrafe=$DESC$Ouvi a pedra cortar o ar antes de ver o bicho. Quando vi, ja era tarde para o que estava do meu lado.$DESC$,
descricao=$DESC$E um macaco do tamanho de um celeiro, de braco mais grosso que um homem e mao que fecha em volta de uma rocha como em volta de uma fruta. Nao corre atras: espera o intruso entrar no alcance e atira pedra com forca de ariete, e o que a pedra nao quebra o soco quebra. Aguenta muito ferro antes de cair, e quanto mais perto se chega, pior fica. Nao tem malicia nenhuma; tem fome, cria e o pedaco de mata que e dela, e mata por qualquer um dos tres.$DESC$,
supersticao_popular=$DESC$Dizem em Thornmarak que ha um trecho de mata onde nao se entra, porque as pedras voam sozinhas. O conselho e simples e meio certo: nao subir o desfiladeiro marcado por galho quebrado, e se a primeira pedra passar perto, deitar e nao correr em linha reta. Contam que o bicho cansa se a gente o faz errar muito, mas quem testou raramente voltou para confirmar.$DESC$,
sinais_presenca=$DESC$Pedras grandes fora de lugar, viradas com o lado umido para cima. Galhos grossos quebrados na altura de um homem montado. Trilhas de mato pisado largas demais para gente. Um cheiro forte de bicho em toda a encosta. Silencio de passaro num trecho que devia ter passaro.$DESC$,
fraqueza_conhecida=$DESC$O povo diz para nao deixar ela mirar: ziguezague, cobertura de tronco grosso, e nunca atravessar o aberto em linha reta enquanto ela tem pedra na mao. Dizem que de perto ela e pior, entao a manha e nunca chegar perto.$DESC$,
fraqueza_real=$DESC$Ela e bruta e direta, sem nenhuma manha: mira no que se move em linha e no aberto. Quem quebra a linha de visada com tronco e pedra, e a obriga a gastar arremesso atras de arremesso, a faz cansar e errar. Fogo a faz recuar, porque a mata e dela e ela teme perder a mata. Cercar e fazer barulho de muitos lados confunde o alvo unico que ela escolhe.$DESC$,
descricao_sensorial=$DESC$O som e o estalo de pedra arrancada do chao e um grunhido de peito fundo que se sente na barriga. O cheiro e de bicho grande e folha apodrecida. Ao toque, e pelo aspero sobre musculo duro como raiz. Aos olhos, e uma massa escura que se ergue mais alta que se esperava, com a pedra ja na mao.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Cabras e veados grandes da encosta de Thornmarak$DESC$, $DESC$Qualquer intruso que entra no trecho de mata dela$DESC$),
'predador', jsonb_build_array($DESC$Quase nada a enfrenta de frente; so o fogo da mata e a fome num ano ruim a tiram dali$DESC$),
'competidor', jsonb_build_array($DESC$Outros brutos de encosta que disputam o mesmo desfiladeiro$DESC$, $DESC$Peçonha-Viva$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presenca dela diz que aquele trecho de mata e fechado a gente, e que pedra fora de lugar ali nao caiu sozinha.$DESC$,
'evitado_por', jsonb_build_array($DESC$Cacadores velhos que conhecem o desfiladeiro marcado e dao a volta$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$Maos e tendoes do braco, de forca enorme$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Corpo / forca bruta, arremesso, tracao)$DESC$, 'risco', $DESC$Pesa demais para quem nao tem dorso treinado.$DESC$),
jsonb_build_object('material', $DESC$Couro grosso das costas$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (couro de armadura rude, resistente)$DESC$, 'risco', $DESC$Nenhum.$DESC$),
jsonb_build_object('material', $DESC$Dentes e unhas grandes$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (cabo de faca, adorno)$DESC$, 'risco', $DESC$Nenhum.$DESC$),
jsonb_build_object('material', $DESC$Pelo aspero aos tufos$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (estofo, isolamento)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Estalo de pedra arrancada e grunhido de peito fundo.$DESC$,
'cheiro', $DESC$Bicho grande e folha podre.$DESC$,
'quer', $DESC$Manter o trecho de mata dela livre de intruso e comer o que passa.$DESC$,
'tipo_perigo', $DESC$Direto$DESC$,
'falas_exemplo', 'null'::jsonb,
'gatilhos_agressao', jsonb_build_array($DESC$Alguem cruza o limite marcado por galho quebrado e pedra virada$DESC$, $DESC$Um movimento rapido em linha reta no aberto, ao alcance do arremesso$DESC$, $DESC$Chegam perto do filhote ou da arvore onde ela dorme$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Fogo se espalha na mata e ameaca o trecho dela$DESC$, $DESC$Leva ferro demais e o intruso nao recua, entao ela larga e sobe a encosta$DESC$, $DESC$Muitos alvos de muitos lados que ela nao consegue fixar$DESC$),
'descoberta_fazendo', $DESC$Empoleirada num desfiladeiro alto, virando pedras atras de larva e raiz, de olho no caminho que sobe.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Dar a volta pelo desfiladeiro marcado e nao entrar no trecho dela$DESC$, $DESC$Deitar e ficar imovel quando a primeira pedra passa, ate ela perder o interesse$DESC$, $DESC$Tocar fogo controlado a sotavento para empurra-la encosta acima sem briga$DESC$, $DESC$Atravessar o aberto so com tronco grosso entre voce e a mao dela$DESC$)
),
status_conversao='canonizada'
WHERE id=907;

-- 1109 Rancor-Teimoso | Sombra | tactical | Persistente | 5 Ameaça | Vyrkhor | fala
UPDATE ref_criaturas SET
nome=$DESC$Rancor-Teimoso$DESC$,
nome_ptbr=$DESC$Rancor-Teimoso$DESC$,
slug=$DESC$rancor-teimoso$DESC$,
origem=$DESC$Cicatricial$DESC$,
andar_primario=$DESC$Eco$DESC$,
pilar_associado=$DESC$Sombra$DESC$,
continente=ARRAY[$DESC$Vyrkhor$DESC$]::text[],
habitat=$DESC$Trilhas geladas e ruinas de Vyrkhor por onde passou quem o matou; vai aonde o alvo for.$DESC$,
comportamento=$DESC$Levanta com uma divida so: a morte de quem o traiu. Caca esse alvo e ignora o resto, atravessa quem se mete na frente sem raiva, e se cai, junta o corpo e volta. So para quando cumpre.$DESC$,
organizacao=$DESC$Sozinho, sempre. A divida e dele.$DESC$,
perigo=$DESC$Ameaça$DESC$,
behavior_archetype=$DESC$tactical$DESC$,
morale_modifier=0,
morale_immune=true,
epigrafe=$DESC$Ele passou pela minha frente como se eu nao existisse. So tinha olhos para o homem atras de mim, e o homem atras de mim correu.$DESC$,
descricao=$DESC$E um morto que nao apodrece direito, de olhar fixo e passo que nao cansa. Carrega uma raiva fria e exata: sabe o nome e a cara de quem o matou, e anda atras dessa pessoa por leguas, por estacoes, sem comer, sem dormir, sem desviar. O olhar dele prega medo em quem o encara. Ferido, fecha a carne sozinho; desfeito, monta de novo o corpo dias depois e retoma a caca de onde parou. Quem nao e o alvo dele e so um obstaculo, e ele remove obstaculo sem prazer.$DESC$,
supersticao_popular=$DESC$Em Vyrkhor dizem que ha mortos que voltam por um so, e que o perigo nao e para o viajante qualquer, e sim para quem tem uma divida de sangue a pagar. O conselho dos que sabem: nao se meter entre ele e o alvo, porque ele atravessa quem atravanca e nao guarda rancor de quem sai do caminho. Dizem que matar o alvo dele o apaga; alguns dizem que pedir perdao nunca apaga.$DESC$,
sinais_presenca=$DESC$Um vulto que anda na neve sem rastro de cansaco, sempre na mesma direcao. Bichos de carga que empacam e nao querem seguir certa trilha. Um morto que ninguem enterrou sumido da cova. Gente sumindo de um grupo, sempre a que devia algo a alguem. Um frio de nuca quando ele fixa o olhar em quem tem culpa.$DESC$,
fraqueza_conhecida=$DESC$O povo diz que ferro e fogo so o atrasam, porque ele fecha a ferida e volta. Acham que correr resolve, mas ele nao cansa e a distancia nao o despista. Sabem que ele so quer um, e que ficar perto desse um e o erro.$DESC$,
fraqueza_real=$DESC$A teima e a forca e a cura dele: regenera e remonta, entao gastar arma com ele e perder tempo. O que o encerra de verdade e o fim da divida. Tirar de cena o alvo que ele caca, por morte, fuga longa ou um trato que salde a conta, e o que o faz deitar. Quem entende isso protege o resto e nao briga com a teima dele.$DESC$,
descricao_sensorial=$DESC$O som e um passo seco e parelho que nao muda de ritmo, e nenhuma respiracao. O cheiro e de geada e de carne que parou no tempo, sem podridao franca. Ao toque, e frio e duro, e a ferida que se abre nele ja se fecha. Aos olhos, e um morto de pe firme e olhar travado num so ponto, indiferente a tudo mais.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$O alvo unico: quem o traiu ou matou em vida$DESC$, $DESC$Qualquer um que se ponha de proposito entre ele e o alvo$DESC$),
'predador', jsonb_build_array($DESC$Nada o vence a forca; so o fim da divida o encerra$DESC$),
'competidor', jsonb_build_array($DESC$Outros mortos de Vyrkhor que disputam o mesmo trecho de ruina$DESC$, $DESC$Garra-de-Longe$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presenca dele diz que alguem ali por perto tem uma divida de sangue por pagar, e que essa pessoa nao tem mais paz.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem sabe sair da frente e deixar a caca seguir$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$O olhar que ele fixa, recolhido do morto enfim deitado$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Sombra / fixar medo e travar a vontade de quem encara)$DESC$, 'risco', $DESC$Quem o porta sem treino passa a ser encarado pela propria culpa.$DESC$),
jsonb_build_object('material', $DESC$Carne que se fecha sozinha, ainda morna$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Corpo / fechar ferida, retomar forca)$DESC$, 'risco', $DESC$Cicatriza rapido demais e prende lasca dentro da pele.$DESC$),
jsonb_build_object('material', $DESC$Ferro velho que ele carregava$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (arma simples, marcada de uso)$DESC$, 'risco', $DESC$Nenhum alem do peso da historia.$DESC$),
jsonb_build_object('material', $DESC$Trapo do que vestia em vida$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (pano grosso)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Passo seco e parelho que nunca muda de ritmo, sem respiracao.$DESC$,
'cheiro', $DESC$Geada e carne parada no tempo.$DESC$,
'quer', $DESC$Cobrar a unica divida que o levantou: a morte de quem o matou.$DESC$,
'tipo_perigo', $DESC$Persistente$DESC$,
'falas_exemplo', jsonb_build_array($DESC$Sai da frente. Nao e contigo.$DESC$, $DESC$Ele sabe o que fez. Eu tambem sei, e eu nao canso.$DESC$, $DESC$(registro: voz baixa, parelha, sem raiva nem pressa; fala pouco e so para quem atravanca o caminho)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Alguem se poe de proposito entre ele e o alvo que ele caca$DESC$, $DESC$Tentam levar o alvo para longe do alcance dele$DESC$, $DESC$O alvo o ataca primeiro$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Vai embora, sem fugir, quando o alvo enfim cai e a divida se cumpre$DESC$, $DESC$Larga o obstaculo e segue assim que a passagem se abre$DESC$, $DESC$Para a caca quando a conta e saldada por um trato que tira o alvo de cena$DESC$),
'descoberta_fazendo', $DESC$Andando por uma trilha de Vyrkhor numa linha so, atras de um rastro de quem o traiu, indiferente ao frio e ao resto.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Sair da frente e deixar ele passar atras de quem ele caca$DESC$, $DESC$Apontar o alvo da divida e nao se meter$DESC$, $DESC$Tirar o alvo do alcance dele por fuga longa, ja que a distancia o atrasa mais que o ferro$DESC$, $DESC$Saldar a conta de outro jeito que encerre a divida de sangue que o prende$DESC$)
),
status_conversao='canonizada'
WHERE id=1109;

-- 783 Borralho-Quente | Arcano | artillery | Ambiental | 6 Letal | Kethara | fala
UPDATE ref_criaturas SET
nome=$DESC$Borralho-Quente$DESC$,
nome_ptbr=$DESC$Borralho-Quente$DESC$,
slug=$DESC$borralho-quente$DESC$,
origem=$DESC$Ressonante$DESC$,
andar_primario=$DESC$Superfície$DESC$,
pilar_associado=$DESC$Arcano$DESC$,
continente=ARRAY[$DESC$Kethara$DESC$]::text[],
habitat=$DESC$Forjas mortas e ruinas de areia de Kethara, perto de veios de fogo subterraneo onde o ar ja ferve.$DESC$,
comportamento=$DESC$Mantem em volta de si um ar que queima sozinho, e dali lanca jatos de fogo a distancia. Nao busca corpo a corpo: deixa o calor trabalhar e castiga de longe quem se aproxima do circulo quente. Trata a propria forja como posto a guardar.$DESC$,
organizacao=$DESC$Sozinho ou em dupla, cada um cuidando de uma boca de forja.$DESC$,
perigo=$DESC$Letal$DESC$,
behavior_archetype=$DESC$artillery$DESC$,
morale_modifier=1,
morale_immune=false,
epigrafe=$DESC$Nao precisei chegar perto dele. O ar perto dele ja tinha me cozinhado por dentro da armadura.$DESC$,
descricao=$DESC$Tem forma de homem baixo e atarracado, feito de metal vivo e brasa, e por onde anda o ar esquenta ate doer. O perigo dele e o espaco: um circulo de calor que racha a pele e cega o olho antes mesmo do primeiro golpe, e de dentro desse circulo ele atira fogo a distancia em quem tenta cruzar. A armadura nao salva; esquenta junto. Onde ele para, a area vira armadilha quente, e ele aguenta no posto enquanto houver veio de fogo embaixo para o sustentar.$DESC$,
supersticao_popular=$DESC$Em Kethara contam que certas forjas velhas voltaram a esquentar sozinhas, e que e melhor nao entrar onde o ar treme acima da areia. O conselho e ler o ar antes do chao: se a respiracao arde a dez passos, ja se entrou longe demais. Dizem que agua o apaga, e em parte e verdade, mas pouca agua so vira vapor e cega mais.$DESC$,
sinais_presenca=$DESC$O ar tremendo acima da areia num dia sem sol forte. Metal velho de uma forja morta brilhando de quente outra vez. Pegadas que deixam a areia vidrada, dura e lisa. Um cheiro de metal quente e pedra cozida. Bichos e plantas mortos num circulo certo em volta de um ponto.$DESC$,
fraqueza_conhecida=$DESC$O povo joga agua e foge do calor, e diz que sombra e distancia salvam. Acham que e so nao encostar, sem ver que o perigo comeca longe do toque, no ar.$DESC$,
fraqueza_real=$DESC$A forca dele e a area quente em volta e o tiro de longe; de perto, parado, ele e so um corpo atarracado. Muita agua de uma vez, ou cortar o veio de fogo que o alimenta, mata o circulo de calor e o deixa fraco e exposto. Quem aguenta a area com couro molhado e fecha rapido a distancia, antes do proximo jato, o pega antes de ele reacender o ar.$DESC$,
descricao_sensorial=$DESC$O som e o assobio do ar quente e o estalo de brasa dentro do metal. O cheiro e de metal quente, pedra cozida e cabelo chamuscado. Ao toque, e o calor que chega antes da mao, e doi sem encostar. Aos olhos, e uma figura baixa de metal e brasa dentro de um ar que treme.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Quem cruza o circulo de calor da forja dele$DESC$, $DESC$Bicho e planta que secam no chao quente em volta$DESC$),
'predador', jsonb_build_array($DESC$A agua farta e o fim do veio de fogo embaixo o apagam$DESC$),
'competidor', jsonb_build_array($DESC$Outras coisas de fogo de Kethara que disputam os veios quentes$DESC$, $DESC$Serpe-Fornalha$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presenca dele diz que ha um veio de fogo vivo embaixo daquela ruina, e que o ar ali mata antes da mao.$DESC$,
'evitado_por', jsonb_build_array($DESC$Caravaneiros que leem o ar tremido e contornam a forja morta$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$A brasa do peito, que nao apaga$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Arcano / fogo que arde sem combustivel, calor de forja)$DESC$, 'risco', $DESC$Acende o que esta perto e queima a mao despreparada.$DESC$),
jsonb_build_object('material', $DESC$Metal vivo da carcaca, ainda quente$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Arcano / forja, ligas que guardam calor)$DESC$, 'risco', $DESC$Esquenta sozinho se deixado ao sol.$DESC$),
jsonb_build_object('material', $DESC$Escoria vidrada das pegadas$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (vidro de forja, lente rude)$DESC$, 'risco', $DESC$Corta como caco.$DESC$),
jsonb_build_object('material', $DESC$Cinza grossa do circulo queimado$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (potassa, curtume)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Assobio de ar quente e estalo de brasa dentro do metal.$DESC$,
'cheiro', $DESC$Metal quente, pedra cozida, cabelo chamuscado.$DESC$,
'quer', $DESC$Guardar o veio de fogo da forja dele e queimar quem chega perto.$DESC$,
'tipo_perigo', $DESC$Ambiental$DESC$,
'falas_exemplo', jsonb_build_array($DESC$O calor e meu. Voce so esta dentro dele.$DESC$, $DESC$Recue enquanto a pele ainda obedece.$DESC$, $DESC$(registro: voz que estala como metal esfriando, seca, em lingua de forja antiga e no comum com sotaque duro)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Alguem entra no circulo de ar quente em volta dele$DESC$, $DESC$Tentam tomar ou apagar o veio de fogo da forja$DESC$, $DESC$Agua jogada de leve que so o irrita sem apagar$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Recolhe-se ao veio de fogo quando o circulo de calor e apagado com agua farta$DESC$, $DESC$Larga o posto se o veio embaixo seca e ele esfria$DESC$, $DESC$Some forja adentro quando cercado de longe por muitos arqueiros$DESC$),
'descoberta_fazendo', $DESC$Parado no centro de uma forja morta de Kethara, reacendendo o metal velho em volta, dentro de um ar que ja treme de quente.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Ler o ar e contornar a forja sem entrar no circulo quente$DESC$, $DESC$Cortar ou desviar o veio de fogo que o alimenta, de longe$DESC$, $DESC$Despejar agua farta de uma vez para matar o calor e passar enquanto ele esfria$DESC$, $DESC$Negociar passagem: ele guarda a forja, nao o deserto, e deixa ir quem nao toca o fogo dele$DESC$)
),
status_conversao='canonizada'
WHERE id=783;

-- 1877 Juízo-Claro | Espírito | striker | Condicional | 13 Letal | Thornmarak | fala
UPDATE ref_criaturas SET
nome=$DESC$Juízo-Claro$DESC$,
nome_ptbr=$DESC$Juízo-Claro$DESC$,
slug=$DESC$juizo-claro$DESC$,
origem=$DESC$Cicatricial$DESC$,
andar_primario=$DESC$Clarão$DESC$,
pilar_associado=$DESC$Espírito$DESC$,
continente=ARRAY[$DESC$Thornmarak$DESC$]::text[],
habitat=$DESC$Altos de Thornmarak onde o Clarao chega perto, cristas de cristal e templos abertos ao ceu.$DESC$,
comportamento=$DESC$Fica parado como sentinela ate alguem cruzar uma linha que so ele conhece; ai acende e golpeia com fogo limpo, uma vez, certeiro, e volta a parar. Nao persegue inocente nem poupa culpado. Julga por regra, nao por do.$DESC$,
organizacao=$DESC$Sozinho, no posto que lhe coube.$DESC$,
perigo=$DESC$Letal$DESC$,
behavior_archetype=$DESC$striker$DESC$,
morale_modifier=0,
morale_immune=true,
epigrafe=$DESC$Chamam aquilo de anjo. Eu vi de perto: nao ha bondade nele, so uma regua, e a regua nao perdoa quem a cruza.$DESC$,
descricao=$DESC$Tem forma alta e severa, de luz dura e gume erguido, e o povo o chama de anjo por engano. Nao guarda ninguem por carinho: guarda uma regra. Enquanto ninguem cruza a linha, fica parado, frio, quase ornamento. Cruzada a linha, acende em fogo limpo e desce o gume uma vez so, no culpado, sem aviso e sem segunda chance, e depois volta ao posto como se nada. O fogo dele nao e raiva; e sentenca. Quem nao transgride passa ao lado dele e nada acontece.$DESC$,
supersticao_popular=$DESC$Em Thornmarak dizem que ha guardioes de luz nos altos, e que sao bons, e nisso o povo erra: eles nao sao bons, sao exatos. O conselho que funciona e saber a regra do lugar antes de subir, porque a punicao vem so de quem a quebra. Dizem que rezar amolece o guardiao; nao amolece. Saber o limite e nao cruzar, isso sim salva.$DESC$,
sinais_presenca=$DESC$Uma figura imovel de luz num alto, que parece estatua ate nao ser. Um calor seco e claro sem fonte de fogo. Marcas de queimado limpas, so num ponto, sem fuligem em volta. Cristal que zumbe baixinho perto do posto dele. Bichos que passam ao largo de uma linha invisivel no chao.$DESC$,
fraqueza_conhecida=$DESC$O povo tenta resistir ao fogo com agua e escudo, e reza pedindo do. Acha que e um inimigo a vencer, sem ver que ele so reage a quem transgride.$DESC$,
fraqueza_real=$DESC$Ele e condicional: parado e inofensivo ate a linha ser cruzada, e a linha e uma regra fixa do lugar. Quem descobre a regra e a respeita atravessa intocado; o fogo dele e forte mas vem uma vez e demora a recarregar. Lutar e o caminho ruim, porque ele e sentinela e nao cansa. O jeito e ler o limite, nao pisa-lo, e se ja foi pisado, sair da linha antes do gume descer.$DESC$,
descricao_sensorial=$DESC$O som e um cristal zumbindo baixo e o estalo de luz que acende de uma vez. O cheiro e de ar seco e limpo, sem fumaca. Ao toque, e calor de gume aceso que queima reto, sem brasa em volta. Aos olhos, e uma figura alta e severa de luz dura, parada ate o instante exato em que decide.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Nao caca; pune so quem cruza a linha que ele guarda$DESC$, $DESC$O transgressor que pisa o limite do posto dele$DESC$),
'predador', jsonb_build_array($DESC$Nada o derruba no posto; ele so deixa o lugar quando a regra que o prende se desfaz$DESC$),
'competidor', jsonb_build_array($DESC$Outras sentinelas de luz de Thornmarak com regras vizinhas$DESC$, $DESC$Clarim-Solene$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presenca dele diz que aquele alto guarda uma regra antiga, e que ha uma linha ali que custa caro cruzar.$DESC$,
'evitado_por', jsonb_build_array($DESC$Peregrinos que aprendem a regra do alto e a cumprem antes de subir$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$Um fio da luz dura que ele empunha$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Eco do Clarao / corte limpo, luz que julga)$DESC$, 'risco', $DESC$Queima reto quem o segura sem direito, sem deixar marca de fumaca.$DESC$),
jsonb_build_object('material', $DESC$Lasca de cristal que zumbe do posto dele$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Arcano / foco de luz, alarme contra transgressao)$DESC$, 'risco', $DESC$Zumbe e aquece perto de quem mente.$DESC$),
jsonb_build_object('material', $DESC$Po claro do chao queimado limpo$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (pigmento branco, marca de limite)$DESC$, 'risco', $DESC$Nenhum alem do brilho que denuncia.$DESC$),
jsonb_build_object('material', $DESC$Cinza seca do ponto de sentenca$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (po alvejante)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Cristal zumbindo baixo e o estalo de luz acesa de uma vez.$DESC$,
'cheiro', $DESC$Ar seco e limpo, sem fumaca.$DESC$,
'quer', $DESC$Guardar a regra do alto e punir, uma vez e certeiro, quem cruza a linha.$DESC$,
'tipo_perigo', $DESC$Condicional$DESC$,
'falas_exemplo', jsonb_build_array($DESC$A regra esta posta. Eu nao a fiz; eu a cumpro.$DESC$, $DESC$Recue do limite e nada lhe acontece. Pise-o e ja esta feito.$DESC$, $DESC$(registro: voz clara, igual, sem do nem raiva, como quem le uma sentenca ja escrita)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Alguem cruza a linha invisivel que marca o posto dele$DESC$, $DESC$Toca-se ou se profana o que ele guarda no alto$DESC$, $DESC$Um transgressor confesso entra no alcance do gume$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Volta a imovel assim que o transgressor sai da linha ou cai$DESC$, $DESC$Deixa o posto so quando a regra antiga que o prende e desfeita$DESC$, $DESC$Cessa o golpe quando o erro e desfeito antes do gume descer$DESC$),
'descoberta_fazendo', $DESC$Imovel como estatua num alto de cristal de Thornmarak, de gume baixo, esperando que alguem cruze a linha que ele guarda.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Descobrir a regra do alto e cumpri-la, passando intocado$DESC$, $DESC$Recuar da linha no instante em que se percebe que foi pisada$DESC$, $DESC$Desfazer a transgressao, devolvendo, saindo ou reparando, antes da sentenca$DESC$, $DESC$Achar e desfazer a regra antiga que o prende ali, para que ele largue o posto$DESC$)
),
status_conversao='canonizada'
WHERE id=1877;

-- 1833 Sorvo-Calado | Engenho | lurker | Oculto | 14 Letal | Voranthar | fala
UPDATE ref_criaturas SET
nome=$DESC$Sorvo-Calado$DESC$,
nome_ptbr=$DESC$Sorvo-Calado$DESC$,
slug=$DESC$sorvo-calado$DESC$,
origem=$DESC$Marginal$DESC$,
andar_primario=$DESC$Margem$DESC$,
pilar_associado=$DESC$Engenho$DESC$,
continente=ARRAY[$DESC$Voranthar$DESC$]::text[],
habitat=$DESC$Ruinas fundas de Voranthar onde a Margem e fina e o ar para; corredores sem vento.$DESC$,
comportamento=$DESC$Anda invisivel e calado, passa atraves de parede, e chega por tras para sorver o folego de quem dorme ou se distrai. Bate e some antes de virem o que foi. Some quando notado, e volta quando o ar aquieta.$DESC$,
organizacao=$DESC$Sozinho, um por trecho de ruina.$DESC$,
perigo=$DESC$Letal$DESC$,
behavior_archetype=$DESC$lurker$DESC$,
morale_modifier=-1,
morale_immune=false,
epigrafe=$DESC$O folego do meu companheiro simplesmente parou de sair, na frente do nada. Quando virei a tocha, nao havia o que iluminar.$DESC$,
descricao=$DESC$E uma coisa que quase nao se ve: um corte no ar, um arrepio, e o folego de alguem que falha sem motivo. Anda invisivel e passa por parede como por cortina, e por tras enfia uma garra que tira a forca, ou cola na boca e sorve o folego e a vontade ate a pessoa amolecer. Sente a luz e a engole; tocha perto dela dura menos. Bate uma vez, forte, e some, e so reaparece quando o trecho volta a ficar quieto. Caca folego, nao carne.$DESC$,
supersticao_popular=$DESC$Em Voranthar dizem que ha corredores onde a tocha morre e o ar suga, e que e ali que alguem fica sem folego do nada. O conselho dos que sabem: nao andar calado e separado naquele fundo, manter luz farta e gente perto, porque ela odeia ser vista. Dizem que metal sagrado a fere; o que fere mesmo e o olho que a acha.$DESC$,
sinais_presenca=$DESC$Tochas que encurtam e morrem sem vento. Um arrepio de nuca num corredor sem corrente de ar. O folego de um companheiro que falha sem ferida nenhuma. Poeira que se mexe onde nada passou. Um silencio denso, sem eco, num trecho fundo.$DESC$,
fraqueza_conhecida=$DESC$O povo anda em grupo, com muita luz, e bate no ar quando sente o arrepio. Acha que arma sagrada resolve, sem ver que primeiro tem de achar onde ela esta.$DESC$,
fraqueza_real=$DESC$Ela vive de nao ser vista: invisivel, sorve e some, e foge cedo quando a descobrem. O que a quebra e a revelacao, fazer o invisivel aparecer, com po, fumaca, agua jogada no ar ou um sentido que nao depende do olho. Vista e cercada, ela e fraca e foge; e ela come a luz, entao luz demais a incomoda mas nao a mata. Marcar o ar e fechar a saida vale mais que golpear no escuro.$DESC$,
descricao_sensorial=$DESC$O som e quase nenhum: um chiado fino de ar sendo puxado e o silencio que vem junto. O cheiro e de ar parado, frio e sem poeira, limpo demais. Ao toque, e um frio cortante de nada solido, e a garra que tira a forca sem peso. Aos olhos, e o que nao se ve: um vinco no ar, a tocha que cede, o folego do outro que para.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$O folego e a vontade de quem dorme ou se distrai no fundo de Voranthar$DESC$, $DESC$Viajantes separados do grupo num corredor sem vento$DESC$),
'predador', jsonb_build_array($DESC$Vista e cercada, e fraca; o olho que a acha a encerra$DESC$),
'competidor', jsonb_build_array($DESC$Outras coisas da Margem em Voranthar que disputam o ar parado$DESC$, $DESC$Suga-Juízo$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presenca dela diz que a Margem esta fina naquele corredor, e que a tocha e o folego ali nao duram.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem anda em grupo cerrado, com muita luz, e marca o ar ao primeiro arrepio$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$A glandula com que ela sorve o folego$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Engenho / tirar folego e amolecer a vontade alheia)$DESC$, 'risco', $DESC$Puxa o ar de quem a manuseia sem preparo.$DESC$),
jsonb_build_object('material', $DESC$O resto frio que ela deixa onde a luz morreu$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Sombra / apagar luz, abafar som num trecho)$DESC$, 'risco', $DESC$Encurta a chama perto de si.$DESC$),
jsonb_build_object('material', $DESC$Po que so aparece colado nela$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (revela o invisivel quando soprado no ar)$DESC$, 'risco', $DESC$Denuncia tambem quem o carrega.$DESC$),
jsonb_build_object('material', $DESC$Ar parado preso num frasco selado$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (curiosidade, vazio para experimento)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Chiado fino de ar puxado e um silencio sem eco.$DESC$,
'cheiro', $DESC$Ar parado, frio, limpo demais.$DESC$,
'quer', $DESC$Sorver folego e vontade sem nunca ser vista, e sumir antes que a achem.$DESC$,
'tipo_perigo', $DESC$Oculto$DESC$,
'falas_exemplo', jsonb_build_array($DESC$Voce nao vai me ver. Vai so sentir o ar ficar curto.$DESC$, $DESC$Fique quieto. Quem grita gasta o folego que eu quero.$DESC$, $DESC$(registro: voz que chega por dentro da cabeca, sem som no ar, baixa e sem pressa, em lingua do fundo e no comum)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Alguem se separa do grupo num corredor sem vento$DESC$, $DESC$Uma luz forte a incomoda e ela cala a fonte$DESC$, $DESC$Acham um dorminhoco de folego farto e desprotegido$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Some assim que e revelada e cercada, porque odeia ser vista$DESC$, $DESC$Larga a presa e atravessa a parede quando a luz vira demais$DESC$, $DESC$Recua para o ar parado mais fundo quando marcam o ar dela$DESC$),
'descoberta_fazendo', $DESC$Invisivel num corredor fundo de Voranthar, colada na boca de alguem que dorme, sorvendo o folego em silencio enquanto a tocha do grupo morre devagar.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Andar em grupo cerrado e com muita luz, negando a ela a presa separada$DESC$, $DESC$Revelar o invisivel com po, fumaca ou agua no ar e cerca-la para faze-la fugir$DESC$, $DESC$Fechar a saida do corredor e marcar o ar, sem golpear o escuro a esmo$DESC$, $DESC$Tirar o ferido do trecho sem vento, ja que ela nao segue para fora do ar parado$DESC$)
),
status_conversao='canonizada'
WHERE id=1833;

-- ========================= GRUPO 2 =========================

-- 915 Tora-Quieta | Corpo | ambusher | Oculto | 5 Ameaça | Kethara | MUDO
UPDATE ref_criaturas SET
nome=$DESC$Tora-Quieta$DESC$,
nome_ptbr=$DESC$Tora-Quieta$DESC$,
slug=$DESC$tora-quieta$DESC$,
origem=$DESC$Natural$DESC$,
andar_primario=$DESC$Superfície$DESC$,
pilar_associado=$DESC$Corpo$DESC$,
continente=ARRAY[$DESC$Kethara$DESC$]::text[],
habitat=$DESC$Os poucos rios e oasis de Kethara, as margens de lama e os vaus onde a caravana atravessa.$DESC$,
comportamento=$DESC$Boia parada como tronco, so olhos e narina de fora, e espera o que vem beber. Quando a presa chega ao alcance, fecha a boca e arrasta para o fundo num giro. Fora isso, fica quieta, economizando o corpo.$DESC$,
organizacao=$DESC$Sozinha, cada uma com seu trecho de agua. Varias podem dividir um oasis grande.$DESC$,
perigo=$DESC$Ameaça$DESC$,
behavior_archetype=$DESC$ambusher$DESC$,
morale_modifier=1,
morale_immune=false,
epigrafe=$DESC$O tronco no vau mexeu quando o boi passou. Nao era tronco, e o boi nao chegou na outra margem.$DESC$,
descricao=$DESC$De longe e um tronco velho boiando no vau, imovel, com casca de lama. De perto, tarde demais, e uma boca do tamanho de uma porta. Fica parada horas, so os olhos de fora, e deixa a sede dos outros trazer o jantar ate ela. No bote, fecha a mandibula, gira e leva para o fundo, onde a presa se afoga antes de virar comida. Nao persegue em terra por muito tempo; o oficio dela e a espera e o primeiro bote.$DESC$,
supersticao_popular=$DESC$Nos vaus de Kethara dizem para nunca beber no mesmo ponto duas vezes, e para desconfiar de tronco que nao estava ali ontem. O conselho e atravessar onde a agua e rasa e corre, nunca na poca parada, e mandar o animal de carga na frente. Dizem que bater na agua a espanta; as vezes so a avisa que chegou comida.$DESC$,
sinais_presenca=$DESC$Um tronco no vau que mudou de lugar desde a ultima vez. Dois pontos de olho na linha da agua, parados. Trilhas largas de arrasto na lama da margem. Ossos limpos presos numa toca submersa. Passaros que nao pousam em certo trecho de margem.$DESC$,
fraqueza_conhecida=$DESC$O povo evita a agua parada, manda o bicho na frente e bate na superficie. Acha que em terra esta a salvo, e em parte esta, se nao estiver na beira.$DESC$,
fraqueza_real=$DESC$A forca dela e o primeiro bote da emboscada e o arrasto para o fundo; gasto o bote, em terra firme ela e lenta e cansa rapido. Quem a tira da agua, ou a obriga a dar o bote cedo e fora do alcance, fica com um bicho pesado e sem manha longe do elemento dele. Ver o tronco antes do bote e meio caminho; uma vara longa que cutuca a poca revela a quieta.$DESC$,
descricao_sensorial=$DESC$O som e quase nenhum, so um marulho oleoso quando ela se ajeita e o estalo seco da mandibula no bote. O cheiro e de lama podre e peixe velho. Ao toque, e couro de placa fria coberto de lodo. Aos olhos, e um tronco escuro e imovel que, de repente, tem olhos e abre ao meio.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Bichos de carga e gente que para para beber no vau$DESC$, $DESC$Animais que cruzam o trecho de agua dela$DESC$),
'predador', jsonb_build_array($DESC$Em terra firme e lenta e vulneravel; fora dagua perde a vantagem$DESC$),
'competidor', jsonb_build_array($DESC$Outros bichos de emboscada de Kethara que disputam o mesmo vau$DESC$, $DESC$Couraça-Afogada$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presenca dela diz que aquele vau e caro de cruzar, e que tronco parado ali pode nao ser tronco.$DESC$,
'evitado_por', jsonb_build_array($DESC$Caravaneiros que so atravessam na agua rasa e corrente e mandam o animal na frente$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$Couro de placa das costas$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Corpo / couro duro de armadura, escudo)$DESC$, 'risco', $DESC$Pesa e endurece se nao curtido a tempo.$DESC$),
jsonb_build_object('material', $DESC$Dentes longos da mandibula$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (ponta de lanca, anzol grande)$DESC$, 'risco', $DESC$Corta a mao que limpa sem cuidado.$DESC$),
jsonb_build_object('material', $DESC$Banha que boia$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (graxa de impermeabilizar couro)$DESC$, 'risco', $DESC$Nenhum.$DESC$),
jsonb_build_object('material', $DESC$Lodo e casca seca das costas$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (camuflagem, adubo)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Marulho oleoso e o estalo seco da mandibula no bote.$DESC$,
'cheiro', $DESC$Lama podre e peixe velho.$DESC$,
'quer', $DESC$Esperar imovel e abocanhar o que vem beber, sem gastar corpo a toa.$DESC$,
'tipo_perigo', $DESC$Oculto$DESC$,
'falas_exemplo', 'null'::jsonb,
'gatilhos_agressao', jsonb_build_array($DESC$Uma presa para para beber ao alcance do bote dela$DESC$, $DESC$Algo entra na poca parada onde ela espera$DESC$, $DESC$Mexem na toca submersa onde ela guarda a comida$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Some para o fundo quando o bote falha e a presa reage em peso$DESC$, $DESC$Larga a caca se a tiram para terra firme, onde e lenta$DESC$, $DESC$Abandona o vau quando ele seca ou vira passagem movimentada demais$DESC$),
'descoberta_fazendo', $DESC$Boiando imovel como tronco num vau de Kethara, so olhos e narina de fora, esperando a proxima sede chegar a margem.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Atravessar na agua rasa e corrente, nunca na poca parada$DESC$, $DESC$Mandar o animal de carga na frente e cruzar atras$DESC$, $DESC$Cutucar a poca com vara longa para revelar o tronco antes do bote$DESC$, $DESC$Dar a volta e usar outro vau quando o tronco mudou de lugar$DESC$)
),
status_conversao='canonizada'
WHERE id=915;

-- 1190 Lívido-Sôfrego | Sombra | predator | Direto | 5 Ameaça | Vyrkhor | fala
UPDATE ref_criaturas SET
nome=$DESC$Lívido-Sôfrego$DESC$,
nome_ptbr=$DESC$Lívido-Sôfrego$DESC$,
slug=$DESC$livido-sofrego$DESC$,
origem=$DESC$Cicatricial$DESC$,
andar_primario=$DESC$Eco$DESC$,
pilar_associado=$DESC$Sombra$DESC$,
continente=ARRAY[$DESC$Vyrkhor$DESC$]::text[],
habitat=$DESC$Ruinas e criptas geladas de Vyrkhor, vilarejos de montanha onde alguem maior os deixou para tras.$DESC$,
comportamento=$DESC$Caca sangue de noite, sobe parede e teto, e ataca direto e rapido, garra e dentada, sem muita manha. Servo de algo maior, as vezes solto e por conta. Foge da luz do dia para a cripta.$DESC$,
organizacao=$DESC$Em ninhada de poucos, sob um mestre que pode nao estar mais por perto.$DESC$,
perigo=$DESC$Ameaça$DESC$,
behavior_archetype=$DESC$predator$DESC$,
morale_modifier=0,
morale_immune=false,
epigrafe=$DESC$Entrou pela janela do segundo andar, de cabeca para baixo no teto, com pressa de quem nao comia ha dias.$DESC$,
descricao=$DESC$Foi gente, e ainda lembra a forma, mas o que sobrou e fome e palidez. Bebe sangue para nao secar, e sem ele murcha e enfraquece. Sobe parede e teto como inseto e cai sobre a presa com garra e dentada, direto, sem rodeio: e rapido e faminto, nao astuto. A luz do sol o queima e o apavora, entao caca de noite e dorme na pedra fria de dia. Sozinho e perigo de uma noite; em ninhada, de uma vila inteira.$DESC$,
supersticao_popular=$DESC$Em Vyrkhor dizem que certas criptas cospem bebedores de sangue de noite, e que a luz do dia e a salvacao. O conselho que vale: trancar-se com fogo e janela alta vedada, e nunca convidar para entrar o que bate palido a porta. Dizem que estaca no peito mata; ajuda, mas o que de fato resolve e o sol e o fogo.$DESC$,
sinais_presenca=$DESC$Gado e gente achados secos, com duas feridas no pescoco e pouco sangue em volta. Marcas de mao subindo parede ate a janela alta. Janelas abertas por dentro em noite fria. Um cheiro adocicado de sangue velho na cripta. Sumico de moradores so depois do anoitecer.$DESC$,
fraqueza_conhecida=$DESC$O povo usa luz, fogo e estaca, e se tranca de noite. Sabe do sol, e por isso espera o amanhecer. Acha a estaca o ponto, sem ver que e o atraso, nao o fim.$DESC$,
fraqueza_real=$DESC$Ele e direto e faminto, sem astucia, e a fome o torna imprudente: cai numa isca de presa exposta. O sol o queima de verdade e o fogo o apavora; preso fora da cripta ate o amanhecer, ele mesmo se acaba na luz. Cortar o acesso a cripta e segura-lo ate o dia vale mais que troca-lo golpe a golpe no escuro, onde ele e rapido.$DESC$,
descricao_sensorial=$DESC$O som e o arranhar de unha em parede e um rosnado faminto, baixo. O cheiro e adocicado e enjoativo, de sangue velho e pedra fria. Ao toque, e pele fria e seca, dura como couro curtido. Aos olhos, e uma figura palida de gente, de boca suja, que se move rapido demais e no lugar errado, no teto.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Sangue de gado e de gente das vilas de montanha de Vyrkhor$DESC$, $DESC$Viajantes pegos sozinhos depois do anoitecer$DESC$),
'predador', jsonb_build_array($DESC$O sol do dia e o fogo o acabam; preso na luz, termina sozinho$DESC$),
'competidor', jsonb_build_array($DESC$Outros bebedores e mortos de Vyrkhor que disputam o mesmo sangue$DESC$, $DESC$Sede-Pálida$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presenca dele diz que ha uma cripta ativa por perto e um mestre maior que pode estar solto, e que a noite ali cobra sangue.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem se tranca com fogo ao anoitecer e veda a janela alta$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$A glandula de sede que o mantem de pe$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Sombra / sugar vigor e resistir ao secar)$DESC$, 'risco', $DESC$Da uma sede que nao passa a quem prova sem preparo.$DESC$),
jsonb_build_object('material', $DESC$Unhas de subir parede, ainda presas a mao$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Corpo / escalar liso, agarrar firme)$DESC$, 'risco', $DESC$Fincam na carne de quem as usa errado.$DESC$),
jsonb_build_object('material', $DESC$Dentes finos da dentada$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (agulha, ponta fina)$DESC$, 'risco', $DESC$Mancham de sangue velho o que tocam.$DESC$),
jsonb_build_object('material', $DESC$Trapo da mortalha que ainda veste$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (pano de cripta)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Arranhar de unha em parede e um rosnado faminto e baixo.$DESC$,
'cheiro', $DESC$Adocicado e enjoativo, sangue velho e pedra fria.$DESC$,
'quer', $DESC$Beber sangue para nao secar, e cacar farto antes que o sol volte.$DESC$,
'tipo_perigo', $DESC$Direto$DESC$,
'falas_exemplo', jsonb_build_array($DESC$Tao pouco sangue, e ja correm. Fiquem. So um gole.$DESC$, $DESC$Faz tanto tempo. Voce nem vai sentir, no frio.$DESC$, $DESC$(registro: voz rouca e apressada, de fome mal contida, no comum e numa lingua de antes da morte dele)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Uma presa exposta de noite, ao alcance, com a fome dele alta$DESC$, $DESC$Sangue fresco no ar, de ferida ou abate recente$DESC$, $DESC$Alguem bloqueia o caminho de volta dele para a cripta$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Corre para a cripta quando o ceu comeca a clarear$DESC$, $DESC$Recua do fogo, que o apavora mais que o ferro$DESC$, $DESC$Larga a caca e foge quando o sol e usado contra ele de proposito$DESC$),
'descoberta_fazendo', $DESC$De cabeca para baixo num teto de cripta gelada de Vyrkhor, ou subindo a parede de uma casa atras da janela alta, faminto, pouco antes da meia-noite.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Trancar-se com fogo e vedar a janela alta ate o amanhecer$DESC$, $DESC$Atrai-lo para fora da cripta e segura-lo ate o sol nascer$DESC$, $DESC$Cortar e selar o acesso a cripta onde a ninhada dorme de dia$DESC$, $DESC$Usar isca de presa exposta para leva-lo a um aberto que o sol vai varrer$DESC$)
),
status_conversao='canonizada'
WHERE id=1190;

-- 1106 Inço-Rubro | Arcano | brute | Persistente | 5 Ameaça | Thornmarak | fala
UPDATE ref_criaturas SET
nome=$DESC$Inço-Rubro$DESC$,
nome_ptbr=$DESC$Inço-Rubro$DESC$,
slug=$DESC$inco-rubro$DESC$,
origem=$DESC$Marginal$DESC$,
andar_primario=$DESC$Margem$DESC$,
pilar_associado=$DESC$Arcano$DESC$,
continente=ARRAY[$DESC$Thornmarak$DESC$]::text[],
habitat=$DESC$Brejos e baixadas de Thornmarak onde a Margem vazou, mato encharcado e poca quente.$DESC$,
comportamento=$DESC$Avança reto, aguenta golpe e fecha a carne sozinho; a garra dele nao so corta, injeta uma praga vermelha que adoece e se espalha. Nao recua quase nunca: o corpo se conserta mais rapido do que se gasta.$DESC$,
organizacao=$DESC$Sozinho ou em poucos, espalhando o mal pela baixada.$DESC$,
perigo=$DESC$Ameaça$DESC$,
behavior_archetype=$DESC$brute$DESC$,
morale_modifier=2,
morale_immune=false,
epigrafe=$DESC$Cortei o bicho ao meio e ele se levantou inteiro. O corte que ele me deu, esse nao fechou; piorou.$DESC$,
descricao=$DESC$E um bruto vermelho de corpo de sapo grande, alto como um homem e largo como dois, vindo de onde a Margem vazou no brejo. Avança de frente e aguenta o que recebe, porque a carne dele se costura sozinha quase tao rapido quanto se rasga. A garra abre a pele e enfia dentro uma praga rubra que adoece a ferida e nao quer parar de crescer. Cansa-se pouco e recua menos; o jeito dele e a teima do corpo que nao acaba.$DESC$,
supersticao_popular=$DESC$Em Thornmarak dizem que ha sapos vermelhos do tamanho de gente nas baixadas ruins, e que o corte deles apodrece. O conselho e fogo: queimar a ferida na hora, antes que a praga pegue, e queimar o bicho todo, porque ferro so o irrita. Dizem que a cabeca cortada mata; nao mata, se o resto ainda se mexe.$DESC$,
sinais_presenca=$DESC$Carcacas de bicho inchadas e vermelhas na beira do brejo. Poca de agua quente com um veu rubro por cima. Um coaxar grave que faz a lama tremer. Plantas mortas em circulo, com brotos vermelhos no meio. Feridas que nao fecham em quem passou por ali.$DESC$,
fraqueza_conhecida=$DESC$O povo usa fogo na ferida e no bicho, e sabe que ferro nao basta. Acha que cortar em pedacos resolve, sem ver que cada pedaco ainda e perigo enquanto se mexe.$DESC$,
fraqueza_real=$DESC$A forca dele e a regeneracao: gasta-se devagar e conserta-se rapido, entao a troca de golpes favorece ele. O fogo e o acido fecham a cura, porque o que ele refaz de carne nao volta do que foi queimado. Quem o mantem em chama, ou o tira da agua e do calor do brejo que o sustenta, ve a teima ceder. A praga da garra se mata cauterizando a ferida cedo, antes de pegar.$DESC$,
descricao_sensorial=$DESC$O som e um coaxar grave que vibra na lama e o estalo molhado da carne se fechando. O cheiro e de brejo quente, podre e adocicado. Ao toque, e pele umida e febril, quente demais para um bicho. Aos olhos, e uma massa vermelha e larga que se ergue do mato encharcado, ja se curando do ultimo corte.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Bichos e gente das baixadas de Thornmarak que ele adoece e come$DESC$, $DESC$Tudo que vive no brejo que ele toma e corrompe$DESC$),
'predador', jsonb_build_array($DESC$Fogo e acido, que impedem a cura; sem isso, poucos o derrubam$DESC$),
'competidor', jsonb_build_array($DESC$Outras coisas da Margem em Thornmarak que disputam a baixada$DESC$, $DESC$Vulto-de-Fora$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presenca dele diz que a Margem vazou naquela baixada, e que a praga rubra ja esta na agua e na carne dali.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem nao entra em brejo de veu vermelho e queima a ferida na hora$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$A carne que se recose sozinha$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Corpo / regenerar, fechar ferida grave)$DESC$, 'risco', $DESC$Cresce alem do molde e pega a praga rubra junto.$DESC$),
jsonb_build_object('material', $DESC$A glandula da garra que injeta a praga$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Arcano / praga que adoece e se espalha)$DESC$, 'risco', $DESC$Contamina quem a abre sem queimar as maos.$DESC$),
jsonb_build_object('material', $DESC$Couro vermelho e umido das costas$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (couro grosso, impermeavel)$DESC$, 'risco', $DESC$Apodrece se nao salgado rapido.$DESC$),
jsonb_build_object('material', $DESC$Limo rubro do brejo dele$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (tinta, isca de podre)$DESC$, 'risco', $DESC$Nenhum se seco.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Coaxar grave que vibra na lama e o estalo molhado da carne se fechando.$DESC$,
'cheiro', $DESC$Brejo quente, podre e adocicado.$DESC$,
'quer', $DESC$Espalhar a praga rubra pela baixada e comer o que ela adoece, sem nunca parar de se refazer.$DESC$,
'tipo_perigo', $DESC$Persistente$DESC$,
'falas_exemplo', jsonb_build_array($DESC$Corta. Corta de novo. Eu volto inteiro, e voce nao.$DESC$, $DESC$O que entrou em voce ja esta crescendo. Sente?$DESC$, $DESC$(registro: voz grave e gargarejada, em lingua de fundo de brejo, lenta e sem medo)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Algo entra na baixada que ele tomou$DESC$, $DESC$Alguem o fere e fica ao alcance da garra que injeta$DESC$, $DESC$Tentam tirar dali a agua quente que o sustenta$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Mergulha na poca quente para se refazer quando o fogo o cerca$DESC$, $DESC$Recua so quando a chama impede a cura e nao ha agua perto$DESC$, $DESC$Larga a presa se a baixada seca ou queima inteira$DESC$),
'descoberta_fazendo', $DESC$Parado numa poca quente de Thornmarak coberta de veu vermelho, coaxando grave, enquanto a praga rubra dele toma a baixada em volta.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Nao entrar em brejo de veu vermelho e contornar a baixada$DESC$, $DESC$Queimar a ferida na hora se a garra pegar, antes de a praga crescer$DESC$, $DESC$Drenar ou esfriar a poca quente que o sustenta, tirando a vantagem dele$DESC$, $DESC$Atrai-lo para terra seca e firme, longe da agua que o refaz$DESC$)
),
status_conversao='canonizada'
WHERE id=1106;

-- 2024 Aurora-Morta | Espírito | controller | Ambiental | 5 Ameaça | Vyrkhor | MUDO
UPDATE ref_criaturas SET
nome=$DESC$Aurora-Morta$DESC$,
nome_ptbr=$DESC$Aurora-Morta$DESC$,
slug=$DESC$aurora-morta$DESC$,
origem=$DESC$Cicatricial$DESC$,
andar_primario=$DESC$Eco$DESC$,
pilar_associado=$DESC$Espírito$DESC$,
continente=ARRAY[$DESC$Vyrkhor$DESC$]::text[],
habitat=$DESC$Campos de neve e passos altos de Vyrkhor, onde uma luz fria anda sozinha de noite.$DESC$,
comportamento=$DESC$Caminha devagar e leva o frio consigo: em volta, o ar congela e a mortandade gelada toma quem fica perto demais. A luz fria que solta cega o olho. Nao corre, nao recua, so avanca e deixa o gelo trabalhar a area.$DESC$,
organizacao=$DESC$Sozinha, rara, marcando um passo de montanha inteiro.$DESC$,
perigo=$DESC$Ameaça$DESC$,
behavior_archetype=$DESC$controller$DESC$,
morale_modifier=0,
morale_immune=true,
epigrafe=$DESC$Pensei que fosse o amanhecer chegando cedo no passo. Era uma luz que andava, e onde ela passou o riacho virou pedra.$DESC$,
descricao=$DESC$Parece uma aurora fria que se soltou do ceu e desceu a andar pela neve: uma figura de luz palida e azulada, devagar, que nao aquece nada. Onde ela passa, o ar congela, a agua endurece e quem fica perto sente o frio mortal subir pelos pes. A luz que ela emana cega quem olha de frente. Nao tem pressa nem raiva, e nao se demove: e morta, e leva o inverno consigo como quem leva a propria sombra.$DESC$,
supersticao_popular=$DESC$Em Vyrkhor dizem que ha uma luz que anda nos passos altos, e que e a aurora errada, e que segui-la mata. O conselho e nunca caminhar na direcao de uma luz baixa que se move no campo de neve, e procurar abrigo quente e fechado quando ela aparece. Dizem que fogo a afasta; o fogo mantem o frio dela longe, mas nao a apaga.$DESC$,
sinais_presenca=$DESC$Uma luz fria e baixa que anda devagar no campo de neve, sem fonte. Agua corrente que virou pedra de gelo de um lado so. Cristais de geada subindo onde nao havia. Um clarao palido que cega quem encara. Bichos congelados de pe, no rumo por onde a luz passou.$DESC$,
fraqueza_conhecida=$DESC$O povo foge da luz, busca abrigo e acende fogo grande. Sabe que olhar de frente cega. Acha que e questao de correr mais que a luz, e a luz e lenta, entao em parte funciona.$DESC$,
fraqueza_real=$DESC$O perigo dela e a area: o frio que mata em volta e a luz que cega, nao um golpe. Ela e lenta e nao persegue longe; quem sai do raio do frio fica a salvo. Fogo forte e abrigo fechado seguram o gelo, e calor concentrado contra ela a enfraquece. Nao se deve encara-la nem ficar parado no rasto dela; basta sair da area e ela segue o caminho dela, indiferente.$DESC$,
descricao_sensorial=$DESC$O som e um estalo fino de agua virando gelo e um zumbido baixo de luz. O cheiro e de ar limpo e cortante, sem cheiro de vida. Ao toque, e o frio que queima de tao gelado, antes do contato. Aos olhos, e uma figura palida e luminosa, azulada, que cega se encarada e nao projeta calor nenhum.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Nao caca; congela e cega o que fica no caminho dela$DESC$, $DESC$Viajantes que seguem a luz achando que e o amanhecer$DESC$),
'predador', jsonb_build_array($DESC$O calor concentrado e o fogo grande a enfraquecem; sair da area basta$DESC$),
'competidor', jsonb_build_array($DESC$Outras coisas frias de Vyrkhor que disputam os passos altos$DESC$, $DESC$Brasa-Óssea$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presenca dela diz que aquele passo virou armadilha de frio, e que a luz baixa ali nao e amanhecer nenhum.$DESC$,
'evitado_por', jsonb_build_array($DESC$Montanheses que se abrigam e nunca seguem luz que anda na neve$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$O nucleo de luz fria do peito$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Eco / frio que mata em area, luz que cega)$DESC$, 'risco', $DESC$Congela a mao e cega o olho de quem o destampa.$DESC$),
jsonb_build_object('material', $DESC$Geada que nao derrete, colhida do rasto$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Arcano / conservar no frio, endurecer agua)$DESC$, 'risco', $DESC$Queima de gelo ao toque longo.$DESC$),
jsonb_build_object('material', $DESC$Cristais palidos do chao por onde passou$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (lente fria, adorno que reluz)$DESC$, 'risco', $DESC$Embaca e racha no calor.$DESC$),
jsonb_build_object('material', $DESC$Neve compactada do rasto$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (agua limpa quando derretida)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Estalo fino de agua virando gelo e um zumbido baixo de luz.$DESC$,
'cheiro', $DESC$Ar limpo e cortante, sem cheiro de vida.$DESC$,
'quer', $DESC$Caminhar seu passo levando o inverno, congelando e cegando o que ficar perto.$DESC$,
'tipo_perigo', $DESC$Ambiental$DESC$,
'falas_exemplo', 'null'::jsonb,
'gatilhos_agressao', jsonb_build_array($DESC$Alguem entra no raio de frio que anda com ela$DESC$, $DESC$Encaram a luz dela de frente, ao alcance do clarao$DESC$, $DESC$Param no rasto gelado dela em vez de sair$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Segue o proprio caminho, indiferente, quando saem da area dela$DESC$, $DESC$Recua do fogo grande e do calor concentrado$DESC$, $DESC$Perde forca e cede quando o frio dela e quebrado por calor farto$DESC$),
'descoberta_fazendo', $DESC$Caminhando devagar por um passo alto de Vyrkhor, uma luz fria e baixa na neve, deixando agua virada em pedra e bicho congelado de pe no rasto.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Sair do raio de frio e deixar a luz seguir o caminho dela$DESC$, $DESC$Buscar abrigo fechado e acender fogo grande ate ela passar$DESC$, $DESC$Nunca seguir a luz baixa achando que e o amanhecer$DESC$, $DESC$Usar calor concentrado para abrir passagem sem encara-la$DESC$)
),
status_conversao='canonizada'
WHERE id=2024;

-- 2135 Eleito-Torto | Engenho | soldier | Condicional | 5 Ameaça | Kethara | fala
UPDATE ref_criaturas SET
nome=$DESC$Eleito-Torto$DESC$,
nome_ptbr=$DESC$Eleito-Torto$DESC$,
slug=$DESC$eleito-torto$DESC$,
origem=$DESC$Marginal$DESC$,
andar_primario=$DESC$Margem$DESC$,
pilar_associado=$DESC$Engenho$DESC$,
continente=ARRAY[$DESC$Kethara$DESC$]::text[],
habitat=$DESC$Ruinas de areia e cavernas de Kethara onde a Margem tocou; postos tomados por bandos.$DESC$,
comportamento=$DESC$Lidera um bando com a vontade: ataca com lamina carregada de pensamento e so se acende quando o bando dele e desafiado ou quando se ve como o eleito de algo. Soldado disciplinado, briga em formacao e usa os menores como linha de frente.$DESC$,
organizacao=$DESC$A frente de um bando, como chefe-eleito; raramente sozinho.$DESC$,
perigo=$DESC$Ameaça$DESC$,
behavior_archetype=$DESC$soldier$DESC$,
morale_modifier=1,
morale_immune=false,
epigrafe=$DESC$O bicho pequeno no meio deles nao gritava ordem. So olhava, e os outros sabiam o que fazer.$DESC$,
descricao=$DESC$E um goblinoide tocado pela Margem que se diz o eleito, e o bando dele acredita. Carrega uma lamina que zumbe de pensamento e corta a mente junto com a carne, e comanda a tropa sem precisar gritar: a vontade dele chega direto na cabeca dos seus. Disciplinado, briga em linha, poe os menores na frente e guarda a si. So se acende de fato quando o bando e desafiado ou quando duvidam do posto dele de eleito; ai vira soldado frio e exato.$DESC$,
supersticao_popular=$DESC$Em Kethara dizem que certos bandos das ruinas tem um chefe pequeno que manda pelo olhar, e que matar a tropa nao resolve enquanto o pequeno vive. O conselho dos que sabem: achar o eleito no meio da linha e ir nele, porque sem ele a tropa perde o rumo. Dizem que ele e covarde; nao e bem isso, ele e cuidadoso e se guarda atras dos seus.$DESC$,
sinais_presenca=$DESC$Um bando que se move junto demais, em silencio, sem ordem gritada. Laminas que zumbem baixo num tom que da dor de cabeca. Postos de ruina tomados e organizados, com sentinela. Pegadas miudas no centro de pegadas maiores. Uma pressao na testa de quem chega perto do chefe.$DESC$,
fraqueza_conhecida=$DESC$O povo tenta quebrar a tropa, e ela se refaz; tenta o chefe, e ele se esconde atras. Sabe que o pequeno e a chave, mas nao consegue chegar nele.$DESC$,
fraqueza_real=$DESC$O perigo dele e condicional: enquanto o posto de eleito nao e ameacado, ele luta medido e poupa o corpo. Quebrar a crenca da tropa, ou alcanca-lo no meio da linha, derruba o comando e o bando se esfarela. Ele resiste a dobra da mente e aguenta golpe, mas sozinho, sem a tropa para por na frente, e so um soldado a mais. Ir no eleito vale mais que ceifar os menores.$DESC$,
descricao_sensorial=$DESC$O som e um zumbido fino de lamina e o silencio disciplinado de um bando que nao precisa de ordem falada. O cheiro e de areia, suor de tropa e metal. Ao toque, a lamina dele formiga a mao e a cabeca. Aos olhos, e uma figura pequena e ereta no centro da linha, calma enquanto os maiores se gastam na frente.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Caravanas e postos de Kethara que o bando dele assalta$DESC$, $DESC$Quem desafia o territorio ou o posto de eleito dele$DESC$),
'predador', jsonb_build_array($DESC$Tirado o eleito, o bando se desfaz; sozinho, e so mais um soldado$DESC$),
'competidor', jsonb_build_array($DESC$Outros chefes de bando de Kethara que disputam ruinas e rota$DESC$, $DESC$Sósia-Oco$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presenca dele diz que aquele bando tem um eleito que manda pela cabeca, e que a tropa nao vai ceder enquanto ele viver.$DESC$,
'evitado_por', jsonb_build_array($DESC$Mercadores que pagam pedagio e nao desafiam o posto do eleito$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$A lamina que zumbe de pensamento$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Engenho / cortar a mente, comandar os seus a distancia)$DESC$, 'risco', $DESC$Formiga a cabeca de quem a empunha e atrai a duvida dos proprios.$DESC$),
jsonb_build_object('material', $DESC$O orgao com que ele manda sem falar$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Engenho / passar ordem calada a um grupo)$DESC$, 'risco', $DESC$Da dor de cabeca e ecoa a vontade alheia em quem o porta.$DESC$),
jsonb_build_object('material', $DESC$Insignia de eleito que a tropa respeita$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (simbolo de comando, blefe de posto)$DESC$, 'risco', $DESC$Atrai a fe e a inimizade do bando que a conhece.$DESC$),
jsonb_build_object('material', $DESC$Couro e correia de tropa$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (arreio, correame)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Zumbido fino de lamina e o silencio disciplinado de um bando sem ordem falada.$DESC$,
'cheiro', $DESC$Areia, suor de tropa e metal.$DESC$,
'quer', $DESC$Manter o posto de eleito e o bando que o segue, e tomar postos e rotas de Kethara.$DESC$,
'tipo_perigo', $DESC$Condicional$DESC$,
'falas_exemplo', jsonb_build_array($DESC$Eu nao grito. Eles ja sabem. Olhe para eles, nao para mim.$DESC$, $DESC$Voce veio cedo demais para o que vai me desafiar.$DESC$, $DESC$(registro: voz seca e medida, no comum e em goblin, e uma ordem que chega sem som na cabeca dos seus)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Duvidam ou ameacam o posto de eleito dele diante do bando$DESC$, $DESC$Entram no posto de ruina que a tropa dele guarda$DESC$, $DESC$Atacam um dos seus na frente dele$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Recua para tras da linha quando alcancado no meio da tropa$DESC$, $DESC$Larga o posto e dispersa o bando quando a crenca neles e quebrada$DESC$, $DESC$Some nas ruinas quando o eleito fica exposto sem tropa para por na frente$DESC$),
'descoberta_fazendo', $DESC$No centro de um bando, num posto de ruina de Kethara, passando ordem calada enquanto a tropa organiza a guarda e os menores tomam a frente.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Pagar pedagio e nao desafiar o posto de eleito dele$DESC$, $DESC$Furar a linha e ir direto no eleito para desmanchar o comando$DESC$, $DESC$Quebrar a crenca da tropa nele, que entao se dispersa$DESC$, $DESC$Negociar passagem reconhecendo o posto dele sem briga$DESC$)
),
status_conversao='canonizada'
WHERE id=2135;

-- ========================= GRUPO 3 =========================

-- 851 Torreão-Quieto | Corpo | defender | Condicional | 6 Letal | Kethara | fala
UPDATE ref_criaturas SET
nome=$DESC$Torreão-Quieto$DESC$,
nome_ptbr=$DESC$Torreão-Quieto$DESC$,
slug=$DESC$torreao-quieto$DESC$,
origem=$DESC$Natural$DESC$,
andar_primario=$DESC$Superfície$DESC$,
pilar_associado=$DESC$Corpo$DESC$,
continente=ARRAY[$DESC$Kethara$DESC$]::text[],
habitat=$DESC$Passos e portões de ruina de areia em Kethara, onde um gigante de um olho so fica de guarda.$DESC$,
comportamento=$DESC$Fica parado como torre no posto que lhe deram, e deixa passar quem nao mexe no que ele guarda. Cruzado o limite ou tocado o que protege, fecha a passagem com o corpo e a clava, e arremessa pedra em quem insiste. Defende, nao caca.$DESC$,
organizacao=$DESC$Sozinho, um por portão ou desfiladeiro.$DESC$,
perigo=$DESC$Letal$DESC$,
behavior_archetype=$DESC$defender$DESC$,
morale_modifier=0,
morale_immune=true,
epigrafe=$DESC$Passamos a tarde inteira ao lado dele sem problema. So quando o tolo mexeu no portão e que ele se moveu, e ai foi rapido.$DESC$,
descricao=$DESC$E um gigante de um olho so, alto como dois homens, parado a guardar um portão ou um passo de Kethara desde antes da memoria de quem vive ali. Quieto, parece coluna; o povo passa ao lado e nada. Mas o que ele guarda e sagrado para ele, e quem cruza o limite ou poe a mao no portão acorda uma muralha de carne e pedra: fecha o caminho com o corpo, baixa a clava e arremessa rocha em quem nao recua. Nao tem fome de gente; tem um posto, e o posto e tudo.$DESC$,
supersticao_popular=$DESC$Em Kethara dizem que ha gigantes de um olho que guardam portões mortos, e que sao mansos se a gente nao mexe no que e deles. O conselho e claro: passar de mansinho, nao tocar no portão nem levar o que ha atras, e nao encarar o olho como desafio. Dizem que cegar o olho o derruba; ajuda, mas ele conhece o posto de cor mesmo cego.$DESC$,
sinais_presenca=$DESC$Uma coluna que respira, parada num portão de ruina. Pedras de arremesso empilhadas e prontas ao lado dele. Um portão antigo bem-guardado no meio do abandono. Pegadas enormes que so vao e voltam num trecho curto. Ossos de quem mexeu no que nao devia, perto da soleira.$DESC$,
fraqueza_conhecida=$DESC$O povo cega o olho e foge do alcance da clava e da pedra. Acha que e so questao de derrubar o gigante, sem ver que ele so reage a quem mexe no posto.$DESC$,
fraqueza_real=$DESC$Ele e condicional e preso ao posto: enquanto ninguem cruza o limite nem toca o que ele guarda, e inofensivo e ate util de rodear. Cego, perde a mira do arremesso mas ainda defende a soleira de cor; o caminho bom e nao dar o gatilho. Quem precisa passar tira o que quer sem cruzar a linha dele, ou o atrai para longe da soleira, onde ele fica perdido e mole, porque sem o posto ele nao sabe o que fazer.$DESC$,
descricao_sensorial=$DESC$O som e uma respiracao lenta de fole e o arrasto de pedra sendo apanhada. O cheiro e de poeira de pedra e suor velho de gigante. Ao toque, e pele grossa sobre musculo de pedreira, morna de sol. Aos olhos, e uma coluna de carne com um olho so no alto, imovel ate decidir que voce passou da linha.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Nao caca; esmaga so quem cruza o limite do posto dele$DESC$, $DESC$Quem poe a mao no portão ou leva o que ha atras$DESC$),
'predador', jsonb_build_array($DESC$Tirado do posto, fica perdido e mole; cego, perde a mira de longe$DESC$),
'competidor', jsonb_build_array($DESC$Outros guardas e brutos de Kethara que disputam ruinas$DESC$, $DESC$Monte-Antigo$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presenca dele diz que aquele portão guarda algo que alguem quis muito proteger, e que ha uma linha ali que custa caro cruzar.$DESC$,
'evitado_por', jsonb_build_array($DESC$Caravaneiros que passam de mansinho e nao tocam no que e dele$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$O olho unico, grande e claro$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Corpo / mira firme, vigilia longa)$DESC$, 'risco', $DESC$Resseca e racha se nao guardado em salmoura.$DESC$),
jsonb_build_object('material', $DESC$Tendoes do braco de arremesso$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (corda de arco grande, tracao)$DESC$, 'risco', $DESC$Pesa e endurece com o tempo.$DESC$),
jsonb_build_object('material', $DESC$Lascas da clava de pedra$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (pedra de amolar, contrapeso)$DESC$, 'risco', $DESC$Nenhum.$DESC$),
jsonb_build_object('material', $DESC$Couro grosso da palma$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (sola, correia rude)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Respiracao lenta de fole e o arrasto de pedra sendo apanhada.$DESC$,
'cheiro', $DESC$Poeira de pedra e suor velho de gigante.$DESC$,
'quer', $DESC$Guardar o posto e o portão que lhe deram, e barrar quem cruza o limite.$DESC$,
'tipo_perigo', $DESC$Condicional$DESC$,
'falas_exemplo', jsonb_build_array($DESC$Voce pode passar. Aquilo, nao.$DESC$, $DESC$Tire a mao do portão e siga seu caminho.$DESC$, $DESC$(registro: voz grave e lenta, em gigante e num comum truncado, repetindo poucas frases como ordem decorada)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Alguem cruza o limite do posto que ele guarda$DESC$, $DESC$Poem a mao no portão ou tentam levar o que ha atras$DESC$, $DESC$Encaram o olho dele como desafio e avancam$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Volta a imovel quando o intruso recua do limite$DESC$, $DESC$Cessa a defesa quando tiram do posto a coisa que o gatilho protegia$DESC$, $DESC$Larga a soleira so se for atraido para longe e perder a referencia$DESC$),
'descoberta_fazendo', $DESC$Parado como coluna num portão de ruina de areia de Kethara, olho fixo no caminho, pedras de arremesso empilhadas ao lado, esperando que ninguem cruze o limite.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Passar de mansinho sem tocar no portão nem no que ele guarda$DESC$, $DESC$Tirar o que se quer sem cruzar a linha do posto dele$DESC$, $DESC$Atrai-lo para longe da soleira, onde fica perdido e mole$DESC$, $DESC$Mostrar as maos vazias e nao encarar o olho como desafio$DESC$)
),
status_conversao='canonizada'
WHERE id=851;

-- 1130 Borrão-Lento | Sombra | controller | Ambiental | 0.5 Ameaça | Vyrkhor | MUDO
UPDATE ref_criaturas SET
nome=$DESC$Borrão-Lento$DESC$,
nome_ptbr=$DESC$Borrão-Lento$DESC$,
slug=$DESC$borrao-lento$DESC$,
origem=$DESC$Cicatricial$DESC$,
andar_primario=$DESC$Eco$DESC$,
pilar_associado=$DESC$Sombra$DESC$,
continente=ARRAY[$DESC$Vyrkhor$DESC$]::text[],
habitat=$DESC$Cavernas e criptas sem luz de Vyrkhor, pocos de escuro que nunca esquentaram.$DESC$,
comportamento=$DESC$Espalha-se devagar pelo escuro e tira a forca de quem se demora; cada toque enfraquece, ate a pessoa nao erguer o braco. Lenta e calada. Foge da luz, desfaz-se ao sol.$DESC$,
organizacao=$DESC$Sozinha ou em poucas, cada uma dona de um trecho de breu.$DESC$,
perigo=$DESC$Ameaça$DESC$,
behavior_archetype=$DESC$controller$DESC$,
morale_modifier=0,
morale_immune=true,
epigrafe=$DESC$Nao me feriu, nao me mordeu. So fiquei mais fraco a cada passo naquele escuro, ate nao levantar o braco.$DESC$,
descricao=$DESC$E uma mancha de escuro que se move por conta, devagar, no fundo sem luz de Vyrkhor. Nao bate forte; encosta, e quem encosta vai ficando fraco, perde a forca do braco e da perna a cada toque, ate nao conseguir erguer a arma. Espalha-se pelo chao e pela parede e faz do trecho escuro uma armadilha lenta: ficar ali e secar de forca. Some na luz e a luz do sol a desfaz, mas no breu ela e dona do espaco.$DESC$,
supersticao_popular=$DESC$Em Vyrkhor dizem que ha escuros que comem a forca da gente, e que num certo fundo de caverna os bracos pesam sem motivo. O conselho e luz: nao entrar sem tocha farta, e sair do trecho assim que a forca comecar a faltar. Dizem que ferro corta a sombra; ferro passa por ela e nao resolve, luz sim.$DESC$,
sinais_presenca=$DESC$Uma sombra no chao que se move contra a luz da tocha, sem dono. Bracos e pernas que pesam sem ferida num trecho escuro. Tochas que parecem nao iluminar certo canto. Frio sem corrente de ar. Restos de quem ficou fraco demais para sair, perto da mancha.$DESC$,
fraqueza_conhecida=$DESC$O povo leva tocha e corre quando a forca falta. Sabe da luz. Acha que da para corta-la, e nao da.$DESC$,
fraqueza_real=$DESC$Ela vive do escuro e da demora: faz da area uma zona que drena, e quem fica perde forca. A luz e o fim dela, a do sol a desfaz e a da tocha a encolhe; ferro nao a toca. Quem ilumina o trecho e nao se demora no breu sai com a forca inteira. Nao se luta com ela, ilumina-se e atravessa rapido.$DESC$,
descricao_sensorial=$DESC$O som e nenhum, so o silencio e a propria respiracao ficando curta. O cheiro e de pedra fria e mofo, sem mais nada. Ao toque, e um frio que tira a forca, sem peso e sem borda. Aos olhos, e uma sombra escura demais que se move devagar onde a luz devia bater.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$A forca de quem se demora no escuro do fundo de Vyrkhor$DESC$, $DESC$Bichos e gente que entram sem luz farta$DESC$),
'predador', jsonb_build_array($DESC$A luz do sol a desfaz; a tocha a encolhe$DESC$),
'competidor', jsonb_build_array($DESC$Outras coisas do breu de Vyrkhor que disputam o mesmo fundo$DESC$, $DESC$Manto-Cego$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presenca dela diz que aquele fundo seca a forca de quem fica, e que a tocha ali nao e luxo, e sobrevivencia.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem entra com tocha farta e nao se demora no breu$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$O nucleo de breu que dela sobra na luz$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Sombra / drenar forca, escurecer um trecho)$DESC$, 'risco', $DESC$Pesa os bracos de quem o carrega sem luz.$DESC$),
jsonb_build_object('material', $DESC$O frio sem fonte preso num pote escuro$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Sombra / abafar luz e calor numa area)$DESC$, 'risco', $DESC$Esfria e enfraquece quem dorme perto.$DESC$),
jsonb_build_object('material', $DESC$Po de pedra que ela rondava$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (pigmento negro fosco)$DESC$, 'risco', $DESC$Nenhum alem da cor que nao reflete.$DESC$),
jsonb_build_object('material', $DESC$Mofo seco do fundo dela$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (isca, tinta rala)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Nenhum, so o silencio e a propria respiracao ficando curta.$DESC$,
'cheiro', $DESC$Pedra fria e mofo.$DESC$,
'quer', $DESC$Espalhar-se pelo escuro e secar a forca de quem se demora ali.$DESC$,
'tipo_perigo', $DESC$Ambiental$DESC$,
'falas_exemplo', 'null'::jsonb,
'gatilhos_agressao', jsonb_build_array($DESC$Alguem se demora no trecho escuro que ela domina$DESC$, $DESC$Apagam a ultima luz num fundo onde ela esta$DESC$, $DESC$Encostam na mancha tentando atravessar no breu$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Encolhe e foge da tocha forte trazida para o trecho$DESC$, $DESC$Desfaz-se na luz do sol que entra no fundo$DESC$, $DESC$Recua para o breu mais fundo quando iluminam a area$DESC$),
'descoberta_fazendo', $DESC$Espalhada pelo chao e pela parede de um fundo sem luz de Vyrkhor, drenando devagar a forca de tudo que se demora no escuro.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Atravessar o trecho rapido, com tocha farta, sem se demorar$DESC$, $DESC$Iluminar o fundo com fogo grande para encolhe-la e passar$DESC$, $DESC$Esperar a luz do dia entrar, onde houver fresta, e ela se desfazer$DESC$, $DESC$Tirar do breu quem ja esta fraco antes que seque de forca$DESC$)
),
status_conversao='canonizada'
WHERE id=1130;

-- 891 Caveira-Acesa | Arcano | artillery | Oculto | 4 Ameaça | Voranthar | fala
UPDATE ref_criaturas SET
nome=$DESC$Caveira-Acesa$DESC$,
nome_ptbr=$DESC$Caveira-Acesa$DESC$,
slug=$DESC$caveira-acesa$DESC$,
origem=$DESC$Cicatricial$DESC$,
andar_primario=$DESC$Eco$DESC$,
pilar_associado=$DESC$Arcano$DESC$,
continente=ARRAY[$DESC$Voranthar$DESC$]::text[],
habitat=$DESC$Ruinas e tumbas de Voranthar, salas de ossos onde uma caveira acesa monta guarda.$DESC$,
comportamento=$DESC$Esconde-se entre ossos e escuro, imovel e apagada, e so acende ao ver intruso; ai flutua e atira raio de fogo de longe. Quebrada, reacende dias depois no mesmo lugar. Guarda um ponto e nao o larga.$DESC$,
organizacao=$DESC$Sozinha, uma por sala ou tumba.$DESC$,
perigo=$DESC$Ameaça$DESC$,
behavior_archetype=$DESC$artillery$DESC$,
morale_modifier=0,
morale_immune=true,
epigrafe=$DESC$A pilha de cranios no canto estava igual a todas. Ate uma delas abrir os olhos de fogo e mirar.$DESC$,
descricao=$DESC$E um cranio que flutua, apagado e imovel entre outros ossos ate alguem entrar, e ai acende em chama e abre olhos de fogo. Atira raio de fogo de longe, preciso, e foge do corpo a corpo girando pelo ar. Guarda um ponto, uma sala, uma tumba, e nao sai dali. Quebrada, a chama volta dias depois no mesmo canto, e a guarda recomeca. O perigo dela e estar escondida onde se acha so osso morto.$DESC$,
supersticao_popular=$DESC$Em Voranthar dizem que ha cranios que pegam fogo e atiram, e que vivem nas salas de osso das tumbas. O conselho e nao confiar em pilha de cranio em ruina ativa, e levar algo que apague chama. Dizem que esmagar o osso acaba com ela; acaba so por uns dias, depois reacende.$DESC$,
sinais_presenca=$DESC$Marcas de queimado nas paredes de uma sala de ossos. Um cranio sem po, limpo demais, no meio de ossos empoeirados. Cheiro de osso queimado em tumba fechada. Um claraozinho que aparece e some no fundo de um corredor. Vitimas com queimadura de tiro certeiro, longe de qualquer fogo.$DESC$,
fraqueza_conhecida=$DESC$O povo apaga a chama com agua e areia e esmaga o cranio. Acha que esmagar resolve. Sabe que ela atira, e busca cobertura.$DESC$,
fraqueza_real=$DESC$Ela e artilharia escondida: o perigo e nao ser vista ate o primeiro tiro, e ela se reacende se so quebrada. O que a encerra de vez e desfazer o osso e o que a prende ao lugar, espalhar e selar o canto, nao so quebrar. Fechar a distancia rapido, sob cobertura, tira o tiro dela; molhar a chama a enfraquece. Procurar o cranio limpo demais antes de entrar evita a emboscada.$DESC$,
descricao_sensorial=$DESC$O som e o estalo de chama acendendo de repente e um assobio de fogo cortando o ar. O cheiro e de osso queimado e po quente. Ao toque, e osso quente que queima a mao. Aos olhos, e um cranio flutuante de chama, com dois olhos de fogo fixos no alvo.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Quem entra na sala de ossos que ela guarda$DESC$, $DESC$Intrusos de tumba ao alcance do raio de fogo$DESC$),
'predador', jsonb_build_array($DESC$Desfeita e selada, nao reacende; agua e cobertura tiram a vantagem$DESC$),
'competidor', jsonb_build_array($DESC$Outros mortos de Voranthar que disputam as tumbas$DESC$, $DESC$Voz-Funda$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presenca dela diz que aquela tumba ainda e guardada, e que ha osso ali que nao e so osso.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem desconfia de cranio limpo demais e nao entra em sala de osso sem cobertura$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$A chama fria-azul que nao apaga sozinha$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Arcano / fogo guardiao, raio a distancia)$DESC$, 'risco', $DESC$Acende o que esta perto e reacende se so abafada.$DESC$),
jsonb_build_object('material', $DESC$O osso do cranio, que reluz de quente$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Arcano / foco de fogo, lampada que nao cansa)$DESC$, 'risco', $DESC$Queima a mao e atrai outros fogos.$DESC$),
jsonb_build_object('material', $DESC$Po de osso queimado$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (pigmento, po inflamavel)$DESC$, 'risco', $DESC$Pega fogo facil.$DESC$),
jsonb_build_object('material', $DESC$Ossos comuns da sala$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (cola, adubo de cal)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Estalo de chama acendendo de repente e um assobio de fogo cortando o ar.$DESC$,
'cheiro', $DESC$Osso queimado e po quente.$DESC$,
'quer', $DESC$Guardar a sala de ossos que lhe deram e queimar de longe quem entra.$DESC$,
'tipo_perigo', $DESC$Oculto$DESC$,
'falas_exemplo', jsonb_build_array($DESC$Mais um osso, voce pensou. Agora olhe para o fogo.$DESC$, $DESC$Este lugar e guardado. Voce ja entrou longe demais.$DESC$, $DESC$(registro: voz seca e crepitante, em varias linguas mortas, frases curtas entre os tiros)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Alguem entra na sala de ossos que ela guarda$DESC$, $DESC$Mexem no que ha na tumba sob a guarda dela$DESC$, $DESC$Acendem luz que a revela antes de ela escolher a hora$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Apaga-se e se esconde de novo entre os ossos quando perde a vantagem$DESC$, $DESC$Gira para longe do corpo a corpo, mantendo a distancia do tiro$DESC$, $DESC$Recolhe-se ao canto e finge osso morto quando cercada de perto$DESC$),
'descoberta_fazendo', $DESC$Apagada e imovel entre os ossos de uma tumba de Voranthar, fingindo cranio morto, pronta a acender e atirar no primeiro que cruzar a sala.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Desconfiar do cranio limpo demais e nao entrar sem cobertura$DESC$, $DESC$Apagar a chama com agua e areia e fechar rapido a distancia$DESC$, $DESC$Levar o que se quer sem entrar na linha de tiro da sala$DESC$, $DESC$Desfazer e selar o canto de ossos para que ela nao reacenda$DESC$)
),
status_conversao='canonizada'
WHERE id=891;

-- 1932 Voto-Submerso | Espírito | striker | Direto | 3 Ameaça | Vyrkhor | MUDO
UPDATE ref_criaturas SET
nome=$DESC$Voto-Submerso$DESC$,
nome_ptbr=$DESC$Voto-Submerso$DESC$,
slug=$DESC$voto-submerso$DESC$,
origem=$DESC$Cicatricial$DESC$,
andar_primario=$DESC$Eco$DESC$,
pilar_associado=$DESC$Espírito$DESC$,
continente=ARRAY[$DESC$Vyrkhor$DESC$]::text[],
habitat=$DESC$Lagos gelados e cisternas afundadas de Vyrkhor, sob o gelo de monasterios alagados.$DESC$,
comportamento=$DESC$Anda no fundo da agua e sobe quando alguem perturba o lago; golpeia direto, so com as maos, num ritmo de quem rezava, sem parar nem recuar. Vem em grupo, ligados, e batem juntos. Nao fala; so cumpre o gesto que sobrou.$DESC$,
organizacao=$DESC$Em grupos ligados, irmandade afogada de um mesmo monasterio.$DESC$,
perigo=$DESC$Ameaça$DESC$,
behavior_archetype=$DESC$striker$DESC$,
morale_modifier=0,
morale_immune=true,
epigrafe=$DESC$Saiu do buraco do gelo sem pressa, escorrendo, e bateu com as maos abertas, no compasso de uma reza que ninguem mais reza.$DESC$,
descricao=$DESC$Foi um asceta que se afogou rezando, e o que sobrou no corpo nao foi a pessoa, foi a devocao: o gesto, o ritmo, a teima de continuar. Anda no fundo do lago gelado e sobe quando o gelo e quebrado ou a agua e perturbada, e golpeia so com as maos, direto, num compasso parelho de oracao, sem cansar e sem recuar. Vem ligado a outros como ele, e batem no mesmo tempo. Nao tem raiva; tem um voto que nao soube parar de cumprir.$DESC$,
supersticao_popular=$DESC$Em Vyrkhor dizem que os lagos de certos monasterios afundados devolvem os que se afogaram rezando, e que eles batem no compasso de uma reza morta. O conselho e nao quebrar o gelo desses lagos nem rezar alto na beira, porque o som e o movimento os chamam. Dizem que agua benta os deita; o que os deita e desfazer o voto que os prende, ou tirar a agua que os guarda.$DESC$,
sinais_presenca=$DESC$Vultos parados no fundo de um lago gelado, em pe, virados para a margem. Um compasso surdo de batida vindo de baixo do gelo. Buracos no gelo abertos de baixo para cima. Habitos de monge boiando, encharcados, sem dono. Marcas de mao molhada subindo a margem em fila.$DESC$,
fraqueza_conhecida=$DESC$O povo joga agua benta e evita a beira do lago. Acha que e questao de bencao. Sabe que o barulho os chama, e faz silencio.$DESC$,
fraqueza_real=$DESC$Eles sao diretos e teimosos, ligados uns aos outros, e batem ate cumprir o gesto; trocar golpe com eles e entrar no compasso deles. O que os encerra e desfazer o voto que os prende, dar fim a reza inacabada, ou tirar a agua que os guarda, drenar ou abrir o lago ao sol. Quebrar o elo entre eles os deixa lentos e perdidos. Nao se grita nem se reza alto na beira; faz-se silencio e some-se.$DESC$,
descricao_sensorial=$DESC$O som e um compasso surdo de batida sob o gelo e o pingar de agua de habito encharcado. O cheiro e de agua parada, fria e de pano mofado. Ao toque, e carne fria e inchada de afogado, firme demais. Aos olhos, e um monge escorrendo, de olhos baixos, batendo com as maos no tempo de uma reza muda.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Nao caca; golpeia quem perturba o lago gelado deles$DESC$, $DESC$Quem quebra o gelo ou reza alto na beira$DESC$),
'predador', jsonb_build_array($DESC$Desfeito o voto ou tirada a agua, deitam; o sol no lago aberto os encerra$DESC$),
'competidor', jsonb_build_array($DESC$Outros mortos de agua de Vyrkhor que disputam as cisternas$DESC$, $DESC$Guarda-Cova$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presenca deles diz que ali embaixo houve um monasterio que afundou, e que o lago devolve o que se afogou rezando.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem nao quebra o gelo nem reza alto na beira e passa em silencio$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$A agua que escorre do habito e nao seca$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Eco / teima que nao cessa, gesto que se repete)$DESC$, 'risco', $DESC$Embebe quem a guarda numa devocao que nao e sua.$DESC$),
jsonb_build_object('material', $DESC$As maos calejadas de reza, ainda firmes$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Corpo / golpe parelho, resistencia ao cansaco)$DESC$, 'risco', $DESC$Movem-se sozinhas no compasso de uma oracao.$DESC$),
jsonb_build_object('material', $DESC$Conta de oracao do habito$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (rosario, foco de concentracao)$DESC$, 'risco', $DESC$Nenhum alem do compasso que sugere.$DESC$),
jsonb_build_object('material', $DESC$Pano encharcado do habito$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (estopa, vedacao)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Compasso surdo de batida sob o gelo e o pingar de agua de habito encharcado.$DESC$,
'cheiro', $DESC$Agua parada, fria, e pano mofado.$DESC$,
'quer', $DESC$Cumprir o gesto da reza que sobrou, batendo no compasso ate a agua aquietar.$DESC$,
'tipo_perigo', $DESC$Direto$DESC$,
'falas_exemplo', 'null'::jsonb,
'gatilhos_agressao', jsonb_build_array($DESC$Quebram o gelo ou perturbam a agua do lago deles$DESC$, $DESC$Rezam ou fazem barulho alto na beira, chamando o compasso$DESC$, $DESC$Tentam tirar do fundo o que afundou com o monasterio$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Voltam ao fundo quando a agua aquieta e o silencio volta$DESC$, $DESC$Param e ficam perdidos quando o elo entre eles e quebrado$DESC$, $DESC$Deitam quando o voto que os prende e desfeito ou o lago e aberto ao sol$DESC$),
'descoberta_fazendo', $DESC$Em pe no fundo de um lago gelado de Vyrkhor, virados para a margem, batendo com as maos no compasso surdo de uma reza muda, sob o monasterio afundado.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Passar em silencio, sem quebrar o gelo nem rezar alto na beira$DESC$, $DESC$Drenar ou abrir o lago ao sol, tirando a agua que os guarda$DESC$, $DESC$Desfazer o voto inacabado que os prende, dando fim a reza$DESC$, $DESC$Quebrar o elo entre eles para deixa-los lentos e perdidos$DESC$)
),
status_conversao='canonizada'
WHERE id=1932;

-- 501 Miolo-Regente | Engenho | tactical | Persistente | 14 Letal | Voranthar | fala
UPDATE ref_criaturas SET
nome=$DESC$Miolo-Regente$DESC$,
nome_ptbr=$DESC$Miolo-Regente$DESC$,
slug=$DESC$miolo-regente$DESC$,
origem=$DESC$Marginal$DESC$,
andar_primario=$DESC$Margem$DESC$,
pilar_associado=$DESC$Engenho$DESC$,
continente=ARRAY[$DESC$Voranthar$DESC$]::text[],
habitat=$DESC$Cisternas e cavernas alagadas de Voranthar onde a Margem e fina; pocos de salmoura no fundo de cidade morta.$DESC$,
comportamento=$DESC$Fica imovel numa poca de salmoura e governa de longe: toma a cabeca de quem tem por perto e os usa como maos, olhos e tropa. Nao briga de corpo; manda os dominados na frente e castiga com um golpe de mente quem chega perto. Quanto mais tempo, mais gente sob o dominio dele.$DESC$,
organizacao=$DESC$Sozinho na poca, mas no centro de uma rede de dominados.$DESC$,
perigo=$DESC$Letal$DESC$,
behavior_archetype=$DESC$tactical$DESC$,
morale_modifier=-1,
morale_immune=false,
epigrafe=$DESC$A aldeia inteira obedecia a coisa na cisterna. Eles sorriam ao nos receber, e os olhos diziam socorro.$DESC$,
descricao=$DESC$E um miolo grande demais, parado numa poca de salmoura no fundo de Voranthar, fraco de corpo e forte de vontade. Nao se mexe; governa. Toma a cabeca de quem fica por perto e os transforma em maos, olhos e tropa, uma rede de dominados que faz o trabalho dele e morre por ele. Castiga com um golpe que estoura a mente quem se aproxima da poca. Quanto mais tempo num lugar, mais gente cai na rede, e a rede se alastra como mancha. O perigo nao e o corpo dele, e quem ele ja tomou.$DESC$,
supersticao_popular=$DESC$Em Voranthar dizem que ha aldeias afundadas onde todos obedecem a uma coisa numa cisterna, e que o sorriso deles e mentira. O conselho dos que sabem: desconfiar de gente boa demais, calada demais, que protege um poco no fundo, e nunca chegar a poca pela frente dos dominados. Dizem que matar os enfeiticados liberta; nao liberta, e fazer o jogo da coisa, que os pos na frente de proposito.$DESC$,
sinais_presenca=$DESC$Uma comunidade inteira que age junto demais, sem briga e sem vontade propria. Olhos vazios sob sorrisos educados. Um poco ou cisterna bem-guardado que ninguem deixa ninguem chegar. Dor de cabeca crescente quanto mais fundo se vai. Gente que repete as mesmas palavras, no mesmo tom.$DESC$,
fraqueza_conhecida=$DESC$O povo luta contra os dominados e tenta fugir da aldeia. Acha que matar os enfeiticados resolve. Sabe que ha algo no poco, mas nao chega.$DESC$,
fraqueza_real=$DESC$O perigo e a rede, nao o corpo: ele e fraco e imovel, e poe os dominados entre ele e o mundo. O dominio cai com a morte dele, com a distancia, ou ferindo o dominado, que ganha chance de acordar. Furar a linha dos enfeiticados e ir na poca, ou tirar o dominado do alcance, encerra o controle. Brigar com o amigo de olhos vazios e o que ele quer. Sozinho, na salmoura, ele quase nao se defende.$DESC$,
descricao_sensorial=$DESC$O som e um borbulhar baixo de salmoura e uma voz que chega sem som dentro da cabeca. O cheiro e de agua salgada parada e carne crua. Ao toque, e mole, frio e umido, e cede como geleia. Aos olhos, e um miolo enorme numa poca, pulsando devagar, sem rosto e sem pressa.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$A vontade de quem vive por perto, tomada e usada como tropa$DESC$, $DESC$Aldeias e grupos inteiros do fundo de Voranthar$DESC$),
'predador', jsonb_build_array($DESC$Sozinho e fraco e imovel; a morte dele ou a distancia soltam a rede$DESC$),
'competidor', jsonb_build_array($DESC$Outras coisas de dominio da Margem em Voranthar$DESC$, $DESC$Mente-Fria$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presenca dele diz que aquela comunidade nao manda em si, e que ha uma vontade so governando do fundo.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem desconfia de gente boa e calada demais e nao chega ao poco pela frente dos dominados$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$O nucleo de salmoura onde a vontade dele se guarda$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Engenho / tomar e reger varias cabecas, rede de dominio)$DESC$, 'risco', $DESC$Tenta reger quem o abre e ecoa ordens que nao sao suas.$DESC$),
jsonb_build_object('material', $DESC$O fio invisivel que liga ele aos dominados$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Engenho / passar ordem a distancia a um grupo)$DESC$, 'risco', $DESC$Prende quem o segura a uma vontade alheia.$DESC$),
jsonb_build_object('material', $DESC$Sal grosso cristalizado da poca$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (conserva, sal de cura)$DESC$, 'risco', $DESC$Nenhum alem do gosto de carne.$DESC$),
jsonb_build_object('material', $DESC$Agua salgada parada da cisterna$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (salmoura, curtume)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Borbulhar baixo de salmoura e uma voz que chega sem som dentro da cabeca.$DESC$,
'cheiro', $DESC$Agua salgada parada e carne crua.$DESC$,
'quer', $DESC$Tomar toda vontade por perto e reger de longe, alastrando a rede sem nunca se expor.$DESC$,
'tipo_perigo', $DESC$Persistente$DESC$,
'falas_exemplo', jsonb_build_array($DESC$Eles ja sao meus. Voce fala com a minha boca quando fala com eles.$DESC$, $DESC$Chegue mais perto. Eu tenho uma cadeira vazia na minha cabeca para a sua.$DESC$, $DESC$(registro: voz fria e paciente que chega por dentro, sem som, em varias linguas ao mesmo tempo)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Alguem se aproxima da poca pela frente dos dominados$DESC$, $DESC$Tentam tirar um dominado do alcance dele$DESC$, $DESC$Uma vontade forte resiste e ameaca a rede dele$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Manda os dominados na frente e se encolhe na salmoura quando exposto$DESC$, $DESC$Larga o dominio de longe quando furam a linha e chegam nele$DESC$, $DESC$Solta a rede e adormece a poca quando a distancia ou o dano o forcam$DESC$),
'descoberta_fazendo', $DESC$Imovel numa poca de salmoura no fundo de uma cidade morta de Voranthar, regendo uma aldeia de olhos vazios que faz a guarda e o trabalho por ele.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Desconfiar da gente calada demais e nao chegar a poca pela frente dos dominados$DESC$, $DESC$Furar a linha dos enfeiticados e ir direto na poca, sem brigar com eles$DESC$, $DESC$Tirar os dominados do alcance dele, o que quebra o controle$DESC$, $DESC$Ferir de leve o dominado para dar-lhe chance de acordar, em vez de mata-lo$DESC$)
),
status_conversao='canonizada'
WHERE id=501;

-- ========================= GRUPO 4 =========================

-- 698 Podridão-Lenta | Corpo | brute | Persistente | 9 Letal | Thornmarak | fala
UPDATE ref_criaturas SET
nome=$DESC$Podridão-Lenta$DESC$,
nome_ptbr=$DESC$Podridão-Lenta$DESC$,
slug=$DESC$podridao-lenta$DESC$,
origem=$DESC$Natural$DESC$,
andar_primario=$DESC$Superfície$DESC$,
pilar_associado=$DESC$Corpo$DESC$,
continente=ARRAY[$DESC$Thornmarak$DESC$]::text[],
habitat=$DESC$Brejos e charcos podres de Thornmarak, valas e lixoes onde a carne apodrece sem parar.$DESC$,
comportamento=$DESC$Avança devagar e aguenta tudo, porque a carne podre se refaz sozinha; em volta dela o ar apodrece e fere quem fica perto. Nao tem pressa: deixa o corpo dela durar mais que o do adversario.$DESC$,
organizacao=$DESC$Sozinha, cada uma dona de um charco podre.$DESC$,
perigo=$DESC$Letal$DESC$,
behavior_archetype=$DESC$brute$DESC$,
morale_modifier=2,
morale_immune=false,
epigrafe=$DESC$A gente cortava e ela crescia de volta, mais podre. E o fedor sozinho ja abria ferida na boca da gente.$DESC$,
descricao=$DESC$E um trol de carne mole e podre, lento e teimoso, que cheira a vala antes de ser visto. Aguenta corte, lança e fogo fraco, porque a podridao se costura de novo, e enquanto se refaz solta um bafo de apodrecimento que adoece quem fica perto. Nao corre; arrasta-se e cansa o adversario, deixando o proprio corpo durar mais que o do outro. So o fogo forte e o acido fecham a cura dela.$DESC$,
supersticao_popular=$DESC$Em Thornmarak dizem que ha trois de podre nos charcos, e que so o fogo grande os mata. O conselho e nao lutar perto, por causa do bafo que apodrece, e levar chama farta. Dizem que afogar resolve; nao resolve, ela se refaz na agua parada.$DESC$,
sinais_presenca=$DESC$Um fedor de carne podre que chega antes do bicho. Charco com a agua cheia de bolha e veu cinza. Moscas em nuvem num trecho de brejo. Plantas e bichos mortos e moles em volta de um rastro. Feridas que infeccionam rapido em quem passou.$DESC$,
fraqueza_conhecida=$DESC$O povo usa fogo grande e distancia, e sabe que ferro nao basta. Acha que afogar mata, e nao mata.$DESC$,
fraqueza_real=$DESC$A forca dela e a regeneracao e o bafo: gasta-se devagar e se refaz, e o ar perto adoece. O fogo forte e o acido fecham a cura, porque o que ela refaz nao volta do que foi queimado. Tira-la da agua e da umidade do charco que a sustenta reduz a teima. Lutar de longe, fora do alcance do bafo, vale mais que troca-la golpe a golpe.$DESC$,
descricao_sensorial=$DESC$O som e um arrasto molhado e o estalo de carne se fechando. O cheiro e de vala e podre, forte o bastante para enjoar. Ao toque, e carne mole e quente de febre. Aos olhos, e uma massa podre que escorre e ja se refaz do ultimo corte.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Carcacas e bichos do charco de Thornmarak$DESC$, $DESC$Gente que luta perto demais e adoece no bafo dela$DESC$),
'predador', jsonb_build_array($DESC$Fogo forte e acido, que impedem a cura$DESC$),
'competidor', jsonb_build_array($DESC$Outras coisas de podre de Thornmarak que disputam o charco$DESC$, $DESC$Ventre-de-Vala$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presenca dela diz que aquele charco virou foco de apodrecimento, e que o ar perto adoece quem demora.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem nao luta perto e leva chama farta$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$A carne que se recose sozinha$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Corpo / regenerar, fechar ferida grave)$DESC$, 'risco', $DESC$Cresce alem do molde e apodrece a mao que a guarda.$DESC$),
jsonb_build_object('material', $DESC$A glandula do bafo de apodrecimento$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Arcano / miasma que adoece em area)$DESC$, 'risco', $DESC$Apodrece o ar e a comida perto.$DESC$),
jsonb_build_object('material', $DESC$Couro podre das costas$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (couro rude impermeavel)$DESC$, 'risco', $DESC$Fede e apodrece se nao salgado rapido.$DESC$),
jsonb_build_object('material', $DESC$Limo do charco dela$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (adubo, isca de podre)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Arrasto molhado e o estalo de carne se fechando.$DESC$,
'cheiro', $DESC$Vala e podre, forte o bastante para enjoar.$DESC$,
'quer', $DESC$Durar mais que o adversario e apodrecer tudo em volta do charco.$DESC$,
'tipo_perigo', $DESC$Persistente$DESC$,
'falas_exemplo', jsonb_build_array($DESC$Corta a vontade. Eu tenho mais carne do que voce tem dia.$DESC$, $DESC$Sente o ar? Voce ja esta apodrecendo um pouco.$DESC$, $DESC$(registro: voz mole e arrastada, em gigante, sem pressa nenhuma)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Algo entra no charco podre dela$DESC$, $DESC$Alguem luta ao alcance do bafo que apodrece$DESC$, $DESC$Tentam tirar dali a agua podre que a refaz$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Mergulha no charco para se refazer quando o fogo a cerca$DESC$, $DESC$Recua so quando a chama impede a cura e nao ha agua perto$DESC$, $DESC$Larga a presa se o charco seca ou queima inteiro$DESC$),
'descoberta_fazendo', $DESC$Arrastando-se num charco podre de Thornmarak, refazendo a carne, o bafo apodrecendo o ar em volta.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Contornar o charco e nao lutar perto do bafo$DESC$, $DESC$Queimar com chama farta e a distancia, sem trocar golpe$DESC$, $DESC$Drenar ou secar o charco que a refaz$DESC$, $DESC$Atrai-la para terra seca e firme, longe da agua$DESC$)
),
status_conversao='canonizada'
WHERE id=698;

-- 717 Estandarte-Roto | Sombra | tactical | Condicional | 8 Letal | Voranthar | fala
UPDATE ref_criaturas SET
nome=$DESC$Estandarte-Roto$DESC$,
nome_ptbr=$DESC$Estandarte-Roto$DESC$,
slug=$DESC$estandarte-roto$DESC$,
origem=$DESC$Cicatricial$DESC$,
andar_primario=$DESC$Eco$DESC$,
pilar_associado=$DESC$Sombra$DESC$,
continente=ARRAY[$DESC$Voranthar$DESC$]::text[],
habitat=$DESC$Campos de batalha mortos de Voranthar, o Eco da Primeira Travessia, exercitos caidos sob a areia e a pedra.$DESC$,
comportamento=$DESC$Comanda os mortos do campo onde tombou; ergue a tropa caida e ataca em formacao quando o campo e pisado ou a honra dele desafiada. Frio e metodico, nao recua do posto de comando.$DESC$,
organizacao=$DESC$Sozinho como comandante, mas no centro de uma tropa erguida.$DESC$,
perigo=$DESC$Letal$DESC$,
behavior_archetype=$DESC$tactical$DESC$,
morale_modifier=0,
morale_immune=true,
epigrafe=$DESC$O campo estava vazio. Ele soprou uma ordem, e o chao se levantou em soldados.$DESC$,
descricao=$DESC$Foi um comandante que tombou e nao aceitou perder o campo. Ergue os soldados mortos em volta e os poe em formacao, e lidera com a frieza de quem ja morreu uma vez. So se acende quando o campo de batalha dele e pisado ou quando se ergue contra ele algum padrao de honra que o desafie; ai chama a tropa e avanca metodico. Resiste a ser afastado e nao larga o posto.$DESC$,
supersticao_popular=$DESC$Em Voranthar dizem que certos campos de batalha velhos se levantam se a gente pisa errado, sob um comandante morto. O conselho: nao acampar nem hastear estandarte em campo de osso, nao tocar as armas caidas. Dizem que derrubar o comandante dispersa a tropa; verdade, mas ele resiste a ser afastado.$DESC$,
sinais_presenca=$DESC$Armas e estandartes caidos arrumados em ordem boa demais. Toques de corneta surdos sem corneta. Ossos de soldado dispostos em formacao. Um frio de disciplina no ar. A tropa que se ergue quando alguem pisa o campo.$DESC$,
fraqueza_conhecida=$DESC$O povo tenta derrubar o comandante e fugir do campo. Acha que afastar a tropa resolve, e ele resiste a ser afastado.$DESC$,
fraqueza_real=$DESC$Ele e condicional ao campo e a honra: fica parado se ninguem pisa o campo nem o desafia. Derrubar o comandante desfaz a tropa erguida, porque a disciplina vem dele. O caminho bom e nao hastear padrao nem acampar no campo, e sair dele encerra o avanco. Lutar a tropa toda e perder tempo; tudo se prende ao comando.$DESC$,
descricao_sensorial=$DESC$O som e uma corneta surda e o tinir de arnes sem corpo dentro. O cheiro e de ferro velho e terra de cova. Ao toque, e metal frio de armadura vazia. Aos olhos, e um comandante de arnes oco erguendo a tropa caida em formacao.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Quem pisa ou acampa no campo de batalha dele$DESC$, $DESC$Quem desafia a honra do posto de comando$DESC$),
'predador', jsonb_build_array($DESC$Derrubado o comandante, a tropa erguida cai junto$DESC$),
'competidor', jsonb_build_array($DESC$Outros mortos de guerra de Voranthar que disputam os campos$DESC$, $DESC$Marechal-Roto$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presenca dele diz que ali tombou um exercito e que o comando nao aceitou a derrota.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem nao acampa nem hasteia padrao em campo de osso$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$O toque de comando que ergue a tropa$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Sombra / erguer e comandar os caidos)$DESC$, 'risco', $DESC$Chama mortos perto de quem o usa sem direito.$DESC$),
jsonb_build_object('material', $DESC$Arnes que resiste a ser afastado$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Corpo / firmeza, resistir a recuo e medo)$DESC$, 'risco', $DESC$Prende quem o veste a um posto que nao quer largar.$DESC$),
jsonb_build_object('material', $DESC$Estandarte roto do campo$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (insignia, blefe de comando)$DESC$, 'risco', $DESC$Atrai a tropa morta que o reconhece.$DESC$),
jsonb_build_object('material', $DESC$Ferro das armas caidas$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (sucata, refundir)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Corneta surda e o tinir de arnes sem corpo dentro.$DESC$,
'cheiro', $DESC$Ferro velho e terra de cova.$DESC$,
'quer', $DESC$Manter o campo que perdeu e nao aceitar a derrota, erguendo a tropa caida.$DESC$,
'tipo_perigo', $DESC$Condicional$DESC$,
'falas_exemplo', jsonb_build_array($DESC$De pe. A batalha nao acabou. Nunca acaba.$DESC$, $DESC$Voce pisou no meu campo. Agora e meu soldado ou meu morto.$DESC$, $DESC$(registro: voz de comando seca e fria, em linguas de guerra antigas, ordens curtas)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Pisam ou acampam no campo de batalha dele$DESC$, $DESC$Hasteiam padrao ou tocam as armas caidas$DESC$, $DESC$Desafiam a honra do posto de comando$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Cessa o avanco quando saem do campo$DESC$, $DESC$Deixa o posto so quando o campo e desconsagrado da guerra$DESC$, $DESC$Para quando o comando dele e derrubado e a tropa cai$DESC$),
'descoberta_fazendo', $DESC$No centro de um campo de osso de Voranthar, erguendo soldados caidos em formacao sob ordens surdas.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Nao acampar nem hastear padrao no campo de batalha$DESC$, $DESC$Sair do campo para encerrar o avanco da tropa$DESC$, $DESC$Derrubar so o comandante para desfazer a tropa erguida$DESC$, $DESC$Dar fim a guerra inacabada que o prende ao campo$DESC$)
),
status_conversao='canonizada'
WHERE id=717;

-- 1842 Mazela-Crua | Arcano | artillery | Direto | 15 Letal | Kethara | fala
UPDATE ref_criaturas SET
nome=$DESC$Mazela-Crua$DESC$,
nome_ptbr=$DESC$Mazela-Crua$DESC$,
slug=$DESC$mazela-crua$DESC$,
origem=$DESC$Cicatricial$DESC$,
andar_primario=$DESC$Eco$DESC$,
pilar_associado=$DESC$Arcano$DESC$,
continente=ARRAY[$DESC$Kethara$DESC$]::text[],
habitat=$DESC$Cidades mortas de peste em Kethara, quarentenas de areia e pocos contaminados.$DESC$,
comportamento=$DESC$Anda como arauto de doenca: lanca dardos de praga de longe e leva consigo um halo que adoece quem chega perto. Avanca direto, sem medo, cumprindo a cruzada de espalhar a mazela.$DESC$,
organizacao=$DESC$Sozinho, arauto de uma cruzada de peste.$DESC$,
perigo=$DESC$Letal$DESC$,
behavior_archetype=$DESC$artillery$DESC$,
morale_modifier=0,
morale_immune=true,
epigrafe=$DESC$Ele nao precisou nos tocar. Apontou o cajado, e a febre chegou de longe, certeira.$DESC$,
descricao=$DESC$E um campeao morto de peste, alto e seco, que se arvora em arauto da doenca. Atira dardos de praga a distancia, certeiros, e onde para abre um halo que adoece quem respira perto. Nao recua: cumpre uma cruzada fria de espalhar a mazela, cidade a cidade, e trata a propria morte como prova de que a doenca venceu. Ferro o atinge, mas ele nao teme nada que ja perdeu.$DESC$,
supersticao_popular=$DESC$Em Kethara dizem que ha um arauto de peste que anda nas cidades mortas, e que o cajado dele apontado e febre certa. O conselho: nao entrar em quarentena de areia, queimar o que ele toca, cobrir boca e nariz. Dizem que matar o arauto limpa a cidade; ajuda, mas a praga que ele semeou fica.$DESC$,
sinais_presenca=$DESC$Gente e bicho mortos de febre em fila por uma rua. Um cajado fincado com panos de doente. Moscas e cheiro de doenca num poco. Marcas de mao febril nas portas. Um arauto seco que aponta de longe.$DESC$,
fraqueza_conhecida=$DESC$O povo cobre boca e nariz, queima o que ele toca e tenta matar o arauto. Acha que mata-lo limpa tudo.$DESC$,
fraqueza_real=$DESC$O perigo dele e o dardo de longe e o halo de perto; ele nao foge e nao cansa. Calor seco, fogo e barreira contra a doenca, cobrir-se e manter distancia, tiram a forca da praga. Fechar a distancia sob cobertura corta o tiro, mas a doenca que ele ja semeou precisa ser queimada a parte. Matar so o arauto nao limpa o que ja pegou.$DESC$,
descricao_sensorial=$DESC$O som e uma tosse seca e o assobio do dardo de praga cortando o ar. O cheiro e de doenca, suor febril e cal. Ao toque, e pele seca e quente de febre velha. Aos olhos, e um campeao seco de cajado erguido, com um halo doente em volta.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Quem respira o halo dele ou e atingido pelo dardo de praga$DESC$, $DESC$Cidades de Kethara que ele cruza espalhando peste$DESC$),
'predador', jsonb_build_array($DESC$Calor seco e fogo; matar o arauto corta a fonte, mas nao a praga ja semeada$DESC$),
'competidor', jsonb_build_array($DESC$Outros mortos de peste de Kethara que disputam as cidades$DESC$, $DESC$Pira-Viva$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presenca dele diz que aquela cidade morreu de peste e que o que a espalhou ainda anda.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem cobre boca e nariz e nao entra em quarentena de areia$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$A glandula do halo de peste$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Arcano / praga em area, dardo de doenca)$DESC$, 'risco', $DESC$Adoece quem a abre sem se cobrir.$DESC$),
jsonb_build_object('material', $DESC$O cajado que aponta a febre$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Arcano / lançar doenca a distancia)$DESC$, 'risco', $DESC$A mao que o segura ferve de febre.$DESC$),
jsonb_build_object('material', $DESC$Panos de doente do cajado$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (estopa de quarentena, isca)$DESC$, 'risco', $DESC$Contagia se nao queimado.$DESC$),
jsonb_build_object('material', $DESC$Cal seca do chao dele$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (cal de cova, alvejante)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Tosse seca e o assobio do dardo de praga cortando o ar.$DESC$,
'cheiro', $DESC$Doenca, suor febril e cal.$DESC$,
'quer', $DESC$Espalhar a peste cidade a cidade, cumprindo a cruzada que o levantou.$DESC$,
'tipo_perigo', $DESC$Direto$DESC$,
'falas_exemplo', jsonb_build_array($DESC$Nao corra. A febre corre mais rapido, e ja saiu daqui.$DESC$, $DESC$Eu fui o primeiro a cair. Voce vai ser so mais um.$DESC$, $DESC$(registro: voz seca e rouca de tosse, no comum e numa lingua morta, calma como quem ja venceu)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Alguem entra no alcance do dardo de peste$DESC$, $DESC$Respiram o halo dele de perto$DESC$, $DESC$Tentam barrar a cruzada de cidade em cidade$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Nao foge; avanca cumprindo a cruzada ate cair$DESC$, $DESC$Cessa o avanco so quando o voto de peste que o prende e desfeito$DESC$, $DESC$Deixa a cidade quando ja a semeou de doenca$DESC$),
'descoberta_fazendo', $DESC$Cruzando uma rua morta de Kethara, apontando o cajado e lançando dardos de peste, um halo doente em volta.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Cobrir boca e nariz e nao entrar na quarentena$DESC$, $DESC$Fechar a distancia sob cobertura para cortar o tiro$DESC$, $DESC$Queimar a parte o foco de praga que ele semeou$DESC$, $DESC$Desfazer a cruzada que o prende, dando fim ao voto de peste$DESC$)
),
status_conversao='canonizada'
WHERE id=1842;

-- 958 Jazigo-Cioso | Espírito | lurker | Oculto | 7 Letal | Kethara | fala
UPDATE ref_criaturas SET
nome=$DESC$Jazigo-Cioso$DESC$,
nome_ptbr=$DESC$Jazigo-Cioso$DESC$,
slug=$DESC$jazigo-cioso$DESC$,
origem=$DESC$Cicatricial$DESC$,
andar_primario=$DESC$Eco$DESC$,
pilar_associado=$DESC$Espírito$DESC$,
continente=ARRAY[$DESC$Kethara$DESC$]::text[],
habitat=$DESC$Necropoles de areia e campos-santos de Kethara, jazigos consagrados sob o deserto.$DESC$,
comportamento=$DESC$Fica escondido na terra do campo-santo, imovel, ate alguem profanar uma cova; ai sobe sem aviso, sufoca o profanador e prega medo com o olhar. Volta a terra quando o tumulo e respeitado. So pune quem mexe nos mortos.$DESC$,
organizacao=$DESC$Sozinho, guardiao de um campo-santo inteiro.$DESC$,
perigo=$DESC$Letal$DESC$,
behavior_archetype=$DESC$lurker$DESC$,
morale_modifier=0,
morale_immune=true,
epigrafe=$DESC$Cavaram o tumulo a noite. De manha, os tres estavam mortos sem marca, de boca aberta, e a terra estava intacta de novo.$DESC$,
descricao=$DESC$E o resto cioso de um morto que se fez guardiao do proprio campo-santo. Fica enterrado, imovel, indistinguivel da terra consagrada, ate alguem profanar uma cova: roubar, cavar, quebrar uma lapide. Ai sobe sem aviso, fecha a garganta do profanador a distancia e prega um medo que trava o corpo, e quando termina volta a terra, que se fecha como se nada. Quem respeita os mortos passa pelo campo-santo a salvo. Quem mexe neles nao ve o que o mata.$DESC$,
supersticao_popular=$DESC$Em Kethara dizem que certos campos-santos punem quem cava, e que os mortos ali se guardam sozinhos. O conselho: nao roubar tumba, nao quebrar lapide, e pedir licenca em voz alta ao passar. Dizem que so age de noite; age a qualquer hora contra quem profana.$DESC$,
sinais_presenca=$DESC$Tumbas reviradas que amanhecem fechadas de novo. Profanadores mortos sem marca, de boca aberta. Terra de cova que se mexe sem vento. Um frio cioso sobre um campo-santo. Lapides que voltam ao lugar sozinhas.$DESC$,
fraqueza_conhecida=$DESC$O povo respeita a tumba e tenta agir de dia. Acha que ele so age de noite, e nisso erra.$DESC$,
fraqueza_real=$DESC$Ele e condicional e oculto: so se ergue contra quem profana, e fica invisivel na terra ate o golpe. Quem nao mexe nos mortos nunca o encontra. Para quem ja profanou, devolver o que roubou e refechar a cova o aplaca; desfaze-lo de vez exige desfazer o laço que o prende a guardar o campo, raro e custoso. Nao se vence cavando mais; vence-se restaurando.$DESC$,
descricao_sensorial=$DESC$O som e um sopro abafado de quem perde o ar e o ranger de terra. O cheiro e de areia seca e cova aberta. Ao toque, e terra fria que aperta a garganta sem mao. Aos olhos, e quase nada, ate a terra se erguer em forma de morto sobre o profanador.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Nao caca; sufoca quem profana as covas que guarda$DESC$, $DESC$Ladroes de tumba e quebradores de lapide$DESC$),
'predador', jsonb_build_array($DESC$Respeitada a tumba, nunca se ergue; restaurar a cova o aplaca$DESC$),
'competidor', jsonb_build_array($DESC$Outros guardioes de morte de Kethara que zelam por necropoles$DESC$, $DESC$Cinza-Faminta$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presenca dele diz que aquele campo-santo se guarda sozinho e cobra de quem profana.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem nao rouba tumba e pede licenca ao passar$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$A terra ciosa que fecha a garganta$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Eco / sufocar a distancia, guardar um lugar)$DESC$, 'risco', $DESC$Aperta o folego de quem a guarda sem respeito.$DESC$),
jsonb_build_object('material', $DESC$O olhar que trava o corpo, do morto enfim solto$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Sombra / pregar medo, paralisar de pavor)$DESC$, 'risco', $DESC$Encara de volta quem o porta com culpa.$DESC$),
jsonb_build_object('material', $DESC$Lasca de lapide consagrada$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (marco de cova, ancora)$DESC$, 'risco', $DESC$Atrai o guardiao se levada para longe do campo.$DESC$),
jsonb_build_object('material', $DESC$Areia seca do campo-santo$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (lastro, ampulheta)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Sopro abafado de quem perde o ar e o ranger de terra.$DESC$,
'cheiro', $DESC$Areia seca e cova aberta.$DESC$,
'quer', $DESC$Guardar as covas do campo-santo e sufocar quem as profana.$DESC$,
'tipo_perigo', $DESC$Oculto$DESC$,
'falas_exemplo', jsonb_build_array($DESC$Os que dormem aqui sao meus. Recoloque o que tirou.$DESC$, $DESC$Voce cavou. Agora respire, enquanto ainda da.$DESC$, $DESC$(registro: voz abafada como vinda de baixo da terra, no comum e em linguas de luto)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Profanam uma cova: cavam, roubam ou quebram lapide$DESC$, $DESC$Levam o que pertence aos mortos do campo-santo$DESC$, $DESC$Ferem ou desonram um tumulo na frente dele$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Volta a terra quando a cova e refechada e respeitada$DESC$, $DESC$Cessa contra quem devolve o que roubou$DESC$, $DESC$Deita so quando o laço que o prende a guardar e desfeito$DESC$),
'descoberta_fazendo', $DESC$Enterrado e invisivel num campo-santo de areia de Kethara, imovel, ate alguem por a mao numa cova.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Respeitar as tumbas e pedir licenca ao atravessar$DESC$, $DESC$Devolver o roubado e refechar a cova para aplaca-lo$DESC$, $DESC$Nao cavar mais, ja que se vence restaurando e nao profanando$DESC$, $DESC$Desfazer o laço que o prende a guardar o campo, para solta-lo$DESC$)
),
status_conversao='canonizada'
WHERE id=958;

-- 457 Zunido-Surdo | Engenho | controller | Ambiental | 10 Letal | Voranthar | fala
UPDATE ref_criaturas SET
nome=$DESC$Zunido-Surdo$DESC$,
nome_ptbr=$DESC$Zunido-Surdo$DESC$,
slug=$DESC$zunido-surdo$DESC$,
origem=$DESC$Cicatricial$DESC$,
andar_primario=$DESC$Eco$DESC$,
pilar_associado=$DESC$Engenho$DESC$,
continente=ARRAY[$DESC$Voranthar$DESC$]::text[],
habitat=$DESC$Criptas e bibliotecas afundadas de Voranthar onde a Margem e fina e o silencio zumbe.$DESC$,
comportamento=$DESC$Enche o ar de um zumbido que estoura a mente em area e controla o espaco com ondas de pensamento; agarra com frio quem se aproxima. Nao briga de corpo: domina o ambiente, e quem entra nele perde o juizo aos poucos.$DESC$,
organizacao=$DESC$Sozinho, regente de uma cripta.$DESC$,
perigo=$DESC$Letal$DESC$,
behavior_archetype=$DESC$controller$DESC$,
morale_modifier=0,
morale_immune=false,
epigrafe=$DESC$Nao houve grito. So um zumbido que cresceu ate eu nao lembrar por que tinha entrado naquela sala.$DESC$,
descricao=$DESC$E um morto de cabeca de tentaculo que ja morreu e nao parou de pensar, frio e seco, regente de uma cripta de Voranthar. Enche o ar de um zumbido surdo que, quando estoura, derruba a mente de todos no alcance, e controla a sala com ondas de pensamento que confundem e travam. Agarra com a mao gelada quem chega perto, mas o oficio dele e a area: fazer do espaco uma armadilha de juizo. Aguenta golpe e resiste a magia; o corpo nao e o problema, e o ar que ele tomou.$DESC$,
supersticao_popular=$DESC$Em Voranthar dizem que ha salas onde a cabeca para de funcionar, e que um morto de tentaculo mora la. O conselho: nao entrar em silencio que zumbe, recuar ao primeiro zumbido crescente, e nunca ir sozinho. Dizem que tampar os ouvidos resolve; nao adianta, o zumbido nao e som.$DESC$,
sinais_presenca=$DESC$Um zumbido surdo que cresce numa sala fechada. Gente que esquece o que ia fazer perto de certa cripta. Livros e ossos arrumados por uma mao paciente. Frio de toque sem fonte. Dor de cabeca que piora a cada passo adentro.$DESC$,
fraqueza_conhecida=$DESC$O povo recua do zumbido e tampa o ouvido, sem ver que nao e som. Acha que e barulho, e foge dele como de barulho.$DESC$,
fraqueza_real=$DESC$O perigo e a area de pensamento, nao o som nem o corpo. Resistir a dobra da mente, ou cortar o alcance do zumbido, atravessar rapido e atacar de varios pontos para ele nao concentrar a onda, tira o controle. Ele e fisicamente fraco e foge se a sala dele e invadida por muitos de uma vez. Mente treinada e disciplina aguentam o zumbido; entrar sozinho e devagar e o erro.$DESC$,
descricao_sensorial=$DESC$O som e um zumbido surdo que cresce e o estalo de uma onda de pensamento. O cheiro e de cripta seca e tinta velha. Ao toque, e mao gelada que prende. Aos olhos, e um morto de cabeca de tentaculo, parado e atento, no centro da sala.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$O juizo de quem entra na cripta que ele tomou$DESC$, $DESC$Estudiosos e curiosos do fundo de Voranthar$DESC$),
'predador', jsonb_build_array($DESC$Invadido por muitos de uma vez, e fraco e foge$DESC$),
'competidor', jsonb_build_array($DESC$Outras mentes mortas da Margem em Voranthar$DESC$, $DESC$Caco-Lúcido$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presenca dele diz que aquela sala tira o juizo de quem entra, e que ha um regente frio no centro.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem recua ao primeiro zumbido e nao entra sozinho$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$O orgao que emite o zumbido$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Engenho / golpe de mente em area, confundir um espaco)$DESC$, 'risco', $DESC$Zumbe na cabeca de quem o guarda e atrai a propria distracao.$DESC$),
jsonb_build_object('material', $DESC$A mao que agarra com frio$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Engenho / prender, esfriar o toque)$DESC$, 'risco', $DESC$Gela e entorpece a mao que a usa.$DESC$),
jsonb_build_object('material', $DESC$Tinta e folha de nota da cripta$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (registro antigo, formula rude)$DESC$, 'risco', $DESC$Confunde quem le sem preparo.$DESC$),
jsonb_build_object('material', $DESC$Po de osso e papel$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (massa, enchimento)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Zumbido surdo que cresce e o estalo de uma onda de pensamento.$DESC$,
'cheiro', $DESC$Cripta seca e tinta velha.$DESC$,
'quer', $DESC$Tomar o ar de uma sala e fazer do espaco uma armadilha de juizo, regendo do centro.$DESC$,
'tipo_perigo', $DESC$Ambiental$DESC$,
'falas_exemplo', jsonb_build_array($DESC$Voce ja esqueceu por que entrou. Bom. Fique.$DESC$, $DESC$O silencio aqui e meu. Voce so ouve o que eu deixo.$DESC$, $DESC$(registro: voz que chega por dentro, fria e precisa, em fala profunda e no comum, sob um zumbido constante)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Alguem entra na sala que ele tomou e enche de zumbido$DESC$, $DESC$Resistem a onda de pensamento dele$DESC$, $DESC$Ameacam o centro de onde ele rege a area$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Recua quando a sala e invadida por muitos de uma vez$DESC$, $DESC$Larga o controle e foge quando alcancado no centro$DESC$, $DESC$Some cripta adentro quando o zumbido e furado por varios pontos$DESC$),
'descoberta_fazendo', $DESC$No centro de uma cripta afundada de Voranthar, enchendo o ar de um zumbido surdo que confunde quem entra.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Recuar ao primeiro zumbido crescente e nao entrar sozinho$DESC$, $DESC$Atravessar rapido e atacar de varios pontos para ele nao concentrar a onda$DESC$, $DESC$Resistir com disciplina e ir direto no centro$DESC$, $DESC$Selar a sala e privar o regente de presas$DESC$)
),
status_conversao='canonizada'
WHERE id=457;

-- ========================= GRUPO 5 =========================

-- 926 Ferrão-Seco | Corpo | ambusher | Ambiental | 3 Ameaça | Kethara | MUDO
UPDATE ref_criaturas SET
nome=$DESC$Ferrão-Seco$DESC$,
nome_ptbr=$DESC$Ferrão-Seco$DESC$,
slug=$DESC$ferrao-seco$DESC$,
origem=$DESC$Natural$DESC$,
andar_primario=$DESC$Superfície$DESC$,
pilar_associado=$DESC$Corpo$DESC$,
continente=ARRAY[$DESC$Kethara$DESC$]::text[],
habitat=$DESC$Dunas e pedregais quentes de Kethara, sob a areia solta perto de oasis e trilhas.$DESC$,
comportamento=$DESC$Enterra-se na areia com so o ferrao curvo de prontidao, e o trecho de duna vira armadilha: quem pisa perto leva o ferrao de baixo. Caca por emboscada e veneno, nao por perseguicao.$DESC$,
organizacao=$DESC$Sozinho, cada um com seu trecho de areia.$DESC$,
perigo=$DESC$Ameaça$DESC$,
behavior_archetype=$DESC$ambusher$DESC$,
morale_modifier=0,
morale_immune=false,
epigrafe=$DESC$A areia parecia firme. Meu pe afundou um palmo e a coisa subiu com o ferrao primeiro.$DESC$,
descricao=$DESC$E um escorpiao do tamanho de um cao, de casca seca cor de areia, que se enterra e some. Nao corre atras: faz da duna a armadilha, enterrado com o ferrao curvo de prontidao, e sobe quando algo pisa perto. As pinças prendem, o ferrao injeta um veneno que endurece o corpo. De dia some no calor; o trecho dele e um campo de espera onde cada passo pode ser o errado.$DESC$,
supersticao_popular=$DESC$Em Kethara dizem que ha trechos de duna onde nao se pisa fora da trilha batida, porque a areia tem ferrao. O conselho: seguir a pedra firme, sondar a areia solta com vara, nao pisar onde o chao parece fofo demais. Dizem que o calor do dia o tira; o calor o esconde, nao o tira.$DESC$,
sinais_presenca=$DESC$Buracos de respiro na areia, do tamanho de um punho. Pinça ou ferrao de fora por um instante e some. Carcaças secas e duras perto de uma duna. Trilha de arrasto em V na areia de manha. Silencio de inseto num trecho quente.$DESC$,
fraqueza_conhecida=$DESC$O povo segue a pedra firme e sonda a areia com vara. Acha que o calor do dia o afasta.$DESC$,
fraqueza_real=$DESC$A forca dele e a emboscada e o veneno do primeiro ferrao; revelado e fora da areia, e so um bicho de casca que se quebra. Sondar a areia, andar na pedra e faze-lo dar o bote cedo tira a vantagem. Agua e frio o deixam lento. Uma vez de fora, cercado, cai rapido.$DESC$,
descricao_sensorial=$DESC$O som e quase nada, um raspar seco de casca sob a areia e o estalo do ferrao. O cheiro e de areia quente e casca seca. Ao toque, e casca dura e seca, quente de sol. Aos olhos, e um trecho de duna comum, ate a areia abrir e o ferrao subir.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Bichos e gente que pisam o trecho de duna dele$DESC$, $DESC$Animais que vem ao oasis perto$DESC$),
'predador', jsonb_build_array($DESC$Fora da areia e revelado, quebra facil; agua e frio o lentificam$DESC$),
'competidor', jsonb_build_array($DESC$Outros bichos de veneno de Kethara que disputam as dunas$DESC$, $DESC$Nó-de-Víboras$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presenca dele diz que aquele trecho de areia esconde ferrao, e que cada passo ali conta.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem segue a pedra firme e sonda a areia solta com vara$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$Ferrao com a glandula de veneno$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Corpo / veneno que endurece o corpo)$DESC$, 'risco', $DESC$Ferroa a mao que o limpa sem cuidado.$DESC$),
jsonb_build_object('material', $DESC$Pinças e casca dura$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (placa rude, ferramenta)$DESC$, 'risco', $DESC$Corta nas bordas.$DESC$),
jsonb_build_object('material', $DESC$Carapaça cor de areia$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (camuflagem, tigela)$DESC$, 'risco', $DESC$Nenhum.$DESC$),
jsonb_build_object('material', $DESC$Areia compactada da toca$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (lastro, abrasivo)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Raspar seco de casca sob a areia e o estalo do ferrao.$DESC$,
'cheiro', $DESC$Areia quente e casca seca.$DESC$,
'quer', $DESC$Esperar enterrado e ferroar o que pisa perto, sem gastar corpo.$DESC$,
'tipo_perigo', $DESC$Ambiental$DESC$,
'falas_exemplo', 'null'::jsonb,
'gatilhos_agressao', jsonb_build_array($DESC$Algo pisa o trecho de areia onde ele esta enterrado$DESC$, $DESC$Uma presa para perto do respiro dele$DESC$, $DESC$Mexem na areia solta da toca$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Enterra-se mais fundo quando o bote falha e a presa reage$DESC$, $DESC$Foge para a sombra fria quando tirado da areia quente$DESC$, $DESC$Abandona o trecho se ele e sondado e pisado demais$DESC$),
'descoberta_fazendo', $DESC$Enterrado na areia de uma duna de Kethara, so o ferrao curvo de prontidao, esperando um passo errado perto do respiro.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Seguir a pedra firme e sondar a areia solta com vara$DESC$, $DESC$Nao pisar onde o chao parece fofo demais$DESC$, $DESC$Faze-lo dar o bote cedo, de longe, e passar$DESC$, $DESC$Jogar agua e frio para lentifica-lo e contornar$DESC$)
),
status_conversao='canonizada'
WHERE id=926;

-- 1189 Beijo-Roxo | Sombra | predator | Direto | 8 Letal | Thornmarak | fala
UPDATE ref_criaturas SET
nome=$DESC$Beijo-Roxo$DESC$,
nome_ptbr=$DESC$Beijo-Roxo$DESC$,
slug=$DESC$beijo-roxo$DESC$,
origem=$DESC$Cicatricial$DESC$,
andar_primario=$DESC$Eco$DESC$,
pilar_associado=$DESC$Sombra$DESC$,
continente=ARRAY[$DESC$Thornmarak$DESC$]::text[],
habitat=$DESC$Matas e vilas de Thornmarak a noite, casaroes abandonados nas terras baixas umidas.$DESC$,
comportamento=$DESC$Caca de noite, surge do escuro com um golpe de sombra e a dentada, e bebe rapido; bonito de longe, frio de perto. Some antes do sol. Mata direto, sem brincar.$DESC$,
organizacao=$DESC$Sozinho, ou poucos repartindo uma regiao de caca.$DESC$,
perigo=$DESC$Letal$DESC$,
behavior_archetype=$DESC$predator$DESC$,
morale_modifier=0,
morale_immune=false,
epigrafe=$DESC$Ele beijou a testa dela como quem consola, e ela caiu sem sangue. Depois sorriu para nos, roxo nos labios.$DESC$,
descricao=$DESC$Foi gente de porte, e ainda guarda o charme; veste-se bem e fala macio, mas o que quer e sangue. Caca de noite e ataca direto: surge do escuro com um golpe de sombra, crava a dentada e bebe depressa, deixando o beijo roxo da boca na pele fria da vitima. E rapido e forte, e o sol o queima mais que aos seus pares, entao some bem antes do amanhecer. De perto, o charme cai e sobra a fome.$DESC$,
supersticao_popular=$DESC$Em Thornmarak dizem que ha um galante que vem de noite e deixa os labios roxos nos mortos. O conselho: nao receber estranho de noite, manter luz e fogo, e atravessar o sol em aberto se perseguido. Dizem que o convite o barra; o que o barra mesmo e o dia.$DESC$,
sinais_presenca=$DESC$Mortos palidos com a boca e a testa roxas, sem sangue. Um visitante elegante que so aparece de noite. Janelas e portas abertas por dentro de madrugada. Um perfume adocicado sobre cheiro de sangue. Caes que uivam e fogem de certa casa a noite.$DESC$,
fraqueza_conhecida=$DESC$O povo usa luz e fogo e nao recebe de noite. Sabe do sol. Acha o charme inofensivo, e ai erra.$DESC$,
fraqueza_real=$DESC$Ele e predador direto, e a fome o deixa afoito atras de presa exposta. O sol o queima mais que aos outros da laia, e ele teme isso; preso no aberto ao amanhecer, acaba. Cortar a retirada para o escuro e segura-lo ate o sol, ou usar a luz de proposito, vale mais que duelar de noite, quando e rapido. O charme e blefe; quem nao o convida nem o ouve nao cai.$DESC$,
descricao_sensorial=$DESC$O som e um sussurro macio e o roçar de capa, depois o estalo da dentada. O cheiro e de perfume doce sobre ferro de sangue. Ao toque, e mao fria e firme, de cortesia falsa. Aos olhos, e um galante palido de labios roxos que se move rapido demais no escuro.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Sangue de gente das vilas de Thornmarak$DESC$, $DESC$Hospedes e incautos recebidos de noite$DESC$),
'predador', jsonb_build_array($DESC$O sol, que o queima mais que aos seus; preso na luz, termina$DESC$),
'competidor', jsonb_build_array($DESC$Outros caçadores noturnos de Thornmarak que disputam as vilas$DESC$, $DESC$Matilha-Surda$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presenca dele diz que ha um que caça de noite por ali e deixa os labios roxos nos mortos.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem nao recebe estranho de noite e guarda luz e fogo$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$A glandula que tinge o beijo de roxo$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Sombra / golpe de sangue, sede que arrebata)$DESC$, 'risco', $DESC$Da uma sede fria a quem prova.$DESC$),
jsonb_build_object('material', $DESC$O manto de sombra com que surge$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Sombra / surgir do escuro, golpe furtivo)$DESC$, 'risco', $DESC$Escurece em volta de quem o veste e atrai o sol contra ele.$DESC$),
jsonb_build_object('material', $DESC$Anel ou joia de cortesia$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (adorno fino, blefe de nobreza)$DESC$, 'risco', $DESC$Atrai quem reconhece o dono.$DESC$),
jsonb_build_object('material', $DESC$Capa boa de tecido nobre$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (agasalho, disfarce)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Sussurro macio e o roçar de capa, depois o estalo da dentada.$DESC$,
'cheiro', $DESC$Perfume doce sobre ferro de sangue.$DESC$,
'quer', $DESC$Beber sangue farto na noite e sumir antes do sol, com charme ou sem.$DESC$,
'tipo_perigo', $DESC$Direto$DESC$,
'falas_exemplo', jsonb_build_array($DESC$Entre. Esta frio la fora, e eu sou boa companhia.$DESC$, $DESC$So um beijo. Voce nem vai sentir o frio depois.$DESC$, $DESC$(registro: voz macia e cortes, no comum e numa lingua antiga, que esfria quando a fome aparece)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Uma presa exposta de noite, ao alcance, com a fome alta$DESC$, $DESC$Sangue fresco no ar$DESC$, $DESC$O convidam ou o recebem de noite$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Corre para o escuro fechado quando o ceu clareia$DESC$, $DESC$Recua da luz forte e do fogo usado de proposito$DESC$, $DESC$Larga a caça e some quando o sol e usado contra ele$DESC$),
'descoberta_fazendo', $DESC$A noite, surgindo do escuro de um casarao das terras baixas de Thornmarak, charmoso, pouco antes de cravar a dentada.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Nao receber estranho de noite e guardar luz e fogo$DESC$, $DESC$Cortar a retirada dele para o escuro e segura-lo ate o sol$DESC$, $DESC$Atravessar o aberto ao amanhecer se perseguido$DESC$, $DESC$Recusar o charme e o convite, que e o que o deixa entrar$DESC$)
),
status_conversao='canonizada'
WHERE id=1189;

-- 810 Mácula-Crua | Arcano | brute | Persistente | 7 Letal | Voranthar | fala
UPDATE ref_criaturas SET
nome=$DESC$Mácula-Crua$DESC$,
nome_ptbr=$DESC$Mácula-Crua$DESC$,
slug=$DESC$macula-crua$DESC$,
origem=$DESC$Marginal$DESC$,
andar_primario=$DESC$Margem$DESC$,
pilar_associado=$DESC$Arcano$DESC$,
continente=ARRAY[$DESC$Voranthar$DESC$]::text[],
habitat=$DESC$Ruinas de Voranthar onde a Margem vazou, fendas de onde a desordem escorre.$DESC$,
comportamento=$DESC$Avança de frente, aguenta e se refaz, e a garra dele nao so fere: macula, e a maculacao muda e adoece quem pega, e nao para. Teimoso, resiste a magia, recua pouco.$DESC$,
organizacao=$DESC$Sozinho ou em poucos, perto de uma fenda da Margem.$DESC$,
perigo=$DESC$Letal$DESC$,
behavior_archetype=$DESC$brute$DESC$,
morale_modifier=2,
morale_immune=false,
epigrafe=$DESC$A garra entrou raso, quase nada. Tres dias depois meu braco nao era mais meu braco.$DESC$,
descricao=$DESC$E um bruto azul de couro grosso e cara de sapo, vindo de uma fenda da Margem em Voranthar. Avança reto, aguenta golpe e fecha a carne, e resiste a magia que se joga nele. A arma de verdade e a garra que macula: o corte raso planta uma desordem que muda a carne de quem pega, devagar, dia a dia, sem parar. Nao tem pressa nem medo; tem um corpo que dura e uma macula que se alastra sozinha.$DESC$,
supersticao_popular=$DESC$Em Voranthar dizem que ha brutos azuis nas ruinas da Margem, e que o arranhao deles vira a gente em outra coisa. O conselho: nao deixar a garra encostar, e cortar fora o que for maculado antes que se espalhe. Dizem que magia o derruba; ele resiste a magia, fogo e aço fazem mais.$DESC$,
sinais_presenca=$DESC$Carne mudada em bichos e gente perto de uma fenda da Margem. Couro azul mudado largado na muda. Um cheiro de coisa errada, nem podre nem vivo. Ruina com a pedra torcida fora de esquadro. Feridas rasas que mudam de cor e de forma com os dias.$DESC$,
fraqueza_conhecida=$DESC$O povo nao deixa encostar e corta fora o maculado. Acha que magia o resolve, e ele resiste a magia.$DESC$,
fraqueza_real=$DESC$Regeneracao, macula e resistencia a magia: a troca de golpes e o feitiço favorecem ele. Fogo e aço bruto, que ele nao regenera de volta do queimado, e tira-lo da fenda da Margem que o sustenta enfraquecem a teima. A macula se mata cortando ou queimando o ferido cedo, antes de pegar fundo. Nao se conta com feitiço; conta-se com chama e lamina.$DESC$,
descricao_sensorial=$DESC$O som e um coaxo grave e o estalo da carne se fechando. O cheiro e de coisa errada, nem podre nem viva. Ao toque, e couro umido e frio que repuxa a mao. Aos olhos, e um bruto azul que se ergue da ruina, ja curado do ultimo corte.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Bichos e gente que ele macula e muda perto da fenda$DESC$, $DESC$Tudo que vive na ruina que ele toma$DESC$),
'predador', jsonb_build_array($DESC$Fogo e aço bruto, e o fim da fenda da Margem que o sustenta$DESC$),
'competidor', jsonb_build_array($DESC$Outras coisas da Margem em Voranthar que disputam as ruinas$DESC$, $DESC$Polpa-Cinza$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presenca dele diz que a Margem vazou naquela ruina e que a carne em volta esta mudando.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem nao deixa a garra encostar e queima o maculado cedo$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$A glandula da garra que macula$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Arcano / mudar a carne, desordem que se alastra)$DESC$, 'risco', $DESC$Macula a mao que a abre sem queimar.$DESC$),
jsonb_build_object('material', $DESC$A carne que se recose sozinha$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Corpo / regenerar, resistir a magia)$DESC$, 'risco', $DESC$Muda de forma se guardada viva.$DESC$),
jsonb_build_object('material', $DESC$Couro azul mudado$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (couro estranho, resistente a feitiço)$DESC$, 'risco', $DESC$Repuxa e formiga ao toque longo.$DESC$),
jsonb_build_object('material', $DESC$Limo da fenda$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (cola, tinta azul)$DESC$, 'risco', $DESC$Nenhum se seco.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Coaxo grave e o estalo da carne se fechando.$DESC$,
'cheiro', $DESC$Coisa errada, nem podre nem viva.$DESC$,
'quer', $DESC$Alastrar a macula pela ruina e mudar a carne em volta, sem nunca parar de se refazer.$DESC$,
'tipo_perigo', $DESC$Persistente$DESC$,
'falas_exemplo', jsonb_build_array($DESC$Cortou? Bom. Agora deixei algo seu mudando.$DESC$, $DESC$Eu nao mudo. Voce e que muda, devagar.$DESC$, $DESC$(registro: voz grave e coaxada, em fala da Margem, lenta e sem medo)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Algo entra na ruina que ele tomou$DESC$, $DESC$Alguem fica ao alcance da garra que macula$DESC$, $DESC$Tentam fechar a fenda da Margem que o sustenta$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Recolhe-se a fenda da Margem para se refazer quando o fogo cerca$DESC$, $DESC$Recua so quando a chama impede a cura$DESC$, $DESC$Larga a presa se a fenda e fechada e a ruina queima$DESC$),
'descoberta_fazendo', $DESC$Numa ruina de Voranthar perto de uma fenda da Margem, maculando a carne em volta, refazendo-se de cada corte.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Nao deixar a garra encostar e contornar a ruina$DESC$, $DESC$Cortar ou queimar o maculado cedo, antes de pegar fundo$DESC$, $DESC$Atacar com fogo e aço bruto, nao com feitiço que ele resiste$DESC$, $DESC$Fechar a fenda da Margem que o sustenta para enfraquece-lo$DESC$)
),
status_conversao='canonizada'
WHERE id=810;

-- 2449 Murcho-Sôfrego | Espírito | striker | Oculto | 4 Ameaça | Voranthar | fala
UPDATE ref_criaturas SET
nome=$DESC$Murcho-Sôfrego$DESC$,
nome_ptbr=$DESC$Murcho-Sôfrego$DESC$,
slug=$DESC$murcho-sofrego$DESC$,
origem=$DESC$Cicatricial$DESC$,
andar_primario=$DESC$Eco$DESC$,
pilar_associado=$DESC$Espírito$DESC$,
continente=ARRAY[$DESC$Voranthar$DESC$]::text[],
habitat=$DESC$Ruinas escuras e poroes de Voranthar, onde o sol nao chega e a vida e rara.$DESC$,
comportamento=$DESC$Esconde-se no escuro, seco e murcho, e bota a mao ou a lamina em quem passa para sugar a vida e se encher um pouco; sofrego, quer sempre mais. Recua da luz, foge do sol.$DESC$,
organizacao=$DESC$Sozinho, num canto escuro que e so dele.$DESC$,
perigo=$DESC$Ameaça$DESC$,
behavior_archetype=$DESC$striker$DESC$,
morale_modifier=-1,
morale_immune=false,
epigrafe=$DESC$Ele parecia so mais um trapo seco no canto, ate a mao agarrar meu pulso e eu sentir os anos saindo.$DESC$,
descricao=$DESC$E um morto seco, de face encovada e pele de pergaminho, que segura uma lamina velha e se esconde no escuro de Voranthar. Nao murcha mais; faz murchar os outros. Surge do canto e crava a mao ou a lamina para sugar a vida de quem passa, e cada gole o enche um pouco e o deixa querer mais. Sofrego, nunca se farta. A luz o fere e o sol o apavora, entao caça no breu e some quando alguem traz tocha demais.$DESC$,
supersticao_popular=$DESC$Em Voranthar dizem que ha secos que sugam a vida no escuro das ruinas, e que envelhecem quem tocam. O conselho: luz farta, nao encostar, nao se demorar no canto escuro. Dizem que cortar a lamina dele o deita; deita por pouco, a fome o reergue.$DESC$,
sinais_presenca=$DESC$Gente achada envelhecida de repente, seca e fraca. Um trapo seco num canto escuro que nao estava ali. Frio de pulso quando se passa perto de uma sombra. Tochas que ele evita, deixando um canto sempre escuro. Lamina velha largada onde houve um seco.$DESC$,
fraqueza_conhecida=$DESC$O povo usa luz e nao encosta. Acha que cortar a lamina dele resolve, e a fome o reergue.$DESC$,
fraqueza_real=$DESC$E um golpeador que vive de surpresa e de escuro: revelado pela luz e exposto ao sol, foge e enfraquece. Nao se demorar no breu, iluminar o canto e força-lo ao aberto o quebram, porque a fome o torna afoito e ele se expoe atras de mais um gole. Cortar so a lamina nao basta; e a luz e o sol que o desfazem.$DESC$,
descricao_sensorial=$DESC$O som e um arquejo seco e faminto e o roçar de pano velho. O cheiro e de poeira, pergaminho e mofo. Ao toque, e mao seca e fria que repuxa a vida pelo pulso. Aos olhos, e um morto encovado de lamina, encolhido no escuro, ate a mao sair.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$A vida de quem passa pelo escuro das ruinas de Voranthar$DESC$, $DESC$Incautos que se demoram no canto sem luz$DESC$),
'predador', jsonb_build_array($DESC$A luz e o sol, que o ferem e o expoem$DESC$),
'competidor', jsonb_build_array($DESC$Outros secos e drenadores do Eco em Voranthar$DESC$, $DESC$Mágoa-de-Pedra$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presenca dele diz que aquele escuro suga a vida de quem fica, e que ha um seco sofrego no canto.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem leva luz farta e nao se demora no breu$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$A mao que repuxa a vida$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Eco / drenar vida, encher-se do vigor alheio)$DESC$, 'risco', $DESC$Envelhece a mao que a usa sem preparo.$DESC$),
jsonb_build_object('material', $DESC$A lamina velha que ele crava$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Sombra / golpe que suga, ferir no escuro)$DESC$, 'risco', $DESC$Da sede de vida a quem a empunha demais.$DESC$),
jsonb_build_object('material', $DESC$Pergaminho seco do que vestia$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (papel velho, registro ilegivel)$DESC$, 'risco', $DESC$Esfarela ao sol.$DESC$),
jsonb_build_object('material', $DESC$Po seco do canto dele$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (po de traça, isca)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Arquejo seco e faminto e o roçar de pano velho.$DESC$,
'cheiro', $DESC$Poeira, pergaminho e mofo.$DESC$,
'quer', $DESC$Sugar a vida de quem passa para se encher, sempre querendo mais, longe da luz.$DESC$,
'tipo_perigo', $DESC$Oculto$DESC$,
'falas_exemplo', jsonb_build_array($DESC$So um pouco. Voce tem tantos anos, e eu nao tenho nenhum.$DESC$, $DESC$Apague essa luz. Fique aqui no canto comigo, so um instante.$DESC$, $DESC$(registro: voz seca e arquejada, faminta, no comum e numa lingua de antes, baixinha para nao chamar a luz)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Alguem se demora no canto escuro onde ele se esconde$DESC$, $DESC$Passa uma presa de vida farta ao alcance da mao$DESC$, $DESC$Apagam a luz e deixam o breu para ele$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Recua e some quando trazem tocha demais para o canto$DESC$, $DESC$Foge do sol e da luz forte, que o ferem$DESC$, $DESC$Larga a presa quando e força ao aberto iluminado$DESC$),
'descoberta_fazendo', $DESC$Encolhido como trapo seco num canto escuro de uma ruina de Voranthar, lamina na mao, esperando alguem se demorar perto.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Levar luz farta e nao se demorar no canto escuro$DESC$, $DESC$Iluminar o breu e força-lo ao aberto, onde enfraquece$DESC$, $DESC$Nao encostar e negar a ele o gole que o reergue$DESC$, $DESC$Atrai-lo com presa exposta a um trecho que o sol vai varrer$DESC$)
),
status_conversao='canonizada'
WHERE id=2449;

-- 1958 Pupila-Imunda | Engenho | controller | Condicional | 10 Letal | Thornmarak | fala
UPDATE ref_criaturas SET
nome=$DESC$Pupila-Imunda$DESC$,
nome_ptbr=$DESC$Pupila-Imunda$DESC$,
slug=$DESC$pupila-imunda$DESC$,
origem=$DESC$Marginal$DESC$,
andar_primario=$DESC$Margem$DESC$,
pilar_associado=$DESC$Engenho$DESC$,
continente=ARRAY[$DESC$Thornmarak$DESC$]::text[],
habitat=$DESC$Aguas paradas e esgotos de Thornmarak, cisternas e canais das terras baixas umidas.$DESC$,
comportamento=$DESC$Fica perto da agua, de que depende, e controla pela corrupcao: um olho que, provocado, lanca um raio que torce a mente e o corpo de quem mira. Luta de espada se obrigado, mas prefere dominar a distancia. So abre o olho quando desafiado.$DESC$,
organizacao=$DESC$Sozinho, anfitriao de um canal ou cisterna.$DESC$,
perigo=$DESC$Letal$DESC$,
behavior_archetype=$DESC$controller$DESC$,
morale_modifier=0,
morale_immune=false,
epigrafe=$DESC$Ele foi cortes ate eu sacar a arma. Ai o olho dele abriu, e por um instante a arma estava apontada para o meu proprio amigo.$DESC$,
descricao=$DESC$E um senhor de fala mansa e um olho a mais, que vive perto da agua e murcha longe dela. Controla pela corrupcao: provocado, abre o olho e lanca um raio que torce a vontade e a carne de quem fixa, virando aliado contra aliado por um instante. Resiste a magia e maneja a espada, mas prefere o controle a distancia e a cortesia ate ser desafiado. Fora da agua, definha; perto dela, e dono da sala.$DESC$,
supersticao_popular=$DESC$Em Thornmarak dizem que ha um senhor de um olho a mais nos canais, cortes ate ser provocado, e que o olhar dele vira a gente contra a gente. O conselho: nao sacar arma perto dele, nao ameacar, e afasta-lo da agua se for preciso brigar. Dizem que e so um nobre estranho; e ate alguem desafiar.$DESC$,
sinais_presenca=$DESC$Um anfitriao cortes que nunca se afasta da agua. Gente que por um instante ataca o proprio aliado e nao sabe explicar. Peixe e planta de agua mortos e torcidos em volta. Um olho a mais que pisca fora de hora. Canais e cisternas guardados por alguem educado demais.$DESC$,
fraqueza_conhecida=$DESC$O povo evita provoca-lo e tenta afasta-lo da agua. Acha que e so um nobre esquisito, e ai baixa a guarda.$DESC$,
fraqueza_real=$DESC$Condicional e dependente de agua: enquanto ninguem o desafia, ele e so cortesia, e o olho fica fechado. Provocado, o raio de corrupcao e o perigo, nao a espada. Tira-lo da agua, de que depende, o enfraquece rapido; resistir a torcao da vontade e fechar a distancia antes da recarga do olho o derrubam. Nao se saca arma a toa perto dele; controla-se o gatilho.$DESC$,
descricao_sensorial=$DESC$O som e uma fala mansa e o marulho de agua perto. O cheiro e de agua parada e perfume sobre mofo. Ao toque, e pele umida e fria de quem nunca seca. Aos olhos, e um senhor cortes com um olho a mais que abre quando desafiado.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$A vontade de quem o desafia perto da agua$DESC$, $DESC$Viajantes que ele torce um contra o outro$DESC$),
'predador', jsonb_build_array($DESC$Longe da agua, definha; resistir e fechar distancia o derruba$DESC$),
'competidor', jsonb_build_array($DESC$Outras coisas de agua e mente da Margem em Thornmarak$DESC$, $DESC$Lacuna-Faminta$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presenca dele diz que aquele canal tem um anfitriao que vira a gente contra a gente quando provocado.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem nao saca arma nem ameaca perto dele e o mantem longe da agua$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$O olho da corrupcao$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Engenho / raio que torce a vontade e a carne)$DESC$, 'risco', $DESC$Torce quem o destampa e mira sozinho o aliado mais perto.$DESC$),
jsonb_build_object('material', $DESC$O orgao que o prende a agua$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Engenho / controle a distancia enquanto perto dagua)$DESC$, 'risco', $DESC$Definha e apodrece fora da agua.$DESC$),
jsonb_build_object('material', $DESC$A rapieira de cortesia$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (espada fina, lamina de duelo)$DESC$, 'risco', $DESC$Atrai o duelo que ele evita.$DESC$),
jsonb_build_object('material', $DESC$Agua parada da cisterna dele$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (lastro, agua de molho)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Fala mansa e o marulho de agua perto.$DESC$,
'cheiro', $DESC$Agua parada e perfume sobre mofo.$DESC$,
'quer', $DESC$Dominar pela corrupcao perto da agua, virando aliado contra aliado, sem largar a cortesia ate ser desafiado.$DESC$,
'tipo_perigo', $DESC$Condicional$DESC$,
'falas_exemplo', jsonb_build_array($DESC$Guarde a arma, amigo. Nao ha briga aqui. Ainda.$DESC$, $DESC$Voce me desafiou. Agora olhe para o seu companheiro, e veja o que faz.$DESC$, $DESC$(registro: voz mansa e cortes, no comum, em fala profunda e numa lingua de fundo, que esfria ao ser desafiado)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Sacam arma ou o ameacam perto da agua$DESC$, $DESC$Desafiam a cortesia ou o territorio de agua dele$DESC$, $DESC$Tentam tira-lo da agua de que depende$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Recua para a agua quando exposto em terra seca$DESC$, $DESC$Larga o controle e mergulha quando furam a distancia$DESC$, $DESC$Cessa o jogo e foge quando definha longe da agua$DESC$),
'descoberta_fazendo', $DESC$Perto de um canal ou cisterna das terras baixas de Thornmarak, cortes, de olho extra fechado, ate alguem o desafiar.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Nao sacar arma nem ameacar perto dele$DESC$, $DESC$Mante-lo ou atrai-lo para longe da agua, onde definha$DESC$, $DESC$Resistir a torcao e fechar a distancia antes da recarga do olho$DESC$, $DESC$Aceitar a hospitalidade fria e seguir sem desafiar$DESC$)
),
status_conversao='canonizada'
WHERE id=1958;

-- ========================= GRUPO 6 =========================

-- 928 Bocarra-Surda | Corpo | predator | Direto | 5 Ameaça | Kethara | MUDO
UPDATE ref_criaturas SET
nome=$DESC$Bocarra-Surda$DESC$,
nome_ptbr=$DESC$Bocarra-Surda$DESC$,
slug=$DESC$bocarra-surda$DESC$,
origem=$DESC$Natural$DESC$,
andar_primario=$DESC$Superfície$DESC$,
pilar_associado=$DESC$Corpo$DESC$,
continente=ARRAY[$DESC$Kethara$DESC$]::text[],
habitat=$DESC$Aguas costeiras e fundos de Kethara, recifes e ancoradouros onde o fundo some.$DESC$,
comportamento=$DESC$Nada em circulos e vem reto na mordida quando sente sangue ou movimento; cego de luz, ve pela vibracao da agua. Nao desiste de presa ferida. Dono da agua funda.$DESC$,
organizacao=$DESC$Sozinha, ou poucas rondando o mesmo fundo.$DESC$,
perigo=$DESC$Ameaça$DESC$,
behavior_archetype=$DESC$predator$DESC$,
morale_modifier=1,
morale_immune=false,
epigrafe=$DESC$A agua estava calma. Ai um deles sangrou de leve, e a calma virou espuma e dentes.$DESC$,
descricao=$DESC$E um tubarao do tamanho de um barco, que enxerga pouco e sente tudo pela vibracao da agua. Vem reto, sem aviso, e a mordida leva o pedaco; cheiro de sangue ou debater na agua o chama de longe. Nao tem astucia, tem fome e faro de vibracao, e nao larga presa ferida. Na agua funda, e dono; perto da praia, e onde a gente corre.$DESC$,
supersticao_popular=$DESC$Na costa de Kethara dizem para nao sangrar nem se debater na agua funda, e para nao nadar onde o fundo some. O conselho: ficar no raso, nao jogar tripa de peixe perto de gente, e sair da agua se um deles ronda. Dizem que bater na agua o afasta; bater o chama.$DESC$,
sinais_presenca=$DESC$Barbatana cortando a agua em circulo. Cardumes que fogem em massa para o raso. Agua turva de sangue sem ferido a vista. Mordidas em meia-lua no casco de barco. Silencio de ave marinha sobre um trecho de mar.$DESC$,
fraqueza_conhecida=$DESC$O povo fica no raso e nao sangra a agua. Acha que bater na agua o afasta, e bater o chama.$DESC$,
fraqueza_real=$DESC$E predador de agua funda guiado por vibracao; no raso e na areia perde a vantagem, e encalhado e so peso. Nao sangrar, nao se debater e sair para o raso o frustram. Ele vem pelo movimento e pelo sangue, entao quietude e raso salvam; lutar na agua funda e o erro.$DESC$,
descricao_sensorial=$DESC$O som e um corte de agua e o baque surdo do corpo grande. O cheiro e de mar e sangue. Ao toque, e pele de lixa que rala a carne. Aos olhos, e uma sombra longa sob a agua, depois a bocarra abrindo.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Peixe grande, foca e gente na agua funda de Kethara$DESC$, $DESC$Qualquer coisa ferida que sangra na agua$DESC$),
'predador', jsonb_build_array($DESC$No raso e encalhada perde tudo; poucos a enfrentam na agua funda$DESC$),
'competidor', jsonb_build_array($DESC$Outros predadores de agua de Kethara que disputam o fundo$DESC$, $DESC$Ninhada-Sedenta$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presenca dela diz que aquele trecho de mar funda e caçada dela, e que sangue ali e chamado.$DESC$,
'evitado_por', jsonb_build_array($DESC$Pescadores que ficam no raso e nao sangram a agua$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$Mandibula com fileiras de dente$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Corpo / mordida, faro de vibracao)$DESC$, 'risco', $DESC$Corta a mao em qualquer descuido.$DESC$),
jsonb_build_object('material', $DESC$Pele de lixa$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (lixa natural, couro abrasivo)$DESC$, 'risco', $DESC$Rala a pele de quem manuseia.$DESC$),
jsonb_build_object('material', $DESC$Oleo de figado$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (oleo de lampada, unguento)$DESC$, 'risco', $DESC$Nenhum.$DESC$),
jsonb_build_object('material', $DESC$Cartilagem grande$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (cola, gelatina)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Corte de agua e o baque surdo do corpo grande.$DESC$,
'cheiro', $DESC$Mar e sangue.$DESC$,
'quer', $DESC$Comer o que se move ou sangra na agua funda, sem largar presa ferida.$DESC$,
'tipo_perigo', $DESC$Direto$DESC$,
'falas_exemplo', 'null'::jsonb,
'gatilhos_agressao', jsonb_build_array($DESC$Sangue ou debater na agua funda ao alcance$DESC$, $DESC$Uma presa isolada longe do raso$DESC$, $DESC$Jogam restos de peixe perto de gente$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Vai para o fundo quando a presa alcanca o raso$DESC$, $DESC$Larga a caça quando encalha ou bate em pedra$DESC$, $DESC$Perde o rastro quando a agua aquieta e ninguem sangra$DESC$),
'descoberta_fazendo', $DESC$Rondando em circulo um trecho de mar funda de Kethara, guiada pela vibracao, a espera de sangue ou debater.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Ficar no raso e nao nadar onde o fundo some$DESC$, $DESC$Nao sangrar nem se debater na agua$DESC$, $DESC$Sair da agua quando uma barbatana ronda$DESC$, $DESC$Atrai-la para o raso ou pedra, onde perde a vantagem$DESC$)
),
status_conversao='canonizada'
WHERE id=928;

-- 1934 Afogado-Salgado | Sombra | ambusher | Condicional | 2 Ameaça | Thornmarak | MUDO
UPDATE ref_criaturas SET
nome=$DESC$Afogado-Salgado$DESC$,
nome_ptbr=$DESC$Afogado-Salgado$DESC$,
slug=$DESC$afogado-salgado$DESC$,
origem=$DESC$Cicatricial$DESC$,
andar_primario=$DESC$Eco$DESC$,
pilar_associado=$DESC$Sombra$DESC$,
continente=ARRAY[$DESC$Thornmarak$DESC$]::text[],
habitat=$DESC$Pantanos salgados e vaus alagados de Thornmarak, baixadas onde um exercito ou navio afundou.$DESC$,
comportamento=$DESC$Jaz no fundo da agua salobra, imovel, ligado a outros como ele, e sobe em grupo quando alguem cruza o vau ou perturba a agua; ataca com a espada enferrujada e arrasta para o fundo. So se ergue quando a agua e pisada.$DESC$,
organizacao=$DESC$Em grupos ligados, tropa ou tripulacao afogada junta.$DESC$,
perigo=$DESC$Ameaça$DESC$,
behavior_archetype=$DESC$ambusher$DESC$,
morale_modifier=0,
morale_immune=true,
epigrafe=$DESC$O vau parecia vazio. Quando entramos ate a cintura, o fundo se levantou em espadas.$DESC$,
descricao=$DESC$Foi soldado, morreu afogado de armadura, e o sal o conservou no fundo. Jaz imovel na agua salobra, ligado a outros afogados do mesmo naufragio ou batalha, e sobe em fila quando alguem cruza o vau ou mexe na agua. Golpeia com a espada enferrujada e puxa para o fundo. Nao caça; espera ser pisado. Fora dagua e lento e pesado; na agua salobra dele, e uma emboscada de muitos.$DESC$,
supersticao_popular=$DESC$Em Thornmarak dizem que certos vaus alagados tem soldados no fundo, e que cruza-los a pe e convite. O conselho: nao atravessar vau parado e salobro a pe, sondar o fundo, e procurar ponte ou barco. Dizem que sal os mantem; tirar a agua os deita.$DESC$,
sinais_presenca=$DESC$Cabos de espada enferrujada de fora no fundo raso. Armadura coberta de craca na lama. Agua salobra parada com brilho de oleo. Bolhas em fila subindo de um vau. Um frio salgado na agua na altura da canela.$DESC$,
fraqueza_conhecida=$DESC$O povo nao cruza a pe e sonda o fundo. Acha que o sal os mantem, sem ver que e a agua.$DESC$,
fraqueza_real=$DESC$Sao condicionais ao vau: ficam quietos se ninguem pisa a agua. Ligados, sobem juntos; quebrar o elo entre eles os deixa lentos e perdidos. Drenar a agua ou cruzar por ponte e barco nega o gatilho. Fora dagua sao pesados e lentos. Nao se atravessa a pe a agua salobra parada.$DESC$,
descricao_sensorial=$DESC$O som e um borbulhar surdo e o ranger de armadura encrostada. O cheiro e de sal, lama e ferro velho. Ao toque, e mao fria e encrostada que agarra o tornozelo. Aos olhos, e cabos de espada no fundo, depois a fila de afogados subindo.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Quem cruza o vau alagado deles a pe$DESC$, $DESC$Bichos e gente que perturbam a agua salobra$DESC$),
'predador', jsonb_build_array($DESC$Drenada a agua, deitam; fora dagua sao lentos$DESC$),
'competidor', jsonb_build_array($DESC$Outros mortos de agua de Thornmarak que disputam os vaus$DESC$, $DESC$Pardo-Calado$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presenca deles diz que ali afundou tropa ou navio, e que o vau cobra de quem pisa.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem nao cruza vau salobro a pe e procura ponte ou barco$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$O elo salgado que liga uns aos outros$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Sombra / agir em grupo ligado, emboscar do fundo)$DESC$, 'risco', $DESC$Prende quem o guarda a um grupo que nao e seu.$DESC$),
jsonb_build_object('material', $DESC$Armadura encrostada de sal e craca$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Corpo / peso no fundo, resistir a corrente)$DESC$, 'risco', $DESC$Arrasta para baixo na agua funda.$DESC$),
jsonb_build_object('material', $DESC$Espada enferrujada$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (ferro velho, sucata)$DESC$, 'risco', $DESC$Quebra e fere com farpa.$DESC$),
jsonb_build_object('material', $DESC$Sal grosso da agua salobra$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (conserva, salga)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Borbulhar surdo e o ranger de armadura encrostada.$DESC$,
'cheiro', $DESC$Sal, lama e ferro velho.$DESC$,
'quer', $DESC$Jazer no fundo e arrastar para baixo quem cruza o vau, sem se erguer a toa.$DESC$,
'tipo_perigo', $DESC$Condicional$DESC$,
'falas_exemplo', 'null'::jsonb,
'gatilhos_agressao', jsonb_build_array($DESC$Alguem cruza a pe o vau alagado deles$DESC$, $DESC$Perturbam ou mexem na agua salobra do fundo$DESC$, $DESC$Tentam tirar do fundo o que afundou com a tropa$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Voltam ao fundo quando a agua aquieta e ninguem pisa$DESC$, $DESC$Param e se perdem quando o elo entre eles e quebrado$DESC$, $DESC$Deitam quando a agua e drenada ou o vau seca$DESC$),
'descoberta_fazendo', $DESC$Jazendo no fundo de um vau salobro de Thornmarak, imoveis e ligados, ate alguem entrar na agua.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Nao cruzar o vau a pe e procurar ponte ou barco$DESC$, $DESC$Drenar a agua ou desviar o curso para deita-los$DESC$, $DESC$Quebrar o elo entre eles para deixa-los lentos$DESC$, $DESC$Sondar o fundo e contornar o trecho alagado$DESC$)
),
status_conversao='canonizada'
WHERE id=1934;

-- 1049 Atadura-Régia | Arcano | controller | Ambiental | 15 Letal | Kethara | fala
UPDATE ref_criaturas SET
nome=$DESC$Atadura-Régia$DESC$,
nome_ptbr=$DESC$Atadura-Régia$DESC$,
slug=$DESC$atadura-regia$DESC$,
origem=$DESC$Cicatricial$DESC$,
andar_primario=$DESC$Eco$DESC$,
pilar_associado=$DESC$Arcano$DESC$,
continente=ARRAY[$DESC$Kethara$DESC$]::text[],
habitat=$DESC$Tumbas reais sob a areia de Kethara, camaras seladas de antigos senhores.$DESC$,
comportamento=$DESC$Governa a propria tumba como reino: enche a camara de uma maldicao seca que apodrece e enfraquece quem entra, prega medo com o olhar e ergue os servos sepultados. Nao sai do tumulo; faz da camara a arma. So age contra quem entra.$DESC$,
organizacao=$DESC$Sozinha no trono, cercada dos servos sepultados que ergue.$DESC$,
perigo=$DESC$Letal$DESC$,
behavior_archetype=$DESC$controller$DESC$,
morale_modifier=0,
morale_immune=true,
epigrafe=$DESC$A camara inteira nos odiava. O ar secava a garganta, a luz morria, e na cadeira a coisa enfaixada nem se levantou.$DESC$,
descricao=$DESC$Foi um senhor enfaixado e selado com riqueza, e a maldicao o manteve regente da propria tumba. Governa a camara como reino seco: o ar apodrece, a areia se levanta, a luz minga, e quem entra enfraquece a cada passo. Prega um medo que trava com o olhar e ergue os servos sepultados em volta. Nao persegue para fora; faz do tumulo a arma e espera o profanador vir ate o trono. Resiste a magia e nao teme nada que ja perdeu.$DESC$,
supersticao_popular=$DESC$Em Kethara dizem que as tumbas dos senhores antigos matam quem as abre, e que o ar la dentro odeia os vivos. O conselho: nao abrir camara selada de rei, nao levar o ouro, e fugir se a luz comeca a morrer. Dizem que fogo a queima; a faixa queima, mas a maldicao da camara fica.$DESC$,
sinais_presenca=$DESC$Uma camara selada com riqueza intacta sob a areia. Ar seco que apodrece comida e enfraquece o corpo. Tochas que minguam ao cruzar a soleira. Servos enfaixados de pe nas paredes. Um medo subito ao encarar a cadeira do fundo.$DESC$,
fraqueza_conhecida=$DESC$O povo nao abre, nao leva o ouro e foge da luz que morre. Acha que fogo resolve, e a maldicao da camara fica.$DESC$,
fraqueza_real=$DESC$Controlador preso a camara: o perigo e a maldicao do espaco e os servos, e ele nao sai do tumulo. Nao entrar, ou entrar sem cobiçar o que e dele, evita o gatilho. Para quem ja entrou, devolver o que tomou e selar de novo aplaca; desfaze-lo de vez exige quebrar a maldicao que o prende ao trono, e nao so queimar a faixa. Luz e fogo seguram a camara, mas o regente so cai com a maldicao desfeita.$DESC$,
descricao_sensorial=$DESC$O som e um sussurro seco de areia e o ranger de faixa, e o silencio que abafa a voz. O cheiro e de incenso velho, po e carne seca. Ao toque, e faixa seca e areia que arde nos olhos. Aos olhos, e um senhor enfaixado, imovel numa cadeira de ouro, e a camara escurecendo em volta.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Profanadores que abrem e saqueiam a tumba dele$DESC$, $DESC$Quem entra na camara e cobiça o que e seu$DESC$),
'predador', jsonb_build_array($DESC$A maldicao desfeita o encerra; nada o tira do trono a forca$DESC$),
'competidor', jsonb_build_array($DESC$Outros senhores mortos de Kethara que guardam tumbas$DESC$, $DESC$Cauda-Acesa$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presenca dele diz que aquela tumba ainda tem dono, e que a camara mata quem entra cobiçando.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem nao abre camara selada de rei nem leva o ouro$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$A faixa que carrega a maldicao da camara$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Arcano / maldicao em area, apodrecer e enfraquecer um espaco)$DESC$, 'risco', $DESC$Seca e enfraquece quem a guarda sem selo.$DESC$),
jsonb_build_object('material', $DESC$O olho seco que prega o medo$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Sombra / pregar pavor que trava o corpo)$DESC$, 'risco', $DESC$Da pesadelos a quem o porta.$DESC$),
jsonb_build_object('material', $DESC$Amuleto regio da tumba$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (joia antiga, insignia de senhor)$DESC$, 'risco', $DESC$Atrai a cobiça e os outros guardioes.$DESC$),
jsonb_build_object('material', $DESC$Incenso e po de tumba$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (incenso velho, po de cal)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Sussurro seco de areia e o ranger de faixa, sob um silencio que abafa a voz.$DESC$,
'cheiro', $DESC$Incenso velho, po e carne seca.$DESC$,
'quer', $DESC$Reger a propria tumba como reino e punir quem profana a camara.$DESC$,
'tipo_perigo', $DESC$Ambiental$DESC$,
'falas_exemplo', jsonb_build_array($DESC$Voce entrou no meu reino. Aqui o ar e meu, e a luz, e o seu medo.$DESC$, $DESC$Deixe o ouro e talvez eu deixe seu folego.$DESC$, $DESC$(registro: voz seca e regia, no comum e em varias linguas mortas, lenta como quem nunca teve pressa)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Abrem ou saqueiam a camara selada dele$DESC$, $DESC$Levam o ouro ou a insignia da tumba$DESC$, $DESC$Cobiçam ou tocam o que e do senhor$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Nao sai do trono; cessa a maldicao quando devolvem o tomado e selam$DESC$, $DESC$Aquieta a camara quando o profanador recua e nada leva$DESC$, $DESC$Deita so quando a maldicao que o prende e desfeita$DESC$),
'descoberta_fazendo', $DESC$Imovel numa cadeira de ouro no fundo de uma tumba selada de Kethara, regendo a camara que escurece e apodrece em volta.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Nao abrir a camara selada nem levar o ouro$DESC$, $DESC$Devolver o tomado e selar a tumba de novo para aplaca-lo$DESC$, $DESC$Sair antes que a luz morra de vez$DESC$, $DESC$Desfazer a maldicao que o prende ao trono para encerra-lo$DESC$)
),
status_conversao='canonizada'
WHERE id=1049;

-- 1870 Égide-Severa | Espírito | defender | Persistente | 16 Destruidor | Thornmarak | fala
UPDATE ref_criaturas SET
nome=$DESC$Égide-Severa$DESC$,
nome_ptbr=$DESC$Égide-Severa$DESC$,
slug=$DESC$egide-severa$DESC$,
origem=$DESC$Cicatricial$DESC$,
andar_primario=$DESC$Clarão$DESC$,
pilar_associado=$DESC$Espírito$DESC$,
continente=ARRAY[$DESC$Thornmarak$DESC$]::text[],
habitat=$DESC$Altos de cristal de Thornmarak onde o Clarao desce, santuarios e marcos postos sob guarda.$DESC$,
comportamento=$DESC$Guarda um marco ou um ser sob sua tutela e nao cede: apara golpes com a espada-egide, fere de longe com o arco e refaz o que protege. Frio e metodico, nao recua enquanto o que guarda existe. Nao e bondoso; e inabalavel.$DESC$,
organizacao=$DESC$Sozinho, sentinela de um unico marco ou tutela.$DESC$,
perigo=$DESC$Destruidor$DESC$,
behavior_archetype=$DESC$defender$DESC$,
morale_modifier=0,
morale_immune=true,
epigrafe=$DESC$Pedimos ajuda, e ele curou o ferido sem nos olhar. Depois barrou a saida, porque sair nao estava na regra dele.$DESC$,
descricao=$DESC$E um guardiao de luz alto e severo do Clarao, que o povo confunde com salvador. Nao salva por do; protege o que lhe coube guardar e refaz o que se quebra do seu lado, com a mesma frieza com que apara o golpe e fere de longe quem ameaca o marco. E inabalavel: enquanto o que ele guarda existe, nao cede um passo, nao foge, nao cansa. Ajuda quem esta sob a tutela dele e barra todo o resto, sem raiva e sem carinho, so regra.$DESC$,
supersticao_popular=$DESC$Em Thornmarak dizem que ha guardioes de luz que protegem certos marcos, e que sao bons porque curam. O povo erra: eles curam so o que e deles e barram todo o resto. O conselho: saber o que ele guarda e nao ameacar, e nao confundir a cura com bondade. Dizem que e aliado; e ate voce ficar entre ele e o que ele protege.$DESC$,
sinais_presenca=$DESC$Um marco ou santuario de cristal sempre intacto no meio da ruina. Um guardiao alto de luz que apara e refaz sem se cansar. Feridos do lado dele que saram rapido demais. Flechas de luz que vem de longe e certeiras. Uma linha que ninguem do lado errado cruza.$DESC$,
fraqueza_conhecida=$DESC$O povo evita ameacar o que ele guarda. Acha que e aliado bondoso, e ai se poe no lugar errado.$DESC$,
fraqueza_real=$DESC$Defensor persistente e preso a um encargo: enquanto o que ele guarda existe, nao cede e refaz tudo. Ele nao persegue para longe do marco; sair do alcance do que ele protege encerra o confronto. Ataca-lo de frente e perder, porque apara e cura; o caminho e tirar o motivo, afastar a ameaca ao marco, ou desfazer o encargo que o prende, e nao trocar golpe com o inabalavel.$DESC$,
descricao_sensorial=$DESC$O som e um tinir de luz aparada e o zunido do arco. O cheiro e de ar limpo e cristal quente. Ao toque, e gume de luz que apara sem ceder. Aos olhos, e um guardiao alto e severo de luz, parado entre voce e o que ele protege.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Nao caça; fere quem ameaca o marco que guarda$DESC$, $DESC$Quem fica entre ele e o que protege$DESC$),
'predador', jsonb_build_array($DESC$Nada o derruba enquanto o encargo existe; desfeito o encargo, ele cede$DESC$),
'competidor', jsonb_build_array($DESC$Outras sentinelas de luz de Thornmarak com marcos vizinhos$DESC$, $DESC$Fulgor-Alheio$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presenca dele diz que ali ha um marco do Clarao sob guarda que nao cede, e uma regra fria em volta.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem sabe o que ele guarda e nao ameaca o marco$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$A egide de luz que apara o golpe$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Eco do Clarao / aparar, proteger um ponto)$DESC$, 'risco', $DESC$So obedece a quem guarda algo, e pesa morta na mao do egoista.$DESC$),
jsonb_build_object('material', $DESC$O toque que refaz o que se quebra$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Eco do Clarao / refazer, restaurar o protegido)$DESC$, 'risco', $DESC$So cura o que esta sob tutela de quem o usa.$DESC$),
jsonb_build_object('material', $DESC$Lasca de cristal do marco guardado$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (foco de luz, ancora de guarda)$DESC$, 'risco', $DESC$Zumbe perto de ameaca.$DESC$),
jsonb_build_object('material', $DESC$Po claro do santuario$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (pigmento branco)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Tinir de luz aparada e o zunido do arco.$DESC$,
'cheiro', $DESC$Ar limpo e cristal quente.$DESC$,
'quer', $DESC$Guardar o marco que lhe coube e refazer o que se quebra do seu lado, sem ceder um passo.$DESC$,
'tipo_perigo', $DESC$Persistente$DESC$,
'falas_exemplo', jsonb_build_array($DESC$Voce nao esta sob minha guarda. Afaste-se do que esta.$DESC$, $DESC$Eu o curei. Isso nao faz de voce meu. Saia.$DESC$, $DESC$(registro: voz clara e fria, sem do, como quem cumpre um encargo e nao uma vontade)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Ameacam o marco ou o ser que ele guarda$DESC$, $DESC$Ficam entre ele e o que protege$DESC$, $DESC$Atacam quem esta sob a tutela dele$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Nao foge; cessa quando a ameaca ao marco se afasta$DESC$, $DESC$Para de ferir quem sai do alcance do protegido$DESC$, $DESC$Cede o posto so quando o encargo que o prende e desfeito$DESC$),
'descoberta_fazendo', $DESC$Parado entre um marco de cristal de Thornmarak e o mundo, aparando, curando o seu lado e ferindo de longe quem ameaca.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Saber o que ele guarda e nao ameacar o marco$DESC$, $DESC$Afastar-se do que ele protege para encerrar o confronto$DESC$, $DESC$Nao confundir a cura com bondade nem se por entre ele e o marco$DESC$, $DESC$Desfazer o encargo que o prende, em vez de troca-lo golpe$DESC$)
),
status_conversao='canonizada'
WHERE id=1870;

-- 512 Espia-Miúda | Engenho | lurker | Oculto | 0.5 Ameaça | Voranthar | MUDO
UPDATE ref_criaturas SET
nome=$DESC$Espia-Miúda$DESC$,
nome_ptbr=$DESC$Espia-Miúda$DESC$,
slug=$DESC$espia-miuda$DESC$,
origem=$DESC$Marginal$DESC$,
andar_primario=$DESC$Margem$DESC$,
pilar_associado=$DESC$Engenho$DESC$,
continente=ARRAY[$DESC$Voranthar$DESC$]::text[],
habitat=$DESC$Ruinas e fendas estreitas de Voranthar onde a Margem e fina, cantos altos e frestas.$DESC$,
comportamento=$DESC$Pequena e medrosa, flutua nos cantos altos, espia e imita vozes para atrair ou enganar, e ataca com raios miudos dos olhinhos de longe. Some ao primeiro perigo serio. Serve de olho a coisas maiores.$DESC$,
organizacao=$DESC$Sozinha, ou poucas a servico de algo maior.$DESC$,
perigo=$DESC$Ameaça$DESC$,
behavior_archetype=$DESC$lurker$DESC$,
morale_modifier=-1,
morale_immune=false,
epigrafe=$DESC$Ouvi minha mae me chamar de dentro da ruina. Minha mae morreu ha dez anos. Era a coisinha dos olhos.$DESC$,
descricao=$DESC$E um olho flutuante do tamanho de um punho, com olhinhos numa coroa de talos, que vive nos cantos altos das ruinas de Voranthar. Medrosa e curiosa, espia tudo e imita vozes e sons que ouviu, para atrair, enganar ou pregar sustos, e fere de longe com raios miudos. Sozinha, foge do primeiro perigo serio; perto de algo maior, e o olho e o espia dele. O veneno dela e a informacao e o engano, mais que o dano.$DESC$,
supersticao_popular=$DESC$Em Voranthar dizem que ha olhinhos voadores que imitam voz de gente morta nas ruinas, e que seguir a voz e cair em cilada. O conselho: nao seguir voz conhecida em ruina, e olhar para cima, nos cantos altos. Dizem que e inofensiva; e, sozinha, mas o que ela espia para nao e.$DESC$,
sinais_presenca=$DESC$Uma voz conhecida vinda de onde nao devia. Um olhinho que aparece e some num canto alto. Raios finos de luz que queimam de leve, sem fonte clara. Ecos de som repetidos fora de hora. A sensacao de estar sendo observado de cima.$DESC$,
fraqueza_conhecida=$DESC$O povo evita seguir voz e olha para cima. Acha a coisinha inofensiva, e ai cai no que ela arma.$DESC$,
fraqueza_real=$DESC$E fraca e medrosa: encurralada, foge ou cai facil. O perigo e o que ela informa a coisas maiores e o engano que arma com as vozes. Nao seguir a imitacao, fecha-la num canto e nao a deixar voltar para o dono cortam o mal. Sozinha, qualquer rede ou pancada a pega; o erro e tratar a isca como inofensiva e cair no que ela prepara.$DESC$,
descricao_sensorial=$DESC$O som e de vozes imitadas e ecos repetidos, e um zunir fino de raio. O cheiro e quase nenhum, um traco de mofo de fresta. Ao toque, e mole e leve, de bolha de olho. Aos olhos, e um olhinho numa coroa de talos espiando de um canto alto.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Informacao e descuido de quem entra na ruina$DESC$, $DESC$Pequenos bichos que ela morde$DESC$),
'predador', jsonb_build_array($DESC$Encurralada, foge ou cai facil; sozinha e fraca$DESC$),
'competidor', jsonb_build_array($DESC$Outros olhos e espias da Margem em Voranthar$DESC$, $DESC$Chão-Erguido$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presenca dela diz que ali ha olhos da Margem espiando, e talvez algo maior atras do que eles veem.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem nao segue voz conhecida em ruina e vigia os cantos altos$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$A coroa de olhinhos que lança raios$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Engenho / raios miudos, espiar de longe)$DESC$, 'risco', $DESC$Abre olhos que veem o que voce nao quer ver.$DESC$),
jsonb_build_object('material', $DESC$O orgao que imita voz e som$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Engenho / imitar vozes, enganar pelo ouvido)$DESC$, 'risco', $DESC$Repete vozes que voce preferia esquecer.$DESC$),
jsonb_build_object('material', $DESC$Talos e pele de olho$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (curiosidade, foco leve)$DESC$, 'risco', $DESC$Nenhum alem do desconforto.$DESC$),
jsonb_build_object('material', $DESC$Bolha ocular pequena$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (lente rude, isca)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Vozes imitadas e ecos repetidos, e um zunir fino de raio.$DESC$,
'cheiro', $DESC$Quase nenhum, um traco de mofo de fresta.$DESC$,
'quer', $DESC$Espiar tudo, enganar com vozes e servir de olho a algo maior, sem se arriscar.$DESC$,
'tipo_perigo', $DESC$Oculto$DESC$,
'falas_exemplo', 'null'::jsonb,
'gatilhos_agressao', jsonb_build_array($DESC$Alguem segue a voz imitada para perto dela$DESC$, $DESC$Encurralam-na num canto sem saida$DESC$, $DESC$Ameacam a coisa maior a quem ela serve de olho$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Foge ao primeiro perigo serio$DESC$, $DESC$Some na fresta alta quando quase pega$DESC$, $DESC$Larga a isca e corre para o dono quando descoberta$DESC$),
'descoberta_fazendo', $DESC$Flutuando num canto alto de uma ruina de Voranthar, espiando e imitando vozes para atrair ou enganar quem entra.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Nao seguir voz conhecida em ruina e vigiar os cantos altos$DESC$, $DESC$Fecha-la num canto e nao deixa-la voltar ao dono$DESC$, $DESC$Tratar a voz como isca e procurar o que ela serve$DESC$, $DESC$Capturar a miuda com rede, ja que sozinha e fraca$DESC$)
),
status_conversao='canonizada'
WHERE id=512;

-- ========================= GRUPO 7 =========================

-- 2304 Casco-Falso | Corpo | ambusher | Oculto | 5 Ameaça | Kethara | MUDO
UPDATE ref_criaturas SET
nome=$DESC$Casco-Falso$DESC$,
nome_ptbr=$DESC$Casco-Falso$DESC$,
slug=$DESC$casco-falso$DESC$,
origem=$DESC$Natural$DESC$,
andar_primario=$DESC$Superfície$DESC$,
pilar_associado=$DESC$Corpo$DESC$,
continente=ARRAY[$DESC$Kethara$DESC$]::text[],
habitat=$DESC$Dunas e pedregais de Kethara, leitos secos onde uma pedra a mais nao chama atencao.$DESC$,
comportamento=$DESC$Passa o dia fingindo pedra ou casco vazio, meio enterrado na areia quente, e so se move quando a presa chega ao alcance; abocanha de uma vez e se enterra de novo. Paciente, imovel, nao persegue.$DESC$,
organizacao=$DESC$Sozinho, um por trecho de descampado.$DESC$,
perigo=$DESC$Ameaça$DESC$,
behavior_archetype=$DESC$ambusher$DESC$,
morale_modifier=0,
morale_immune=false,
epigrafe=$DESC$Sentamos a sombra da unica pedra do descampado. A pedra abriu uma boca.$DESC$,
descricao=$DESC$E um bicho de carapaca que imita uma pedra grande ou um casco vazio, meio enterrado na areia quente de Kethara. Fica imovel o dia inteiro, sem cheiro e sem sombra que denuncie, e espera a presa procurar a sua sombra ou pisar perto. Ai abocanha de uma vez e se enterra de novo, como se nada tivesse acontecido. Nao persegue, nao corre; e so paciencia e uma boca que a areia esconde.$DESC$,
supersticao_popular=$DESC$Em Kethara dizem para desconfiar da unica pedra de um descampado, e para nao descansar a sombra de pedra que aparece onde nao havia. O conselho: cutucar de longe antes de encostar, olhar se a pedra tem juntas ou se respira, e nao dormir colado a ela. Dizem que pedra nao morde; essa morde.$DESC$,
sinais_presenca=$DESC$Uma pedra ou casco grande sozinho num descampado liso. Marcas de arrasto na areia em volta de uma pedra. A pedra esta morna do lado errado, sem bater sol. Ausencia de bicho pequeno perto dela. Uma juntura fina demais para ser racha de rocha.$DESC$,
fraqueza_conhecida=$DESC$O povo cutuca de longe e nao descansa na sombra dela. Acha que pedra nao morde, e essa morde.$DESC$,
fraqueza_real=$DESC$E emboscada pura: so vale enquanto passa por pedra e a presa chega perto. Descoberta, e lenta e nao persegue; afastar-se basta. Cutucar de longe revela a boca antes do bote; nao chegar ao alcance nega o ataque. O erro e confiar na pedra solitaria e descansar na sombra dela.$DESC$,
descricao_sensorial=$DESC$O som e quase nada, um raspar surdo de areia quando se move. O cheiro e nenhum, e o disfarce. Ao toque, e casca quente e aspera, com uma juntura escondida. Aos olhos, e uma pedra como tantas, ate a boca abrir no chao.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Bicho e gente que descansam ou pisam perto da pedra falsa$DESC$, $DESC$Quem procura a sombra dela no descampado$DESC$),
'predador', jsonb_build_array($DESC$Descoberto, e lento e facil de evitar; nao persegue$DESC$),
'competidor', jsonb_build_array($DESC$Outros emboscadores de Kethara que disputam o pouco que passa$DESC$, $DESC$Pata-Peçonha$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presenca dele diz que ali a unica sombra do descampado e isca, e que o chao tem dono.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem cutuca de longe e nao descansa colado a pedra solitaria$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$Carapaca que imita pedra$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Corpo / disfarce de pedra, casco duro)$DESC$, 'risco', $DESC$Pesa demais e ainda parece pedra na mochila.$DESC$),
jsonb_build_object('material', $DESC$Placa de mandibula$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (mordida de uma vez, foco de emboscada)$DESC$, 'risco', $DESC$Fecha sozinha no descuido.$DESC$),
jsonb_build_object('material', $DESC$Carne de casco$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (carne dura, sebo)$DESC$, 'risco', $DESC$Nenhum.$DESC$),
jsonb_build_object('material', $DESC$Areia compactada do covil$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (lastro, abrasivo)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Quase nada, um raspar surdo de areia quando se move.$DESC$,
'cheiro', $DESC$Nenhum, e o disfarce.$DESC$,
'quer', $DESC$Passar por pedra e abocanhar de uma vez o que chega ao alcance, sem perseguir.$DESC$,
'tipo_perigo', $DESC$Oculto$DESC$,
'falas_exemplo', 'null'::jsonb,
'gatilhos_agressao', jsonb_build_array($DESC$Uma presa chega ao alcance da boca enterrada$DESC$, $DESC$Alguem descansa ou dorme colado a pedra falsa$DESC$, $DESC$Procuram a sombra dela no descampado$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Se enterra de novo apos o bote, certo ou errado$DESC$, $DESC$Descoberto, fica imovel e deixa a presa se afastar$DESC$, $DESC$Nao persegue quem sai do alcance$DESC$),
'descoberta_fazendo', $DESC$Imovel num descampado de Kethara, passando por pedra ou casco vazio, a espera de que a presa chegue perto.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Desconfiar da unica pedra do descampado e cutuca-la de longe$DESC$, $DESC$Nao descansar nem dormir colado a ela$DESC$, $DESC$Afastar-se assim que a boca se revela, ja que nao persegue$DESC$, $DESC$Contornar o trecho e nao chegar ao alcance$DESC$)
),
status_conversao='canonizada'
WHERE id=2304;

-- 1160 Dedos-Soltos | Sombra | swarm | Persistente | 3 Ameaça | Voranthar | MUDO
UPDATE ref_criaturas SET
nome=$DESC$Dedos-Soltos$DESC$,
nome_ptbr=$DESC$Dedos-Soltos$DESC$,
slug=$DESC$dedos-soltos$DESC$,
origem=$DESC$Cicatricial$DESC$,
andar_primario=$DESC$Eco$DESC$,
pilar_associado=$DESC$Sombra$DESC$,
continente=ARRAY[$DESC$Voranthar$DESC$]::text[],
habitat=$DESC$Ruinas e criptas de Voranthar onde a Margem e fina, pisos e frestas por onde se arrasta.$DESC$,
comportamento=$DESC$Muitas maos soltas se arrastam pelo chao e parede em silencio, sobem pelo corpo e apertam; espalham-se, voltam, e nao param so porque algumas viram po. Agem em massa, sem dono a vista, ou as ordens de algo escondido.$DESC$,
organizacao=$DESC$Em bando grande, dezenas de uma vez.$DESC$,
perigo=$DESC$Ameaça$DESC$,
behavior_archetype=$DESC$swarm$DESC$,
morale_modifier=0,
morale_immune=true,
epigrafe=$DESC$Pisamos numa so. Depois eram dez no tornozelo, e mais subindo da fresta.$DESC$,
descricao=$DESC$Sao maos decepadas que se arrastam por conta propria pelo chao das ruinas de Voranthar, em silencio, muitas de uma vez. Sobem pela perna, agarram o pulso, tapam a boca, e o perigo nao e a forca de uma, e o numero e a teima: pisar em uma traz dez, e o bando nao recua so porque parte virou po. As vezes agem soltas; as vezes obedecem a algo escondido que as soltou. E um incomodo que nao acaba, ate achar de onde vem.$DESC$,
supersticao_popular=$DESC$Em Voranthar dizem que em certas ruinas o chao tem maos, e que matar umas nao resolve. O conselho: nao pisar descalço nem dormir no chao dessas criptas, vedar fresta, e procurar de onde elas saem em vez de esmagar uma a uma. Dizem que fogo limpa; espalha as que fogem.$DESC$,
sinais_presenca=$DESC$Arranhados finos no chao e na parede, em fila. Uma mao decepada que se mexe sozinha. Frestas com marca de dedo gasta nas bordas. Pertences pequenos sumindo de noite. Um peso subitamente subindo pela perna no escuro.$DESC$,
fraqueza_conhecida=$DESC$O povo nao pisa descalço e veda as frestas. Acha que fogo limpa, e ele so espalha as que fogem.$DESC$,
fraqueza_real=$DESC$Persistente pelo numero, nao pela forca: cada uma e fraca, o bando e teimoso. Esmagar uma a uma nao acaba; achar a fresta-ninho ou a coisa que as comanda corta o fornecimento. Luz forte e fogo nas frestas as espalham, mas e selar a origem que resolve. O erro e gastar a noite esmagando maos enquanto a fonte despeja mais.$DESC$,
descricao_sensorial=$DESC$O som e um sussurro de unha raspando pedra, muitos ao mesmo tempo. O cheiro e de carne seca e po de cripta. Ao toque, sao dedos frios fechando no tornozelo e no pulso. Aos olhos, e o chao se mexendo em pontos, maos subindo das frestas.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Gente e bicho que dormem ou pisam no chao das criptas$DESC$, $DESC$Dedos e descuido de quem nao veda a fresta$DESC$),
'predador', jsonb_build_array($DESC$Selada a origem, o bando seca; cada uma e fraca$DESC$),
'competidor', jsonb_build_array($DESC$Outros restos que se arrastam em Voranthar disputando as criptas$DESC$, $DESC$Hóspede-Pálido$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presenca delas diz que ali a Margem deixou maos soltas, e talvez algo que as comanda.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem nao dorme no chao e veda as frestas das criptas$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$O dedo-mestre que comanda o bando$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Sombra / mover muitos em massa, agir sem dono)$DESC$, 'risco', $DESC$Se mexe na bolsa e arrasta companhia atras.$DESC$),
jsonb_build_object('material', $DESC$Maos secas que ainda apertam$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Corpo / agarrar, prender)$DESC$, 'risco', $DESC$Fecham no escuro sobre quem dorme.$DESC$),
jsonb_build_object('material', $DESC$Aneis e bugigangas que elas juntaram$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (despojos, miudezas)$DESC$, 'risco', $DESC$Alguem vem procurar o que sumiu.$DESC$),
jsonb_build_object('material', $DESC$Po de cripta$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (po seco, enchimento)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Sussurro de unha raspando pedra, muitos ao mesmo tempo.$DESC$,
'cheiro', $DESC$Carne seca e po de cripta.$DESC$,
'quer', $DESC$Arrastar-se em massa, agarrar e prender, sem parar so porque parte virou po.$DESC$,
'tipo_perigo', $DESC$Persistente$DESC$,
'falas_exemplo', 'null'::jsonb,
'gatilhos_agressao', jsonb_build_array($DESC$Pisam ou dormem no chao das criptas deles$DESC$, $DESC$Mexem ou esmagam algumas das maos$DESC$, $DESC$Deixam fresta aberta perto de quem repousa$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$As que sobram recuam para a fresta quando a origem e selada$DESC$, $DESC$Param de subir onde ha luz forte e fogo na fresta$DESC$, $DESC$Largam o alvo que sobe alto, longe do chao$DESC$),
'descoberta_fazendo', $DESC$Arrastando-se aos montes pelo chao de uma cripta de Voranthar, subindo das frestas atras de quem repousa.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Nao dormir no chao nem pisar descalço nessas criptas$DESC$, $DESC$Vedar as frestas e subir para longe do piso$DESC$, $DESC$Achar e selar a fresta-ninho ou o que as comanda$DESC$, $DESC$Sair da cripta em vez de esmagar uma a uma$DESC$)
),
status_conversao='canonizada'
WHERE id=1160;

-- 2444 Capuz-Velado | Arcano | controller | Condicional | 21 Destruidor | Vyrkhor | fala
UPDATE ref_criaturas SET
nome=$DESC$Capuz-Velado$DESC$,
nome_ptbr=$DESC$Capuz-Velado$DESC$,
slug=$DESC$capuz-velado$DESC$,
origem=$DESC$Cicatricial$DESC$,
andar_primario=$DESC$Eco$DESC$,
pilar_associado=$DESC$Arcano$DESC$,
continente=ARRAY[$DESC$Vyrkhor$DESC$]::text[],
habitat=$DESC$Arquivos e criptas geladas sob os picos de Vyrkhor, salas onde um sabio se recusou a terminar.$DESC$,
comportamento=$DESC$Um velho encapuzado que trocou o fim por mais tempo de estudo; comanda o frio, os mortos e as defesas da sala a distancia, e raramente levanta a mao em pessoa. So se volta com furia contra quem mexe na obra dele ou acha a ancora escondida que o traz de volta.$DESC$,
organizacao=$DESC$Sozinho na cadeira, cercado dos servos que ergue.$DESC$,
perigo=$DESC$Destruidor$DESC$,
behavior_archetype=$DESC$controller$DESC$,
morale_modifier=1,
morale_immune=false,
epigrafe=$DESC$Nos o derrubamos. Tres dias depois estava de novo na cadeira, virando a pagina onde tinha parado.$DESC$,
descricao=$DESC$Foi um sabio que se recusou a morrer antes de terminar, e pagou o preco: ficou encapuzado, seco e frio, dono do tempo que roubou. Governa a sala gelada a distancia, movendo o frio, os servos sepultados e as defesas sem sair da cadeira, e trata intrusos como interrupcao, nao como ameaca. So mostra a furia inteira quando alguem mexe na obra de uma vida ou se aproxima da ancora escondida que o traz de volta. Derruba-lo nao basta: enquanto essa ancora existe, ele volta a cadeira e a pagina onde parou.$DESC$,
supersticao_popular=$DESC$Em Vyrkhor dizem que ha sabios velhos que nao morrem e voltam sempre para a mesma sala. O conselho: nao mexer nos livros e na obra deles, sair se o frio cresce, e lembrar que mata-los nao resolve, e preciso achar o que os traz de volta. Dizem que e so um velho; o velho ja enterrou quem o matou.$DESC$,
sinais_presenca=$DESC$Uma sala que o frio nao larga, mesmo longe do gelo de fora. Um velho encapuzado imovel sobre um trabalho que nunca termina. Servos que se erguem sem que ele se levante. Paginas que viram sozinhas no silencio. O mesmo morto voltando depois de derrubado.$DESC$,
fraqueza_conhecida=$DESC$O povo nao mexe na obra e sai do frio. Sabe que mata-lo nao resolve, mas raramente acha a ancora.$DESC$,
fraqueza_real=$DESC$E condicional a ancora escondida: enquanto ela existe, ele retorna, e enquanto ninguem mexe na obra dele, ele quase ignora a sala. Nao perturbar o trabalho mantem a paz fria; mas encerra-lo de vez exige achar e destruir a ancora que o traz de volta, e nao derrubar o corpo na cadeira. O erro e comemorar a queda dele e virar as costas para a sala.$DESC$,
descricao_sensorial=$DESC$O som e um virar de pagina e um estalo de gelo, sob um silencio que pesa. O cheiro e de pergaminho velho, gelo e poeira. Ao toque, e frio que entra pelo osso ao cruzar a soleira. Aos olhos, e um vulto encapuzado e seco, curvado sobre um trabalho, sem pressa nenhuma.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Nao caça; pune quem mexe na obra dele ou procura a ancora$DESC$, $DESC$Intrusos que insistem na sala depois do aviso frio$DESC$),
'predador', jsonb_build_array($DESC$Destruida a ancora escondida, ele acaba; antes disso, sempre volta$DESC$),
'competidor', jsonb_build_array($DESC$Outros sabios que nao morreram em Vyrkhor, ciumentos da obra$DESC$, $DESC$Arauto-Trêmulo$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presenca dele diz que ali um sabio trocou o fim por tempo, e a sala guarda o que ele nao quer perder.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem nao mexe na obra e nao volta a sala depois de o derrubar$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$A ancora escondida que o traz de volta$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Arcano / voltar do fim, prender-se ao tempo roubado)$DESC$, 'risco', $DESC$Quem a guarda e procurado por ele ate devolver ou destruir.$DESC$),
jsonb_build_object('material', $DESC$O foco gelado com que comanda a sala$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Arcano / mover o frio e os servos a distancia)$DESC$, 'risco', $DESC$Congela o que toca sem aviso.$DESC$),
jsonb_build_object('material', $DESC$Paginas da obra inacabada$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (saber raro, notas antigas)$DESC$, 'risco', $DESC$Atrai a furia de quem as escreveu.$DESC$),
jsonb_build_object('material', $DESC$Pergaminho e tinta velha$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (papel, tinta)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Virar de pagina e estalo de gelo, sob um silencio que pesa.$DESC$,
'cheiro', $DESC$Pergaminho velho, gelo e poeira.$DESC$,
'quer', $DESC$Terminar a obra que trocou pela morte, sem ser interrompido, e sempre voltar a ela.$DESC$,
'tipo_perigo', $DESC$Condicional$DESC$,
'falas_exemplo', jsonb_build_array($DESC$Voce interrompe. Saia, e talvez eu nem registre que esteve aqui.$DESC$, $DESC$Ja me mataram antes. Foi um adiamento, nada mais.$DESC$, $DESC$(registro: voz seca e paciente, no comum e em linguas que ninguem mais le, sem pressa de quem tem todo o tempo)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Mexem na obra de uma vida dele$DESC$, $DESC$Procuram ou ameacam a ancora escondida$DESC$, $DESC$Insistem na sala depois do aviso frio$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Nao foge; volta a obra quando o intruso recua e nada toca$DESC$, $DESC$Ignora quem so passa sem mexer no trabalho$DESC$, $DESC$So acaba quando a ancora que o traz de volta e destruida$DESC$),
'descoberta_fazendo', $DESC$Curvado sobre um trabalho inacabado numa sala gelada de Vyrkhor, comandando o frio e os servos sem levantar da cadeira.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Nao mexer na obra nem nos livros e sair do frio que cresce$DESC$, $DESC$Achar e destruir a ancora escondida, em vez de derrubar o corpo$DESC$, $DESC$Negociar passagem oferecendo nao tocar no trabalho dele$DESC$, $DESC$Recuar e nao voltar a sala depois de o derrubar$DESC$)
),
status_conversao='canonizada'
WHERE id=2444;

-- 1140 Auréola-Severa | Espírito | artillery | Ambiental | 21 Destruidor | Thornmarak | fala
UPDATE ref_criaturas SET
nome=$DESC$Auréola-Severa$DESC$,
nome_ptbr=$DESC$Auréola-Severa$DESC$,
slug=$DESC$aureola-severa$DESC$,
origem=$DESC$Cicatricial$DESC$,
andar_primario=$DESC$Clarão$DESC$,
pilar_associado=$DESC$Espírito$DESC$,
continente=ARRAY[$DESC$Thornmarak$DESC$]::text[],
habitat=$DESC$Cumes de cristal de Thornmarak banhados pelo Clarao, alturas de onde a luz julga sem do.$DESC$,
comportamento=$DESC$Julga a distancia: enche o campo de uma luz que cega e queima quem considera indigno, e fere de muito longe com dardos de fogo claro. Nao desce para o corpo a corpo; faz do espaco inteiro a sentenca. Nao odeia; aplica uma regra que nao e a sua.$DESC$,
organizacao=$DESC$Sozinha no alto, ou guiando servos menores de luz.$DESC$,
perigo=$DESC$Destruidor$DESC$,
behavior_archetype=$DESC$artillery$DESC$,
morale_modifier=0,
morale_immune=true,
epigrafe=$DESC$Rezamos pedindo que descesse. Ele desceu, olhou a aldeia toda e queimou metade, a que reprovou.$DESC$,
descricao=$DESC$E um alto do Clarao, de auréola e asas de luz, que o povo reza para que desca como salvador. Desce, e nao salva: olha o campo de cima, separa o que aprova do que reprova por uma regra fria, e queima de longe o que reprovou, enchendo o ar de uma luz que cega e fere quem fica do lado errado. Nao luta de perto; transforma o espaco inteiro em julgamento. O engano do povo e achar que luz que vem do alto vem por bem.$DESC$,
supersticao_popular=$DESC$Em Thornmarak ha quem reze para os altos de luz descerem e salvarem, e e ai que o povo erra: eles nao salvam, julgam, e queimam o reprovado. O conselho: nao chamar o que desce do Clarao, nao reunir multidao sob a luz que cresce, e sair do campo aberto quando o ar comeca a arder. Dizem que e bencao; a bencao tem lado de fora.$DESC$,
sinais_presenca=$DESC$Uma luz que cresce no alto sem ser o sol, e esquenta o campo todo. Sombras que encurtam onde nao deviam. Um vulto alado e radiante longe demais para o arco alcancar. Queimaduras em linha reta, do alto para baixo. Um calor de julgamento antes de qualquer golpe.$DESC$,
fraqueza_conhecida=$DESC$O povo nao chama o que desce e sai do campo aberto. Acha que e bencao, e ai se ajoelha no claro.$DESC$,
fraqueza_real=$DESC$E artilharia ambiental: domina o campo aberto de longe e de cima, e o perigo e a luz que enche o espaco. Cobertura, teto e parede cortam o alcance dele; o corpo a corpo, que ele evita, e onde perde. Nao se reunir sob a luz que cresce nem ficar em campo aberto salva. O erro e implorar que desca e se ajoelhar no claro a espera de bencao.$DESC$,
descricao_sensorial=$DESC$O som e um zunido agudo de luz e o estalo do ar quente. O cheiro e de ar queimado e cristal. Ao toque, e calor que arde na pele sem chama a vista. Aos olhos, e uma auréola distante e fria, e o campo todo clareando demais.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Nao caça; queima de longe o que sua regra reprova$DESC$, $DESC$Multidoes reunidas sob a luz no campo aberto$DESC$),
'predador', jsonb_build_array($DESC$Sob teto e no corpo a corpo perde o alcance; quem se cobre escapa$DESC$),
'competidor', jsonb_build_array($DESC$Outros altos de luz de Thornmarak que julgam os mesmos campos$DESC$, $DESC$Sentença-Velada$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presenca dele diz que ali a luz do alto julga, e estar no claro do lado errado e condenacao.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem nao chama o que desce e nao se reune no campo aberto sob a luz$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$O dardo de luz que fere de longe$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Eco do Clarao / ferir a distancia, julgar de cima)$DESC$, 'risco', $DESC$So acerta o que o portador, no fundo, ja condenou.$DESC$),
jsonb_build_object('material', $DESC$A auréola que enche o campo de luz$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Eco do Clarao / clarear e arder um espaco)$DESC$, 'risco', $DESC$Cega tambem quem a porta sem regra.$DESC$),
jsonb_build_object('material', $DESC$Pena de luz das asas$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (foco claro, talisma)$DESC$, 'risco', $DESC$Esquenta quando ha mentira por perto.$DESC$),
jsonb_build_object('material', $DESC$Cinza clara do campo queimado$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (pigmento, cal)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Zunido agudo de luz e o estalo do ar quente.$DESC$,
'cheiro', $DESC$Ar queimado e cristal.$DESC$,
'quer', $DESC$Separar o aprovado do reprovado e queimar de longe o que sua regra condena.$DESC$,
'tipo_perigo', $DESC$Ambiental$DESC$,
'falas_exemplo', jsonb_build_array($DESC$Eu vim. Nao para salvar. Para separar.$DESC$, $DESC$Afaste-se do claro se nao quer ser pesado.$DESC$, $DESC$(registro: voz alta e clara, sem calor humano, no comum e numa lingua de luz, como quem le uma sentenca)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Reunem multidao sob a luz que cresce no campo aberto$DESC$, $DESC$Chamam ou imploram que desca e o atraem$DESC$, $DESC$Ficam no claro do lado que a regra dele reprova$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Nao foge; cessa o fogo de quem se cobre sob teto ou parede$DESC$, $DESC$Poupa quem sai do campo aberto e do claro$DESC$, $DESC$Encerra quando nao ha mais reprovado a vista no aberto$DESC$),
'descoberta_fazendo', $DESC$Pairando alto sobre um campo aberto de Thornmarak, banhando o chao de luz e queimando de longe o que sua regra reprova.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Nao chamar o que desce do Clarao nem implorar bencao$DESC$, $DESC$Sair do campo aberto e buscar teto, parede ou caverna$DESC$, $DESC$Nao reunir multidao sob a luz que cresce$DESC$, $DESC$Force-lo ao corpo a corpo sob cobertura, onde perde o alcance$DESC$)
),
status_conversao='canonizada'
WHERE id=1140;

-- 2086 Converso-Torto | Engenho | striker | Direto | 8 Letal | Voranthar | fala
UPDATE ref_criaturas SET
nome=$DESC$Converso-Torto$DESC$,
nome_ptbr=$DESC$Converso-Torto$DESC$,
slug=$DESC$converso-torto$DESC$,
origem=$DESC$Marginal$DESC$,
andar_primario=$DESC$Margem$DESC$,
pilar_associado=$DESC$Engenho$DESC$,
continente=ARRAY[$DESC$Voranthar$DESC$]::text[],
habitat=$DESC$Vielas e ruinas de Voranthar onde a Margem e fina, becos e passagens estreitas.$DESC$,
comportamento=$DESC$Vem reto e rapido, sem rodeio, e acaba a briga em poucos golpes; usa truques e ferro escondido para abrir a guarda e entao crava fundo. Foi gente, virou outra coisa na Margem, e luta como quem nao tem mais o que perder. Nao recua de um contra um.$DESC$,
organizacao=$DESC$Sozinho, ou poucos rondando as mesmas vielas.$DESC$,
perigo=$DESC$Letal$DESC$,
behavior_archetype=$DESC$striker$DESC$,
morale_modifier=1,
morale_immune=false,
epigrafe=$DESC$Ele estendeu a mao como quem se rende. A mao tinha uma lamina, e ja estava no meu flanco.$DESC$,
descricao=$DESC$Foi gente que a Margem torceu e refez, e o que sobrou e um lutador que vem reto e nao adia: abre a guarda com um truque ou um ferro escondido e crava fundo em poucos golpes. E habil e frio, mas nao se esconde para matar; encara, finge render-se ou pedir tregua, e ataca de frente no instante seguinte. Luta como quem ja perdeu tudo o que prendia a mao, e por isso nao hesita nem foge de um duelo.$DESC$,
supersticao_popular=$DESC$Em Voranthar dizem que a Margem torce gente e devolve assassinos que parecem aliados. O conselho: nao baixar a guarda para quem se rende ou pede tregua nesses becos, e desconfiar do que estende a mao. Dizem que e so um bandido; bandido hesita, esse nao.$DESC$,
sinais_presenca=$DESC$Alguem que se rende rapido demais num beco estreito. Uma mao sempre meio escondida na capa. Cortes precisos, fundos e em poucos lugares. Pegada de quem anda reto, sem rodear. Um pedido de tregua dito sem medo nenhum.$DESC$,
fraqueza_conhecida=$DESC$O povo nao baixa a guarda para quem se rende e desconfia da mao estendida nos becos.$DESC$,
fraqueza_real=$DESC$E golpe direto de curta distancia: brilha no um contra um e no aperto do beco, e cai quando o tiram da medida e o cercam. Nao deixar abrir a guarda, manter distancia e enfrenta-lo em numero negam o estilo dele. Ele conta com o duelo de frente; recusar o duelo e abrir espaco o desarmam. O erro e aceitar a tregua e o um contra um que ele oferece.$DESC$,
descricao_sensorial=$DESC$O som e de passos firmes e o tinir de ferro saindo da capa. O cheiro e de couro, oleo de lamina e rua. Ao toque, e corte limpo e fundo, sem aviso. Aos olhos, e alguem de mao estendida que num pisco vira lamina no flanco.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Quem aceita o duelo e a tregua dele nos becos$DESC$, $DESC$Viajantes que baixam a guarda para um pedido de paz$DESC$),
'predador', jsonb_build_array($DESC$Tirado da medida e cercado, cai; so e perigoso no aperto$DESC$),
'competidor', jsonb_build_array($DESC$Outros refeitos da Margem em Voranthar que disputam as mesmas vielas$DESC$, $DESC$Grilhão-Frio$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presenca dele diz que ali a Margem devolveu um assassino de cara limpa, e que tregua e isca.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem nao baixa a guarda para rendicao e nao aceita duelo no beco$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$O ferro escondido que abre a guarda$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Engenho / golpe de surpresa de perto, abrir defesa)$DESC$, 'risco', $DESC$Corta a propria mao de quem o saca sem jeito.$DESC$),
jsonb_build_object('material', $DESC$A capa de muitos bolsos e laminas$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Engenho / esconder arma, fingir desarme)$DESC$, 'risco', $DESC$Da a quem veste o habito de confiar demais no truque.$DESC$),
jsonb_build_object('material', $DESC$Lamina fina de duelo$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (arma leve, estilete)$DESC$, 'risco', $DESC$Quebra a ponta no osso.$DESC$),
jsonb_build_object('material', $DESC$Oleo de lamina$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (lubrificante, conserva ferro)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Passos firmes e o tinir de ferro saindo da capa.$DESC$,
'cheiro', $DESC$Couro, oleo de lamina e rua.$DESC$,
'quer', $DESC$Abrir a guarda com um falso gesto de paz e cravar fundo em poucos golpes, de frente.$DESC$,
'tipo_perigo', $DESC$Direto$DESC$,
'falas_exemplo', jsonb_build_array($DESC$Calma. Eu me rendo. Veja, baixei a mao.$DESC$, $DESC$Nada pessoal. Voce so estava no caminho reto.$DESC$, $DESC$(registro: voz mansa e curta, no comum, do tom de quem ja decidiu o golpe antes de falar)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Alguem baixa a guarda diante da rendicao ou tregua dele$DESC$, $DESC$Um contra um no aperto de um beco estreito$DESC$, $DESC$Chegam ao alcance curto onde ele crava fundo$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Recua quando o tiram da medida e o cercam em numero$DESC$, $DESC$Perde o jeito quando negam o duelo e abrem espaco$DESC$, $DESC$Desiste do alvo que nao baixa a guarda nem aceita a tregua$DESC$),
'descoberta_fazendo', $DESC$Num beco estreito de Voranthar, de mao estendida em falso pedido de paz, a um pisco de cravar o ferro escondido.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Nao baixar a guarda para quem se rende nem aceitar tregua no beco$DESC$, $DESC$Manter distancia e tira-lo do aperto onde ele brilha$DESC$, $DESC$Enfrenta-lo em numero e em espaco aberto, recusando o duelo$DESC$, $DESC$Desconfiar da mao estendida e nao chegar ao alcance curto$DESC$)
),
status_conversao='canonizada'
WHERE id=2086;

-- ========================= GRUPO 8 =========================

-- 629 Tronco-Sarnento | Corpo | brute | Persistente | 13 Letal | Thornmarak | fala
UPDATE ref_criaturas SET
nome=$DESC$Tronco-Sarnento$DESC$,
nome_ptbr=$DESC$Tronco-Sarnento$DESC$,
slug=$DESC$tronco-sarnento$DESC$,
origem=$DESC$Natural$DESC$,
andar_primario=$DESC$Superfície$DESC$,
pilar_associado=$DESC$Corpo$DESC$,
continente=ARRAY[$DESC$Thornmarak$DESC$]::text[],
habitat=$DESC$Brejos e matas baixas de Thornmarak, lamacais onde a carne podre nao falta.$DESC$,
comportamento=$DESC$Avanca reto, esmaga e morde com fome bruta, e o que voce corta volta a crescer; nao recua, nao teme, e so para de verdade quando o fogo ou o acido fecham a conta. Teimoso como ferida que nao cura.$DESC$,
organizacao=$DESC$Sozinho, ou poucos disputando o mesmo lamacal.$DESC$,
perigo=$DESC$Letal$DESC$,
behavior_archetype=$DESC$brute$DESC$,
morale_modifier=2,
morale_immune=false,
epigrafe=$DESC$Cortamos o braço fora. Ficamos olhando ele crescer de novo enquanto o resto avancava.$DESC$,
descricao=$DESC$E um brutamontes coberto de casca sarnenta e cheio de fome, que vive nos brejos de Thornmarak. Avanca reto, esmaga com os bracos e morde, e o pior nao e a forca, e a teima: o que voce corta dele torna a crescer, e ele nao sente o golpe que num bicho normal seria o fim. So o fogo e o acido fecham a ferida de vez. Burro, faminto e quase impossivel de demover, ele cansa o inimigo antes de cair.$DESC$,
supersticao_popular=$DESC$Em Thornmarak dizem que ha brutos de brejo que crescem de volta o que se corta, e que so o fogo os mata. O conselho: nao trocar golpe de aco com eles, levar tocha e oleo, e queimar o que cair para nao se reerguer. Dizem que sao burros; sao, e isso nao ajuda quem so tem espada.$DESC$,
sinais_presenca=$DESC$Arvores novas quebradas em linha reta na mata baixa. Carcaças meio comidas e largadas no lamacal. Um fedor de carne podre e mofo forte. Pegadas fundas e largas que o brejo nao apaga. Pedaços de carne escura que ainda se mexem no chao.$DESC$,
fraqueza_conhecida=$DESC$O povo nao troca aco e anda com tocha e oleo. Sabe que so o fogo o resolve de vez.$DESC$,
fraqueza_real=$DESC$Persistente pela cura, nao pela esperteza: corta-lo so o irrita, porque cresce de volta; fogo e acido impedem a regeneracao e fecham a conta. E burro e reto, facil de enganar e atrair para armadilha, fosso ou fogo. Cansa-lo de aco e o erro; queima-lo, ou faze-lo cair em algo que o prenda e queime, e o caminho.$DESC$,
descricao_sensorial=$DESC$O som e um ronco grave e o estalo de madeira quebrando. O cheiro e de carne podre e mofo de brejo. Ao toque, e casca grossa e sarnenta, quente de febre. Aos olhos, e um brutamontes alto e curvado, com feridas que se fecham sozinhas.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Bicho grande e gente que cruzam o brejo dele$DESC$, $DESC$Carniça e carne podre que junta no lamacal$DESC$),
'predador', jsonb_build_array($DESC$Fogo e acido o matam de vez; de aco, so cresce de volta$DESC$),
'competidor', jsonb_build_array($DESC$Outros brutos de brejo de Thornmarak que disputam carniça$DESC$, $DESC$Talha-Pedra$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presenca dele diz que ali um bruto de brejo reina, e o que se corta dele volta a crescer.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem nao troca aco com ele e anda com tocha e oleo$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$A carne que torna a crescer$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Corpo / regenerar, fechar ferida)$DESC$, 'risco', $DESC$Continua se mexendo e apodrecendo na bolsa.$DESC$),
jsonb_build_object('material', $DESC$Casca sarnenta e grossa$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Corpo / aguentar golpe, resistir)$DESC$, 'risco', $DESC$Coça e infecta arranhao.$DESC$),
jsonb_build_object('material', $DESC$Presas e garras$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (ferramenta de corte, gancho)$DESC$, 'risco', $DESC$Fede e atrai mosca.$DESC$),
jsonb_build_object('material', $DESC$Sebo de brejo$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (graxa, combustivel)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Ronco grave e o estalo de madeira quebrando.$DESC$,
'cheiro', $DESC$Carne podre e mofo de brejo.$DESC$,
'quer', $DESC$Comer e esmagar o que cruza o brejo, sem recuar, crescendo de volta o que perde.$DESC$,
'tipo_perigo', $DESC$Persistente$DESC$,
'falas_exemplo', jsonb_build_array($DESC$Corta. Cresce. Corta de novo. Eu canso depois de voce.$DESC$, $DESC$Fome. Voce e carne. Para de mexer.$DESC$, $DESC$(registro: voz grave e arrastada, no idioma gigante e um comum quebrado, frases curtas de quem nao pensa muito)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Cruzam o brejo dele ou chegam ao alcance do braço$DESC$, $DESC$Cheiram a carne ou sangue que ele quer comer$DESC$, $DESC$Ferem-no de aco, o que so o enfurece$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Recua so do fogo e do acido, que ele teme de verdade$DESC$, $DESC$Larga a presa que se atira em chama ou agua funda$DESC$, $DESC$Hesita diante de tocha acesa balançada na cara$DESC$),
'descoberta_fazendo', $DESC$Vagando um brejo de Thornmarak atras de carne, esmagando o que cruza e curando sozinho o que leva.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Nao trocar golpe de aco e andar com tocha e oleo$DESC$, $DESC$Atrai-lo para fosso, armadilha ou fogo que o prenda e queime$DESC$, $DESC$Queimar o que cair dele para nao se reerguer$DESC$, $DESC$Dar-lhe carniça longe da trilha para desviar a fome$DESC$)
),
status_conversao='canonizada'
WHERE id=629;

-- 1920 Capa-Vasta | Sombra | controller | Ambiental | 17 Destruidor | Voranthar | fala
UPDATE ref_criaturas SET
nome=$DESC$Capa-Vasta$DESC$,
nome_ptbr=$DESC$Capa-Vasta$DESC$,
slug=$DESC$capa-vasta$DESC$,
origem=$DESC$Marginal$DESC$,
andar_primario=$DESC$Margem$DESC$,
pilar_associado=$DESC$Sombra$DESC$,
continente=ARRAY[$DESC$Voranthar$DESC$]::text[],
habitat=$DESC$Saloes soterrados e poços de Voranthar onde a Margem e fina, lugares que a luz abandonou.$DESC$,
comportamento=$DESC$Estende-se como um manto vasto de escuro vivo sobre um salao inteiro, apaga a luz, abafa o som e tira o rumo de quem entra; nao golpeia de perto, governa o espaco e deixa o escuro fazer o servico. Fala baixo de todo lado.$DESC$,
organizacao=$DESC$Uma so, vasta, cobrindo o salao inteiro.$DESC$,
perigo=$DESC$Destruidor$DESC$,
behavior_archetype=$DESC$controller$DESC$,
morale_modifier=0,
morale_immune=true,
epigrafe=$DESC$A tocha apagou sozinha. Depois a saida sumiu, e a voz vinha de todo lado e de lugar nenhum.$DESC$,
descricao=$DESC$E uma vastidao de escuro vivo que veio da Margem e se estende sobre um salao como um manto sem fim. Nao tem corpo para golpear; engole a luz, abafa a voz, embaralha o rumo e faz o proprio lugar virar a arma, enquanto sussurra de todo lado para separar e perder quem entrou. Quem fica perde a saida, a tocha e os companheiros de vista, e o escuro aperta sozinho. Nao e do alem; e a Margem derramada num lugar que a luz largou.$DESC$,
supersticao_popular=$DESC$Em Voranthar dizem que ha saloes onde o escuro e vivo e engole a luz, e que entrar com uma tocha so e morrer no escuro. O conselho: nao entrar sem muitas luzes e sem corda que ligue um ao outro, marcar a saida, e nao seguir voz no escuro. Dizem que reza espanta; luz espanta, reza nao.$DESC$,
sinais_presenca=$DESC$Tochas e lampiões que apagam ao cruzar a soleira. Um escuro que a luz nao fura como devia. Vozes baixas vindas de todo lado no breu. O som dos proprios passos sumindo. A saida que estava ali e nao esta mais.$DESC$,
fraqueza_conhecida=$DESC$O povo entra com muitas luzes e corda e marca a saida. Acha que reza espanta, e so a luz espanta.$DESC$,
fraqueza_real=$DESC$Controlador do espaco escuro: manda enquanto o lugar esta no breu, e nao tem corpo que se enfrente. Muita luz junta, fogo forte e nao se separar quebram o dominio dele; achar e abrir uma fonte de luz no salao o encolhe. Nao seguir a voz e ficar ligado por corda nega o engano. O erro e entrar com uma luz so e se espalhar no escuro.$DESC$,
descricao_sensorial=$DESC$O som e de sussurros de todo lado e o silencio que come o resto. O cheiro e de ar parado, frio e sem cheiro. Ao toque, e frio que adensa o ar como pano molhado. Aos olhos, e escuro que a luz nao vence, e formas que se movem so na borda do olho.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Quem entra no salao escuro dele com pouca luz$DESC$, $DESC$Gente que se separa e segue voz no breu$DESC$),
'predador', jsonb_build_array($DESC$Muita luz e fogo o encolhem; sem escuro, nao manda$DESC$),
'competidor', jsonb_build_array($DESC$Outros escuros e vazios da Margem em Voranthar$DESC$, $DESC$Vazio-Faminto$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presenca dela diz que ali a Margem cobriu um lugar de escuro vivo, e a luz nao basta.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem entra com muitas luzes, corda e nao segue voz no escuro$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$Um retalho do manto de escuro vivo$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Sombra / apagar luz, dominar um espaco no breu)$DESC$, 'risco', $DESC$Apaga a luz de quem o guarda e abafa a sua voz.$DESC$),
jsonb_build_object('material', $DESC$O fio de voz que sussurra de todo lado$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Sombra / falar de toda parte, separar e perder)$DESC$, 'risco', $DESC$Repete sussurros que confundem o portador a noite.$DESC$),
jsonb_build_object('material', $DESC$Cristal apagado do salao$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (foco escuro, lastro)$DESC$, 'risco', $DESC$Engole um pouco da luz por perto.$DESC$),
jsonb_build_object('material', $DESC$Po frio do breu$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (pigmento negro)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Sussurros de todo lado e o silencio que come o resto.$DESC$,
'cheiro', $DESC$Ar parado, frio e sem cheiro.$DESC$,
'quer', $DESC$Cobrir um lugar de escuro, apagar a luz e perder quem entra, sem precisar de corpo.$DESC$,
'tipo_perigo', $DESC$Ambiental$DESC$,
'falas_exemplo', jsonb_build_array($DESC$Fique. A saida nao tem pressa, e voce ja a perdeu.$DESC$, $DESC$Apague a luz. E mais facil sem ela. Para mim.$DESC$, $DESC$(registro: muitos sussurros baixos ao mesmo tempo, de todo lado e de lugar nenhum, no comum e numa lingua que arranha o ouvido)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Entram no salao escuro dele com pouca luz$DESC$, $DESC$Espalham-se e perdem o contato no breu$DESC$, $DESC$Trazem luz forte que ameaca o dominio dele$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Recua do fogo forte e de muita luz junta$DESC$, $DESC$Solta o grupo que se mantem ligado por corda e nao se perde$DESC$, $DESC$Encolhe quando uma fonte de luz e aberta no salao$DESC$),
'descoberta_fazendo', $DESC$Estendido como um manto de escuro vivo sobre um salao soterrado de Voranthar, apagando a luz e sussurrando para perder quem entra.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Entrar so com muitas luzes e corda que ligue um ao outro$DESC$, $DESC$Abrir ou acender uma fonte de luz forte no salao para encolhe-lo$DESC$, $DESC$Nao seguir a voz no escuro e nao se separar$DESC$, $DESC$Recuar pela saida marcada antes que o breu a engula$DESC$)
),
status_conversao='canonizada'
WHERE id=1920;

-- 1015 Grimório-Morto | Arcano | artillery | Direto | 21 Destruidor | Vyrkhor | fala
UPDATE ref_criaturas SET
nome=$DESC$Grimório-Morto$DESC$,
nome_ptbr=$DESC$Grimório-Morto$DESC$,
slug=$DESC$grimorio-morto$DESC$,
origem=$DESC$Cicatricial$DESC$,
andar_primario=$DESC$Eco$DESC$,
pilar_associado=$DESC$Arcano$DESC$,
continente=ARRAY[$DESC$Vyrkhor$DESC$]::text[],
habitat=$DESC$Torres e criptas geladas de Vyrkhor, gabinetes onde um mago trocou a morte por poder.$DESC$,
comportamento=$DESC$Ataca de longe e de frente, despejando golpes de forca e frio sem parar para conversar; e seco, frio e maquinal, e nao morre de vez enquanto o jarro onde guarda o resto que o prende a vida estiver inteiro. Queima quem chega, refaz-se se cai.$DESC$,
organizacao=$DESC$Sozinho na torre, cercado das defesas que ergue.$DESC$,
perigo=$DESC$Destruidor$DESC$,
behavior_archetype=$DESC$artillery$DESC$,
morale_modifier=1,
morale_immune=false,
epigrafe=$DESC$Derrubamos o mago. Ele riu da propria queda e voltou inteiro na lua seguinte, porque o jarro continuava la.$DESC$,
descricao=$DESC$Foi um mago que trocou a morte por poder e ficou seco, frio e oco, com olhos de brasa fria. Luta de longe e de frente, despejando golpes de forca e gelo num castigo continuo, sem astucia e sem do, como uma maquina que nao cansa. Derruba-lo nao basta: enquanto o jarro escondido onde ele guarda o resto que o prende a vida estiver inteiro, ele se refaz e volta. O caminho nao e o corpo na torre; e o jarro.$DESC$,
supersticao_popular=$DESC$Em Vyrkhor dizem que ha magos que trocaram a morte por poder e nao ficam mortos, e que voltam sempre. O conselho: nao enfrenta-lo de longe no campo dele, achar o jarro escondido onde ele guarda o que o prende a vida, e quebra-lo antes de tudo. Dizem que aco o mata; aco so o adia.$DESC$,
sinais_presenca=$DESC$Uma torre ou cripta de frio antinatural sob os picos. Golpes de luz fria e forca vindos de longe, sem fonte de chama. Um mago seco de olhos de brasa que nao se cansa nem recua. O mesmo morto voltando inteiro depois de derrubado. Um jarro ou objeto guardado com cuidado estranho, longe do corpo.$DESC$,
fraqueza_conhecida=$DESC$O povo procura e quebra o jarro escondido. Sabe que aco so o adia, nao o encerra.$DESC$,
fraqueza_real=$DESC$E artilharia direta presa a um jarro: castiga de longe, mas no aperto do corpo a corpo, sob cobertura, perde o ritmo. E enquanto o jarro onde guarda o resto que o prende a vida estiver inteiro, derruba-lo e inutil, ele volta. Fechar a distancia e quebrar o jarro e o caminho; troca-lo tiro de longe no campo aberto e o erro que ele quer.$DESC$,
descricao_sensorial=$DESC$O som e um zunido seco de forca disparada e o estalo do gelo. O cheiro e de ar queimado, gelo e poeira de tumba. Ao toque, e frio que queima como brasa ao contrario. Aos olhos, e um mago seco de olhos de brasa fria, despejando luz de longe sem se mover.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Quem o enfrenta de longe no campo aberto dele$DESC$, $DESC$Intrusos na torre que nao acham o jarro$DESC$),
'predador', jsonb_build_array($DESC$Quebrado o jarro, ele acaba; no corpo a corpo e sob cobertura perde o ritmo$DESC$),
'competidor', jsonb_build_array($DESC$Outros magos que nao morreram em Vyrkhor, rivais de poder$DESC$, $DESC$Punho-de-Terra$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presenca dele diz que ali um mago trocou a morte por poder, e guarda longe o que o traz de volta.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem nao o enfrenta de longe e procura primeiro o jarro escondido$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$O jarro onde guarda o resto que o prende a vida$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Arcano / voltar do fim, prender-se a vida roubada)$DESC$, 'risco', $DESC$Quem o guarda inteiro mantem o dono vivo e e caçado por ele.$DESC$),
jsonb_build_object('material', $DESC$O foco com que despeja golpes de longe$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Arcano / ferir a distancia, golpe de forca e gelo)$DESC$, 'risco', $DESC$Descarrega sozinho e gela a mao no susto.$DESC$),
jsonb_build_object('material', $DESC$Grimorio seco de feiticos$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (saber proibido, notas de magia)$DESC$, 'risco', $DESC$As paginas mordem a curiosidade de quem le.$DESC$),
jsonb_build_object('material', $DESC$Po de tumba e tinta gelada$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (po seco, tinta)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Zunido seco de forca disparada e o estalo do gelo.$DESC$,
'cheiro', $DESC$Ar queimado, gelo e poeira de tumba.$DESC$,
'quer', $DESC$Castigar de longe quem entra no seu campo e sempre voltar, enquanto o jarro durar.$DESC$,
'tipo_perigo', $DESC$Direto$DESC$,
'falas_exemplo', jsonb_build_array($DESC$Voce veio morrer perto. Eu prefiro de longe, mas serve.$DESC$, $DESC$Quebre o que quiser do meu corpo. Eu volto. Sempre volto.$DESC$, $DESC$(registro: voz seca e metalica, no comum e em linguas de feitiço, sem calor, como quem recita)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Entram na torre ou cripta gelada dele$DESC$, $DESC$O enfrentam de longe no campo aberto, como ele quer$DESC$, $DESC$Procuram ou ameacam o jarro escondido$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Nao foge do campo dele; recua so quando fecham a distancia sob cobertura$DESC$, $DESC$Perde o ritmo quando o pressionam de perto$DESC$, $DESC$So acaba quando o jarro que o prende a vida e quebrado$DESC$),
'descoberta_fazendo', $DESC$Numa torre gelada de Vyrkhor, despejando golpes de forca e gelo de longe sobre quem ousa entrar, sem se mover do lugar.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Nao enfrenta-lo de longe no campo aberto dele$DESC$, $DESC$Fechar a distancia sob cobertura, onde ele perde o ritmo$DESC$, $DESC$Achar e quebrar o jarro escondido antes de tudo$DESC$, $DESC$Recuar da torre e nao trocar tiro de longe com ele$DESC$)
),
status_conversao='canonizada'
WHERE id=1015;

-- 1145 Enigma-Régio | Espírito | tactical | Condicional | 17 Destruidor | Thornmarak | fala
UPDATE ref_criaturas SET
nome=$DESC$Enigma-Régio$DESC$,
nome_ptbr=$DESC$Enigma-Régio$DESC$,
slug=$DESC$enigma-regio$DESC$,
origem=$DESC$Cicatricial$DESC$,
andar_primario=$DESC$Clarão$DESC$,
pilar_associado=$DESC$Espírito$DESC$,
continente=ARRAY[$DESC$Thornmarak$DESC$]::text[],
habitat=$DESC$Portais e marcos de cristal de Thornmarak tocados pelo Clarao, limiares postos sob guarda com enigma.$DESC$,
comportamento=$DESC$Guarda uma passagem ou um saber por meio de provacao: poe um enigma, uma regra, um preco, e deixa passar quem honra o teste. So vira inimigo quando trapaceiam, forcam a passagem ou quebram a palavra dada; ai luta com calculo frio, mudando de posicao e usando as proprias regras.$DESC$,
organizacao=$DESC$Sozinho, guardiao de um unico limiar.$DESC$,
perigo=$DESC$Destruidor$DESC$,
behavior_archetype=$DESC$tactical$DESC$,
morale_modifier=0,
morale_immune=true,
epigrafe=$DESC$Respondemos certo e passamos. O tolo atras de nos tentou empurrar sem responder. Nao sobrou tolo.$DESC$,
descricao=$DESC$E um guardiao de limiar do Clarao, severo e antigo, que protege uma passagem ou um saber com provacao, nao com violencia. Poe um enigma, uma regra ou um preco e observa: quem honra o teste, passa; quem trapaceia, forca ou mente, encontra um inimigo frio e calculista que usa o proprio limiar como tabuleiro. Nao tem raiva, tem regra; e a regra so vira morte quando voce a quebra primeiro.$DESC$,
supersticao_popular=$DESC$Em Thornmarak dizem que ha guardioes de limiar que cobram enigma e deixam passar quem responde, mas matam quem trapaceia. O conselho: nao tentar passar a forca nem mentir para um deles, ouvir a regra e honra-la, e admitir quando nao sabe a resposta. Dizem que sao monstros; sao juizes, e o monstro e quem trapaceia.$DESC$,
sinais_presenca=$DESC$Um limiar de cristal guardado por uma figura antiga que faz perguntas. Uma regra ou enigma dito em voz calma a quem se aproxima. Corpos de quem tentou forcar a passagem, intactos de medo. Uma passagem aberta que ninguem ousa cruzar sem responder. Um silencio de prova antes de qualquer ameaca.$DESC$,
fraqueza_conhecida=$DESC$O povo ouve a regra e a honra, nao trapaceia nem forca. Sabe admitir quando nao sabe a resposta.$DESC$,
fraqueza_real=$DESC$E condicional ao teste: so ataca quem trapaceia, forca ou mente, e poupa quem honra a provacao. Responder com verdade, aceitar o preco ou admitir derrota encerra o confronto sem golpe. Em luta, e tatico e frio, usa o limiar a favor; mas a saida nao e venta-lo, e passar pela regra dele. O erro e tentar engana-lo ou empurrar a passagem.$DESC$,
descricao_sensorial=$DESC$O som e de uma voz calma e pausada e o tinir de cristal. O cheiro e de ar limpo de altura e pedra fria. Ao toque, e cristal liso e antigo, frio como pergunta. Aos olhos, e uma figura antiga e severa diante de um limiar de luz, esperando resposta.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Nao caça; pune quem trapaceia, mente ou forca o limiar$DESC$, $DESC$Tolos que empurram a passagem sem responder$DESC$),
'predador', jsonb_build_array($DESC$Honrado o teste, ele poupa; so a quebra da regra o torna inimigo$DESC$),
'competidor', jsonb_build_array($DESC$Outros guardioes de limiar do Clarao em Thornmarak$DESC$, $DESC$Bênção-Vazia$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presenca dele diz que ali um limiar e guardado por prova, e a passagem se paga com verdade, nao com forca.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem ouve a regra, honra o teste e nao tenta enganar$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$A regra que pesa a verdade de quem responde$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Eco do Clarao / provar, julgar resposta)$DESC$, 'risco', $DESC$Vira-se contra o portador que mente para si mesmo.$DESC$),
jsonb_build_object('material', $DESC$O enigma que tranca a passagem$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Eco do Clarao / selar um limiar com prova)$DESC$, 'risco', $DESC$Fecha caminhos a quem nao sabe responder.$DESC$),
jsonb_build_object('material', $DESC$Lasca de cristal do limiar$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (foco de luz, marco)$DESC$, 'risco', $DESC$Zumbe diante de mentira.$DESC$),
jsonb_build_object('material', $DESC$Po claro de pedra antiga$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (pigmento, cal)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Voz calma e pausada e o tinir de cristal.$DESC$,
'cheiro', $DESC$Ar limpo de altura e pedra fria.$DESC$,
'quer', $DESC$Guardar a passagem por prova e deixar passar so quem honra o teste.$DESC$,
'tipo_perigo', $DESC$Condicional$DESC$,
'falas_exemplo', jsonb_build_array($DESC$Responda, e a passagem e sua. Minta, e ela e sua tumba.$DESC$, $DESC$Nao sei nao e vergonha. Trapacear, sim, e a ultima que voce comete.$DESC$, $DESC$(registro: voz calma, antiga e pausada, no comum e numa lingua de luz, do tom de quem ja ouviu todas as respostas)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Tentam forcar a passagem sem responder a prova$DESC$, $DESC$Mentem ou trapaceiam na resposta ao enigma$DESC$, $DESC$Quebram a palavra ou o preco aceito no teste$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Nao foge; cessa quando honram o teste e respondem com verdade$DESC$, $DESC$Poupa quem admite que nao sabe e recua sem forcar$DESC$, $DESC$Encerra quando o preco da provacao e pago$DESC$),
'descoberta_fazendo', $DESC$Diante de um limiar de cristal de Thornmarak, propondo enigma e regra a quem se aproxima, e observando se honram a prova.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Ouvir a regra e honrar o teste, respondendo com verdade$DESC$, $DESC$Admitir que nao sabe e recuar sem forcar a passagem$DESC$, $DESC$Aceitar e pagar o preco da provacao em vez de trapacear$DESC$, $DESC$Nao tentar engana-lo nem empurrar a passagem a forca$DESC$)
),
status_conversao='canonizada'
WHERE id=1145;

-- 2034 Disfarce-Manso | Engenho | lurker | Oculto | 5 Ameaça | Voranthar | fala
UPDATE ref_criaturas SET
nome=$DESC$Disfarce-Manso$DESC$,
nome_ptbr=$DESC$Disfarce-Manso$DESC$,
slug=$DESC$disfarce-manso$DESC$,
origem=$DESC$Marginal$DESC$,
andar_primario=$DESC$Margem$DESC$,
pilar_associado=$DESC$Engenho$DESC$,
continente=ARRAY[$DESC$Voranthar$DESC$]::text[],
habitat=$DESC$Vilarejos de beira e ruinas habitadas de Voranthar onde a Margem e fina, lugares de gente comum.$DESC$,
comportamento=$DESC$Veste a forma de um pequeno e manso ajudante, prestativo e inofensivo, e se infiltra; espia, ganha confiança e colhe o que quer da cabeça de quem confia, sem nunca brigar de frente. Exposta, foge; nao encara.$DESC$,
organizacao=$DESC$Sozinha, infiltrada entre gente comum.$DESC$,
perigo=$DESC$Ameaça$DESC$,
behavior_archetype=$DESC$lurker$DESC$,
morale_modifier=-1,
morale_immune=false,
epigrafe=$DESC$O ajudantezinho manso de sempre. So reparei nos olhos quando ja era tarde, e ele ja sabia o que eu nao tinha contado.$DESC$,
descricao=$DESC$Parece um pequeno ajudante manso e prestativo, do tipo que ninguem desconfia, mas e coisa que a Margem fez vestir essa forma emprestada. Infiltra-se entre gente comum, serve, escuta, ganha confiança, e colhe da cabeça de quem confia o que quer saber, sem jamais brigar de frente. O perigo dela e o disfarce e o que ela rouba do que voce pensa, nao a forca. Descoberta, ela nao luta; some, troca de cara e recomeça noutro lugar.$DESC$,
supersticao_popular=$DESC$Em Voranthar dizem que a Margem poe gente falsa entre a verdadeira, mansa e prestativa, para roubar segredo de dentro da cabeça. O conselho: desconfiar do ajudante novo bom demais, reparar nos olhos e no que ele sabe sem ter sido contado, e nao contar tudo a quem chegou de fora. Dizem que e historia de aldeia; ate o segredo vazar.$DESC$,
sinais_presenca=$DESC$Um ajudante novo, manso e prestativo demais, chegado de fora. Alguem que sabe o que voce nao contou a ninguem. Olhos que nao batem com o resto da cara em certa luz. Segredos da vila vazando sem fonte. Um mal-estar de cabeça perto dele, sem motivo.$DESC$,
fraqueza_conhecida=$DESC$O povo desconfia do prestativo bom demais e repara nos olhos. Nao conta tudo a quem chega de fora.$DESC$,
fraqueza_real=$DESC$E lurker fraco no corpo a corpo: o perigo e o disfarce e o que rouba da cabeça, nao a luta. Exposta, foge e nao encara. Desmascara-la em publico, nao a deixar a sos com quem guarda segredo e guardar o que importa longe dela cortam o mal. Forçar luta aberta a vence facil; o erro e confiar no manso e contar o que nao devia.$DESC$,
descricao_sensorial=$DESC$O som e de uma voz mansa e servil, sempre prestativa. O cheiro e comum demais, limpo, sem o cheiro de quem trabalha. Ao toque, e mao fria e macia que evita aperto firme. Aos olhos, e um pequeno ajudante de olhar errado, manso ate voce reparar.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Segredo e confiança de gente comum em Voranthar$DESC$, $DESC$O que as pessoas pensam e nao contam$DESC$),
'predador', jsonb_build_array($DESC$Exposta, foge; no corpo a corpo e fraca$DESC$),
'competidor', jsonb_build_array($DESC$Outros infiltrados e ladroes da Margem em Voranthar$DESC$, $DESC$Mão-Invisível$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presenca dela diz que ali a Margem pos gente falsa entre a de verdade, e o que voce pensa nao esta seguro.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem desconfia do prestativo de fora e guarda segredo longe dele$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$A face emprestada que engana todo mundo$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Engenho / disfarce, passar por inofensivo)$DESC$, 'risco', $DESC$Quem a veste comeca a esquecer a propria cara.$DESC$),
jsonb_build_object('material', $DESC$O orgao que colhe o que voce pensa$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Engenho / tirar segredo da cabeça, ler o nao dito)$DESC$, 'risco', $DESC$Enche o portador de pensamentos que nao sao dele.$DESC$),
jsonb_build_object('material', $DESC$Pertences mansos do disfarce$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (roupa comum, ferramenta de ajudante)$DESC$, 'risco', $DESC$Fazem quem veste parecer inofensivo demais para o proprio bem.$DESC$),
jsonb_build_object('material', $DESC$Bugigangas roubadas da vila$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (miudezas, lembrancas)$DESC$, 'risco', $DESC$Alguem reconhece o que sumiu.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Voz mansa e servil, sempre prestativa.$DESC$,
'cheiro', $DESC$Comum demais, limpo, sem o cheiro de quem trabalha.$DESC$,
'quer', $DESC$Passar por inofensivo, ganhar confiança e colher o que a gente pensa e nao conta.$DESC$,
'tipo_perigo', $DESC$Oculto$DESC$,
'falas_exemplo', jsonb_build_array($DESC$Deixa que eu carrego, senhor. Eu ajudo, eu nao incomodo.$DESC$, $DESC$O senhor pode confiar em mim. Me conte, eu guardo segredo.$DESC$, $DESC$(registro: voz mansa, baixa e servil, no comum perfeito demais, sempre se oferecendo para ajudar)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Ficam a sos com ela guardando um segredo que ela quer$DESC$, $DESC$Baixam a guarda e contam o que ela busca$DESC$, $DESC$A deixam servir perto do que ela quer colher$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Foge assim que e desmascarada em publico$DESC$, $DESC$Some e troca de cara quando alguem repara nos olhos$DESC$, $DESC$Larga o alvo que nao a deixa a sos nem confia segredo$DESC$),
'descoberta_fazendo', $DESC$Passando por um ajudante manso e prestativo num vilarejo de Voranthar, servindo e escutando para colher o que a gente pensa e nao conta.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Desconfiar do prestativo de fora bom demais e reparar nos olhos$DESC$, $DESC$Nao ficar a sos com ela nem lhe contar segredo$DESC$, $DESC$Desmascara-la em publico, onde ela foge em vez de lutar$DESC$, $DESC$Guardar o que importa longe dela e forçar a luz sobre o disfarce$DESC$)
),
status_conversao='canonizada'
WHERE id=2034;

-- ========================= POST-CHECK (antes do COMMIT) =========================
-- devem vir 40 linhas, todas status_conversao='canonizada'
SELECT id, nome, perigo, pilar_associado, status_conversao
FROM ref_criaturas
WHERE id IN (907,1109,783,1877,1833,915,1190,1106,2024,2135,851,1130,891,1932,501,698,717,1842,958,457,926,1189,810,2449,1958,928,1934,1049,1870,512,2304,1160,2444,1140,2086,629,1920,1015,1145,2034)
ORDER BY id;

COMMIT;

-- ========================= VERIFICACAO (sec. 7.5) — rodar APOS o COMMIT =========================

-- 7.5.a — contagem de status: esperado canonizada=148, classificada=351
SELECT status_conversao, COUNT(*) AS n
FROM ref_criaturas
GROUP BY status_conversao
ORDER BY status_conversao;

-- 7.5.b — trava de linguagem: esperado fichas_com_proibida=0
-- (palavra proibida na PROSA de ficcao; 'Espírito' como pilar e 'Eco' no loot sao legitimos e nao contam)
SELECT COUNT(*) AS fichas_com_proibida
FROM ref_criaturas
WHERE status_conversao='canonizada'
  AND (
       descricao            ~* '\m(almas?|fantasmas?|esp[íi]ritos?|dem[ôo]nios?|inferno)\M'
    OR descricao_sensorial   ~* '\m(almas?|fantasmas?|esp[íi]ritos?|dem[ôo]nios?|inferno)\M'
    OR supersticao_popular   ~* '\m(almas?|fantasmas?|esp[íi]ritos?|dem[ôo]nios?|inferno)\M'
    OR comportamento         ~* '\m(almas?|fantasmas?|esp[íi]ritos?|dem[ôo]nios?|inferno)\M'
    OR habitat               ~* '\m(almas?|fantasmas?|esp[íi]ritos?|dem[ôo]nios?|inferno)\M'
    OR sinais_presenca       ~* '\m(almas?|fantasmas?|esp[íi]ritos?|dem[ôo]nios?|inferno)\M'
    OR fraqueza_conhecida    ~* '\m(almas?|fantasmas?|esp[íi]ritos?|dem[ôo]nios?|inferno)\M'
    OR fraqueza_real         ~* '\m(almas?|fantasmas?|esp[íi]ritos?|dem[ôo]nios?|inferno)\M'
    OR epigrafe              ~* '\m(almas?|fantasmas?|esp[íi]ritos?|dem[ôo]nios?|inferno)\M'
    OR ecologia::text        ~* '\m(almas?|fantasmas?|esp[íi]ritos?|dem[ôo]nios?|inferno)\M'
    OR camada_narrativa::text ~* '\m(almas?|fantasmas?|esp[íi]ritos?|dem[ôo]nios?|inferno)\M'
  );

-- 7.5.c — os 3 eixos distintos por grupo (conferencia visual dos 40 recem-canonizados)
SELECT id, nome, pilar_associado, behavior_archetype, (camada_narrativa->>'tipo_perigo') AS tipo_perigo, perigo
FROM ref_criaturas
WHERE id IN (907,1109,783,1877,1833,915,1190,1106,2024,2135,851,1130,891,1932,501,698,717,1842,958,457,926,1189,810,2449,1958,928,1934,1049,1870,512,2304,1160,2444,1140,2086,629,1920,1015,1145,2034)
ORDER BY id;
