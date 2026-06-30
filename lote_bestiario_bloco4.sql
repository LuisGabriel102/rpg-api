-- =====================================================================
-- LOTE BESTIÁRIO — BLOCO 4 (recomposição-âncora APROVADA)
-- 25 criaturas · 5 grupos · UM UPDATE por criatura
-- Regra-âncora: andar_primario = coluna `andar` do pool (copiado, nunca movido)
-- Stat block mecânico INTOCADO. Só as 25 colunas de ficção.
-- 🟢 Gabriel roda no pgAdmin depois da auditoria pesada do Chat Op.
-- =====================================================================

-- ===== BLOCO 0 — SETVAL (proteção de sequência; empty-table guard) =====
SELECT setval(
  pg_get_serial_sequence('ref_criaturas','id'),
  GREATEST(COALESCE((SELECT MAX(id) FROM ref_criaturas), 1), 1),
  true
);

-- =====================================================================
-- GRUPO 1
-- =====================================================================

-- 554 · Vela-Rasante · Corpo · skirmisher · Oculto · Thornmarak · Superfície · MUDO
UPDATE ref_criaturas SET
nome=$DESC$Vela-Rasante$DESC$,
nome_ptbr=$DESC$Vela-Rasante$DESC$,
slug=$DESC$vela-rasante$DESC$,
origem=$DESC$Natural$DESC$,
andar_primario=$DESC$Superfície$DESC$,
pilar_associado=$DESC$Corpo$DESC$,
continente=ARRAY[$DESC$Thornmarak$DESC$]::text[],
habitat=$DESC$Vive nas alturas de Thornmarak, nos picos de cristal e nas correntes de ar quente sobre as baixadas. Pousa pouco; o céu é o território dela.$DESC$,
comportamento=$DESC$Caça de cima. Sobe até virar um ponto contra a luz, dobra as asas e cai. Bate uma vez, com o bico comprido, e já tornou a subir antes que a presa entenda o que a acertou. Não briga no chão; forçada a pousar, é canhestra e foge.$DESC$,
organizacao=$DESC$Sozinha, ou em pares que dividem a mesma corrente de ar.$DESC$,
perigo=$DESC$Ameaça$DESC$,
behavior_archetype=$DESC$skirmisher$DESC$,
morale_modifier=0,
morale_immune=false,
epigrafe=$DESC$A gente olhou pro alto procurando a sombra. Quando ela apareceu, já era em cima do Tomás.$DESC$,
descricao=$DESC$É uma coisa de asas imensas e couro seco, magra, com um bico longo feito lança. Pesa menos do que parece e voa como uma vela solta ao vento. Não tem garra que preste nem força para lutar parada: a arma dela é a queda. Sobe alto, vira um risco contra o céu, e despenca de bico na frente, acerta uma vez e torna a subir na mesma curva. Vive das alturas de Thornmarak e quase nunca toca o chão. No chão é desajeitada e medrosa; no ar, é a dona da luz.$DESC$,
supersticao_popular=$DESC$Dizem em Thornmarak que o perigo das baixadas vem de cima, não dos matos. O conselho dos tropeiros é simples: em campo aberto sob sol forte, ande olhando o céu, e não pare quieto onde a sua sombra fica grande. Contam que ela mira o que anda sozinho e devagar, e que um grupo apertado, de paus erguidos, a faz desviar. Alguns juram que ela foge de fumaça, e acendem fogo verde quando precisam cruzar o aberto.$DESC$,
sinais_presenca=$DESC$Um ponto parado alto demais para ser pássaro comum, que some quando você pisca. A sombra de asa grande passando rápida pelo chão, sem som. Ossos de presa antiga largados num ressalto de pedra alto. Couro de pena, sem pluma, preso nos cristais. O silêncio dos outros bichos quando ela está rondando.$DESC$,
fraqueza_conhecida=$DESC$O povo sabe que ela vive da queda e do susto. Andar acompanhado, de olho no céu, e parar debaixo de cobertura tira a vantagem dela. Erguer paus e gritar quando ela mergulha costuma fazer ela abortar a descida na última hora.$DESC$,
fraqueza_real=$DESC$Ela é frágil e leve, feita para o ar, não para a briga. Forçada ao chão, mal se sustenta e foge canhestra. Um só golpe firme no instante em que ela puxa para subir, quando precisa estar perto, derruba o voo inteiro. Quem aguenta o primeiro mergulho sem quebrar a formação tira dela a única coisa que ela sabe fazer.$DESC$,
descricao_sensorial=$DESC$O som é o estalo seco do couro das asas e o assobio do ar rasgado na queda, e quase nada mais. O cheiro é de poeira de pena e de ninho velho, seco e morno. Ao toque, é leve e quebradiça, couro esticado sobre osso oco, fria do ar de cima. Aos olhos, é uma vela parda contra o claro do céu, de bico comprido, que só vira vulto inteiro quando já está perto demais.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Animais de pasto que andam sozinhos no aberto$DESC$, $DESC$Viajantes desgarrados e devagar sob sol forte$DESC$),
'predador', jsonb_build_array($DESC$Pouca coisa a alcança no ar; no chão, qualquer caçador maior a apanha$DESC$),
'competidor', jsonb_build_array($DESC$Outras aves de rapina das alturas de Thornmarak$DESC$, $DESC$Passada-Longa$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presença dela diz que o aberto sob o sol não é seguro para quem anda só e devagar.$DESC$,
'evitado_por', jsonb_build_array($DESC$Tropeiros que cruzam o campo em grupo apertado, de olho no céu$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$Osso oco e leve das asas$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Material (Superfície / hastes e armações leves e fortes)$DESC$, 'risco', $DESC$Quebra fácil na mão errada.$DESC$),
jsonb_build_object('material', $DESC$Couro de pena, sem pluma$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (forro leve, vela)$DESC$, 'risco', $DESC$Resseca e racha se mal curtido.$DESC$),
jsonb_build_object('material', $DESC$Bico comprido, duro como lança$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (ponta, furador)$DESC$, 'risco', $DESC$Nenhum.$DESC$),
jsonb_build_object('material', $DESC$Tendão das asas$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (corda, amarra)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Estalo seco do couro de asa e o assobio do ar rasgado na queda, e quase nada mais.$DESC$,
'cheiro', $DESC$Poeira de pena e ninho velho, seco e morno.$DESC$,
'quer', $DESC$Comer. Pegar o que anda só e devagar no aberto, com um golpe de cima, sem nunca ter que lutar de igual para igual.$DESC$,
'tipo_perigo', $DESC$Oculto$DESC$,
'falas_exemplo', 'null'::jsonb,
'gatilhos_agressao', jsonb_build_array($DESC$Algo do tamanho certo anda sozinho e devagar no campo aberto$DESC$, $DESC$A sombra dela passa e a presa não procura abrigo$DESC$, $DESC$Fome depois de dias sem caça boa$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$A presa se aperta em grupo e ergue paus quando ela mergulha$DESC$, $DESC$É forçada a pousar e brigar no chão$DESC$, $DESC$Fogo e fumaça na linha de voo dela$DESC$),
'descoberta_fazendo', $DESC$Em círculos altos contra a luz, marcando algo que anda sozinho lá embaixo, ou rasgando uma presa fresca num ressalto de pedra alto.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Cruzar o aberto em grupo apertado e de paus erguidos, tirando a presa fácil$DESC$, $DESC$Mover-se de cobertura em cobertura sob sol forte$DESC$, $DESC$Acender fumaça na linha de voo dela$DESC$, $DESC$Esperar a noite ou o tempo fechado, quando ela não caça do alto$DESC$)
),
status_conversao='canonizada'
WHERE id=554;

-- 2400 · Quatro-Mãos · Sombra · brute · Direto · Kethara · Eco · MUDO
UPDATE ref_criaturas SET
nome=$DESC$Quatro-Mãos$DESC$,
nome_ptbr=$DESC$Quatro-Mãos$DESC$,
slug=$DESC$quatro-maos$DESC$,
origem=$DESC$Cicatricial$DESC$,
andar_primario=$DESC$Eco$DESC$,
pilar_associado=$DESC$Sombra$DESC$,
continente=ARRAY[$DESC$Kethara$DESC$]::text[],
habitat=$DESC$Ruínas e matos secos de Kethara, onde corpos de bichos grandes ficaram sem ser queimados. Anda para onde sente carne quente.$DESC$,
comportamento=$DESC$Não pensa. Vai direto no que se mexe, com os quatro braços e a boca, e não para de avançar enquanto tiver o que rasgar. Não recua, não desvia, não tem manha: é peso, garra e fome surda. Cai aos pedaços e ainda assim continua vindo.$DESC$,
organizacao=$DESC$Sozinha, ou em punhados largados no mesmo sítio amaldiçoado.$DESC$,
perigo=$DESC$Ameaça$DESC$,
behavior_archetype=$DESC$brute$DESC$,
morale_modifier=0,
morale_immune=true,
epigrafe=$DESC$Cortei os dois braços de cima e ele me pegou com os dois de baixo. Não fez um som. Só apertou.$DESC$,
descricao=$DESC$Foi um bicho grande de quatro braços, e a morte não tirou nenhum deles. O que sobrou anda teso e mudo, de pele repuxada e boca sempre aberta, e ataca tudo que tem calor. Bate com os quatro de uma vez e morde no meio do aperto, e o peso dele basta para derrubar um homem feito. Não sente o que você corta. Tira um braço, ele usa os outros três; tira mais, ele rasteja e ainda morde. Só para quando não tem mais com o que segurar.$DESC$,
supersticao_popular=$DESC$Em Kethara dizem para queimar bicho grande que morre perto de ruína velha, senão ele levanta com fome e quatro mãos. O conselho é não deixar ele te abraçar: de longe e em movimento, com fogo, ele cai; preso no aperto dele, não tem força que solte. Contam que ele não cansa e não foge, e que correr em linha reta dele é melhor do que tentar segurar.$DESC$,
sinais_presenca=$DESC$Carcaça grande de bicho de quatro braços sumida do lugar onde apodrecia. Marcas de quatro mãos arrastadas no pó e nas paredes. Rastro reto, sem desvio, indo na direção do primeiro calor. Moscas que largam a carniça antes da hora. Um cheiro de podre que anda.$DESC$,
fraqueza_conhecida=$DESC$O povo sabe que ele é cego de manha: vai sempre reto, não arma nada, não recua. Quem fica longe e em movimento, e usa fogo, gasta ele aos poucos. O erro é deixar entrar no aperto dos quatro braços.$DESC$,
fraqueza_real=$DESC$Ele é só avanço e nenhuma cabeça. Não muda de plano porque não tem plano. Fogo o consome e o medo não o segura porque ele não sente medo, mas também não cobre flanco nem guarda nada: um grupo que se abre e o toca de longe, em volta, o desmonta sem nunca entrar no abraço. O perigo é todo no contato; tirado o contato, ele é lento e burro.$DESC$,
descricao_sensorial=$DESC$O som é o arrastar de pés tesos e o estalo de junta seca, sem grito nenhum. O cheiro é de carne velha curtida no calor de Kethara, doce e ruim. Ao toque, é duro e seco como couro deixado ao sol, frio por dentro do aperto. Aos olhos, é um vulto grande de quatro braços, de boca aberta e pele repuxada, que vem reto e não desvia.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$O que estiver vivo e quente no caminho reto dele$DESC$, $DESC$Viajantes e bichos que cruzam a ruína amaldiçoada$DESC$),
'predador', jsonb_build_array($DESC$O fogo, e quem o desmonta de longe antes do aperto$DESC$),
'competidor', jsonb_build_array($DESC$Outros mortos sem dono nas ruínas de Kethara$DESC$, $DESC$Carne-Avessa$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presença dele diz que morreu bicho grande ali e ninguém queimou o corpo a tempo.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem queima as carcaças grandes e não deixa o morto chegar perto$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$A seiva escura que ainda corre nos quatro braços e não deixa o morto parar$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Sombra / o que ergue e move a carne morta)$DESC$, 'risco', $DESC$Move na mão o que devia estar quieto; mancha que não sai.$DESC$),
jsonb_build_object('material', $DESC$Garras das quatro mãos, duras feito gancho$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Sombra / armas e ganchos que agarram)$DESC$, 'risco', $DESC$Agarram sozinhas no descuido.$DESC$),
jsonb_build_object('material', $DESC$Couro repuxado das costas largas$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (correaria grossa e crua)$DESC$, 'risco', $DESC$Cheira a podre por semanas.$DESC$),
jsonb_build_object('material', $DESC$Osso pesado de braço$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (cabo de marreta, peso bruto)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Arrastar de pés tesos e estalo de junta seca, sem grito.$DESC$,
'cheiro', $DESC$Carne velha curtida no calor, doce e ruim.$DESC$,
'quer', $DESC$Rasgar o que tem calor. Avançar reto até não ter mais o que segurar.$DESC$,
'tipo_perigo', $DESC$Direto$DESC$,
'falas_exemplo', 'null'::jsonb,
'gatilhos_agressao', jsonb_build_array($DESC$Algo vivo e quente entra no campo dele$DESC$, $DESC$Um movimento perto, à curta distância$DESC$, $DESC$Calor de gente ou bicho ao alcance$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Não recua: segue enquanto tiver um membro para arrastar$DESC$, $DESC$Só cessa quando o alvo quente some de todo do alcance$DESC$, $DESC$O fogo o consome antes de ele parar por conta$DESC$),
'descoberta_fazendo', $DESC$Andando reto e teso por uma ruína de Kethara na direção do primeiro calor, ou parado rasgando o que já derrubou.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Manter distância e movimento, tocando de longe, sem entrar no aperto dos quatro braços$DESC$, $DESC$Usar fogo para consumir o morto$DESC$, $DESC$Correr em linha e deixar o lento para trás$DESC$, $DESC$Queimar a carcaça grande antes que ela levante$DESC$)
),
status_conversao='canonizada'
WHERE id=2400;

-- 1839 · Inquilino-Manso · Arcano · lurker · Persistente · Kethara · Eco · fala  [watch: origem Gremorly's Ghost]
UPDATE ref_criaturas SET
nome=$DESC$Inquilino-Manso$DESC$,
nome_ptbr=$DESC$Inquilino-Manso$DESC$,
slug=$DESC$inquilino-manso$DESC$,
origem=$DESC$Cicatricial$DESC$,
andar_primario=$DESC$Eco$DESC$,
pilar_associado=$DESC$Arcano$DESC$,
continente=ARRAY[$DESC$Kethara$DESC$]::text[],
habitat=$DESC$Ruínas de Kethara onde um conjurador morreu sem terminar o que fazia. Fica onde a parede ainda guarda o que ele era.$DESC$,
comportamento=$DESC$Não tem corpo. É um resto que atravessa pedra e gente, e o que ele quer é morar em alguém. Toca de leve, murcha por dentro quem encosta, e quando acha um corpo que serve, entra e passa a usá-lo como seu, calado, por dentro. Some na parede quando o aperto chega nele.$DESC$,
organizacao=$DESC$Sozinho, preso ao lugar onde acabou.$DESC$,
perigo=$DESC$Letal$DESC$,
behavior_archetype=$DESC$lurker$DESC$,
morale_modifier=2,
morale_immune=false,
epigrafe=$DESC$O velho Harn voltou pra casa falando errado, com a letra de outro. Dormiu marido e acordou inquilino.$DESC$,
descricao=$DESC$É o resto de um que sabia conjurar e morreu no meio da obra. Não tem carne: atravessa parede e corpo como se nenhum dos dois fosse firme. Onde toca, a vida murcha, seca, envelhece depressa. Mas a fome de verdade dele é outra: achar gente viva e entrar, morar no corpo, mover a pessoa por dentro como dono novo enquanto o de fora não percebe. Enquanto está em alguém, é manso, educado, quase o de sempre, com um errinho na voz. Ferido, larga o corpo e some na pedra, e volta inteiro depois, porque o que o sustenta está na ruína, não no corpo que ele pegou.$DESC$,
supersticao_popular=$DESC$Em Kethara contam que certas ruínas pegam o visitante e o mandam de volta trocado por dentro, manso demais, errando o nome das coisas. O conselho dos que sabem: desconfiar de quem voltou diferente da ruína, e não dormir sozinho lá dentro. Dizem que ferir não resolve, porque ele troca de dono; que o jeito é achar o canto da ruína onde ele mora e quebrar aquilo, não o corpo que ele veste.$DESC$,
sinais_presenca=$DESC$Alguém que entrou na ruína e saiu manso e errado, falando com a letra de outro. Frio de murcha onde uma coisa sem corpo passou, plantas secas em risco reto. Marcas de mão envelhecida na pedra, sem mão à vista. Objetos do conjurador morto mexidos sozinhos. A sensação de ser atravessado por algo na ruína fechada.$DESC$,
fraqueza_conhecida=$DESC$O povo acha que é caso de matar o corpo possuído, e quase sempre mata o vizinho à toa. O que de fato afasta é não encarar o corpo: é sair da ruína, porque ele não passa muito além das paredes onde mora.$DESC$,
fraqueza_real=$DESC$Ele não está no corpo que veste; está preso ao canto da ruína onde acabou a obra dele. Murchar e morar são as armas, mas a âncora é o lugar. Quebrar a marca, o objeto, o trecho de parede que o segura, encerra o resto de vez; brigar com o hospedeiro só passa o problema para outro corpo. Tirado da ruína, ele míngua. Quem acha a âncora, e não o vizinho de olhos errados, ganha.$DESC$,
descricao_sensorial=$DESC$O som é um sussurro com a letra trocada, e o roçar de algo que não tem pés na pedra. O cheiro é de poeira de túmulo e de coisa seca antes da hora. Ao toque, é um frio que murcha, que envelhece a pele que encosta. Aos olhos, quase não há o que ver: um borrão frio, e depois um conhecido manso demais, falando errado.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Gente viva que entra na ruína e serve de corpo novo$DESC$, $DESC$O vigor de quem ele toca e murcha$DESC$),
'predador', jsonb_build_array($DESC$Quem acha e quebra a âncora dele na ruína, não o corpo que ele veste$DESC$),
'competidor', jsonb_build_array($DESC$Outros restos das ruínas de Kethara que disputam o mesmo canto$DESC$, $DESC$Mazela-Crua$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presença dele diz que um conjurador morreu ali sem terminar, e que a ruína devolve quem entra trocado por dentro.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem sai da ruína ao anoitecer e não dorme entre as paredes dele$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$A marca que o prende ao canto da ruína, raspada da pedra$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Arcano / ancorar e desancorar o que sobrou de um morto)$DESC$, 'risco', $DESC$Tenta morar em quem a carrega sem preparo.$DESC$),
jsonb_build_object('material', $DESC$Pó da murcha que ele deixa onde toca$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Arcano / o que seca e envelhece depressa)$DESC$, 'risco', $DESC$Seca a mão que o manuseia sem luva.$DESC$),
jsonb_build_object('material', $DESC$Caderno do conjurador morto, meio podre$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (estudo de conjuro antigo)$DESC$, 'risco', $DESC$Páginas que se leem sozinhas no escuro.$DESC$),
jsonb_build_object('material', $DESC$Poeira de túmulo da ruína$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (pó seco, lastro)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Sussurro com a letra trocada e o roçar de algo sem pés na pedra.$DESC$,
'cheiro', $DESC$Poeira de túmulo e coisa seca antes da hora.$DESC$,
'quer', $DESC$Achar um corpo vivo e morar nele, mover a pessoa por dentro como dono novo, sem ser percebido.$DESC$,
'tipo_perigo', $DESC$Persistente$DESC$,
'falas_exemplo', jsonb_build_array($DESC$Não precisa ter medo. Eu só vou ficar um pouco. Você nem vai notar a diferença.$DESC$, $DESC$Esse corpo cansa rápido. O seu parece bem mais novo.$DESC$, $DESC$(registro: fala mansa, educada, na letra de quem ele já foi e na de quem ele veste; erra um nome aqui e ali e corrige com calma)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Alguém encosta ou atravessa o canto onde ele mora$DESC$, $DESC$Um corpo são e forte entra sozinho na ruína$DESC$, $DESC$Tentam levar o que pertenceu ao conjurador morto$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Larga o corpo e some na pedra quando o aperto chega nele$DESC$, $DESC$Recolhe-se à âncora quando o sol entra forte na ruína$DESC$, $DESC$Abandona o hospedeiro ferido e espera outro$DESC$),
'descoberta_fazendo', $DESC$Vestindo um morador ou um viajante na ruína de Kethara, manso e calado, fazendo as coisas dele com um errinho na voz.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Sair da ruína, onde ele não alcança$DESC$, $DESC$Achar e quebrar a âncora dele na pedra em vez de ferir o hospedeiro$DESC$, $DESC$Tirar o tomado para longe das paredes, onde o domínio afrouxa$DESC$, $DESC$Não dormir nem andar sozinho lá dentro$DESC$)
),
status_conversao='canonizada'
WHERE id=1839;

-- 862 · Arbítrio-Justo · Espírito · tactical · Condicional · Voranthar · Clarão · fala
UPDATE ref_criaturas SET
nome=$DESC$Arbítrio-Justo$DESC$,
nome_ptbr=$DESC$Arbítrio-Justo$DESC$,
slug=$DESC$arbitrio-justo$DESC$,
origem=$DESC$Cicatricial$DESC$,
andar_primario=$DESC$Clarão$DESC$,
pilar_associado=$DESC$Espírito$DESC$,
continente=ARRAY[$DESC$Voranthar$DESC$]::text[],
habitat=$DESC$Onde o Clarão toca Voranthar, sobre as ruínas e os campos onde houve juramento quebrado. Desce quando há o que julgar.$DESC$,
comportamento=$DESC$Não odeia e não tem dó. Mede pela régua dele e bate no que sai dela. Fala manso, pela cabeça, e oferece a conta antes de cobrar. Quem aceita a régua passa; quem fura, leva a maça de luz. Não persegue inocente e não poupa culpado. Não foge: vai embora quando o juízo está feito.$DESC$,
organizacao=$DESC$Sozinho. Um basta para um julgamento.$DESC$,
perigo=$DESC$Letal$DESC$,
behavior_archetype=$DESC$tactical$DESC$,
morale_modifier=0,
morale_immune=true,
epigrafe=$DESC$Ele não gritou nem ameaçou. Disse o que eu tinha feito, com calma, e perguntou se eu negava. Eu devia ter negado calado.$DESC$,
descricao=$DESC$Vem do alto, do claro, e tem a forma de algo grande e severo, de luz fria que não esquenta. Não é bom; é justo do jeito dele, que é duro. Fala dentro da sua cabeça, sem boca, e diz o que você fez, e pergunta se você nega. Aceite a régua dele e ele baixa a maça. Minta, fure, ataque o que ele guarda, e a maça de luz cai, e luz não se apara com escudo comum. Magia jogada nele escorrega. Ferido, ele se refaz e continua a conta de onde parou. Não se cansa de cobrar.$DESC$,
supersticao_popular=$DESC$Em Voranthar dizem que sobre certos campos desce um que pesa o que você fez e cobra na hora. O conselho dos velhos é não mentir para ele e não tocar no que ele guarda, porque ele lê a treta e a luz dele queima frio. Contam que com o inocente ele é só severo, e com o culpado é o fim, e que o pior negócio é fingir limpeza diante de quem mede certo.$DESC$,
sinais_presenca=$DESC$Uma luz fria parada no alto que não vem do sol nem aquece. O silêncio dos bichos e um cheiro de ar limpo demais. Uma voz sem som que pergunta na sua cabeça o que você fez. O lugar onde ele desceu fica marcado, a grama deitada em roda. A calma errada de quem não tem culpa e a aflição de quem tem.$DESC$,
fraqueza_conhecida=$DESC$O povo acha que é briga de força, e perde. O que funciona é não dar a ele o que ele cobra: não mentir, não roubar o que ele guarda, aceitar a régua. Quem está limpo costuma passar; quem briga, não.$DESC$,
fraqueza_real=$DESC$Ele cobra por régua, não por raiva, e a régua é a brecha. Não persegue quem se entrega nem inventa culpa; o que dispara a maça é a transgressão e a mentira diante dele. Magia direta escorrega, mas a régua tem limite: cumprida a conta, ele para e sobe. Quem entende que é um juízo, e não um monstro, e paga ou prova limpeza, sai vivo; quem trata como bicho, morre certo.$DESC$,
descricao_sensorial=$DESC$O som é uma voz sem som que chega por dentro, e um zumbido baixo de luz parada. O cheiro é de ar limpo demais, sem poeira, quase sem cheiro. Ao toque, a luz dele é fria e seca, e queima sem brasa. Aos olhos, é uma figura grande e severa de claridade que não esquenta, bela de um jeito que não conforta.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Não caça: cobra de quem furou a régua e mentiu diante dele$DESC$, $DESC$Os que tocam o que ele guarda em Voranthar$DESC$),
'predador', jsonb_build_array($DESC$Nada o caça; ele encerra e sobe quando o juízo está feito$DESC$),
'competidor', jsonb_build_array($DESC$Outras forças do Clarão sobre Voranthar que medem por réguas diferentes$DESC$, $DESC$Escama-Soberana$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presença dele diz que houve juramento quebrado ali, e que veio a conta.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem não mente diante dele e não toca no que ele guarda$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$Um caco da luz fria que sobra onde a maça caiu$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Clarão / a luz que julga e queima sem brasa)$DESC$, 'risco', $DESC$Cega e queima frio quem a segura sem régua na consciência.$DESC$),
jsonb_build_object('material', $DESC$A cinza limpa do lugar onde ele desceu$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Clarão / o que separa limpo de sujo)$DESC$, 'risco', $DESC$Resseca tudo que toca.$DESC$),
jsonb_build_object('material', $DESC$Lasca da maça, dura e clara$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (foco de luz, peso justo)$DESC$, 'risco', $DESC$Esquenta na mão da treta.$DESC$),
jsonb_build_object('material', $DESC$Grama deitada do círculo dele$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (palha seca, marca de presença)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Voz sem som por dentro e um zumbido baixo de luz parada.$DESC$,
'cheiro', $DESC$Ar limpo demais, quase sem cheiro.$DESC$,
'quer', $DESC$Medir o que você fez e cobrar pela régua dele. Fechar a conta e subir.$DESC$,
'tipo_perigo', $DESC$Condicional$DESC$,
'falas_exemplo', jsonb_build_array($DESC$Eu sei o que você fez. Diga você mesmo, e diga se nega.$DESC$, $DESC$A régua não é a minha raiva. É só a régua. Você sabia dela.$DESC$, $DESC$(registro: fala fria e clara, direto na cabeça, sem aspereza e sem dó; oferece a conta antes de cobrar)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Mentir para ele sobre o que se fez$DESC$, $DESC$Tocar ou roubar o que ele guarda$DESC$, $DESC$Ferir quem está sob a régua dele$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Não foge: sobe quando o juízo está cumprido$DESC$, $DESC$Recua de quem se entrega e paga a conta$DESC$, $DESC$Encerra e parte quando não há mais transgressão diante dele$DESC$),
'descoberta_fazendo', $DESC$Descendo do claro sobre um campo de Voranthar, parado no ar, perguntando na cabeça de alguém o que ele fez.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Aceitar a régua e provar limpeza, em vez de brigar$DESC$, $DESC$Entregar ou devolver o que ele cobra$DESC$, $DESC$Não mentir diante dele$DESC$, $DESC$Afastar-se do que ele guarda e deixá-lo encerrar a conta$DESC$)
),
status_conversao='canonizada'
WHERE id=862;

-- 859 · Cúpula-Morta · Engenho · artillery · Ambiental · Kethara · Eco · fala
UPDATE ref_criaturas SET
nome=$DESC$Cúpula-Morta$DESC$,
nome_ptbr=$DESC$Cúpula-Morta$DESC$,
slug=$DESC$cupula-morta$DESC$,
origem=$DESC$Cicatricial$DESC$,
andar_primario=$DESC$Eco$DESC$,
pilar_associado=$DESC$Engenho$DESC$,
continente=ARRAY[$DESC$Kethara$DESC$]::text[],
habitat=$DESC$Câmaras fundas das ruínas de Kethara, salões de teto alto onde ela pode flutuar e ver tudo de uma vez. Fica parada no alto, como um teto que olha.$DESC$,
comportamento=$DESC$Flutua e vigia. Não persegue: faz do salão inteiro a arma dela, varrendo o ar com feixes dos muitos olhos, cada um com um efeito ruim, de modo que não há canto seguro debaixo dela. Morde quem chega perto, mas prefere que ninguém chegue. O campo de visão dela é o salão todo.$DESC$,
organizacao=$DESC$Sozinha, dona de uma câmara só.$DESC$,
perigo=$DESC$Letal$DESC$,
behavior_archetype=$DESC$artillery$DESC$,
morale_modifier=1,
morale_immune=false,
epigrafe=$DESC$Não tinha onde se esconder. O teto era um olho, e os olhos do teto eram muitos, e cada feixe fazia uma desgraça diferente.$DESC$,
descricao=$DESC$É um bolo de carne morta do tamanho de um carro de boi, que boia sem peso, com um olho grande no meio e vários menores em hastes, todos sem vida e ainda assim olhando. Onde a vista dela alcança, o ar vira armadilha: de cada olho menor sai um feixe, e cada feixe faz uma coisa ruim diferente, e juntos cobrem o salão inteiro. Não há lugar fora do alcance debaixo dela. O olho grande do meio não pisca e nega o que tenta se aproximar. Chega perto e ela morde; fica longe e ela varre. Aguenta muito e some pouco do lugar dela.$DESC$,
supersticao_popular=$DESC$Em Kethara dizem que há salões fundos onde o teto é um olho morto, e que entrar é virar alvo de tudo ao mesmo tempo. O conselho é não entrar reto, não ficar parado no aberto da câmara, e cortar a linha de visão dela com pilar e pedra. Contam que ela não sai do salão dela, e que quem fica na soleira, fora do alcance, fica vivo.$DESC$,
sinais_presenca=$DESC$Um salão fundo onde nada cresce e o pó está varrido em leques. Marcas de queimadura, de corrosão e de pedra rachada espalhadas em todas as direções, vindas do teto. Corpos largados sem padrão, cada um morto de um jeito diferente. Um zumbido baixo de muitos olhos. A sensação de ser visto de cima no instante em que se entra.$DESC$,
fraqueza_conhecida=$DESC$O povo sabe que o perigo é a visão dela: o que ela vê, ela varre. Usar pilar, escombro e canto para quebrar a linha dos olhos, e não atravessar o aberto da câmara, é o método. Ficar na soleira costuma bastar para não ser alvo.$DESC$,
fraqueza_real=$DESC$A arma dela é cobrir o espaço com a vista; tirada a vista, ela é um saco de carne lento que mal se move. Não larga a câmara e não persegue para fora. Quem a cega, quem fecha os muitos olhos um a um do abrigo dos pilares, ou quem simplesmente não entra no salão, tira dela tudo. O perigo é o lugar sob ela; fora do salão, não há perigo nenhum.$DESC$,
descricao_sensorial=$DESC$O som é um zumbido baixo e o assobio seco dos feixes cortando o ar. O cheiro é de carne morta parada e de pedra queimada. Ao toque, para quem chega a tocar, é fria e flácida, carne sem vida que ainda olha. Aos olhos, é uma cúpula de carne morta presa ao alto, de um olho grande e muitos pequenos, todos abertos e nenhum vivo.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$O que entra na câmara dela e cruza o campo de visão$DESC$, $DESC$Saqueadores das ruínas fundas de Kethara$DESC$),
'predador', jsonb_build_array($DESC$Nada a caça no salão dela; perde só para quem a cega e a deixa lenta$DESC$),
'competidor', jsonb_build_array($DESC$Outras coisas das ruínas de Kethara que disputam as câmaras fundas$DESC$, $DESC$Súcia-Lúcida$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presença dela diz que aquele salão fundo é uma armadilha de visão, e que ninguém o limpou.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem fica na soleira e corta a linha de visão com pilar e escombro$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$O olho grande do meio, morto e ainda atento$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Engenho / ver longe e varrer o que se vê)$DESC$, 'risco', $DESC$Olha de volta de dentro do bornal.$DESC$),
jsonb_build_object('material', $DESC$Os olhos menores das hastes, cada um com um feitio$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Engenho / feixes de efeitos diversos)$DESC$, 'risco', $DESC$Disparam o efeito ao menor toque.$DESC$),
jsonb_build_object('material', $DESC$Couro morto da cúpula, leve e sem peso$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (revestimento que boia)$DESC$, 'risco', $DESC$Fede a carne parada.$DESC$),
jsonb_build_object('material', $DESC$Hastes ocas dos olhos$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (tubos leves)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Zumbido baixo e o assobio seco dos feixes cortando o ar.$DESC$,
'cheiro', $DESC$Carne morta parada e pedra queimada.$DESC$,
'quer', $DESC$Que ninguém cruze a câmara dela vivo. Ver tudo de uma vez e varrer o que vê.$DESC$,
'tipo_perigo', $DESC$Ambiental$DESC$,
'falas_exemplo', jsonb_build_array($DESC$Você entrou no meu salão. Agora está dentro do que eu vejo.$DESC$, $DESC$Não corra para os cantos. Eu sou o teto. Os cantos também são meus.$DESC$, $DESC$(registro: voz seca e funda, em língua do fundo, paciente como quem já viu todos entrarem e caírem)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Alguém entra no salão e cruza o campo de visão dela$DESC$, $DESC$Um movimento no aberto da câmara$DESC$, $DESC$Tentam tomar o que está sob ela$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Não persegue para fora do salão$DESC$, $DESC$Recolhe-se ao alto quando cegada e exposta$DESC$, $DESC$Cessa o varrer quando não há mais nada vivo no campo dela$DESC$),
'descoberta_fazendo', $DESC$Parada no alto de uma câmara funda de Kethara, como um teto de carne morta, varrendo o ar com os feixes ao primeiro que entra.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Não entrar no salão dela, que ela não deixa$DESC$, $DESC$Cortar a linha de visão com pilares e escombro e atravessar pela borda$DESC$, $DESC$Cegar os olhos um a um do abrigo$DESC$, $DESC$Ficar na soleira, fora do alcance, e contornar por outro caminho$DESC$)
),
status_conversao='canonizada'
WHERE id=859;

-- =====================================================================
-- GRUPO 2
-- =====================================================================

-- 885 · Duas-Bocas · Corpo · soldier · Direto · Thornmarak · Superfície · fala
UPDATE ref_criaturas SET
nome=$DESC$Duas-Bocas$DESC$,
nome_ptbr=$DESC$Duas-Bocas$DESC$,
slug=$DESC$duas-bocas$DESC$,
origem=$DESC$Natural$DESC$,
andar_primario=$DESC$Superfície$DESC$,
pilar_associado=$DESC$Corpo$DESC$,
continente=ARRAY[$DESC$Thornmarak$DESC$]::text[],
habitat=$DESC$Encostas e matos de pedra de Thornmarak, perto de trilha de gado e de gente. Faz toca rasa de onde pode emboscar a estrada.$DESC$,
comportamento=$DESC$Tem duas cabeças que nunca concordam e nunca dormem ao mesmo tempo, então quase nunca é pego desprevenido. Briga de frente, com machado numa mão e maça na outra, batendo duas vezes para cada vez que você bate. É burro e teimoso, mas forte feito poucos, e não larga osso fácil.$DESC$,
organizacao=$DESC$Sozinho, dono de um trecho de trilha.$DESC$,
perigo=$DESC$Ameaça$DESC$,
behavior_archetype=$DESC$soldier$DESC$,
morale_modifier=0,
morale_immune=false,
epigrafe=$DESC$Achei que estava dormindo. Uma cabeça estava. A outra me viu a légua.$DESC$,
descricao=$DESC$É um gigante feio de duas cabeças no mesmo tronco largo, cada uma com sua boca e seu mau humor, vivas em brigar entre si. Não pensa direito, mas as duas cabeças se revezam acordadas, e por isso é difícil de surpreender. Luta de frente e sem manha, com um machado numa mão e uma maça de ferro na outra, e desce as duas armas em quem tem pela frente, de novo e de novo. Não recua por orgulho nem por plano; recua quando apanha demais. A força dele é bruta e a guarda, dobrada: são quatro olhos vigiando.$DESC$,
supersticao_popular=$DESC$Em Thornmarak avisam para não tentar passar quieto por onde mora o de duas cabeças, porque uma delas está sempre de vigia. O conselho é não emboscar quem não dorme inteiro: ou se enfrenta de frente, em número, ou se faz um longo desvio. Dizem que as duas cabeças brigam tanto que dá para confundi-las uma contra a outra, e os espertos jogam com isso.$DESC$,
sinais_presenca=$DESC$Pegadas grandes de um só dono pisando pesado nos dois lados da trilha. Restos de duas refeições no mesmo fogo, como se dois comessem. Resmungo dobrado vindo da mesma toca, duas vozes discutindo. Gado e viajante sumidos de um trecho de estrada. Ossos roídos empilhados na boca de uma gruta rasa.$DESC$,
fraqueza_conhecida=$DESC$O povo sabe que não adianta tentar pegá-lo dormindo, porque metade dele está sempre acordada. Encará-lo de frente em número, ou desviar de longe, é o que resta. Os mais frios provocam uma cabeça contra a outra para ele perder o tempo brigando consigo.$DESC$,
fraqueza_real=$DESC$Ele é força sem cabeça boa, e a fraqueza é justo isso: as duas cabeças não se entendem. Confunda-as, dê ordens contrárias, faça uma querer ir e a outra ficar, e ele trava no meio do passo. Não tem manha tática nenhuma; vai de frente sempre. Quem o enfrenta junto, dividindo a atenção das duas bocas, e não tenta o golpe furtivo que ele fareja, derruba o bruto antes que a força dele decida a briga.$DESC$,
descricao_sensorial=$DESC$O som é duas vozes roucas discutindo na mesma garganta e o arrastar pesado de pés grandes. O cheiro é de bode e de suor velho, forte e azedo. Ao toque, é pele grossa e dura, quente, sobre músculo que não cede. Aos olhos, é um vulto enorme de duas cabeças tortas, de machado e maça, que encara você com quatro olhos de uma vez.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Gado e viajantes do trecho de estrada que ele domina$DESC$, $DESC$O que cai na emboscada rasa dele$DESC$),
'predador', jsonb_build_array($DESC$Grupos armados que o enfrentam em número; coisas maiores das alturas de Thornmarak$DESC$),
'competidor', jsonb_build_array($DESC$Outros brutos de Thornmarak que disputam a mesma trilha$DESC$, $DESC$Marfim-Pesado$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presença dele diz que aquele trecho de estrada tem dono, e que o dono nunca dorme inteiro.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem desvia de longe ou passa só em número grande e armado$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$As duas caveiras grandes, de quatro órbitas$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Material (Superfície / troféu, marco de aviso na trilha)$DESC$, 'risco', $DESC$Atrai outros brutos curiosos.$DESC$),
jsonb_build_object('material', $DESC$Couro grosso das costas largas$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (couraça crua, correaria pesada)$DESC$, 'risco', $DESC$Fede a bode por semanas.$DESC$),
jsonb_build_object('material', $DESC$Machado e maça tortos que ele usava$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (ferro para refundir)$DESC$, 'risco', $DESC$Nenhum.$DESC$),
jsonb_build_object('material', $DESC$Tendão grosso de braço$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (corda forte)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Duas vozes roucas discutindo na mesma garganta e o arrastar pesado de pés grandes.$DESC$,
'cheiro', $DESC$Bode e suor velho, forte e azedo.$DESC$,
'quer', $DESC$Comer e mandar no seu trecho de estrada. Bater de frente em quem entra, sem ser pego de surpresa.$DESC$,
'tipo_perigo', $DESC$Direto$DESC$,
'falas_exemplo', jsonb_build_array($DESC$Esse caminho é meu. As duas cabeças concordam nisso, pelo menos.$DESC$, $DESC$Cala a boca, eu vi primeiro. Não, eu vi. Pega ele logo!$DESC$, $DESC$(registro: fala grossa em língua de gigante, duas vozes que se atropelam e se contradizem na mesma frase)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Alguém entra no trecho de estrada que ele domina$DESC$, $DESC$Um movimento de quem tenta passar quieto$DESC$, $DESC$Fome e o cheiro de gado ou gente perto$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Recua quando apanha demais de um grupo grande$DESC$, $DESC$Larga a briga quando as duas cabeças discordam de continuar$DESC$, $DESC$Foge da coisa maior que desce das alturas$DESC$),
'descoberta_fazendo', $DESC$Sentado na boca de uma gruta rasa de Thornmarak, roendo osso, com uma cabeça cochilando e a outra de vigia para a trilha.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Desviar de longe do trecho que ele domina$DESC$, $DESC$Enfrentá-lo em número, de frente, sem tentar o furtivo que ele fareja$DESC$, $DESC$Provocar uma cabeça contra a outra e passar enquanto ele briga consigo$DESC$, $DESC$Pagar pedágio de comida e seguir$DESC$)
),
status_conversao='canonizada'
WHERE id=885;

-- 1199 · Montaria-Ossuda · Sombra · skirmisher · Oculto · Voranthar · Eco · MUDO
UPDATE ref_criaturas SET
nome=$DESC$Montaria-Ossuda$DESC$,
nome_ptbr=$DESC$Montaria-Ossuda$DESC$,
slug=$DESC$montaria-ossuda$DESC$,
origem=$DESC$Cicatricial$DESC$,
andar_primario=$DESC$Eco$DESC$,
pilar_associado=$DESC$Sombra$DESC$,
continente=ARRAY[$DESC$Voranthar$DESC$]::text[],
habitat=$DESC$Campos de batalha velhos de Voranthar, onde caiu cavalaria e ninguém recolheu os ossos. Espera na neblina e no mato alto do antigo terreno de guerra.$DESC$,
comportamento=$DESC$Foi montaria de guerra e ainda corre como uma. Fica parada e quieta feito osso largado até algo passar, e então arranca, rápida e calada, e atropela com os cascos. Bate de passagem e segue; volta na curva. Não relincha, não bufa, não avisa. Só os cascos no chão, quando já é tarde.$DESC$,
organizacao=$DESC$Sozinha, ou em punhados largados no mesmo campo caído.$DESC$,
perigo=$DESC$Ameaça$DESC$,
behavior_archetype=$DESC$skirmisher$DESC$,
morale_modifier=0,
morale_immune=true,
epigrafe=$DESC$Não ouvi cavalo nenhum. Ouvi os cascos quando já estava no chão, com a coisa passando por cima.$DESC$,
descricao=$DESC$É a ossada de um cavalo de guerra que a morte não deixou deitar. Sem carne, sem som, fica imóvel no meio dos outros ossos do campo até alguém chegar perto, e então dispara, veloz e calada, e passa por cima com os cascos duros. Não tem mordida nem manha: tem o peso da corrida e a vantagem de não fazer barulho. Atropela, segue na arrancada, contorna e volta. É leve de osso oco e quebra com pancada cega, mas enquanto corre, é difícil de tocar.$DESC$,
supersticao_popular=$DESC$Em Voranthar dizem que os campos onde caiu cavalaria guardam montarias que ainda cavalgam sozinhas, sem cavaleiro e sem som. O conselho é não cruzar o velho terreno de guerra na neblina, e nunca a pé e devagar. Contam que pancada de marreta a desmonta, mas que o difícil é acertá-la em movimento, porque ela não avisa quando vem.$DESC$,
sinais_presenca=$DESC$Ossada de cavalo que não está onde estava ontem. Marcas de casco frescas num campo onde não há cavalo vivo. Silêncio sem grilo nem ave no antigo terreno de guerra. Mato alto pisado em linhas de corrida. O frio parado da neblina que não levanta.$DESC$,
fraqueza_conhecida=$DESC$O povo sabe que ela é osso oco e leve, e que pancada cega de marreta a parte. O custo é acertá-la: ela corre calada e bate de passagem. Quem fica em terreno fechado, onde ela não ganha arrancada, leva vantagem.$DESC$,
fraqueza_real=$DESC$A arma dela é a corrida silenciosa e o atropelo; tirado o espaço de corrida, ela é uma ossada frágil que se quebra com um golpe pesado. Não tem mente para temer nem para recuar; segue até ser desmontada. Quem a prende em lugar apertado, sem reta para a arrancada, e a parte com pancada de contusão quando ela trava, encerra a corrida. No aberto e na neblina, ela é quem escolhe a hora.$DESC$,
descricao_sensorial=$DESC$O som é só o baque seco dos cascos no chão, sem relincho nem fôlego. O cheiro é de osso seco e terra de campo velho, quase nenhum. Ao toque, é osso liso e frio, leve, sem carne nem calor. Aos olhos, é uma armação de cavalo sem pele correndo no escuro, que some no mato alto entre uma passagem e outra.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Quem cruza a pé e devagar o velho terreno de guerra$DESC$, $DESC$Viajantes pegos na neblina do campo$DESC$),
'predador', jsonb_build_array($DESC$Pancada pesada que a desmonta; terreno fechado que tira a arrancada dela$DESC$),
'competidor', jsonb_build_array($DESC$Outros mortos da cavalaria caída de Voranthar$DESC$, $DESC$Estandarte-Roto$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presença dela diz que ali caiu cavalaria e os ossos nunca foram recolhidos.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem não cruza o campo de guerra na neblina e a pé$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$O que mantém a ossada de pé e em corrida depois da morte$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Sombra / o que ergue e move o osso largado)$DESC$, 'risco', $DESC$Faz tremer e andar o osso na mão de quem não sabe.$DESC$),
jsonb_build_object('material', $DESC$Cascos duros, gastos de tanto pisar$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Sombra / peso e ímpeto de carga)$DESC$, 'risco', $DESC$Pisam sozinhos no escuro do bornal.$DESC$),
jsonb_build_object('material', $DESC$Costelas ocas e leves$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (armação leve e resistente)$DESC$, 'risco', $DESC$Nenhum além do arrepio de carregar.$DESC$),
jsonb_build_object('material', $DESC$Poeira de osso e terra de campo$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (pó, enchimento)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Só o baque seco dos cascos no chão, sem relincho nem fôlego.$DESC$,
'cheiro', $DESC$Osso seco e terra de campo velho, quase nenhum.$DESC$,
'quer', $DESC$Correr e atropelar o que cruza o campo dela, calada, como na guerra que não acabou para ela.$DESC$,
'tipo_perigo', $DESC$Oculto$DESC$,
'falas_exemplo', 'null'::jsonb,
'gatilhos_agressao', jsonb_build_array($DESC$Algo cruza a pé e devagar o campo onde ela espera$DESC$, $DESC$Um movimento no mato alto ao alcance da arrancada$DESC$, $DESC$Alguém para quieto no aberto da neblina$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Não teme: segue até ser desmontada$DESC$, $DESC$Cessa a corrida quando o alvo deixa o campo aberto$DESC$, $DESC$Recolhe-se aos ossos largados quando não há mais o que atropelar$DESC$),
'descoberta_fazendo', $DESC$Imóvel entre outros ossos do velho terreno de guerra de Voranthar, na neblina, à espera de algo que cruze para arrancar e atropelar.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Não cruzar o campo a pé e devagar na neblina$DESC$, $DESC$Passar por terreno fechado, onde ela não corre$DESC$, $DESC$Atraí-la para o apertado e desmontá-la com pancada pesada quando ela trava$DESC$, $DESC$Recolher e queimar a ossada da cavalaria caída$DESC$)
),
status_conversao='canonizada'
WHERE id=1199;

-- 622 · Fâmulo-Quedo · Arcano · striker · Condicional · Vyrkhor · Eco · fala
UPDATE ref_criaturas SET
nome=$DESC$Fâmulo-Quedo$DESC$,
nome_ptbr=$DESC$Fâmulo-Quedo$DESC$,
slug=$DESC$famulo-quedo$DESC$,
origem=$DESC$Cicatricial$DESC$,
andar_primario=$DESC$Eco$DESC$,
pilar_associado=$DESC$Arcano$DESC$,
continente=ARRAY[$DESC$Vyrkhor$DESC$]::text[],
habitat=$DESC$Picos e ruínas geladas de Vyrkhor onde um conjurador selou um trato e morreu sem cumprir. Fica de guarda ao que o trato mandou guardar.$DESC$,
comportamento=$DESC$Serve a um pacto que a morte não desfez. Fica quieto no posto, frio e calado, até alguém quebrar a condição do trato: tocar o que ele guarda, passar do limite, dizer o nome errado. Aí ataca, com a mão que mata o calor, certeiro e sem alarde. Cumprida a ordem, volta ao posto. Não foge: serve até o trato se encerrar.$DESC$,
organizacao=$DESC$Sozinho, postado ao que o trato mandou guardar.$DESC$,
perigo=$DESC$Ameaça$DESC$,
behavior_archetype=$DESC$striker$DESC$,
morale_modifier=0,
morale_immune=true,
epigrafe=$DESC$Ele deixou a gente entrar. Foi só quando o Belo tocou a arca que a mão dele encontrou o peito do Belo.$DESC$,
descricao=$DESC$É o que sobrou de um conjurador que selou um trato e morreu antes de pagar, e o trato o segura de pé, frio, no posto. Não respira e não esquenta. Fica parado, paciente, sem ameaçar, enquanto a condição do pacto não é ferida. Quem passa do limite, toca o guardado, fura a regra que ele serve, recebe a mão dele no peito, e onde essa mão pega, o calor da vida vai embora. É difícil de afugentar com reza, porque ele não obedece a isso; obedece ao trato. Ferido, ele aguenta e continua servindo, porque o que o prende não é a carne.$DESC$,
supersticao_popular=$DESC$Em Vyrkhor contam que há guardas frios postados em ruína gelada que deixam você entrar e só matam se você mexer no que não devia. O conselho é não tocar em nada, não passar das marcas, e sair como entrou. Dizem que reza não move esse tipo, porque ele serve a um trato, não a um céu, e que o seguro é descobrir o que ele guarda e simplesmente não querer aquilo.$DESC$,
sinais_presenca=$DESC$Uma figura seca e quieta de pé num posto de ruína gelada, que não reage à sua chegada. Frio mais fundo perto do que ele guarda. Marcas e limites antigos riscados no chão, que ele não deixa passar. Plantas e líquens mortos em volta do guardado. O silêncio de quem espera você errar.$DESC$,
fraqueza_conhecida=$DESC$O povo sabe que ele não ataca quem não mexe no que ele guarda. Entrar com cuidado, não tocar em nada, não passar das marcas, e sair, costuma bastar. Reza não resolve; respeito ao limite, sim.$DESC$,
fraqueza_real=$DESC$Ele é servo de uma condição, não um caçador: o que dispara o golpe é a transgressão, sempre a mesma. Quebre o trato e ele vem; respeite e ele fica de pedra. A mão fria mata o calor, mas ele não persegue além do que o trato manda. Quem entende qual é a regra que ele serve, e não a fere, passa intocado; quem descobre o objeto do pacto e o desfaz por fora encerra o guarda sem briga, porque tirada a razão de servir, ele cai.$DESC$,
descricao_sensorial=$DESC$O som é quase nada, um respirar que não há e o estalo do gelo perto dele. O cheiro é de pedra fria e de coisa seca guardada faz tempo. Ao toque, a mão dele tira o calor, e onde toca fica dormente e gelado. Aos olhos, é uma figura magra e quieta, de pele seca colada ao osso, parada no posto como parte da ruína.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Não caça: fere quem quebra a condição do trato que ele serve$DESC$, $DESC$Saqueadores que tocam o guardado nas ruínas geladas de Vyrkhor$DESC$),
'predador', jsonb_build_array($DESC$Quem desfaz por fora o objeto do pacto e encerra o guarda$DESC$),
'competidor', jsonb_build_array($DESC$Outros restos de Vyrkhor que cobiçam o que ele guarda$DESC$, $DESC$Pacto-Murcho$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presença dele diz que ali um conjurador selou um trato e morreu sem pagar, e que algo está sendo guardado.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem entra sem tocar em nada e respeita as marcas antigas$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$O selo do trato que o mantém de pé, frio na mão$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Arcano / o que prende um servo a uma condição)$DESC$, 'risco', $DESC$Cobra de quem o segura o que o morto não pagou.$DESC$),
jsonb_build_object('material', $DESC$A mão que tira o calor da vida$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Arcano / o que esfria e amortece o que toca)$DESC$, 'risco', $DESC$Gela e adormece a própria mão que a carrega.$DESC$),
jsonb_build_object('material', $DESC$Limites e marcas riscados que ele guardava$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (estudo de pacto e selo)$DESC$, 'risco', $DESC$Confunde quem os lê em voz alta.$DESC$),
jsonb_build_object('material', $DESC$Líquen morto do posto gelado$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (isca seca, lastro)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Quase nada: um respirar que não há e o estalo do gelo perto dele.$DESC$,
'cheiro', $DESC$Pedra fria e coisa seca guardada faz tempo.$DESC$,
'quer', $DESC$Cumprir o trato que a morte não desfez. Guardar o que mandaram guardar, e ferir só quem quebra a regra.$DESC$,
'tipo_perigo', $DESC$Condicional$DESC$,
'falas_exemplo', jsonb_build_array($DESC$Pode olhar. Não toque. Enquanto não tocar, não temos assunto.$DESC$, $DESC$Eu não escolho. O trato escolhe. Você acabou de escolher por mim.$DESC$, $DESC$(registro: fala seca e baixa, paciente, na língua que ele sabia em vida; avisa uma vez, nunca duas)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Tocar ou levar o que ele guarda$DESC$, $DESC$Passar das marcas e limites do posto$DESC$, $DESC$Ferir a regra do trato que o prende$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Não foge: serve até o trato se encerrar$DESC$, $DESC$Volta ao posto quando a transgressão cessa$DESC$, $DESC$Cai e descansa quando o objeto do pacto é desfeito por fora$DESC$),
'descoberta_fazendo', $DESC$De pé, imóvel, num posto de ruína gelada de Vyrkhor, guardando algo, sem reagir a quem só passa e olha.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Entrar sem tocar em nada e respeitar as marcas$DESC$, $DESC$Descobrir a regra que ele serve e não feri-la$DESC$, $DESC$Desfazer por fora o objeto do pacto para encerrar o guarda$DESC$, $DESC$Sair como entrou, devagar e de mãos vazias$DESC$)
),
status_conversao='canonizada'
WHERE id=622;

-- 2371 · Rajada-Cortante · Espírito · controller · Ambiental · Vyrkhor · Superfície · fala
UPDATE ref_criaturas SET
nome=$DESC$Rajada-Cortante$DESC$,
nome_ptbr=$DESC$Rajada-Cortante$DESC$,
slug=$DESC$rajada-cortante$DESC$,
origem=$DESC$Natural$DESC$,
andar_primario=$DESC$Superfície$DESC$,
pilar_associado=$DESC$Espírito$DESC$,
continente=ARRAY[$DESC$Vyrkhor$DESC$]::text[],
habitat=$DESC$Os picos altos e ventados de Vyrkhor, acima da linha onde a árvore cresce. Mora no vento e raramente desce dele.$DESC$,
comportamento=$DESC$Mora no alto e trata o resto de longe. Em volta dele o ar vira muralha: uma ventania que empurra, derruba e atrasa quem tenta chegar, de modo que ele controla quem sobe e quão depressa. Arremessa pedra do tamanho de homem em quem insiste. Não é cruel nem bondoso; é senhor do seu pico e desdenha de quem não pertence a ele. Foge pouco; o vento é dele.$DESC$,
organizacao=$DESC$Sozinho, senhor de um pico.$DESC$,
perigo=$DESC$Letal$DESC$,
behavior_archetype=$DESC$controller$DESC$,
morale_modifier=1,
morale_immune=false,
epigrafe=$DESC$A montanha estava calma. Quando começamos a subir, o vento começou a nos empurrar de volta, com vontade própria.$DESC$,
descricao=$DESC$É um gigante de pele pálida e olhos de céu nublado, alto como uma torre, que vive nos picos de Vyrkhor e carrega um cajado antigo cheio de poder. À volta dele o ar não é ar: é uma ventania presa que empurra, derruba e cega quem se aproxima, e ele a usa como muro e como mão, decidindo quem sobe. Quando o vento não basta, ele arranca uma pedra do tamanho de um homem e a joga reta. Não desce do alto à toa e não se mistura. Olha de cima, mede quem chega, e quase sempre acha que não vale o esforço de descer.$DESC$,
supersticao_popular=$DESC$Em Vyrkhor dizem que certos picos têm dono, e que o vento daquele pico tem vontade: empurra o forasteiro de volta, ladeira abaixo. O conselho dos guias é não subir contra o vento que pensa, e pedir licença antes, com oferenda deixada na pedra. Contam que ele despreza ladrão e poupa quem sobe humilde e de mãos limpas, e que insistir é virar alvo de pedra.$DESC$,
sinais_presenca=$DESC$Vento que sopra contra você de qualquer lado que você suba, forte e teimoso. Pedras grandes largadas longe de qualquer encosta de onde poderiam ter rolado. Nuvem parada num pico só, num dia limpo. O cheiro do ar mudando, frio e cortante, quando você se aproxima. Bichos de montanha que descem com pressa quando ele se irrita.$DESC$,
fraqueza_conhecida=$DESC$O povo sabe que ele manda no vento do pico dele e que subir contra esse vento é perder força à toa. Pedir licença, deixar oferenda, e não cobiçar o que é dele, costuma abrir caminho. Insistir na marra atrai pedra.$DESC$,
fraqueza_real=$DESC$A muralha dele é o vento em volta; tirado o vento, ele é só um gigante grande e vaidoso, longe da própria arma quando descido do alto. Não persegue ladeira abaixo e não larga o pico. O cajado é o que faz a ventania valer tanto: tomado ou quebrado o cajado, o muro de ar afrouxa e o senhor vira só tamanho. Quem não disputa o que é dele e sobe com respeito também passa.$DESC$,
descricao_sensorial=$DESC$O som é o uivo do vento que muda de direção para te barrar e o estalo de pedra arrancada. O cheiro é de ar de altura, frio, limpo e cortante. Ao toque, o vento dele empurra como mão grande e gela a pele exposta. Aos olhos, é um gigante pálido no alto, de olhos de céu fechado, com o ar torcendo visível em volta dele.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Não caça: cobra de quem sobe sem licença e cobiça o pico dele$DESC$, $DESC$Escaladores que insistem contra o vento de Vyrkhor$DESC$),
'predador', jsonb_build_array($DESC$Quem o tira do vento ou lhe toma o cajado; coisas maiores que descem do Clarão sobre Vyrkhor$DESC$),
'competidor', jsonb_build_array($DESC$Outros senhores das alturas de Vyrkhor que disputam pico e vento$DESC$, $DESC$Cornamenta-Severa$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presença dele diz que aquele pico tem dono, e que o vento ali obedece a uma vontade.$DESC$,
'evitado_por', jsonb_build_array($DESC$Guias que pedem licença, deixam oferenda e não cobiçam o que é do pico$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$Couro e pele pálida e grossa de altura$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Material (Superfície / agasalho e couraça que cortam o frio)$DESC$, 'risco', $DESC$Pesa muito para levar inteira.$DESC$),
jsonb_build_object('material', $DESC$Tendão grosso e osso longo do braço$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (corda forte, viga leve)$DESC$, 'risco', $DESC$Nenhum depois de seco.$DESC$),
jsonb_build_object('material', $DESC$Pedra de arremesso que ele carregava, lascada na queda$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (lastro, pedra de funda)$DESC$, 'risco', $DESC$Nenhum.$DESC$),
jsonb_build_object('material', $DESC$Lascas de osso e unha grossa$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (cabo, ponta)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Uivo do vento que muda de direção para te barrar e o estalo de pedra arrancada.$DESC$,
'cheiro', $DESC$Ar de altura, frio, limpo e cortante.$DESC$,
'quer', $DESC$Mandar no próprio pico e no vento dele. Decidir quem sobe, e atrasar ou derrubar quem não pediu licença.$DESC$,
'tipo_perigo', $DESC$Ambiental$DESC$,
'falas_exemplo', jsonb_build_array($DESC$Esse pico é meu, e o vento também. Você sobe quando eu deixar o vento deixar.$DESC$, $DESC$Volte. O ar já está te dizendo isso. Eu só repito.$DESC$, $DESC$(registro: fala alta e desdenhosa em língua de gigante e em comum, de quem fala de cima e raramente se dá ao trabalho)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Subir contra o vento dele sem pedir licença$DESC$, $DESC$Cobiçar ou tomar o cajado e o que é do pico$DESC$, $DESC$Insistir na escalada depois do aviso do vento$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Não desce do pico nem persegue ladeira abaixo$DESC$, $DESC$Afrouxa o vento quando o intruso recua e desce$DESC$, $DESC$Recolhe-se ao alto e à nuvem quando lhe tomam o cajado$DESC$),
'descoberta_fazendo', $DESC$No alto de um pico de Vyrkhor, em pé na nuvem parada, torcendo o vento em volta para barrar quem sobe, o cajado na mão.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Pedir licença e deixar oferenda na pedra antes de subir$DESC$, $DESC$Não cobiçar o cajado nem o que é do pico$DESC$, $DESC$Descer quando o vento avisa, em vez de insistir$DESC$, $DESC$Achar outra encosta, fora do vento dele$DESC$)
),
status_conversao='canonizada'
WHERE id=2371;

-- 704 · Tríade-Óssea · Engenho · tactical · Persistente · Vyrkhor · Eco · fala
UPDATE ref_criaturas SET
nome=$DESC$Tríade-Óssea$DESC$,
nome_ptbr=$DESC$Tríade-Óssea$DESC$,
slug=$DESC$triade-ossea$DESC$,
origem=$DESC$Cicatricial$DESC$,
andar_primario=$DESC$Eco$DESC$,
pilar_associado=$DESC$Engenho$DESC$,
continente=ARRAY[$DESC$Vyrkhor$DESC$]::text[],
habitat=$DESC$Necrópoles e fortes mortos de Vyrkhor, salões gelados onde há muitos ossos para reger. Fica no centro, longe da linha de frente.$DESC$,
comportamento=$DESC$São três crânios numa só vontade, um plano feito de três pareceres frios, e o corpo é só o que carrega isso. Não briga na frente: rege. Levanta e comanda os mortos do lugar, manda os ossos na sua direção e fica atrás, calculando, trocando a tática a cada baixa. Enquanto houver osso no salão, ele repõe a linha. Recua para pensar, nunca por medo.$DESC$,
organizacao=$DESC$Sozinho no centro, com a ossada do lugar inteira por exército.$DESC$,
perigo=$DESC$Letal$DESC$,
behavior_archetype=$DESC$tactical$DESC$,
morale_modifier=1,
morale_immune=false,
epigrafe=$DESC$A gente derrubava dez e levantavam doze. E no fundo do salão, três caveiras nos olhavam decidindo a próxima jogada.$DESC$,
descricao=$DESC$É uma figura de manto que carrega três crânios atentos, e os três pensam juntos, numa só vontade fria de três cabeças. Não é a força dele que mata: é o comando. Onde há mortos, ele os ergue e os move como peças, manda a ossada na frente e fica atrás, lendo a briga, mudando o plano a cada perda. Você derruba os servos e ele levanta outros, e mais outros, enquanto sobrar osso no salão. Esquiva do golpe que devia acertá-lo e aguenta o que não esquiva. Tirá-lo do tabuleiro é difícil, porque ele nunca está onde a luta está.$DESC$,
supersticao_popular=$DESC$Em Vyrkhor dizem que há salões onde os mortos não acabam, porque três caveiras no fundo os repõem sem parar. O conselho é não gastar a luta nos servos, que são infinitos, e furar até o que comanda, lá atrás. Contam que enquanto as três cabeças pensarem juntas, a maré de ossos não seca, e que separar ou calar os três crânios é o que encerra tudo.$DESC$,
sinais_presenca=$DESC$Mortos que se levantam de novo logo depois de caídos, sempre na direção certa. Ossos do salão sumindo da pilha para entrar na linha. Três pontos de luz fria parados no fundo, observando. Um frio de cripta que se aprofunda conforme você avança. O cheiro de osso velho remexido.$DESC$,
fraqueza_conhecida=$DESC$O povo sabe que brigar com os servos é perder tempo, porque ele repõe sem fim. Furar a linha e ir no que comanda, no fundo do salão, é o caminho. Quem chega às três caveiras corta a fonte da maré.$DESC$,
fraqueza_real=$DESC$A força dele é reger, não bater, e a regência mora nos três crânios pensando como um. Quebre a unidade, cale ou separe os três, e a maré de ossos para de obedecer e desaba. Ele esquiva e calcula, mas não suporta a luta no próprio corpo; por isso se mantém atrás. Quem ignora os servos, atravessa até ele e desfaz a tríade encerra de uma vez tudo que ele ergueu, porque os mortos eram a vontade dele emprestada, não deles.$DESC$,
descricao_sensorial=$DESC$O som é três vozes baixas falando em uníssono, um pouco fora de tempo, e o entrechocar de ossos que se erguem. O cheiro é de cripta gelada e osso velho remexido. Ao toque, o manto é frio e os crânios, lisos e secos como pedra. Aos olhos, é uma figura encapuzada de três caveiras vivas de atenção, parada no fundo do salão enquanto a ossada faz o trabalho.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Usa os vivos como peças a abater e os mortos como peças a mover$DESC$, $DESC$Saqueadores das necrópoles geladas de Vyrkhor$DESC$),
'predador', jsonb_build_array($DESC$Quem atravessa a maré e desfaz a tríade no fundo do salão$DESC$),
'competidor', jsonb_build_array($DESC$Outras vontades frias que regem os mortos de Vyrkhor$DESC$, $DESC$Cérebro-Murcho$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presença dele diz que naquele salão os mortos não acabam, porque há quem os reponha sem parar.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem não gasta a luta nos servos e fura direto para o que comanda$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$Os três crânios que pensam como um$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Engenho / reger muitos a partir de uma só vontade)$DESC$, 'risco', $DESC$Sussurram pareceres na cabeça de quem os guarda juntos.$DESC$),
jsonb_build_object('material', $DESC$O cajado de osso com que ele move a linha$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Engenho / comando à distância sobre o que não tem vontade)$DESC$, 'risco', $DESC$Faz mexer o osso parado em volta.$DESC$),
jsonb_build_object('material', $DESC$Manto frio que não esquenta$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (vestimenta de cripta, isolamento)$DESC$, 'risco', $DESC$Gela quem o veste por muito tempo.$DESC$),
jsonb_build_object('material', $DESC$Ossos de servo, gastos de tanto levantar$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (cola de osso, pó)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Três vozes baixas em uníssono, um pouco fora de tempo, e o entrechocar de ossos que se erguem.$DESC$,
'cheiro', $DESC$Cripta gelada e osso velho remexido.$DESC$,
'quer', $DESC$Reger. Mover os mortos como peças de uma só vontade fria, e nunca estar onde a luta está.$DESC$,
'tipo_perigo', $DESC$Persistente$DESC$,
'falas_exemplo', jsonb_build_array($DESC$Derrube quantos quiser. Eu tenho mais osso neste salão do que você tem fôlego.$DESC$, $DESC$Nós três já vimos como isto termina. Você ainda está calculando a primeira jogada.$DESC$, $DESC$(registro: três vozes no mesmo fôlego, levemente fora de compasso, frias como quem decide, não como quem sente)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Alguém entra no salão de muitos ossos que ele rege$DESC$, $DESC$Tentam atravessar até o fundo onde ele se posta$DESC$, $DESC$Ferem a ossada que ele move como linha$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Recua para o fundo para recalcular, nunca por medo$DESC$, $DESC$Cessa a regência quando a tríade é desfeita$DESC$, $DESC$Deixa o salão quando não sobra osso para erguer$DESC$),
'descoberta_fazendo', $DESC$No fundo de uma necrópole gelada de Vyrkhor, parado, erguendo e movendo a ossada do lugar contra quem entrou, calculando cada baixa.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Ignorar os servos e furar direto para a tríade no fundo$DESC$, $DESC$Calar ou separar os três crânios para derrubar a maré$DESC$, $DESC$Tirar a luta do salão cheio de ossos, onde ele repõe$DESC$, $DESC$Cortar o cajado de comando para soltar os mortos da vontade dele$DESC$)
),
status_conversao='canonizada'
WHERE id=704;

-- =====================================================================
-- GRUPO 3
-- =====================================================================

-- 776 · Ilhota-Funda · Corpo · defender · Oculto · Voranthar · Superfície · MUDO
UPDATE ref_criaturas SET
nome=$DESC$Ilhota-Funda$DESC$,
nome_ptbr=$DESC$Ilhota-Funda$DESC$,
slug=$DESC$ilhota-funda$DESC$,
origem=$DESC$Natural$DESC$,
andar_primario=$DESC$Superfície$DESC$,
pilar_associado=$DESC$Corpo$DESC$,
continente=ARRAY[$DESC$Voranthar$DESC$]::text[],
habitat=$DESC$Águas fundas e alagados de Voranthar, canais inundados das cidades mortas e o mar perto delas. Repousa no fundo e sobe pouco.$DESC$,
comportamento=$DESC$Passa o tempo no fundo, parada, parecendo pedra ou ilhota afundada coberta de lodo. Não caça com pressa: espera. Quando algo nada por cima, sobe calada e abocanha, e quem vê primeiro é a boca. Se a presa é grande demais ou a briga não vale, afunda de novo e some. Por baixo da casca, aguenta quase tudo.$DESC$,
organizacao=$DESC$Sozinha, dona de um trecho de fundo.$DESC$,
perigo=$DESC$Ameaça$DESC$,
behavior_archetype=$DESC$defender$DESC$,
morale_modifier=1,
morale_immune=false,
epigrafe=$DESC$A gente remou por cima daquela pedra musgosa a manhã toda. Na volta, a pedra abriu uma boca e levou o bote.$DESC$,
descricao=$DESC$É uma tartaruga velha do tamanho de um barco, de casca grossa coberta de lodo e craca, que parece uma ilhota afundada. Vive no fundo das águas de Voranthar e quase não se mexe. Não persegue nada: fica imóvel, confundida com o leito, e deixa a presa vir por cima. Então sobe sem aviso e morde, e a boca dela pega o que estava em cima sem entender o que era a pedra de baixo. Recolhida na casca, é quase impossível de ferir; quem não a incomoda nunca sabe que passou em cima dela. Forte e lenta, mais muralha do que caçadora.$DESC$,
supersticao_popular=$DESC$Em Voranthar dizem que nem toda ilhota dos canais inundados é ilhota, e que algumas têm boca. O conselho dos barqueiros é não pousar nem ancorar em pedra musgosa que não estava no mapa de ontem, e remar manso por cima do fundo escuro. Contam que ela não vai atrás de quem segue em frente, e que o perigo é só de quem para em cima dela.$DESC$,
sinais_presenca=$DESC$Uma ilhota ou pedra grande que mudou de lugar de uma semana para outra. Bolhas de fundo subindo onde a água deveria estar parada. Craca e lodo num formato grande demais para ser pedra. Peixe que some de um trecho fundo sem rede nenhuma. A água que afunda de leve, como se algo grande respirasse embaixo.$DESC$,
fraqueza_conhecida=$DESC$O povo sabe que ela não caça quem passa, só quem para em cima. Não ancorar em pedra duvidosa e seguir remando manso costuma bastar. Quem precisa enfrentá-la sabe que a casca não cede e mira a cabeça quando ela sobe.$DESC$,
fraqueza_real=$DESC$A defesa dela é a casca e o disfarce; a única abertura é a cabeça, e só quando ela sobe para morder. No fundo, recolhida, é muralha e não há por onde feri-la. Ela não persegue: tirada de cima dela, perde o interesse e afunda. Quem a deixa em paz nunca corre risco; quem precisa matá-la espera a boca abrir e acerta a cabeça no instante curto em que ela se expõe, porque o resto é pedra viva.$DESC$,
descricao_sensorial=$DESC$O som é o gorgolejo fundo da água deslocada e o ranger surdo de uma casca enorme subindo. O cheiro é de lodo, de craca e de água parada de cidade morta. Ao toque, é casca dura e fria, coberta de limo, viva por baixo do que parece pedra. Aos olhos, é uma ilhota musgosa que de repente tem cabeça e boca, e some deixando só ondas.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Peixe grande e o que nada por cima do fundo onde ela repousa$DESC$, $DESC$Barqueiros que ancoram na ilhota errada$DESC$),
'predador', jsonb_build_array($DESC$Quase nada a fere sob a casca; só quem acerta a cabeça quando ela sobe$DESC$),
'competidor', jsonb_build_array($DESC$Outros grandes do fundo dos canais de Voranthar$DESC$, $DESC$Braço-do-Fundo$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presença dela diz que aquele fundo guarda algo grande e antigo, e que nem toda ilhota é ilhota.$DESC$,
'evitado_por', jsonb_build_array($DESC$Barqueiros que não ancoram em pedra duvidosa e remam manso por cima do fundo escuro$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$A casca grossa, dura como muralha$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Material (Superfície / escudo e couraça pesada)$DESC$, 'risco', $DESC$Pesa demais para um homem só carregar.$DESC$),
jsonb_build_object('material', $DESC$Bico córneo da boca enorme$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (lâmina, raspador)$DESC$, 'risco', $DESC$Corta no fio mesmo solto.$DESC$),
jsonb_build_object('material', $DESC$Lodo e craca da casca$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (cola, vedação)$DESC$, 'risco', $DESC$Nenhum.$DESC$),
jsonb_build_object('material', $DESC$Carne dura de tartaruga velha$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (mantimento de viagem)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Gorgolejo fundo da água deslocada e o ranger surdo de uma casca enorme subindo.$DESC$,
'cheiro', $DESC$Lodo, craca e água parada de cidade morta.$DESC$,
'quer', $DESC$Ser deixada em paz no fundo. Abocanhar o que para em cima dela e voltar a afundar.$DESC$,
'tipo_perigo', $DESC$Oculto$DESC$,
'falas_exemplo', 'null'::jsonb,
'gatilhos_agressao', jsonb_build_array($DESC$Algo para ou ancora em cima dela, no fundo$DESC$, $DESC$Uma presa grande nada bem ao alcance da boca$DESC$, $DESC$Alguém cava ou fura o disfarce dela$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Afunda e some quando a briga não vale ou a presa é grande demais$DESC$, $DESC$Recolhe-se na casca e ignora quem segue em frente$DESC$, $DESC$Volta ao fundo quando tiram o peso de cima dela$DESC$),
'descoberta_fazendo', $DESC$Imóvel no fundo de um canal inundado de Voranthar, confundida com uma ilhota de lodo, à espera de que algo pare por cima.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Não ancorar nem pousar em pedra musgosa duvidosa$DESC$, $DESC$Remar manso e seguir em frente, sem parar sobre o fundo$DESC$, $DESC$Tirar o peso de cima e deixá-la afundar$DESC$, $DESC$Mapear e marcar a ilhota que anda, para os próximos desviarem$DESC$)
),
status_conversao='canonizada'
WHERE id=776;

-- 856 · Cruzado-Cinza · Sombra · tactical · Direto · Voranthar · Eco · fala
UPDATE ref_criaturas SET
nome=$DESC$Cruzado-Cinza$DESC$,
nome_ptbr=$DESC$Cruzado-Cinza$DESC$,
slug=$DESC$cruzado-cinza$DESC$,
origem=$DESC$Cicatricial$DESC$,
andar_primario=$DESC$Eco$DESC$,
pilar_associado=$DESC$Sombra$DESC$,
continente=ARRAY[$DESC$Voranthar$DESC$]::text[],
habitat=$DESC$Os antigos campos e fortalezas caídas de Voranthar, onde um comandante quebrou um juramento e a morte não o aposentou. Cavalga onde houve guerra e traição.$DESC$,
comportamento=$DESC$Foi general e ainda comanda. Não se esconde e não recua: vem de frente, com a espada que enche de pavor quem encara, e arremessa uma bola de fogo de cova que estoura e queima. Ergue e ordena os mortos do campo como tropa sua, mas prefere matar com as próprias mãos. Magia comum escorrega dele. Ferido, se refaz. Não foge; está preso à própria condenação.$DESC$,
organizacao=$DESC$Sozinho no comando, com os mortos do campo por tropa.$DESC$,
perigo=$DESC$Destruidor$DESC$,
behavior_archetype=$DESC$tactical$DESC$,
morale_modifier=0,
morale_immune=true,
epigrafe=$DESC$Ele veio reto, sem pressa, no meio da nossa flecharia, e nenhuma flecha importou. Quando ergueu a espada, metade de nós já queria correr.$DESC$,
descricao=$DESC$É um comandante morto de armadura cinzenta e queimada, que a quebra de um juramento prendeu de volta ao mundo. Cavalga e luta de frente, sem manha de esconde: a espada dele carrega um pavor que afrouxa as pernas de quem ousa encará-lo, e da mão livre ele lança uma bola de fogo amaldiçoado, fogo de cova que não apaga com água. Ao redor, ergue os mortos do velho campo e os manda como tropa, mas o gosto dele é cobrar com a própria lâmina. Reza e feitiço comum não o mordem. Cortado, ele se recompõe e volta à carga. Não tem para onde fugir: a condenação é o que o move.$DESC$,
supersticao_popular=$DESC$Em Voranthar contam que sobre os campos de traição ainda cavalga um general que a morte recusou, e que a espada dele espalha pavor e o fogo não se apaga. O conselho dos poucos que voltaram: não encarar a lâmina de frente, porque o medo é arma de verdade, e procurar o juramento quebrado que o prende, não a armadura. Dizem que feitiço escorrega dele, mas que luz pura o fere, e que enquanto a condenação durar, ele se levanta de novo.$DESC$,
sinais_presenca=$DESC$Mortos do velho campo se erguendo em ordem de tropa, em fileira. Um pavor sem causa que cresce conforme uma figura de armadura cinza se aproxima. Marcas de fogo que não se apagou, queimando frio no chão úmido. Cavalgada surda sem cavalo vivo à vista. Estandartes podres de um exército que perdeu, fincados de novo.$DESC$,
fraqueza_conhecida=$DESC$O povo sabe que a espada dele espalha pavor e que encará-la de frente é o erro. Luz pura o fere onde aço comum não. O conselho é não brigar com a tropa de mortos que ele ergue e ir atrás do que o prende, mas poucos chegam perto o bastante.$DESC$,
fraqueza_real=$DESC$Ele não está preso à armadura, e sim a um juramento quebrado que o condena a cavalgar; desfeita ou cumprida essa condenação, ele cai e não se levanta mais. O pavor da espada é a arma de abrir; a tropa de mortos, a parede; o fogo de cova, o castigo. Magia escorrega, mas luz pura o queima de verdade. Quem aguenta o medo, ignora os servos e ataca a condenação na raiz, com luz, encerra o general; quem briga com a armadura sozinha luta para sempre, porque ela se refaz.$DESC$,
descricao_sensorial=$DESC$O som é a cavalgada surda sem cavalo e o sussurro de pavor que a espada espalha antes de cair. O cheiro é de ferro queimado e de fogo que arde sem fumaça doce. Ao toque, a armadura é fria e a lâmina, gelada, mas o fogo de cova queima como brasa que não apaga. Aos olhos, é um general de armadura cinza queimada, alto na sela que não existe, de espada erguida sobre uma tropa de mortos.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Cobra com a lâmina de quem cruza o campo de traição$DESC$, $DESC$Exércitos vivos que ousam o terreno dele$DESC$),
'predador', jsonb_build_array($DESC$A luz pura que o fere; quem desfaz o juramento que o condena$DESC$),
'competidor', jsonb_build_array($DESC$Outros comandos mortos que disputam os campos caídos de Voranthar$DESC$, $DESC$Marechal-Roto$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presença dele diz que ali um general quebrou juramento, e que a morte não o aceitou.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem não encara a lâmina de frente e procura a condenação que o prende$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$A brasa de cova que ele lança e que não apaga com água$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Sombra / fogo amaldiçoado que arde frio e não cede)$DESC$, 'risco', $DESC$Queima sem fumaça quem a guarda e não morre na água.$DESC$),
jsonb_build_object('material', $DESC$A lâmina que espalha pavor em quem a encara$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Sombra / o medo posto como arma)$DESC$, 'risco', $DESC$Afrouxa as pernas de quem a desembainha sem têmpera.$DESC$),
jsonb_build_object('material', $DESC$Armadura cinza, queimada e fria$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (couraça pesada, marcada de guerra)$DESC$, 'risco', $DESC$Carrega o frio do dono.$DESC$),
jsonb_build_object('material', $DESC$Estandarte podre do exército caído$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (pano velho, marca)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Cavalgada surda sem cavalo e o sussurro de pavor que a espada espalha antes de cair.$DESC$,
'cheiro', $DESC$Ferro queimado e fogo que arde sem fumaça doce.$DESC$,
'quer', $DESC$Cumprir uma guerra que não terminou e cobrar a traição com a própria lâmina. Não largar o posto que a condenação lhe deu.$DESC$,
'tipo_perigo', $DESC$Direto$DESC$,
'falas_exemplo', jsonb_build_array($DESC$Eu já comandei mais homens do que você jamais verá. Não preciso da minha tropa para te derrubar, mas ela está aqui mesmo assim.$DESC$, $DESC$Corra, se as pernas deixarem. Elas raramente deixam.$DESC$, $DESC$(registro: voz de comando, fria e sem pressa, em comum e numa língua morta; ordena, não ameaça)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Alguém cruza o campo de traição que ele cavalga$DESC$, $DESC$Um exército ou grupo armado entra no terreno dele$DESC$, $DESC$Tentam tomar o estandarte ou o que ele guarda da velha guerra$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Não foge: cavalga até a condenação se cumprir$DESC$, $DESC$Cessa a carga quando não há mais quem enfrentar no campo$DESC$, $DESC$Cai e descansa quando o juramento que o prende é desfeito$DESC$),
'descoberta_fazendo', $DESC$Cavalgando reto por um campo caído de Voranthar, erguendo os mortos em fileira, a espada de pavor já na mão, contra quem entrou.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Não encarar a lâmina de frente, onde o pavor é a arma$DESC$, $DESC$Descobrir e desfazer o juramento quebrado que o prende$DESC$, $DESC$Afastar-se do campo de traição que ele cavalga$DESC$, $DESC$Usar luz pura, e não aço comum, se a briga for inevitável$DESC$)
),
status_conversao='canonizada'
WHERE id=856;

-- 2069 · Lasca-Gélida · Arcano · skirmisher · Persistente · Vyrkhor · Eco · fala
UPDATE ref_criaturas SET
nome=$DESC$Lasca-Gélida$DESC$,
nome_ptbr=$DESC$Lasca-Gélida$DESC$,
slug=$DESC$lasca-gelida$DESC$,
origem=$DESC$Cicatricial$DESC$,
andar_primario=$DESC$Eco$DESC$,
pilar_associado=$DESC$Arcano$DESC$,
continente=ARRAY[$DESC$Vyrkhor$DESC$]::text[],
habitat=$DESC$Estradas e passos nevados de Vyrkhor, hospedarias isoladas no frio. Anda entre viajantes como um deles, até escolher.$DESC$,
comportamento=$DESC$Parece gente comum, fala manso e educado, e se mistura no frio. Mas serve a uma conta sua de quem merece morrer, e quando decide, conjura lâminas de gelo do nada e golpeia rápido, bate e se afasta, bate e se afasta. No frio, qualquer corte que você abre nele fecha sozinho. Não tem pressa: o gelo é casa dele e o tempo, aliado.$DESC$,
organizacao=$DESC$Sozinho, infiltrado entre viajantes.$DESC$,
perigo=$DESC$Ameaça$DESC$,
behavior_archetype=$DESC$skirmisher$DESC$,
morale_modifier=2,
morale_immune=false,
epigrafe=$DESC$Dividiu o pão com a gente a noite inteira, calado e gentil. De manhã, três estavam mortos, e a neve nem tinha pisada além da nossa.$DESC$,
descricao=$DESC$Tem cara de viajante qualquer, voz mansa e modos bons, e por isso ninguém desconfia até tarde. Carrega na cabeça uma lista própria de quem, segundo ele, precisa morrer, e cumpre essa lista com calma de quem está certo. Quando age, faz nascer das mãos uma espada e uma adaga de gelo, e golpeia veloz, ferindo e recuando antes que você revide. No frio de Vyrkhor ele se cura: o talho que você abre se fecha de gelo enquanto vocês ainda lutam. Some na nevasca tão fácil quanto apareceu.$DESC$,
supersticao_popular=$DESC$Nas estradas nevadas de Vyrkhor avisam para desconfiar do companheiro educado demais que aparece no frio, porque alguns deles matam por uma conta que só eles entendem. O conselho é não dormir desguardado perto de estranho manso, e lembrar que ferir não basta, porque no gelo ele sara. Dizem que para encerrá-lo é preciso tirá-lo do frio ou queimá-lo, senão ele volta inteiro.$DESC$,
sinais_presenca=$DESC$Um viajante educado e calado demais que se junta ao grupo no frio. Lâminas de gelo achadas derretendo onde houve morte, sem ferreiro por perto. Cortes que não sangram do jeito certo, fechados de branco. Mortos escolhidos a dedo num acampamento, e os outros poupados. Pegada que some na nevasca sem deixar trilha de volta.$DESC$,
fraqueza_conhecida=$DESC$O povo sabe que ferir não resolve, porque no frio ele sara, e que o jeito é o fogo ou tirar a briga do gelo. Desconfiar do estranho gentil e não dormir desguardado é a primeira defesa. O segundo erro é tratar como duelo justo o que é execução.$DESC$,
fraqueza_real=$DESC$A vantagem dele é o frio: enquanto está no gelo, ele se regenera, e bate e foge para esticar a luta até você se cansar e ele sarar. Tirado o frio, ou tocado pelo fogo, as feridas param de fechar e ele vira só um homem com facas. Ele tem motivo, não fúria; quem entende a conta dele às vezes sai da lista, e quem o leva para perto de uma fogueira grande, ou de um lugar quente, tira dele a única coisa que o faz invencível na demora.$DESC$,
descricao_sensorial=$DESC$O som é o estalo fino do gelo formando lâmina e a fala mansa que não combina com a faca. O cheiro é de neve limpa e de sangue que congela antes de escorrer. Ao toque, as armas dele queimam de tão frias, e a pele dele é fria como a do morto. Aos olhos, é um viajante comum até as mãos brilharem de gelo, e então é tarde.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Os que ele põe na própria lista de quem merece morrer$DESC$, $DESC$Viajantes desguardados nas estradas nevadas de Vyrkhor$DESC$),
'predador', jsonb_build_array($DESC$O fogo e o calor, que impedem o gelo de fechar suas feridas$DESC$),
'competidor', jsonb_build_array($DESC$Outros caçadores frios das estradas de Vyrkhor$DESC$, $DESC$Refugo-Gélido$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presença dele diz que alguém no grupo foi marcado por uma sentença que não é sua para entender.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem desconfia do estranho gentil no frio e dorme guardado perto do fogo$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$O frio preso no peito dele, que fecha as próprias feridas$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Arcano / regeneração pelo gelo, conjuro de lâmina fria)$DESC$, 'risco', $DESC$Gela por dentro quem o carrega longe do frio.$DESC$),
jsonb_build_object('material', $DESC$Estilha das lâminas de gelo que ele conjura$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Arcano / armas frias temporárias)$DESC$, 'risco', $DESC$Derrete e some se não mantida no gelo.$DESC$),
jsonb_build_object('material', $DESC$A lista de nomes que ele guardava$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (pista de quem ele caçava e por quê)$DESC$, 'risco', $DESC$Põe o leitor a se perguntar se está nela.$DESC$),
jsonb_build_object('material', $DESC$Capa de viajante, comum e gasta$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (agasalho, disfarce)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Estalo fino do gelo formando lâmina e a fala mansa que não combina com a faca.$DESC$,
'cheiro', $DESC$Neve limpa e sangue que congela antes de escorrer.$DESC$,
'quer', $DESC$Cumprir a própria conta de quem merece morrer, com calma, e deixar o frio fechar tudo que o feriu.$DESC$,
'tipo_perigo', $DESC$Persistente$DESC$,
'falas_exemplo', jsonb_build_array($DESC$Não é nada pessoal contra você. Só contra ele. Fique fora disto e dorme em paz.$DESC$, $DESC$Pode me cortar. A neve costura melhor do que qualquer médico que você conheça.$DESC$, $DESC$(registro: fala educada, baixa e calma, de quem se acha justo; nunca levanta a voz, nem para matar)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Alguém da lista dele está ao alcance$DESC$, $DESC$Tentam impedir uma execução que ele julga certa$DESC$, $DESC$O desmascaram no meio do grupo$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Some na nevasca quando a conta do dia está feita$DESC$, $DESC$Recua para o frio quando ferido, para sarar e voltar$DESC$, $DESC$Abandona o alvo se chega fogo grande ou calor que impede a cura$DESC$),
'descoberta_fazendo', $DESC$Misturado a um grupo de viajantes numa hospedaria ou acampamento nevado de Vyrkhor, gentil e calado, decidindo quem na sala está na lista dele.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Não dormir desguardado perto do estranho gentil$DESC$, $DESC$Descobrir a conta dele e provar que não se está nela$DESC$, $DESC$Levar a briga para perto de fogo grande, onde ele não sara$DESC$, $DESC$Tirá-lo do frio antes de tudo$DESC$)
),
status_conversao='canonizada'
WHERE id=2069;

-- 1143 · Charada-Velada · Espírito · controller · Condicional · Voranthar · Clarão · fala
UPDATE ref_criaturas SET
nome=$DESC$Charada-Velada$DESC$,
nome_ptbr=$DESC$Charada-Velada$DESC$,
slug=$DESC$charada-velada$DESC$,
origem=$DESC$Cicatricial$DESC$,
andar_primario=$DESC$Clarão$DESC$,
pilar_associado=$DESC$Espírito$DESC$,
continente=ARRAY[$DESC$Voranthar$DESC$]::text[],
habitat=$DESC$Limiares e portais do Clarão sobre Voranthar, soleiras de ruína onde o que está além é guardado por enigma. Fica na passagem, não no caminho.$DESC$,
comportamento=$DESC$Guarda uma passagem com uma pergunta. Não ataca quem chega: propõe um enigma, e a régua é a resposta. Quem responde certo, ou se vai com humildade, passa intacto. Quem mente, força a passagem, ou erra com arrogância, recebe o brado dela, um rugido que rasga por dentro a quem desafia. É paciente, antiga, e enxerga a treta antes de você falar.$DESC$,
organizacao=$DESC$Sozinha, guarda de um limiar.$DESC$,
perigo=$DESC$Letal$DESC$,
behavior_archetype=$DESC$controller$DESC$,
morale_modifier=0,
morale_immune=true,
epigrafe=$DESC$Ela fez uma pergunta. Eu menti achando que era esperto. O som que ela soltou eu ainda ouço, e metade dos meus não ouvem mais nada.$DESC$,
descricao=$DESC$Tem corpo de fera grande e cara que não se lê, e guarda uma passagem do Clarão com um enigma na boca. Não é monstro de emboscada: senta na soleira e espera, e a quem chega oferece a pergunta antes da garra. Responda com verdade, ou recue com respeito, e ela deixa passar. Minta, force, erre com arrogância, e ela solta um brado que não fere a pele e sim o que está por dentro, dobrando e despedaçando a vontade de quem a desafiou. Enxerga a mentira no rosto antes de ouvi-la. Magia direta escorrega dela, e poucos a movem do limiar que ela guarda.$DESC$,
supersticao_popular=$DESC$Em Voranthar dizem que certas soleiras do claro têm guarda de enigma, e que a senha é a verdade, não a força. O conselho dos que sabem é responder honesto ou dar meia-volta humilde, nunca mentir nem arrombar, porque o brado dela quebra quem desafia. Contam que ela não persegue quem desiste, e que o pior erro é tratar de esperteza quem já viu todas as espertezas.$DESC$,
sinais_presenca=$DESC$Uma soleira ou portal antigo guardado por uma figura grande e parada que faz uma pergunta. Silêncio de Clarão, luz limpa demais, em volta do limiar. Corpos de quem forçou a passagem, sem ferida por fora e quebrados por dentro. Pegadas que chegam ao portal e não passam. A sensação de ser lido antes de abrir a boca.$DESC$,
fraqueza_conhecida=$DESC$O povo sabe que a senha é a verdade: responder honesto ou recuar com respeito passa; mentir ou forçar mata. Não tratar com esperteza quem enxerga a treta é a regra. Quem desiste em paz não é perseguido.$DESC$,
fraqueza_real=$DESC$A arma dela é condicional: o brado só cai sobre quem mente, força ou erra com arrogância, nunca sobre quem responde com verdade ou se afasta humilde. Ela guarda um limiar e não o larga para caçar. Magia escorrega, mas ela respeita uma resposta certa acima de tudo, porque é o que ela guarda. Quem entende que é um guarda de senha, e não um bicho, e paga com verdade ou humildade, atravessa vivo; quem arromba encontra o único golpe dela, e é o que basta.$DESC$,
descricao_sensorial=$DESC$O som é uma voz antiga e clara que pergunta, e, se você erra, um brado que se ouve por dentro dos ossos. O cheiro é de ar limpo de Clarão e pedra velha de limiar. Ao toque, o pelo é frio e a garra, dura; mas quase ninguém chega a tocá-la. Aos olhos, é uma fera grande de rosto ilegível, sentada na soleira, que parece já saber o que você vai dizer.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Cobra de quem mente ou força a passagem que ela guarda$DESC$, $DESC$Arrombadores de limiares do Clarão em Voranthar$DESC$),
'predador', jsonb_build_array($DESC$Nada a tira do limiar; ela só cede a uma resposta verdadeira$DESC$),
'competidor', jsonb_build_array($DESC$Outras guardas do Clarão sobre Voranthar que zelam por outras passagens$DESC$, $DESC$Litania-Funda$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presença dela diz que aquela passagem leva a algo guardado, e que a senha é a verdade.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem responde honesto ou dá meia-volta humilde, sem tentar enganá-la$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$O eco do brado que quebra quem desafia, preso num cristal$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Clarão / a palavra que dobra a vontade de quem mente)$DESC$, 'risco', $DESC$Quebra por dentro quem o desperta sem ter a verdade na boca.$DESC$),
jsonb_build_object('material', $DESC$A pena de Clarão que ela solta no limiar$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Clarão / o que separa verdade de mentira)$DESC$, 'risco', $DESC$Arde na mão de quem mente ao segurá-la.$DESC$),
jsonb_build_object('material', $DESC$Os enigmas antigos gravados na soleira$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (saber velho, senha de passagem)$DESC$, 'risco', $DESC$Atraem quem quer forçar o que está além.$DESC$),
jsonb_build_object('material', $DESC$Pedra de limiar, gasta de tanto guardar$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (marco, soleira)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Voz antiga e clara que pergunta, e, se você erra, um brado que se ouve por dentro dos ossos.$DESC$,
'cheiro', $DESC$Ar limpo de Clarão e pedra velha de limiar.$DESC$,
'quer', $DESC$Guardar a passagem com um enigma. Deixar passar quem traz verdade e quebrar quem mente ou força.$DESC$,
'tipo_perigo', $DESC$Condicional$DESC$,
'falas_exemplo', jsonb_build_array($DESC$Antes de passar, responda. E pense bem: eu vejo a resposta no seu rosto antes de ela chegar à sua boca.$DESC$, $DESC$Você pode recuar agora, com honra. Essa porta também é uma resposta.$DESC$, $DESC$(registro: voz antiga, clara e sem pressa, em comum e na língua do claro; pergunta uma vez e pesa o silêncio)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Mentir na resposta ao enigma dela$DESC$, $DESC$Forçar ou arrombar a passagem que ela guarda$DESC$, $DESC$Tentar enganá-la com esperteza arrogante$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Não foge: guarda o limiar até receber resposta verdadeira$DESC$, $DESC$Cessa o brado quando o desafiante recua humilde$DESC$, $DESC$Deixa em paz quem dá meia-volta sem forçar$DESC$),
'descoberta_fazendo', $DESC$Sentada na soleira de um portal do Clarão em Voranthar, parada, propondo o enigma a quem se aproxima da passagem.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Responder o enigma com verdade$DESC$, $DESC$Recuar com humildade, sem forçar a passagem$DESC$, $DESC$Não tentar enganá-la com esperteza$DESC$, $DESC$Buscar outra entrada, deixando o limiar guardado$DESC$)
),
status_conversao='canonizada'
WHERE id=1143;

-- 1977 · Ossada-Rolante · Engenho · brute · Ambiental · Thornmarak · Eco · MUDO
UPDATE ref_criaturas SET
nome=$DESC$Ossada-Rolante$DESC$,
nome_ptbr=$DESC$Ossada-Rolante$DESC$,
slug=$DESC$ossada-rolante$DESC$,
origem=$DESC$Cicatricial$DESC$,
andar_primario=$DESC$Eco$DESC$,
pilar_associado=$DESC$Engenho$DESC$,
continente=ARRAY[$DESC$Thornmarak$DESC$]::text[],
habitat=$DESC$Túmulos coletivos e ossários de Thornmarak, criptas onde sobrou osso para sobra. Habita onde há ossada bastante para se refazer.$DESC$,
comportamento=$DESC$É uma máquina feita de muitos ossos, montada por algo que não pensa, e roda como avalanche. Vem rolando e esmaga, desfaz quem está no caminho, e quando ferida, se desmonta e remonta com os ossos soltos em volta, sempre maior do que devia ser. Despeja uma avalanche de ossos que enche o espaço e soterra. Não há manha: há massa, peso e o chão virando armadilha de osso.$DESC$,
organizacao=$DESC$Sozinha, dona de um ossário.$DESC$,
perigo=$DESC$Ameaça$DESC$,
behavior_archetype=$DESC$brute$DESC$,
morale_modifier=0,
morale_immune=true,
epigrafe=$DESC$A gente quebrou a coisa em três. Os três montes de osso se juntaram de novo, mais um pedaço de quem a gente perdeu.$DESC$,
descricao=$DESC$É um amontoado de ossos de muitos mortos, prensados numa forma grande que roda e esmaga, movida por algo cego que só sabe avançar e crescer. Vem como pedra ladeira abaixo e soterra; despeja de si uma avalanche de ossos que cobre o chão e prende as pernas. Quebrada, não morre: os pedaços se reúnem, juntam o osso solto do ossário em volta, e ela se levanta maior, com os mortos que colheu somados aos que já era. O espaço todo onde ela está vira chão de osso instável, e parar ali é afundar.$DESC$,
supersticao_popular=$DESC$Em Thornmarak avisam para não brigar com a coisa de osso dentro do ossário dela, porque ali ela tem com que se refazer sem fim. O conselho é arrastá-la para fora, para longe das pilhas de osso, e ali quebrá-la, porque sem osso solto em volta ela não remonta. Contam que pancada de marreta a parte melhor do que corte, mas que dentro da cripta cheia isso não basta.$DESC$,
sinais_presenca=$DESC$Ossários e túmulos coletivos revirados, com osso faltando das pilhas. Um chão de cripta coberto de ossos soltos que rangem sob o pé. Trilha larga de esmagamento, como de pedra rolada. Estalido seco de osso se prensando e se juntando. Restos de quem entrou somados à massa, ainda reconhecíveis aqui e ali.$DESC$,
fraqueza_conhecida=$DESC$O povo sabe que dentro do ossário ela se refaz sem fim, e que o jeito é arrastá-la para fora, longe do osso solto. Pancada de contusão a parte melhor que lâmina. Quem briga com ela na cripta cheia briga para sempre.$DESC$,
fraqueza_real=$DESC$Ela não tem mente nem medo: é uma máquina que só roda, esmaga e remonta enquanto houver osso por perto para colher. Tirada do ossário, sem osso solto em volta, ela quebra e não se reúne mais. A avalanche dela faz do chão uma armadilha, mas é o lugar que a sustenta, não ela mesma. Quem a leva ao aberto, ou ao terreno limpo de osso, e a desmonta com pancada pesada, encerra a máquina; quem fica na cripta alimenta o que tenta matar.$DESC$,
descricao_sensorial=$DESC$O som é o ranger e o estalo de muitos ossos se prensando, e o rolo surdo de uma massa que avança. O cheiro é de osso seco e pó de cripta, sem podre, só velho. Ao toque, é osso prensado, frio e cortante de borda, áspero como cascalho grande. Aos olhos, é um monte rolante de ossos de muita gente, sem forma fixa, que se refaz maior cada vez que se quebra.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Esmaga e colhe o osso de quem cai no caminho$DESC$, $DESC$Saqueadores dos ossários de Thornmarak$DESC$),
'predador', jsonb_build_array($DESC$Terreno limpo de osso, onde ela não remonta; pancada pesada longe das pilhas$DESC$),
'competidor', jsonb_build_array($DESC$Outras coisas que habitam as criptas de Thornmarak e disputam os mortos$DESC$, $DESC$Talha-Pedra$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presença dela diz que aquele ossário foi mexido, e que os mortos ali não ficam quietos nem inteiros.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem a arrasta para fora da cripta antes de enfrentá-la, longe do osso solto$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$O eixo cego que prensa e move a massa de osso$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Engenho / mover e remontar muitas peças sem vontade)$DESC$, 'risco', $DESC$Junta na mão o osso solto que estiver por perto.$DESC$),
jsonb_build_object('material', $DESC$Ossos longos prensados, duros como viga$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Engenho / armação que se refaz, estrutura de carga)$DESC$, 'risco', $DESC$Tentam se encaixar com outro osso à toa.$DESC$),
jsonb_build_object('material', $DESC$Pó de osso prensado da avalanche$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (cimento de osso, lastro)$DESC$, 'risco', $DESC$Range e assenta sozinho.$DESC$),
jsonb_build_object('material', $DESC$Cacos de osso comum$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (cal, enchimento)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Ranger e estalo de muitos ossos se prensando, e o rolo surdo de uma massa que avança.$DESC$,
'cheiro', $DESC$Osso seco e pó de cripta, sem podre, só velho.$DESC$,
'quer', $DESC$Rolar, esmagar e crescer. Colher o osso do que cai e o do lugar para se refazer sempre maior.$DESC$,
'tipo_perigo', $DESC$Ambiental$DESC$,
'falas_exemplo', 'null'::jsonb,
'gatilhos_agressao', jsonb_build_array($DESC$Alguém entra no ossário onde ela se refaz$DESC$, $DESC$Um movimento no chão de osso que ela domina$DESC$, $DESC$Tentam levar os mortos das pilhas dela$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Não teme: roda e remonta enquanto houver osso$DESC$, $DESC$Cessa quando a quebram longe de qualquer osso solto$DESC$, $DESC$Para de crescer quando não sobra ossada em volta para colher$DESC$),
'descoberta_fazendo', $DESC$Rolando devagar por uma cripta de Thornmarak, colhendo osso solto do chão, refazendo-se sobre os mortos do ossário.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Arrastá-la para fora da cripta, longe do osso solto, antes de quebrá-la$DESC$, $DESC$Lutar em terreno limpo de osso, onde ela não remonta$DESC$, $DESC$Usar pancada pesada, não lâmina$DESC$, $DESC$Não pisar parado no chão de osso que ela espalha$DESC$)
),
status_conversao='canonizada'
WHERE id=1977;

-- =====================================================================
-- GRUPO 4
-- =====================================================================

-- 1936 · Faixa-Peçonha · Corpo · ambusher · Oculto · Thornmarak · Superfície · MUDO
UPDATE ref_criaturas SET
nome=$DESC$Faixa-Peçonha$DESC$,
nome_ptbr=$DESC$Faixa-Peçonha$DESC$,
slug=$DESC$faixa-peconha$DESC$,
origem=$DESC$Natural$DESC$,
andar_primario=$DESC$Superfície$DESC$,
pilar_associado=$DESC$Corpo$DESC$,
continente=ARRAY[$DESC$Thornmarak$DESC$]::text[],
habitat=$DESC$Baixadas úmidas e matagais de Thornmarak, sob folha caída e raiz, perto da água parada. Some no chão do mato como se fosse só faixa de luz e sombra.$DESC$,
comportamento=$DESC$Não persegue: espera, enrodilhada e quieta, confundida com o chão riscado de luz. Quando algo passa ao alcance, dá o bote curto e crava a peçonha, e recua para o esconderijo. A arma é a surpresa e o veneno; ela não briga ao aberto. Deixa o passo dar errado e a presa carregar o veneno até cair.$DESC$,
organizacao=$DESC$Sozinha, dona de um trecho de mato.$DESC$,
perigo=$DESC$Ameaça$DESC$,
behavior_archetype=$DESC$ambusher$DESC$,
morale_modifier=1,
morale_immune=false,
epigrafe=$DESC$Eu jurava que o chão era só sombra de folha. A sombra mordeu o tornozelo do guia e sumiu.$DESC$,
descricao=$DESC$É uma cobra grande de faixas vivas, vermelhas, pretas e claras, que de tão riscada some no chão de folha e luz quebrada do mato. Não tem força nem pressa: tem o bote curto e a peçonha. Fica enrodilhada e parada onde você não a vê, e quando o pé chega perto, crava as presas num lance só e se recolhe. O veneno faz o resto, devagar, enquanto ela já voltou ao esconderijo. Cega de olhos, sente o calor e o passo pela terra. No aberto e à vista, é tímida e foge; no escondido, é só esperar você errar onde pisa.$DESC$,
supersticao_popular=$DESC$Nas baixadas de Thornmarak avisam para olhar onde se pisa e não meter a mão sob folha e raiz, porque algumas faixas do chão mordem. O conselho é bater o caminho com vara antes de passar, e andar calçado e atento perto de água parada. Dizem que ela não vai atrás de ninguém, e que quase toda mordida é de quem pisou em cima sem ver.$DESC$,
sinais_presenca=$DESC$Faixas de cor que não combinam com o chão, vistas tarde demais. Bichos pequenos mortos sem ferida grande, só dois furos. Trilha fina e ondulada no pó, sumindo sob folha. Muda de pele largada, riscada, presa em raiz. O silêncio raso de um trecho de mato onde os outros bichos não chegam.$DESC$,
fraqueza_conhecida=$DESC$O povo sabe que ela morde quem pisa em cima e não persegue. Bater o caminho com vara, andar calçado e olhar o chão tira quase todo o risco. Quem a vê a tempo só desvia, porque ela prefere fugir a brigar.$DESC$,
fraqueza_real=$DESC$A força dela é só o disfarce e o bote curto; vista a tempo, ela é frágil e medrosa e some. Não tem fôlego de perseguir nem de brigar ao aberto. Quem anda atento ao chão, prova o caminho antes e não enfia a mão em buraco nunca chega a ser mordido; e a mordida, pega cedo, com o veneno conhecido, se trata. O perigo todo está em não vê-la a tempo.$DESC$,
descricao_sensorial=$DESC$O som é quase nenhum, um roçar seco de escama em folha, e nada mais. O cheiro é de mato úmido e de terra de água parada, sem cheiro próprio. Ao toque, é fria e seca, lisa de escama, e some da mão num puxão. Aos olhos, é uma faixa de cores no chão que você só entende ser cobra quando ela já mordeu.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Bichos pequenos e médios que passam ao alcance do bote$DESC$, $DESC$O pé de quem anda distraído pelo mato$DESC$),
'predador', jsonb_build_array($DESC$Aves e bichos que comem cobra; quem a vê a tempo e abre caminho$DESC$),
'competidor', jsonb_build_array($DESC$Outras peçonhas das baixadas de Thornmarak$DESC$, $DESC$Espiral-Lodosa$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presença dela diz que aquele trecho de mato úmido pede olho no chão e vara na frente.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem bate o caminho com vara, anda calçado e olha onde pisa$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$As glândulas de peçonha, cheias$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Material (Superfície / veneno para lâmina e armadilha, e o antídoto dele)$DESC$, 'risco', $DESC$Mata pelo corte se manuseada sem cuidado.$DESC$),
jsonb_build_object('material', $DESC$Pele de faixas vivas, riscada$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (couro vistoso, disfarce de mato)$DESC$, 'risco', $DESC$Nenhum depois de seca.$DESC$),
jsonb_build_object('material', $DESC$Presas curvas e finas$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (agulha, fino furador)$DESC$, 'risco', $DESC$Guardam veneno na ponta por um tempo.$DESC$),
jsonb_build_object('material', $DESC$Carne magra de cobra$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (mantimento, isca)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Quase nenhum: um roçar seco de escama em folha.$DESC$,
'cheiro', $DESC$Mato úmido e terra de água parada, sem cheiro próprio.$DESC$,
'quer', $DESC$Não ser vista. Cravar a peçonha em quem chega perto e voltar ao esconderijo enquanto o veneno trabalha.$DESC$,
'tipo_perigo', $DESC$Oculto$DESC$,
'falas_exemplo', 'null'::jsonb,
'gatilhos_agressao', jsonb_build_array($DESC$Um pé ou mão chega ao alcance do bote dela$DESC$, $DESC$Algo pisa em cima do esconderijo$DESC$, $DESC$Calor de presa passa rente ao chão$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Recolhe-se e some quando é vista a tempo$DESC$, $DESC$Foge do aberto e da luz para o mato fechado$DESC$, $DESC$Abandona o lugar quando o trecho fica movimentado demais$DESC$),
'descoberta_fazendo', $DESC$Enrodilhada e imóvel sob folha e luz quebrada numa baixada de Thornmarak, confundida com o chão, à espera de um passo errado.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Bater o caminho com vara e olhar o chão antes de passar$DESC$, $DESC$Desviar do trecho dela, que não persegue$DESC$, $DESC$Andar calçado e não enfiar a mão em buraco$DESC$, $DESC$Tratar cedo a mordida com o antídoto conhecido$DESC$)
),
status_conversao='canonizada'
WHERE id=1936;

-- 1935 · Vasa-Salgada · Sombra · controller · Ambiental · Voranthar · Eco · MUDO
UPDATE ref_criaturas SET
nome=$DESC$Vasa-Salgada$DESC$,
nome_ptbr=$DESC$Vasa-Salgada$DESC$,
slug=$DESC$vasa-salgada$DESC$,
origem=$DESC$Cicatricial$DESC$,
andar_primario=$DESC$Eco$DESC$,
pilar_associado=$DESC$Sombra$DESC$,
continente=ARRAY[$DESC$Voranthar$DESC$]::text[],
habitat=$DESC$Canais e portos inundados das cidades mortas de Voranthar, água salobra parada sobre ruas afogadas. Vive submersa, no escuro do fundo.$DESC$,
comportamento=$DESC$Arrasta para baixo. Em volta dela a água fica fria de doer e escura de tinta morta, e quem entra perde o calor e a vista de uma vez. Agarra com um tentáculo que suga a vida e corta com um espadão de afogado, mas a arma de verdade é a água: ela faz do trecho alagado um poço onde você gela, cega e afunda. Está presa a outros afogados, amarrada ao fundo. Não foge: pertence àquela água.$DESC$,
organizacao=$DESC$Atada a outros afogados, no fundo de uma rua submersa.$DESC$,
perigo=$DESC$Letal$DESC$,
behavior_archetype=$DESC$controller$DESC$,
morale_modifier=0,
morale_immune=true,
epigrafe=$DESC$A água esfriou de repente e ficou preta como tinta. Quando o Edo gritou, já estava sendo levado para baixo, e o frio chegou na gente antes do medo.$DESC$,
descricao=$DESC$É um afogado que a morte amarrou ao fundo de uma cidade submersa, e ele faz da água em volta a arma dele. Onde ele está, a água esfria a doer e escurece de uma tinta morta que cega, e quem entra perde o calor e a direção. Agarra com um tentáculo frio que puxa a vida para fora e golpeia com um espadão enferrujado, mas o que mata mesmo é o trecho alagado virar poço de frio e breu. Está atado a outros afogados, peso no fundo, e não sobe além da água que é dele. Magia velha não o solta; a água o sustenta.$DESC$,
supersticao_popular=$DESC$Em Voranthar dizem que as ruas afogadas das cidades mortas têm dono, e que a água que esfria de repente e fica preta é aviso de que ele está perto. O conselho é não nadar nem vadear no escuro da cheia, e nunca de noite, e sair da água ao primeiro frio anormal. Contam que ele não deixa a água dele, e que em terra seca o perigo acaba.$DESC$,
sinais_presenca=$DESC$Água que esfria de repente num trecho só, num dia sem motivo. Uma nuvem de tinta preta subindo do fundo sem peixe morto à vista. Afogados antigos boiando atados uns aos outros, parados. Frio que sai da água e sobe pela margem. O silêncio embaixo, onde nem peixe fica.$DESC$,
fraqueza_conhecida=$DESC$O povo sabe que o perigo é a água dele, fria e preta, e que sair dela acaba com quase tudo. Não vadear no escuro da cheia e fugir ao primeiro frio anormal é a regra. Em terra, dizem, ele não alcança.$DESC$,
fraqueza_real=$DESC$A arma dele é fazer da água um poço de frio e cegueira; tirado da água, ele é um afogado lento e pesado, atado ao próprio fundo, longe do que o torna mortal. Não persegue para a terra e não larga a cidade submersa. Quem fica fora da água dele, ou quem o traz para o seco e o enfrenta longe do frio e da tinta, encerra o perigo; quem entra no escuro alagado luta no terreno que é todo dele.$DESC$,
descricao_sensorial=$DESC$O som é o gorgolejo surdo da água funda e um arrasto de correntes no fundo. O cheiro é de sal podre, lodo e ferrugem de cidade afogada. Ao toque, a água dele gela a doer e o tentáculo puxa frio para dentro da carne. Aos olhos, no breu da tinta quase nada se vê: um vulto inchado de afogado e o brilho sem cor de um espadão.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Quem nada ou vadeia a água escura das cidades afogadas de Voranthar$DESC$, $DESC$Nadadores pegos no frio súbito$DESC$),
'predador', jsonb_build_array($DESC$A terra seca, longe da água dele; quem o tira do alagado$DESC$),
'competidor', jsonb_build_array($DESC$Outros afogados e coisas do fundo de Voranthar que disputam as ruas submersas$DESC$, $DESC$Hóspede-Pálido$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presença dele diz que aquela água parada das ruínas guarda morte, e que esfria antes de levar.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem não vadeia o escuro da cheia e sai da água ao primeiro frio anormal$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$A tinta morta que escurece e gela a água em volta$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Sombra / breu e frio que cegam e roubam o calor de uma área)$DESC$, 'risco', $DESC$Esfria e escurece o que estiver perto na bolsa.$DESC$),
jsonb_build_object('material', $DESC$O tentáculo frio que suga a vida$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Sombra / o que puxa o calor e o vigor de quem agarra)$DESC$, 'risco', $DESC$Esfria a mão que o segura e não solta fácil.$DESC$),
jsonb_build_object('material', $DESC$Espadão de afogado, enferrujado e gelado$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (lâmina pesada, marcada de água)$DESC$, 'risco', $DESC$Sempre úmida e fria.$DESC$),
jsonb_build_object('material', $DESC$Correntes e pesos do fundo que o atavam$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (ferro, lastro)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Gorgolejo surdo da água funda e um arrasto de correntes no fundo.$DESC$,
'cheiro', $DESC$Sal podre, lodo e ferrugem de cidade afogada.$DESC$,
'quer', $DESC$Levar para baixo. Fazer da própria água um poço de frio e breu onde tudo que entra afunda.$DESC$,
'tipo_perigo', $DESC$Ambiental$DESC$,
'falas_exemplo', 'null'::jsonb,
'gatilhos_agressao', jsonb_build_array($DESC$Alguém entra na água escura que é dele$DESC$, $DESC$Um nadador ou bote cruza o trecho alagado$DESC$, $DESC$Tentam tirar algo do fundo que ele guarda$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Não foge: pertence à água e não a deixa$DESC$, $DESC$Recolhe-se ao fundo quando tiram a presa do alagado$DESC$, $DESC$Cessa quando o trecho de água esvazia ou seca$DESC$),
'descoberta_fazendo', $DESC$Submerso no escuro de uma rua afogada de Voranthar, atado a outros afogados, esfriando e escurecendo a água em torno à espera de quem entra.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Não vadear nem nadar no escuro da cheia$DESC$, $DESC$Sair da água ao primeiro frio anormal$DESC$, $DESC$Atraí-lo ou puxá-lo para a terra seca, longe da água dele$DESC$, $DESC$Contornar por terra a rua afogada$DESC$)
),
status_conversao='canonizada'
WHERE id=1935;

-- 623 · Conluio-Calado · Arcano · tactical · Condicional · Thornmarak · Eco · fala
UPDATE ref_criaturas SET
nome=$DESC$Conluio-Calado$DESC$,
nome_ptbr=$DESC$Conluio-Calado$DESC$,
slug=$DESC$conluio-calado$DESC$,
origem=$DESC$Cicatricial$DESC$,
andar_primario=$DESC$Eco$DESC$,
pilar_associado=$DESC$Arcano$DESC$,
continente=ARRAY[$DESC$Thornmarak$DESC$]::text[],
habitat=$DESC$Ruínas e covis sob Thornmarak, salas escuras de onde se comanda sem aparecer. Fica no fundo, atrás dos que manda na frente.$DESC$,
comportamento=$DESC$Manda, não briga. Fica no escuro, que para ele é claro, e move servos e tramas à frente, deixando os outros levarem o golpe. Só age direto quando alguém quebra o plano dele ou chega perto demais: aí lança raios de cova à distância e arranha com a mão que mata, e logo recua para trás dos seus. É calculista e covarde, e a força dele é a trama, não o corpo.$DESC$,
organizacao=$DESC$Sozinho no comando, com servos e iscas postos à frente.$DESC$,
perigo=$DESC$Letal$DESC$,
behavior_archetype=$DESC$tactical$DESC$,
morale_modifier=-1,
morale_immune=false,
epigrafe=$DESC$A gente caçou os capangas a noite toda. Só no fim percebemos que cada passo nosso tinha sido escolhido por alguém que nunca apareceu.$DESC$,
descricao=$DESC$É o que sobrou de um conjurador que aprendeu a mandar de longe, e a morte não tirou dele o gosto de tramar. Enxerga no escuro como em pleno dia, até no breu de feitiço, e usa isso para mover servos, iscas e armadilhas à frente, sempre atrás de tudo. Não quer trocar golpe: deixa os outros sangrarem por ele. Quando o plano é furado, ou alguém o alcança, ele dispara raios frios de cova de longe e arranha com a mão que apaga o calor, e some de novo para o fundo. Aguenta reza melhor que a maioria, mas não aguenta perder a distância: tirado o anteparo, ele é fraco e foge.$DESC$,
supersticao_popular=$DESC$Em Thornmarak dizem que certas ruínas têm uma cabeça escondida que move os perigos como peças, e que o pior inimigo é o que você nunca vê. O conselho é não gastar a noite caçando capanga e sim achar quem comanda, lá no fundo escuro. Contam que ele enxerga no breu e que luz não o cega, mas que sozinho, sem os seus, ele corre.$DESC$,
sinais_presenca=$DESC$Servos e armadilhas bem postos demais para serem acaso, sempre te empurrando para um lado. Raios frios vindos do escuro de onde ninguém aparece. Um covil onde o breu é fundo demais, escuro de feitiço. Ordens cochichadas que você ouve sem achar a boca. Mortos e iscas dispostos como peças num tabuleiro.$DESC$,
fraqueza_conhecida=$DESC$O povo sabe que o perigo é a cabeça escondida, não os capangas, e que luz não cega esse tipo. Furar para o fundo e achar quem comanda é o caminho. Quem só mata os servos cansa à toa enquanto ele trama.$DESC$,
fraqueza_real=$DESC$A arma dele é a distância e a trama: comanda de trás, no escuro que enxerga, e deixa os outros morrerem. O golpe só vem quando o plano é quebrado ou ele é alcançado, e mesmo aí ele prefere recuar. Tirado o anteparo dos servos e a distância, ele é frágil e covarde, e foge cedo. Quem ignora as iscas, atravessa o breu e chega à cabeça, no fundo, encerra a trama inteira; quem joga o jogo dele, no terreno dele, perde gente sem nunca tocá-lo.$DESC$,
descricao_sensorial=$DESC$O som é a ordem cochichada que chega sem dono e o zumbido frio dos raios de cova. O cheiro é de poeira de cova e de breu fechado. Ao toque, a mão dele apaga o calor onde arranha, e a pele é seca e fria. Aos olhos, quase não se vê: ele fica onde o escuro é mais fundo, e você só nota os servos que ele empurra à frente.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Usa os vivos e os servos como peças a gastar$DESC$, $DESC$Saqueadores que entram no covil que ele comanda em Thornmarak$DESC$),
'predador', jsonb_build_array($DESC$Quem atravessa o breu e o alcança sem anteparo; a perda da distância$DESC$),
'competidor', jsonb_build_array($DESC$Outras cabeças que tramam nas ruínas de Thornmarak$DESC$, $DESC$Atalho-Falso$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presença dele diz que os perigos daquela ruína têm dono, e que alguém move tudo do escuro.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem ignora as iscas e fura direto para quem comanda, no fundo$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$O olho de cova que enxerga no breu de feitiço$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Arcano / ver no escuro mágico, comandar à distância)$DESC$, 'risco', $DESC$Mostra a quem o usa mais do que ele queria ver.$DESC$),
jsonb_build_object('material', $DESC$Os raios frios de cova que ele dispara$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Arcano / golpe gelado à distância)$DESC$, 'risco', $DESC$Disparam no susto de quem os carrega.$DESC$),
jsonb_build_object('material', $DESC$As notas de trama que ele guardava$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (planos, mapa de armadilhas e servos)$DESC$, 'risco', $DESC$Confundem quem as segue à risca.$DESC$),
jsonb_build_object('material', $DESC$Manto escuro de covil$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (disfarce, agasalho)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Ordem cochichada que chega sem dono e o zumbido frio dos raios de cova.$DESC$,
'cheiro', $DESC$Poeira de cova e breu fechado.$DESC$,
'quer', $DESC$Mandar de longe e do escuro, sem se expor. Gastar os outros e nunca ser o que recebe o golpe.$DESC$,
'tipo_perigo', $DESC$Condicional$DESC$,
'falas_exemplo', jsonb_build_array($DESC$Eu não preciso te tocar. Tenho gente de sobra entre nós dois para isso.$DESC$, $DESC$Você está exatamente onde eu quis que estivesse. Olhe em volta antes de discordar.$DESC$, $DESC$(registro: fala baixa e calculista, do escuro, em comum e em língua morta; nunca fala de perto)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Alguém quebra o plano que ele armou$DESC$, $DESC$Um intruso atravessa o breu e chega perto demais$DESC$, $DESC$Ferem os servos e as peças que ele move$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Recua para trás dos servos ao primeiro aperto$DESC$, $DESC$Foge cedo quando perde a distância e o anteparo$DESC$, $DESC$Abandona o covil e a trama quando é alcançado sozinho$DESC$),
'descoberta_fazendo', $DESC$No fundo escuro de um covil de Thornmarak, parado, movendo servos e armadilhas como peças contra quem entrou, sem nunca aparecer na frente.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Ignorar as iscas e furar direto para a cabeça no fundo$DESC$, $DESC$Tirar a distância dele, onde ele é fraco e foge$DESC$, $DESC$Não jogar o jogo de caçar capangas a noite toda$DESC$, $DESC$Cortar a trama achando quem a move, não quem a executa$DESC$)
),
status_conversao='canonizada'
WHERE id=623;

-- 706 · Remendo-Pálido · Espírito · brute · Persistente · Vyrkhor · Superfície · fala  [watch: origem Spirit Troll]
UPDATE ref_criaturas SET
nome=$DESC$Remendo-Pálido$DESC$,
nome_ptbr=$DESC$Remendo-Pálido$DESC$,
slug=$DESC$remendo-palido$DESC$,
origem=$DESC$Natural$DESC$,
andar_primario=$DESC$Superfície$DESC$,
pilar_associado=$DESC$Espírito$DESC$,
continente=ARRAY[$DESC$Vyrkhor$DESC$]::text[],
habitat=$DESC$Os passos altos e gelados de Vyrkhor onde um bruto grande caiu sem acabar de morrer. Anda meio dentro da pedra, no trecho onde tombou.$DESC$,
comportamento=$DESC$É o que restou de um bruto que não terminou de morrer no frio, e ele não sabe parar. Atravessa a pedra como quem não está de todo ali, e o aço comum passa por ele sem morder. O que você corta, fecha sozinho na vez seguinte. Vem devagar, sem manha, e te gasta no tempo: aguenta, remenda, volta. Preso ao trecho onde caiu, não se afasta dele.$DESC$,
organizacao=$DESC$Sozinho, preso ao ponto onde tombou.$DESC$,
perigo=$DESC$Letal$DESC$,
behavior_archetype=$DESC$brute$DESC$,
morale_modifier=2,
morale_immune=false,
epigrafe=$DESC$A gente atravessou ele com a lança e a lança não pegou em nada. Ele atravessou a parede atrás de nós como se a parede também não existisse.$DESC$,
descricao=$DESC$É o resto pálido de um bruto grande que caiu no frio de Vyrkhor e não acabou de morrer. Está meio aqui e meio não: passa pela pedra como se ela fosse fumaça, e a lâmina comum cruza o corpo dele sem cortar coisa nenhuma. Tem pouca força e morde e arranha quase por hábito, mas a arma de verdade é não parar: a ferida que você abre se fecha antes do próximo golpe, e ele torna a vir. Não tem pressa e não tem medo. Fica no trecho onde tombou, indo e voltando da pedra, e gasta quem insiste até a pessoa não ter mais o que dar.$DESC$,
supersticao_popular=$DESC$Em Vyrkhor contam que há trechos de passo gelado onde um vulto pálido entra e sai da rocha e não se deixa matar com ferro. O conselho dos guias é não brigar com o que sara sozinho e não pega no aço, e sim atravessar rápido o trecho dele, que ele não segue para longe. Dizem que só gume encantado ou fogo o tocam de verdade, e que ele está amarrado ao lugar onde caiu.$DESC$,
sinais_presenca=$DESC$Um vulto pálido que some na pedra e reaparece um pouco adiante. Lâminas e flechas que atravessam um corpo sem encontrar carne. Feridas que fecham na sua frente, brancas, sem sangrar direito. Frio mais fundo num trecho só do passo. Bichos que não pisam aquele pedaço de trilha.$DESC$,
fraqueza_conhecida=$DESC$O povo sabe que ferro comum não pega nele e que ele sara sozinho, e por isso aconselha atravessar rápido e não brigar. Gume encantado ou fogo o ferem onde o aço passa reto. Ele não segue para longe do trecho onde está.$DESC$,
fraqueza_real=$DESC$Ele está só meio presente e preso ao ponto onde caiu, e essas duas coisas o salvam e o entregam. Meio fora do mundo, a lâmina comum o atravessa sem cortar; mas o gume encantado morde de verdade, e cortando mais rápido do que ele remenda, a sobra se desfaz. Quebrar o que o amarra àquele trecho também o solta. Quem o atravessa correndo nunca o enfrenta; quem precisa acabá-lo usa fio encantado ou fogo e não deixa o remendo alcançar o talho.$DESC$,
descricao_sensorial=$DESC$O som é um arrasto surdo e um estalo molhado de carne que se fecha sozinha. O cheiro é de bicho velho e de frio de pedra, azedo e ralo. Ao toque, é frio e meio sem firmeza, como agarrar algo que não está todo ali. Aos olhos, é um vulto grande e pálido, de pele esticada, que entra e sai da rocha e cujas feridas somem enquanto você olha.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Agarra o que insiste no trecho dele$DESC$, $DESC$Viajantes que demoram no passo gelado de Vyrkhor$DESC$),
'predador', jsonb_build_array($DESC$O gume encantado e o fogo, que o ferem onde o aço passa; quem quebra o que o prende ao lugar$DESC$),
'competidor', jsonb_build_array($DESC$Outras sobras das alturas de Vyrkhor que ocupam os passos$DESC$, $DESC$Aurora-Morta$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presença dele diz que ali um bruto caiu e não acabou de morrer, e que o ferro comum não resolve.$DESC$,
'evitado_por', jsonb_build_array($DESC$Guias que atravessam rápido o trecho dele e não brigam com o que sara sozinho$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$Couro e pele pálida e grossa, esticada e fria$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Material (Superfície / couro grosso, agasalho de altura)$DESC$, 'risco', $DESC$Cheira a bicho velho por semanas.$DESC$),
jsonb_build_object('material', $DESC$Garras pálidas, gastas$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (ponta, gancho)$DESC$, 'risco', $DESC$Nenhum.$DESC$),
jsonb_build_object('material', $DESC$Dentes e osso longo$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (cabo, ponta)$DESC$, 'risco', $DESC$Nenhum.$DESC$),
jsonb_build_object('material', $DESC$Tendão grosso de membro$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (corda, amarra)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Arrasto surdo e um estalo molhado de carne que se fecha sozinha.$DESC$,
'cheiro', $DESC$Bicho velho e frio de pedra, azedo e ralo.$DESC$,
'quer', $DESC$Não parar. Gastar quem insiste no trecho onde ele caiu, remendando-se sem fim, sem nunca acabar de morrer.$DESC$,
'tipo_perigo', $DESC$Persistente$DESC$,
'falas_exemplo', jsonb_build_array($DESC$Você corta, eu fecho. Você cansa, eu não. Veja quem para primeiro.$DESC$, $DESC$Esse passo é onde eu caí. Eu não saio dele. Você é que tem pressa.$DESC$, $DESC$(registro: fala lenta e arrastada em língua de gigante, sem raiva, como quem repete algo que já não tem fim)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Alguém demora ou briga no trecho onde ele caiu$DESC$, $DESC$Tentam levar algo do ponto a que ele está preso$DESC$, $DESC$Uma lâmina encantada ou fogo o tocam e o despertam$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Não foge: remenda e volta enquanto durar$DESC$, $DESC$Recolhe-se à pedra do trecho quando o alvo se afasta$DESC$, $DESC$Cessa quando o gume encantado ou o fogo desfazem o remendo mais rápido do que ele fecha$DESC$),
'descoberta_fazendo', $DESC$Entrando e saindo da rocha num passo gelado de Vyrkhor, no ponto onde caiu, indo devagar atrás de quem demorou ali.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Atravessar rápido o trecho dele, que ele não segue para longe$DESC$, $DESC$Não brigar com o que sara sozinho e não pega no aço$DESC$, $DESC$Usar gume encantado ou fogo, se for preciso acabá-lo$DESC$, $DESC$Quebrar o que o prende ao lugar para soltá-lo$DESC$)
),
status_conversao='canonizada'
WHERE id=706;

-- 2109 · Esgar-Torto · Engenho · striker · Direto · Kethara · Margem · fala
UPDATE ref_criaturas SET
nome=$DESC$Esgar-Torto$DESC$,
nome_ptbr=$DESC$Esgar-Torto$DESC$,
slug=$DESC$esgar-torto$DESC$,
origem=$DESC$Marginal$DESC$,
andar_primario=$DESC$Margem$DESC$,
pilar_associado=$DESC$Engenho$DESC$,
continente=ARRAY[$DESC$Kethara$DESC$]::text[],
habitat=$DESC$Bordas da Margem em Kethara, ruínas de areia e subterrâneos onde a luz do sol não chega. Foge do dia; vive no escuro fresco.$DESC$,
comportamento=$DESC$Foi gente, e a Margem o entortou por dentro. Vem direto e bate com as mãos tortas, mas o golpe que assusta é o de dentro: arremessa um pesadelo na cabeça de quem está perto, uma onda que dobra a mente por um instante. Fala sem boca, encostando o pensamento no seu. Detesta o sol, que o queima e cega. No escuro, é rápido e direto; na luz, recua.$DESC$,
organizacao=$DESC$Sozinho, ou em poucos tortos pela mesma borda.$DESC$,
perigo=$DESC$Ameaça$DESC$,
behavior_archetype=$DESC$striker$DESC$,
morale_modifier=0,
morale_immune=false,
epigrafe=$DESC$Não tinha arma. Veio com as mãos. Mas antes de chegar, jogou uma coisa na minha cabeça que me fez ver o pior que eu já vivi, tudo de uma vez.$DESC$,
descricao=$DESC$Foi um homem, ou coisa parecida, e o contato com a Margem o torceu: o corpo ficou errado, as mãos tortas, e a cabeça virou arma. Vem direto, sem rodeio, e golpeia com os punhos, mas o que derruba mesmo é o pesadelo que ele atira na sua mente quando chega perto, uma onda que enche a cabeça do seu pior medo e trava o corpo. Fala sem voz, pondo o pensamento dentro do seu. A luz do sol o queima e cega, e por isso ele caça no escuro fresco dos subterrâneos. Direto e rápido na sombra, fraco e recuado no claro.$DESC$,
supersticao_popular=$DESC$Nas ruínas de areia de Kethara dizem que há coisas que foram gente e voltaram tortas, que batem com as mãos e com a cabeça, e que jogam pesadelo de perto. O conselho é trazê-las para a luz do sol, que elas não suportam, e não deixá-las chegar perto, porque o golpe de dentro vem no contato curto. Dizem que falam sem boca, e que ouvir a voz na própria cabeça já é sinal de que estão perto demais.$DESC$,
sinais_presenca=$DESC$Pegadas tortas que evitam o sol, sempre na sombra e no subterrâneo. Uma voz que aparece dentro da sua cabeça sem ninguém ter falado. Gente sumida das bordas que dão na Margem, em Kethara. Bichos e pessoas achados vivos mas vazios de susto, como se tivessem visto o pior. Marcas de mão torta na areia fresca das ruínas.$DESC$,
fraqueza_conhecida=$DESC$O povo sabe que essas coisas não aguentam o sol e que o golpe pior vem de perto. Levá-las para a luz, ou esperar o dia, e mantê-las à distância, é o método. Quem deixa chegar perto leva o pesadelo na cabeça e trava.$DESC$,
fraqueza_real=$DESC$A arma de longe dele é o pesadelo que ele atira na mente, e ela só pega de perto; a luz do sol o queima e cega, tirando dele a sombra que é a casa dele. Mantido à distância, no claro, ele é só um corpo torto e fraco que recua. Quem o enfrenta de dia, ou o traz para a luz, e não o deixa encostar a mente na sua, desfaz a vantagem; quem o caça no escuro, no terreno dele e ao alcance do golpe de dentro, joga onde ele é forte.$DESC$,
descricao_sensorial=$DESC$O som é quase nenhum por fora, e por dentro uma voz que não é sua e o eco abafado de um pesadelo. O cheiro é de areia fria de subterrâneo e de carne errada, adocicada. Ao toque, a pele é torta e fria, e o golpe de dentro vem antes do de fora. Aos olhos, é uma figura que foi gente e não é mais, de mãos tortas, recuando da luz para a sombra.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Gente das bordas que dão na Margem em Kethara$DESC$, $DESC$Quem se aventura no escuro das ruínas de areia$DESC$),
'predador', jsonb_build_array($DESC$A luz do sol, que o queima e cega; quem o mantém longe e no claro$DESC$),
'competidor', jsonb_build_array($DESC$Outras coisas tortas da Margem de Kethara$DESC$, $DESC$Sósia-Oco$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presença dele diz que a Margem encosta naquele subterrâneo, e que quem entra pode voltar torto ou não voltar.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem caça de dia, à luz, e não deixa a coisa chegar ao alcance do golpe de dentro$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$A glândula torta com que ele atira o pesadelo na mente$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Engenho / golpe que enche a cabeça de medo e trava)$DESC$, 'risco', $DESC$Atira o pesadelo em quem a manuseia sem firmeza.$DESC$),
jsonb_build_object('material', $DESC$O que nele fala sem boca, direto no pensamento$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Engenho / pôr palavra na mente alheia à curta distância)$DESC$, 'risco', $DESC$Sussurra na cabeça de quem o guarda.$DESC$),
jsonb_build_object('material', $DESC$Pele torta, marcada pela Margem$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (curiosidade, estudo do que a Margem faz)$DESC$, 'risco', $DESC$Incomoda só de olhar.$DESC$),
jsonb_build_object('material', $DESC$Restos do que ele foi antes de torcer$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (trapo, osso)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Quase nenhum por fora, e por dentro uma voz que não é sua e o eco abafado de um pesadelo.$DESC$,
'cheiro', $DESC$Areia fria de subterrâneo e carne errada, adocicada.$DESC$,
'quer', $DESC$Chegar perto e despejar o pesadelo na sua cabeça, no escuro, longe do sol que o queima.$DESC$,
'tipo_perigo', $DESC$Direto$DESC$,
'falas_exemplo', jsonb_build_array($DESC$Não fuja da escuridão. Aqui é mais fresco. Aqui eu falo melhor com você.$DESC$, $DESC$Você já viu isso antes, esse medo. Eu só trouxe ele de volta para a sua frente.$DESC$, $DESC$(registro: fala sem som, posta direto na cabeça, num tom torto e baixo que parece vir de dentro de você)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Alguém chega ao alcance do golpe de dentro dele$DESC$, $DESC$Um intruso entra no escuro fresco que é dele$DESC$, $DESC$A luz forte o encurrala e ele ataca por desespero$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Recua da luz forte do sol, que o queima e cega$DESC$, $DESC$Foge para o subterrâneo quando trazido ao claro$DESC$, $DESC$Abandona a presa que se mantém longe, fora do alcance do pesadelo$DESC$),
'descoberta_fazendo', $DESC$No escuro fresco de um subterrâneo de areia em Kethara, encostando o pensamento na mente de quem entrou, pronto para o golpe de perto.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Enfrentá-lo de dia ou trazê-lo para a luz do sol, que ele não suporta$DESC$, $DESC$Mantê-lo à distância, fora do alcance do golpe de dentro$DESC$, $DESC$Não entrar no escuro das ruínas onde ele caça$DESC$, $DESC$Recuar para o claro ao ouvir a voz na própria cabeça$DESC$)
),
status_conversao='canonizada'
WHERE id=2109;

-- =====================================================================
-- GRUPO 5
-- =====================================================================

-- 1167 · Revoada-Negra · Corpo · swarm · Ambiental · Voranthar · Superfície · MUDO
UPDATE ref_criaturas SET
nome=$DESC$Revoada-Negra$DESC$,
nome_ptbr=$DESC$Revoada-Negra$DESC$,
slug=$DESC$revoada-negra$DESC$,
origem=$DESC$Natural$DESC$,
andar_primario=$DESC$Superfície$DESC$,
pilar_associado=$DESC$Corpo$DESC$,
continente=ARRAY[$DESC$Voranthar$DESC$]::text[],
habitat=$DESC$Os campos de mortos e as ruínas abertas de Voranthar, onde há carniça farta. Pousa em bando nas árvores secas e nos exércitos caídos.$DESC$,
comportamento=$DESC$Vive em bando e age como um. Sozinhos são só aves; juntos, viram uma nuvem que enche o ar, bica de todo lado e faz uma gritaria que ensurdece e confunde, de modo que ninguém pensa nem se ouve no meio dela. Cercam o ferido e o cansado, não o forte. Espalham-se quando apanham, e voltam a juntar logo adiante.$DESC$,
organizacao=$DESC$Em bando, dezenas que se movem como uma coisa só.$DESC$,
perigo=$DESC$Ameaça$DESC$,
behavior_archetype=$DESC$swarm$DESC$,
morale_modifier=-1,
morale_immune=false,
epigrafe=$DESC$Não foi o bico que nos quebrou. Foi o barulho. Mil gritos de uma vez, e a gente não ouvia mais a própria ordem.$DESC$,
descricao=$DESC$São muitos corvos pretos que se movem como uma coisa só. Uma ave dessas não é nada; a revoada inteira é uma nuvem que tapa o ar, bica de todos os lados ao mesmo tempo e solta uma gritaria que ensurdece, espanta e confunde, até a pessoa não ouvir a própria voz nem pensar direito. Não atacam o que reage forte: rondam o ferido, o perdido, o que ficou para trás, e enchem o espaço em volta dele. Espalham-se ao primeiro susto sério e se ajuntam de novo um pouco adiante, pacientes, porque tempo elas têm.$DESC$,
supersticao_popular=$DESC$Em Voranthar dizem que a revoada negra é aviso de morte farta por perto, e que o perigo dela não é o bico, é o barulho que cega os sentidos. O conselho é não se separar do grupo onde elas rondam, cobrir a cabeça, e fazer fogo e fumaça para abrir a nuvem. Contam que elas largam quem se mostra forte e ficam com quem fraqueja.$DESC$,
sinais_presenca=$DESC$Árvores secas cobertas de corvos calados, todos virados para o mesmo lado. Carniça farta e limpa rápido demais. Uma nuvem preta que se forma e se desfaz no ar sobre um ponto. Penas pretas caídas em quantidade num trecho de campo. O silêncio dos corvos um instante antes de levantarem juntos.$DESC$,
fraqueza_conhecida=$DESC$O povo sabe que o perigo é a gritaria que confunde, não o bico, e que fogo e fumaça abrem a nuvem. Não se separar do grupo e cobrir a cabeça basta para a maioria. Quem se mostra forte e firme costuma ser largado.$DESC$,
fraqueza_real=$DESC$A arma da revoada é encher o espaço de barulho e bicadas e roubar os sentidos de quem fica isolado; é dano de área e confusão, não de força. Fogo, fumaça e um grupo firme e junto desfazem a nuvem, porque elas não enfrentam o que reage e se espalham ao primeiro baque sério. Quem não se deixa isolar, abre a nuvem com fumaça e não entra em pânico com o barulho passa; quem corre sozinho e surdo é cercado e caído aos poucos.$DESC$,
descricao_sensorial=$DESC$O som é uma gritaria de mil corvos de uma vez que abafa tudo o mais e dói no ouvido. O cheiro é de pena, de carniça e de campo de morte. Ao toque, são muitas bicadas pequenas e o roçar de asas por todo lado. Aos olhos, é uma nuvem preta que se fecha em volta e tira o céu, feita de bicos e olhos sem conta.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Feridos, perdidos e retardatários dos campos de morte de Voranthar$DESC$, $DESC$Carniça farta dos exércitos caídos$DESC$),
'predador', jsonb_build_array($DESC$O fogo e a fumaça que abrem a nuvem; grupos firmes que não se deixam isolar$DESC$),
'competidor', jsonb_build_array($DESC$Outros bandos e comedores de carniça de Voranthar$DESC$, $DESC$Novelo-Peçonho$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presença dela diz que há morte farta por perto, e que o ferido e o perdido serão os primeiros.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem não se separa do grupo, cobre a cabeça e abre a nuvem com fumaça$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$Pena negra em grande quantidade, da revoada$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Material (Superfície / empena de flecha, enchimento, ornamento)$DESC$, 'risco', $DESC$Atrai mais corvos enquanto fresca.$DESC$),
jsonb_build_object('material', $DESC$Bicos e garras miúdos, aos punhados$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (anzol, ponta fina, miçanga)$DESC$, 'risco', $DESC$Nenhum.$DESC$),
jsonb_build_object('material', $DESC$Restos de carniça que elas limpam$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (isca, adubo)$DESC$, 'risco', $DESC$Atrai outros comedores.$DESC$),
jsonb_build_object('material', $DESC$Penugem e poeira de ninho$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (enchimento)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Gritaria de mil corvos de uma vez que abafa tudo o mais e dói no ouvido.$DESC$,
'cheiro', $DESC$Pena, carniça e campo de morte.$DESC$,
'quer', $DESC$Comer a carniça e o que fraqueja. Cercar o isolado, encher o ar de barulho e bicada, e desfazer-se ao primeiro perigo de verdade.$DESC$,
'tipo_perigo', $DESC$Ambiental$DESC$,
'falas_exemplo', 'null'::jsonb,
'gatilhos_agressao', jsonb_build_array($DESC$Alguém fica ferido, perdido ou para trás onde elas rondam$DESC$, $DESC$Carniça farta atrai a revoada a um ponto$DESC$, $DESC$Um isolado entra no meio da nuvem$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Espalham-se ao primeiro fogo, fumaça ou baque sério$DESC$, $DESC$Largam quem se mostra forte e firme$DESC$, $DESC$Ajuntam-se adiante e desistem se o grupo não se abre$DESC$),
'descoberta_fazendo', $DESC$Em nuvem sobre um campo de mortos de Voranthar, limpando carniça e rondando o ferido e o retardatário, enchendo o ar de gritaria.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Não se separar do grupo onde elas rondam$DESC$, $DESC$Abrir a nuvem com fogo e fumaça$DESC$, $DESC$Cobrir a cabeça e seguir firme, sem pânico com o barulho$DESC$, $DESC$Deixar a carniça e sair do campo que elas dominam$DESC$)
),
status_conversao='canonizada'
WHERE id=1167;

-- 2033 · Gargalho-Rubro · Sombra · predator · Condicional · Kethara · Eco · fala
UPDATE ref_criaturas SET
nome=$DESC$Gargalho-Rubro$DESC$,
nome_ptbr=$DESC$Gargalho-Rubro$DESC$,
slug=$DESC$gargalho-rubro$DESC$,
origem=$DESC$Cicatricial$DESC$,
andar_primario=$DESC$Eco$DESC$,
pilar_associado=$DESC$Sombra$DESC$,
continente=ARRAY[$DESC$Kethara$DESC$]::text[],
habitat=$DESC$Savanas secas e ruínas de Kethara, onde a matilha caça à noite. Esconde-se do sol em covis e tocas frescas durante o dia.$DESC$,
comportamento=$DESC$Caça como bicho e bebe como o que é. Anda em forma de hiena, farejando o rastro do sangue, e quando acha o ferido ou o que se afastou, vira gente-fera e ri, um gargalho que gela e prende as pernas de quem ouve. Morde para beber, e o que perde sangue alimenta o que ele sara. Foge do sol e do que queima. Cobre não enfrenta força igual; escolhe o fraco e o sozinho.$DESC$,
organizacao=$DESC$Sozinho ou em matilha, cada um com seu rastro de sangue.$DESC$,
perigo=$DESC$Letal$DESC$,
behavior_archetype=$DESC$predator$DESC$,
morale_modifier=1,
morale_immune=false,
epigrafe=$DESC$A hiena riu, e a risada não era de hiena. Quando o Saro tentou correr, as pernas dele não obedeceram, e a coisa já estava de pé, com cara de gente.$DESC$,
descricao=$DESC$É um caçador que bebe sangue e troca de pele: anda como hiena para farejar e correr, e vira uma fera de pé, de mãos e dentes, quando chega a hora de matar. Solta um gargalho que gela e trava quem o escuta, e um olhar que embrulha o estômago e tira a força, e então morde para beber. Cada gole que toma fecha as feridas dele. Fareja sangue a distância e escolhe sempre o ferido, o perdido, o que se afastou do fogo. O sol o queima e a luz forte o enfraquece; por isso caça no escuro e dorme escondido de dia.$DESC$,
supersticao_popular=$DESC$Em Kethara contam que algumas hienas que riem como gente bebem sangue e saram do que você corta, e que caçam o que se afasta do fogo à noite. O conselho é não andar sozinho no escuro, manter o fogo aceso, e lembrar que a luz do dia é o que de fato o derruba. Dizem que a risada gela as pernas e que o olhar tira a força, e que o ferido é sempre o primeiro escolhido.$DESC$,
sinais_presenca=$DESC$Rastro de hiena que de repente vira pegada de pé, de gente. Uma risada de hiena que arrepia, ouvida no escuro. Presas achadas sem sangue, com dois furos no pescoço. Bichos e gente sumidos à noite das beiras do acampamento. Covis frescos, fundos, longe do sol, com ossos roídos no fundo.$DESC$,
fraqueza_conhecida=$DESC$O povo sabe que ele sara do que se corta e que o sol é o que o vence. Manter o fogo, não andar sozinho à noite, e levar a briga para o dia ou para a luz forte é o método. A risada e o olhar são avisos de que ele já está perto.$DESC$,
fraqueza_real=$DESC$Ele é predador de oportunidade: ataca sob condição, o ferido, o isolado, o escuro, e some do que reage em força. A regeneração o cura enquanto bebe, mas as fraquezas dele são fundas: o sol o queima, a luz forte o enfraquece, e tirado o sangue e o escuro, ele vira só uma fera acuada. Quem nega a ele o fraco e o sozinho, mantém luz e fogo, e o leva ao dia, desfaz a vantagem; quem o caça à noite, no escuro, dá a ele tudo de que precisa.$DESC$,
descricao_sensorial=$DESC$O som é a risada de hiena que não é de hiena, e o rosnar baixo entre as gargalhadas. O cheiro é de bicho, de sangue velho e de toca quente de savana. Ao toque, a pele é quente e o dente, fundo; e o gole dele esfria quem ele bebe. Aos olhos, é uma hiena grande até se erguer em fera de pé, de olhos que embrulham o estômago de quem encara.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$O ferido, o perdido e o que se afasta do fogo nas savanas de Kethara$DESC$, $DESC$Gado e gente levados à noite$DESC$),
'predador', jsonb_build_array($DESC$O sol e a luz forte, que o queimam e enfraquecem; quem o enfrenta de dia$DESC$),
'competidor', jsonb_build_array($DESC$Outras matilhas e caçadores noturnos de Kethara$DESC$, $DESC$Carraça-Insone$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presença dele diz que a noite ali tem caçador que bebe sangue, e que o ferido é a primeira escolha.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem mantém o fogo aceso, não anda só no escuro e leva a briga para o dia$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$O sangue que ele bebe e com que se cura$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Sombra / regeneração pelo sangue, fechar feridas)$DESC$, 'risco', $DESC$Dá sede de sangue a quem o prova sem preparo.$DESC$),
jsonb_build_object('material', $DESC$A garganta de onde sai o gargalho que gela as pernas$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Sombra / o riso que trava de medo quem ouve)$DESC$, 'risco', $DESC$Gargalha sozinha no escuro da bolsa.$DESC$),
jsonb_build_object('material', $DESC$Os olhos que embrulham o estômago e tiram a força$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (foco de mau-olhado, curiosidade)$DESC$, 'risco', $DESC$Enjoa quem os encara muito tempo.$DESC$),
jsonb_build_object('material', $DESC$Pele malhada de hiena grande$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (couro, agasalho de caçada)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Risada de hiena que não é de hiena, e o rosnar baixo entre as gargalhadas.$DESC$,
'cheiro', $DESC$Bicho, sangue velho e toca quente de savana.$DESC$,
'quer', $DESC$Beber o sangue do fraco e do isolado, e sarar do que bebe, sempre no escuro, longe do sol.$DESC$,
'tipo_perigo', $DESC$Condicional$DESC$,
'falas_exemplo', jsonb_build_array($DESC$Você se afastou do fogo. Foi gentileza sua. Eu nem precisei te chamar.$DESC$, $DESC$Pode correr. Eu adoro quando correm. As pernas é que costumam discordar.$DESC$, $DESC$(registro: fala rosnada entre risos, em língua de matilha e numa língua morta; ri antes e depois de cada ameaça)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Alguém se fere, se perde ou se afasta do fogo à noite$DESC$, $DESC$O cheiro de sangue chega ao faro dele$DESC$, $DESC$Um isolado cruza o escuro do território dele$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Recua do sol e da luz forte, que o queimam$DESC$, $DESC$Foge para o covil fresco quando trazido ao dia$DESC$, $DESC$Larga a presa que se mostra forte e fica perto do fogo$DESC$),
'descoberta_fazendo', $DESC$Em forma de hiena, farejando o rastro de sangue na savana noturna de Kethara, à espreita do ferido que se afastou do fogo.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Manter o fogo aceso e não andar sozinho no escuro$DESC$, $DESC$Levar a briga para o dia ou para a luz forte$DESC$, $DESC$Negar a ele o ferido e o isolado, ficando em grupo$DESC$, $DESC$Recuar para a luz ao ouvir a risada e sentir o olhar$DESC$)
),
status_conversao='canonizada'
WHERE id=2033;

-- 1792 · Estiagem-Surda · Arcano · striker · Persistente · Kethara · Eco · fala
UPDATE ref_criaturas SET
nome=$DESC$Estiagem-Surda$DESC$,
nome_ptbr=$DESC$Estiagem-Surda$DESC$,
slug=$DESC$estiagem-surda$DESC$,
origem=$DESC$Cicatricial$DESC$,
andar_primario=$DESC$Eco$DESC$,
pilar_associado=$DESC$Arcano$DESC$,
continente=ARRAY[$DESC$Kethara$DESC$]::text[],
habitat=$DESC$Ruínas ressecadas de Kethara, oásis mortos e terras que secaram de vez. Onde ele anda, a água some e o verde murcha.$DESC$,
comportamento=$DESC$Onde ele olha, seca. Encara a presa e o olhar dele murcha a carne, envelhece e resseca como estiagem que cai num corpo só. Bate com os punhos para o que chega perto, mas a arma é o olhar que vai secando você de longe enquanto ele aguenta tudo e se refaz. É teimoso, lento e implacável: não corre, não para, e o que você abre nele fecha. Só a luz pura o faz recuar.$DESC$,
organizacao=$DESC$Sozinho, arrastando a estiagem por onde anda.$DESC$,
perigo=$DESC$Letal$DESC$,
behavior_archetype=$DESC$striker$DESC$,
morale_modifier=2,
morale_immune=false,
epigrafe=$DESC$Ele só olhou pra mim. Não me tocou. Mas minha mão envelheceu trinta anos enquanto ele olhava, e a sede que me deu não passou mais.$DESC$,
descricao=$DESC$É um morto seco que carrega a estiagem nos olhos. Encara você e a carne murcha, a pele racha, o corpo resseca e envelhece depressa, como se anos de seca caíssem de uma vez. De perto, soca com os punhos duros; de longe, é o olhar que vai matando, devagar, enquanto ele encaixa o próximo. Aguenta quase tudo e se refaz do que o fere, sem pressa, sem medo. Onde ele passa, a água some e o verde morre. A única coisa que o faz recuar é luz pura, que queima nele o que o resto não toca.$DESC$,
supersticao_popular=$DESC$Em Kethara dizem que há um morto seco cujo olhar resseca tudo, e que onde ele anda a estiagem vem junto. O conselho é não deixar que ele te encare de longe, usar cobertura, e lembrar que ferir não adianta, porque ele sara. Contam que só luz pura o queima de verdade, e que a sede que o olhar dele dá é aviso de que ele te viu.$DESC$,
sinais_presenca=$DESC$Um trecho que secou de repente, com água sumida e planta murcha em volta de um caminho. Gente e bicho achados ressecados, envelhecidos antes da hora. Um morto seco que olha fixo e não tem pressa. Feridas que fecham nele enquanto você luta. Uma sede súbita e funda em quem foi encarado.$DESC$,
fraqueza_conhecida=$DESC$O povo sabe que ferir não resolve, porque ele sara, e que o olhar mata de longe. Não se deixar encarar, usar cobertura, e atacar com luz pura é o método. A sede súbita avisa que ele já te mira.$DESC$,
fraqueza_real=$DESC$A arma dele é o olhar que resseca de longe, e a defesa é a regeneração: ele encara, murcha, e se refaz do que você abre. Mas a luz pura o queima onde nada mais toca, e cega o olhar que ele usa. Quebrada a linha de visão, ou trazida a luz, ele perde o golpe e a guarda. Quem corta a visada, aguenta a sede e o castiga com luz encerra o morto seco; quem fica no aberto, encarado, e só o corta, seca em pé enquanto ele se costura.$DESC$,
descricao_sensorial=$DESC$O som é um arrastar seco e um estalo de pele que racha, e quase nenhuma voz. O cheiro é de poeira, de barro rachado e de coisa seca ao sol. Ao toque, a pele dele é dura e quebradiça, e a mão soca como pedra. Aos olhos, é um morto ressequido de olhos fundos que olham fixo, e em volta dele o chão é seco demais.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Gente e bicho que ele encara nas ruínas secas de Kethara$DESC$, $DESC$Viajantes pegos no aberto sem cobertura$DESC$),
'predador', jsonb_build_array($DESC$A luz pura, que o queima e cega o olhar; quem corta a linha de visão dele$DESC$),
'competidor', jsonb_build_array($DESC$Outros mortos das terras secas de Kethara$DESC$, $DESC$Borralho-Quente$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presença dele diz que aquela terra secou por mais que por sol, e que algo resseca o que olha.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem não se deixa encarar de longe, usa cobertura e leva luz pura$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$O olhar que resseca a carne de longe$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Arcano / o que seca, envelhece e murcha à distância)$DESC$, 'risco', $DESC$Resseca a mão e a garganta de quem o guarda.$DESC$),
jsonb_build_object('material', $DESC$O que nele fecha as feridas e o refaz$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Arcano / regeneração, costura do corpo)$DESC$, 'risco', $DESC$Cresce e seca em volta de si na bolsa.$DESC$),
jsonb_build_object('material', $DESC$Pele rachada de barro seco$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (curiosidade, estopa)$DESC$, 'risco', $DESC$Esfarela ao manuseio.$DESC$),
jsonb_build_object('material', $DESC$Pó da terra rachada que o segue$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (pó, lastro)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Arrastar seco e um estalo de pele que racha, e quase nenhuma voz.$DESC$,
'cheiro', $DESC$Poeira, barro rachado e coisa seca ao sol.$DESC$,
'quer', $DESC$Secar o que olha. Murchar e envelhecer a carne de longe, e refazer-se de tudo que o fere, sem parar.$DESC$,
'tipo_perigo', $DESC$Persistente$DESC$,
'falas_exemplo', jsonb_build_array($DESC$Não precisa fugir. Eu te alcanço com os olhos. A pressa só te cansa antes.$DESC$, $DESC$Está com sede? Vai piorar. Eu apenas comecei a olhar.$DESC$, $DESC$(registro: voz seca e baixa, rouca de pó, lenta como quem tem todo o tempo do mundo)$DESC$),
'gatilhos_agressao', jsonb_build_array($DESC$Alguém fica no aberto, ao alcance do olhar dele$DESC$, $DESC$Tentam atravessar a terra seca que ele guarda$DESC$, $DESC$Uma luz pura o fere e o desperta para a briga$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Recua da luz pura, que o queima onde nada mais toca$DESC$, $DESC$Cessa o avanço quando perde a linha de visão da presa$DESC$, $DESC$Abandona o aberto quando trazem luz forte contra ele$DESC$),
'descoberta_fazendo', $DESC$Parado num trecho ressecado de Kethara, encarando de longe quem cruza o aberto, secando devagar a carne de quem ele mira.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Não se deixar encarar de longe$DESC$, $DESC$Usar cobertura para cortar a linha de visão dele$DESC$, $DESC$Atacar com luz pura, que o queima$DESC$, $DESC$Sair do aberto seco que ele domina$DESC$)
),
status_conversao='canonizada'
WHERE id=1792;

-- 894 · Sino-Oco · Engenho · skirmisher · Oculto · Thornmarak · Margem · MUDO  [voz corrigida -> MUDO]
UPDATE ref_criaturas SET
nome=$DESC$Sino-Oco$DESC$,
nome_ptbr=$DESC$Sino-Oco$DESC$,
slug=$DESC$sino-oco$DESC$,
origem=$DESC$Marginal$DESC$,
andar_primario=$DESC$Margem$DESC$,
pilar_associado=$DESC$Engenho$DESC$,
continente=ARRAY[$DESC$Thornmarak$DESC$]::text[],
habitat=$DESC$Os tetos altos e os vazios da Margem em Thornmarak, cavernas de cristal onde algo flutua sem peso. Paira no escuro de cima, fora do alcance do olhar.$DESC$,
comportamento=$DESC$Flutua quieto, alto, fora da linha do olhar, e quase nunca é notado. Não caça: ronda, observa, e some do pensamento de quem está perto, encobrindo a si e ao que está em volta de modo que ninguém percebe nada ali. Se incomodado, esguicha um fedor que enxota e baixa um tentáculo mole. Vira de costas se derrubado e fica indefeso, debatendo-se para se endireitar. Some no breu de cima ao primeiro susto.$DESC$,
organizacao=$DESC$Sozinho, pairando num vazio da Margem.$DESC$,
perigo=$DESC$Ameaça$DESC$,
behavior_archetype=$DESC$skirmisher$DESC$,
morale_modifier=-1,
morale_immune=false,
epigrafe=$DESC$A gente passou três vezes pela mesma câmara e jurava estar vazia. Só quando o cristal pingou em cima da coisa é que ela apareceu, boiando, calada.$DESC$,
descricao=$DESC$É uma coisa mole em forma de sino, do tamanho de um cão pequeno, que flutua sem peso no alto da Margem e não faz som. Não fala, ainda que entenda o que se diz; quando quer dizer algo, encosta o pensamento sem palavra. A graça dele é não ser visto: encobre a própria presença e a do que está em volta, de modo que uma câmara com ele dentro parece vazia. Incomodado, esguicha um fedor que faz recuar e baixa um tentáculo mole, fraco. Se você o derruba de costas, ele fica de pernas para o ar, indefeso, se debatendo para virar. É mais escondido do que perigoso, mas o que ele esconde pode ser o perigo.$DESC$,
supersticao_popular=$DESC$Na Margem de Thornmarak dizem que há câmaras que parecem vazias e não estão, porque algo flutua no alto encobrindo tudo. O conselho dos que sabem é olhar para cima no escuro, e desconfiar do lugar limpo demais de presença. Contam que a coisa em si é quase inofensiva, mas que ela esconde o que vem junto, e que derrubá-la a deixa de pernas para o ar, sem defesa.$DESC$,
sinais_presenca=$DESC$Uma câmara que parece vazia mas dá uma sensação de não estar. Um fedor súbito e azedo, sem fonte à vista. Algo mole boiando no alto, fora da linha natural do olhar. Pingos e marcas onde algo invisível interrompeu a queda da água. O sumiço estranho da própria atenção quando você tenta olhar para um ponto.$DESC$,
fraqueza_conhecida=$DESC$O povo sabe que ela quase não fere e que se esconde, e que o jeito é olhar para cima e desconfiar do vazio limpo demais. Derrubá-la de costas a deixa indefesa. O cuidado de verdade é com o que ela encobre, não com ela.$DESC$,
fraqueza_real=$DESC$Ela não é o perigo: ela o esconde. Flutua, encobre a si e ao redor, e quem não olha para cima passa sem ver nada, inclusive o que estava junto. De arma, tem só um fedor que enxota e um tentáculo fraco; derrubada de costas, não se endireita e fica à mercê. Quem olha para o alto, desconfia da câmara vazia demais e a derruba neutraliza o disfarce; quem só some por ela some também o que ela cobria.$DESC$,
descricao_sensorial=$DESC$O som é quase nenhum, um leve borbulhar e o pingar de cristal interrompido no alto. O cheiro, quando ela se incomoda, é de um esguicho azedo e podre que enxota. Ao toque, é mole, úmida e fria, sem peso na mão. Aos olhos, é um sino de carne pálida boiando no escuro de cima, que você só vê quando para de procurar.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Não caça: ronda e encobre$DESC$, $DESC$Alimenta-se do que paira na Margem de Thornmarak$DESC$),
'predador', jsonb_build_array($DESC$Quem a derruba de costas, deixando-a indefesa; quem olha para cima e a encontra$DESC$),
'competidor', jsonb_build_array($DESC$Outras coisas que pairam nos vazios da Margem de Thornmarak$DESC$, $DESC$Pupila-Imunda$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presença dela diz que aquela câmara não está tão vazia quanto parece, e que algo ali anda encoberto.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem olha para o alto e desconfia do lugar limpo demais de presença$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$O que nela encobre a presença, a sua e a de quem está perto$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Engenho / esconder do pensamento e do faro alheio uma coisa ou um lugar)$DESC$, 'risco', $DESC$Some da própria lembrança de quem a guarda.$DESC$),
jsonb_build_object('material', $DESC$A glândula do esguicho que enxota$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Engenho / fedor que afasta e desorienta)$DESC$, 'risco', $DESC$Estoura o cheiro em quem a aperta.$DESC$),
jsonb_build_object('material', $DESC$A carne mole em forma de sino$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (foco leve que boia, curiosidade)$DESC$, 'risco', $DESC$Apodrece rápido fora da Margem.$DESC$),
jsonb_build_object('material', $DESC$O tentáculo fino e mole$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (fibra, fio)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Quase nenhum: um leve borbulhar e o pingar de cristal interrompido no alto.$DESC$,
'cheiro', $DESC$Quando incomodada, um esguicho azedo e podre que enxota.$DESC$,
'quer', $DESC$Não ser vista e encobrir o que está perto. Pairar no alto, calada, fora do alcance do olhar.$DESC$,
'tipo_perigo', $DESC$Oculto$DESC$,
'falas_exemplo', 'null'::jsonb,
'gatilhos_agressao', jsonb_build_array($DESC$Alguém a derruba ou a encurrala no alto$DESC$, $DESC$Chegam perto demais do que ela encobre$DESC$, $DESC$Algo a obriga a se mover do breu de cima$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Some no escuro do alto ao primeiro susto$DESC$, $DESC$Esguicha o fedor e recua quando tocada$DESC$, $DESC$Debate-se para se endireitar e foge se derrubada de costas$DESC$),
'descoberta_fazendo', $DESC$Pairando no alto de uma câmara de cristal da Margem em Thornmarak, calada, encobrindo a própria presença e a do que está em volta.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Olhar para o alto e desconfiar da câmara vazia demais$DESC$, $DESC$Derrubá-la de costas para neutralizar o disfarce, sem matá-la$DESC$, $DESC$Procurar o que ela encobre, que é o perigo real$DESC$, $DESC$Deixá-la pairando e seguir, atento ao redor$DESC$)
),
status_conversao='canonizada'
WHERE id=894;

-- 1240 · Colosso-Sacro · Espírito · brute · Direto · Vyrkhor · Clarão · MUDO
UPDATE ref_criaturas SET
nome=$DESC$Colosso-Sacro$DESC$,
nome_ptbr=$DESC$Colosso-Sacro$DESC$,
slug=$DESC$colosso-sacro$DESC$,
origem=$DESC$Cicatricial$DESC$,
andar_primario=$DESC$Clarão$DESC$,
pilar_associado=$DESC$Espírito$DESC$,
continente=ARRAY[$DESC$Vyrkhor$DESC$]::text[],
habitat=$DESC$Os picos mais altos de Vyrkhor, onde o Clarão toca a terra. Caminha raramente, e quando caminha, a montanha sente.$DESC$,
comportamento=$DESC$Anda como sentença que ganhou corpo. Não tem manha nem recuo: vem reto, vasto, e o golpe da arma dele racha pedra e fileira de uma vez, e o raio que ele lança do alto queima reto o que mira. Magia escorrega dele. Não fala e não negocia; mede em silêncio e desce a mão. Não foge: vai até o que veio fazer estar feito. É raro, e onde pisa, pouca coisa fica de pé.$DESC$,
organizacao=$DESC$Sozinho. Um basta para uma correção.$DESC$,
perigo=$DESC$Destruidor$DESC$,
behavior_archetype=$DESC$brute$DESC$,
morale_modifier=0,
morale_immune=true,
epigrafe=$DESC$A gente viu a coisa descer do pico e achou que era avalanche. Avalanche teria sido mais misericordiosa.$DESC$,
descricao=$DESC$É um vulto do tamanho de uma torre, de luz e carne, que desce dos picos mais altos de Vyrkhor quando há algo grande a corrigir. Não fala. Carrega uma arma que, ao cair, racha a pedra e a fileira juntas, e do alto lança um raio reto que queima o que toca. Magia jogada nele escorrega como água. Não tem manha de luta: tem tamanho, peso e uma certeza fria, e vem reto até terminar. Não é bom nem mau; é vasto e indiferente, e o que está entre ele e o que ele veio fazer simplesmente deixa de estar de pé. Poucos o veem e voltam para contar.$DESC$,
supersticao_popular=$DESC$Em Vyrkhor dizem que nos picos mais altos dorme algo enorme do claro, e que quando ele desce não há reza nem fuga que sirva, só sair da frente. O conselho, o único, é não estar onde ele vai pisar. Contam que ele não persegue quem se afasta do que ele veio fazer, e que feitiço não o toca, e que é mais fácil mover a montanha do que ele.$DESC$,
sinais_presenca=$DESC$Um tremor fundo e ritmado, como passos do tamanho de casas. Uma luz vasta descendo de um pico alto, que não é o sol. Pedra rachada em linhas retas, larga demais para qualquer arma. O silêncio total dos bichos e do vento antes dele. O ar pesado e limpo, como antes de uma sentença.$DESC$,
fraqueza_conhecida=$DESC$O povo sabe que não há como enfrentá-lo de força e que feitiço escorrega dele. O único conselho é sair da frente e não estar onde ele vai pisar. Ele não persegue quem se afasta do que ele veio corrigir.$DESC$,
fraqueza_real=$DESC$Não há fraqueza de combate que valha: ele é vasto, magia escorrega, e o golpe e o raio rompem o que tocam. O que o limita é o propósito: ele desce por uma razão, vai reto a ela, e não caça quem não está no caminho dela. Quem entende o que ele veio fazer e simplesmente não se põe no meio sobrevive; quem tenta barrá-lo vira parte da pedra rachada. Contra ele, a sabedoria é geografia, não aço.$DESC$,
descricao_sensorial=$DESC$O som é o tremor fundo dos passos e um zumbido vasto de luz que desce, e nenhuma voz. O cheiro é de ar de altura, limpo e pesado, e de pedra partida. Ao toque, ninguém que tocou viveu para dizer; a luz dele queima a distância. Aos olhos, é uma figura imensa de luz e carne contra o céu de Vyrkhor, alta como uma torre, descendo devagar.$DESC$,
ecologia=jsonb_build_object(
'presa', jsonb_build_array($DESC$Não caça: corrige o que veio corrigir$DESC$, $DESC$Desfaz o que se põe no caminho da correção$DESC$),
'predador', jsonb_build_array($DESC$Nada o caça; ele sobe de volta ao pico quando termina$DESC$),
'competidor', jsonb_build_array($DESC$Outras forças vastas do Clarão sobre Vyrkhor$DESC$, $DESC$Sonâmbulo-Pétreo$DESC$),
'simbionte', jsonb_build_array(),
'indicador', $DESC$A presença dele diz que algo grande demais foi posto fora da régua, e que veio a correção.$DESC$,
'evitado_por', jsonb_build_array($DESC$Quem sai da frente e não se põe entre ele e o que ele veio fazer$DESC$)
),
loot_table=jsonb_build_array(
jsonb_build_object('material', $DESC$Um caco da luz vasta que ele desce a montanha$DESC$, 'raridade', $DESC$Raro$DESC$, 'uso', $DESC$Componente (Clarão / a luz que corrige e queima reto o que mira)$DESC$, 'risco', $DESC$Cega e fulmina quem o desperta sem ter por que.$DESC$),
jsonb_build_object('material', $DESC$Lasca da arma que racha pedra e fileira$DESC$, 'raridade', $DESC$Notável$DESC$, 'uso', $DESC$Componente (Clarão / golpe que parte o que toca em linha)$DESC$, 'risco', $DESC$Parte o que estiver na bancada ao ser erguida.$DESC$),
jsonb_build_object('material', $DESC$Fragmento da carne de luz, frio e denso$DESC$, 'raridade', $DESC$Distinto$DESC$, 'uso', $DESC$Material (foco vasto, peso justo)$DESC$, 'risco', $DESC$Pesa mais do que parece e esquenta na treta.$DESC$),
jsonb_build_object('material', $DESC$Pó da pedra que ele rachou$DESC$, 'raridade', $DESC$Ordinário$DESC$, 'uso', $DESC$Material comum (cascalho, lastro)$DESC$, 'risco', $DESC$Nenhum.$DESC$)
),
camada_narrativa=jsonb_build_object(
'som', $DESC$Tremor fundo dos passos e um zumbido vasto de luz que desce, e nenhuma voz.$DESC$,
'cheiro', $DESC$Ar de altura, limpo e pesado, e pedra partida.$DESC$,
'quer', $DESC$Corrigir o que foi posto fora da régua. Ir reto até estar feito, e subir de volta ao pico.$DESC$,
'tipo_perigo', $DESC$Direto$DESC$,
'falas_exemplo', 'null'::jsonb,
'gatilhos_agressao', jsonb_build_array($DESC$Alguém se põe entre ele e o que ele veio corrigir$DESC$, $DESC$Tentam barrar ou ferir o que ele desceu fazer$DESC$, $DESC$Algo grande foi posto fora da régua e o chamou$DESC$),
'gatilhos_fuga', jsonb_build_array($DESC$Não foge: vai até o propósito estar cumprido$DESC$, $DESC$Não persegue quem se afasta do seu caminho$DESC$, $DESC$Sobe de volta ao pico quando a correção está feita$DESC$),
'descoberta_fazendo', $DESC$Descendo devagar de um pico altíssimo de Vyrkhor, vasto e calado, indo reto na direção do que veio corrigir.$DESC$,
'desfechos_nao_combate', jsonb_build_array($DESC$Sair da frente e não estar onde ele vai pisar$DESC$, $DESC$Entender o que ele veio fazer e não se pôr no meio$DESC$, $DESC$Afastar-se do que ele veio corrigir$DESC$, $DESC$Deixar a montanha entre você e ele, porque aço não serve$DESC$)
),
status_conversao='canonizada'
WHERE id=1240;

-- =====================================================================
-- FIM DO LOTE — BLOCO 4 (25 UPDATEs)
-- =====================================================================
