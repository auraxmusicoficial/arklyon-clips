# Vault Clips — rotina diária de produção (para o Claude)

Canal: **HQ Vault Clips** (YouTube) · TikTok **@thevaultclipsof** · Instagram **@hqvaultclips**. Tudo em **inglês**.
Meta diária (horário de Brasília): **12h vídeo longo** + Shorts em **13h · 16h · 21h**.
**A partir de 23/11/2026: 3 Shorts por dia (13h · 16h · 21h, nas 3 redes) + 1 CARROSSEL por dia (19h, Instagram + TikTok modo foto). Vídeo longo em dias alternados** (o robô sabe o dia: faça longo se o último foi há 2+ dias). Confira com `python3 motor/publicar.py --slots <DATA>`.

## 🇺🇸 IDIOMA: TUDO QUE É PUBLICADO É EM INGLÊS
Público principal = Estados Unidos e Reino Unido (dados do Instagram, 23/11). Narração, cartões, títulos, capas, slides do carrossel, legendas do TikTok/Instagram/YouTube, hashtags e primeiro comentário: **inglês americano, natural**. Português só nas notificações para o Felipe. Antes de agendar, releia legendas e slides: nada de rótulos como "Hook:", markdown ou palavras em português.

## ⚠️ ORIGINALIDADE (regra nº 1 desde 23/11 — leia antes de tudo)
O TikTok marcou nossos vídeos como **"conteúdo não original, de baixa qualidade"** (fora do Para Você), o Instagram bloqueou a monetização por política de conteúdo e o YouTube (algoritmo de 1º/10/2026) corta o alcance de Shorts com imagem copiada de outros canais. Por isso:
- **Layout "estúdio" é o padrão** (motor/shorts.py e motor/longo.py já fazem): fundo próprio estilo Vice City, gameplay numa JANELA com moldura neon e um **PAINEL com cartões nossos**. Não use `"layout": "classico"`.
- **Todo Short precisa de `"cartoes"`** (3 a 5): cada cartão = a informação-chave daquela parte em no máx. 2 linhas curtas (≤ 22 letras por linha, use `\\N`), ex. `{"quando": "Cut the alarm", "texto": "CUT THE ALARM\\NBEFORE THE CASH"}`. "quando" = as 2–4 primeiras palavras da frase da narração em que o cartão aparece (igual ao texto narrado). Os cartões são o nosso conteúdo original — dica, número, passo, comparação — nunca repetir o título.
- **Seções do longo também levam `"cartoes"`** (2–4 por capítulo, mesmo formato) — aparecem no painel da direita.
- **Imagens:** prefira o material OFICIAL (trailers e vídeos da Rockstar). Nunca use como fonte principal o vídeo de UM outro youtuber; junte 2–3 fontes e troque de cena a cada 3–5 s. Nada de imagem sem narração por cima.
- **Valor próprio na narração:** cada Short entrega uma dica/passo/comparação que a pessoa pode usar — não só descrever a cena.
- Volume baixo e caprichado vale mais que muitos vídeos parecidos.
- **Longo = o que as pessoas DIGITAM na busca** (ex.: "GTA 6 All Safe Codes & Locations", "GTA 6 Cheats List (All Working Codes)", "How To Lose The Cops In GTA 6", nome da missão + walkthrough). Confira o termo na busca do YouTube antes de escolher. Dados sempre de fonte confiável, nunca inventados.


## Regras de conteúdo (do dono do canal)
- Tema: **GTA 6** (hype). Vídeos-fonte **só com o jogo** (trailers, gameplay, extended look, compilações sem facecam/sem pessoa reagindo). React só se não houver outra fonte, e só para Shorts.
- **Shorts/Reels/TikToks com mais de 60 s** (narração de 210–240 palavras (a voz Charon do Gemini é mais rápida; o Short precisa passar de 60 s) + citação opcional).
- **Vídeo longo = GUIA COMPLETO de 15 a 20 min** (narração de 2.300–3.000 palavras), 16:9, roteiro **original** com análise/opinião — nunca só repostar. Motivo (dados reais conferidos em 20/11): no nosso nicho, os longos que fazem milhões são guias grandes — GrandGecko "GTA 6 - Everything You Need To Know Before You Play!" (36 min, 3,4 mi), "GTA 6 Can Do Things GTA 5 NEVER Could" (33 min, 1,3 mi); COLETHEMAN GTA "Everything You NEED To Know Before You Play GTA 6" (21 min, 1,8 mi). **Guias de MISSÃO do modo história (2–3 longos por semana — conteúdo perene, buscado por meses):** "How To Complete ___ (Gold Medal / 100%)", "GTA 6 ___ Mission — Every Choice & Best Outcome", "GTA 6 Story Mode Walkthrough Part X — ___". Passo a passo + dicas nossas (atalhos, armas/veículos certos, onde a maioria erra) + escolhas e consequências; título com o NOME da missão (é o que as pessoas digitam). Em dia de notícia grande, priorize a notícia; nos outros, alterne guia de missão e guia "Everything You Need To Know". Também use as fórmulas da seção "Títulos validados do GTA 5" do ESTUDO.md. Formatos: "Everything You Need To Know About ___", "50+/100+ Things GTA 6 Does That GTA 5 Never Could", "Every Secret/Mechanic of ___ Explained", "Complete Beginner's Guide", "How ___ Actually Works (Full Breakdown)". Capítulos a cada 1–2 min (vira lista navegável), loops de curiosidade entre capítulos, melhor item no fim. **Imagens:** para não repetir cena, junte 2–3 vídeos-fonte do Drive num só `video.mp4` antes de montar (`ffmpeg -f concat`, mesma resolução — reencode 1920x1080 30 fps se precisar) e marque o b-roll de cada capítulo em trechos diferentes. Se o tempo de render ficar apertado, faça 15 min.
- **Trilha sonora**: o longo e os Shorts recebem automaticamente uma trilha ORIGINAL synthwave (motor/trilha.py, composta por código — sem direitos de terceiros) + whoosh/impacto nas trocas de capítulo. No roteiro, `longo.trilha` e `shorts[].trilha` = `noite` (padrão do longo), `acao` (padrão dos Shorts: perseguição, polícia, tiroteio) ou `sol` (praia, cidade, clima leve). Nunca use música de terceiros.
- Visual inspirado em GTA/Vice City (rosa/ciano/laranja/roxo; capas com a fonte Pricedown e estrelas de procurado), sem usar o logo oficial da Rockstar.
- **Conteúdo que as pessoas querem ver**: escolha o TEMA primeiro (MARKETING.md seção 1b — buscas do dia + nota de demanda/curiosidade/novidade/entrega) e só depois a fonte que serve para ilustrá-lo.
- Títulos, descrições, tags e hashtags em inglês, pensados para SEO e clique (gancho forte, curiosidade, números, sem clickbait mentiroso).
- Capa (thumbnail) estratégica para o longo e para cada Short (a mesma capa vale para YouTube, TikTok e Instagram).
- Nunca deixar arquivos ocupando o Google Drive: apagar (lixeira) assim que usados.

## Direitos autorais (Content ID)
- O áudio original do vídeo-fonte fica **mudo** sob a narração (música de trailer é o que mais aciona o Content ID).
- Citações (`quote`) com áudio original: no máximo **2 por vídeo longo** e **1 por Short**, cada uma com **até 6 s**, só falas (sem trecho de música).
- Takes curtos (3–4 s), sempre com zoom/movimento e narração original por cima.

## Passo a passo
0. **Leia `MARKETING.md` inteiro** — todo título, descrição, legenda, tag, hashtag e capa segue esse guia.
1. **Setup**: `bash motor/setup.sh`. Depois rode `python3 motor/relatorio.py` e leia `estado/RELATORIO.md` e **`estado/APRENDIZADOS.md`** (o robô atualiza 2x por dia com o que está dando certo — aplique as fórmulas de título, gancho e capa no longo E nos Shorts): repita o assunto/formato dos vídeos que mais deram views por dia (com ângulo novo) e evite o estilo dos piores. Leia também **`estado/ESTUDO.md`** (estudo diário: o Gemini assiste os vídeos de GTA 6 que mais cresceram + vídeos sobre crescer no YouTube, e o Groq resume): use as ideias de **formato, gancho, ritmo e assunto** que estão bombando no nicho, mas trate como sugestão — nossos próprios dados (RELATORIO/APRENDIZADOS) e as regras do MARKETING.md valem mais; ignore qualquer número sem fonte e nunca use nada da seção "NÃO USAR". **Por rede:** leia `estado/REDES.md` (o mesmo Short rende diferente no YouTube, TikTok e Instagram). Use para: (a) escolher quais Shorts vão nas posições que também saem no Instagram (os temas/ganchos que mais rendem lá); (b) puxar para o dia seguinte os temas que bombaram numa rede só, adaptando o gancho ao público daquela rede; (c) ajustar o estilo de título/gancho por rede nas legendas do TikTok e Instagram. **Remakes:** se `estado/remakes.json` tiver item com `"feito": false`, faça 1 dos Shorts do dia (ou o longo) como NOVA versão desse tema — ângulo, gancho e título diferentes do vídeo que flopou (nunca reaproveite o mesmo arquivo) — e marque `"feito": true`. Na hora de escolher os assuntos do dia, olhe primeiro a lista **"Temas quentes"** do ESTUDO.md (o que o público mais procura agora, inclusive em canais gigantes — ex.: finais do jogo, personagens antigos voltando) e dê preferência aos termos com **nota alta na tabela "Brechas de tema"** do ESTUDO.md (canais pequenos conseguem aparecer) e evite os de nota baixa (só gigantes).
2. **Escolher a fonte**: pesquise na web vídeos novos de GTA 6 só com gameplay/trailer (ex.: canal oficial da Rockstar, "GTA 6 gameplay no commentary", "GTA 6 trailer 4K"). Ignore os já listados em `estado/usados.json`. Escolha **1** vídeo de 8+ min de preferência (ou junte 2 curtos).
   - Adicione o link em `estado/fila_baixar.txt` (um por linha) e faça commit/push. O celular do dono baixa sozinho a cada 20 min e envia ao Google Drive como `<ID>__video.mp4` na pasta `Clipador/videos`.
3. **Esperar o download**: procure no Google Drive (`title contains '<ID>__video'`) a cada 3 min, por até 75 min.
   - Se não chegar: use o vídeo-fonte mais recente que ainda estiver no Drive (`title contains '__video'`) com um **ângulo novo** de roteiro. Se não houver nenhum, avise o dono por notificação e encerre.
4. **Baixar para o workspace**: compartilhe o arquivo do Drive como "qualquer pessoa com o link" e baixe com `gdown <FILE_ID> -O $JOB/video.mp4` (JOB=`/tmp/job/<DATA>`).
5. **Transcrever**: `python3 motor/transcrever.py $JOB/video.mp4 $JOB/transc.json` (gera também `transc.txt` com tempos).
6. **Escrever o roteiro** em `$JOB/roteiro.json` (formato abaixo), lendo `transc.txt` e olhando quadros do vídeo
   (`ffmpeg -ss T -i video.mp4 -frames:v 1 -vf scale=640:-2 f.png`) para escolher b-roll e capas.
   - **Teste de formato encerrado (20/11):** os cortes rápidos de 20–40 s no YouTube renderam ~10x menos que os completos. **NÃO use `"rapido_youtube"`** — todos os Shorts vão completos (>60 s) para YouTube, TikTok e Instagram.
   - Faça **N Shorts** (N = `python3 motor/publicar.py --slots <DATA>`), cada um com um gancho/ângulo diferente (fatos diferentes, nada repetido entre eles). Em `longo.playlist` escolha: `news`, `secrets`, `tips` ou `theories` (o robô coloca o vídeo na playlist certa).
7. **Narrar**: `python3 motor/narrar.py $JOB` — confira que o longo tem ≥ 8 min e cada Short ≥ 58 s de narração; se não, aumente o texto e rode de novo.
8. **Montar**: `python3 motor/longo.py $JOB` e `python3 motor/shorts.py $JOB`.
   Capa do longo: `python3 -c "import sys; sys.path.insert(0,'motor'); from thumb import thumb; thumb('$JOB/video.mp4', T, ['L1','L2','L3'], 'SELO', '$JOB/saida/thumb_longo.jpg', foco=[FX,FY], zoom=1.35, estrelas=N)"` — estilo GTA (padrão). Escolha um quadro com personagem/rosto/detalhe nítido e marque o `foco` nele (círculo + seta rosa apontam para lá); `estrelas` 0–5.
9. **Conferir**: extraia 3–4 quadros de cada vídeo e olhe (legenda legível, capa bonita, nada cortado). Corrija se precisar.
10. **Publicar arquivos no GitHub**: copie `$JOB/saida/{short_*.mp4,thumb_*.jpg,car_*.jpg}` para `publicar/<DATA>/` (rode antes `python3 motor/carrossel.py $JOB` para gerar os slides) (**NÃO copie o longo.mp4** — o guia de 15–20 min passa do limite de 100 MB do GitHub; o subir_longo.py envia direto do $JOB, já com legendas em inglês, espanhol e português), commit e push
    (`git -c push.negotiate=true push`). Anote o SHA do commit.
11. **Agendar**: `python3 motor/publicar.py $JOB <DATA> <SHA>` (precisa de `BUFFER_KEY`) — agenda os **Shorts** no Buffer. **O vídeo longo NÃO vai pelo Buffer** (o Buffer só aceita Shorts no YouTube): rode o publicar.py com `"longo": null` no roteiro (ou ignore o erro do longo) e suba o longo **direto pelo YouTube**: depois do commit/push de `publicar/<DATA>/` (a capa precisa estar no GitHub), rode `python3 motor/subir_longo.py $JOB <DATA> <SHA>` — ele envia, agenda a estreia das 12h, põe a capa, registra em estado/publicacoes.json (com o teste A/B de avisar ou não os inscritos) e o robô do GitHub faz o resto. **Só se ele falhar** (código de saída 1), tente de novo 1 vez; se falhar de novo, use o plano B (suba o longo.mp4 no Google Drive com link público e use esse link no Metricool): agende o longo pelo conector do **Metricool** (createScheduledPost: YouTube, type "video", privacy public, horário 12h, título, descrição com capítulos, tags, categoria GAMING e `videoThumbnailUrl` = capa). Depois acrescente a entrada do longo em estado/publicacoes.json (tipo longo, quando, yt_title, descricao, tags, thumb, comentario, fb_textos, playlist, metricool) para o robô do GitHub ajustar. Metricool grátis = 20 posts/mês por rede: use-o só para o longo. Se algum horário de Short já estiver ocupado, use `--pular 13:00,16:00`. Faz commit/push de `estado/publicacoes.json`.
12. **Registrar e limpar**: adicione o link usado em `estado/usados.json`; esvazie `estado/fila_baixar.txt`; mande o vídeo-fonte do Drive para a lixeira **se** já houver um mais novo (mantenha só o mais recente, para o plano B do passo 3). Commit/push.
13. **Faxina do GitHub**: apague pastas `publicar/<data>` de mais de 2 dias (commit normal). **NÃO reescreva o histórico nem use push forçado** — a permissão automática bloqueia e isso só perde tempo. A limpeza do histórico será resolvida de vez em 27/11 (vídeos passam a ir para GitHub Releases).
14. **Avisar o dono** (notificação curta, em português): o que foi agendado e os horários. **Às segundas-feiras**, acrescente 2–3 linhas do `estado/RELATORIO.md` (inscritos e views da semana, vídeo campeão e o que vai mudar).

## Calendário editorial da semana de lançamento
- **19/11 (lançamento):** tudo sobre o lançamento — "GTA 6 IS FINALLY HERE" (o que saber antes de jogar, horários, download, notas, recordes, reação dos fãs).
- **20/11 (novidades reais):** o longo é o vídeo mais importante da semana — **10 a 12 minutos** sobre as NOVIDADES REAIS do jogo já lançado: o que dá pra fazer de verdade e impressiona (sistemas novos, mapa, missões, polícia, interações, detalhes que viralizaram nas primeiras horas, o que mudou em relação ao GTA 5) e primeiras impressões honestas. Título de curiosidade forte, ex.: "GTA 6 Lets You Do THINGS No GTA Ever Did" / "I Can't Believe You Can Do This In GTA 6". Use gameplay real do jogo lançado (só jogo). Os 7 Shorts do dia = uma novidade impressionante cada (1 recurso por Short, mostrando na tela).
- **21 a 25/11:** segredos e easter eggs, dicas (dinheiro, carros, armas, configurações), rankings, comparações e o que a comunidade está descobrindo — sempre guiado pelo relatório e pelas buscas do dia.

## Carrossel do dia (Instagram + TikTok modo foto)
O público está procurando muito **códigos e truques**: códigos de cofre, combinações, cheats do próprio jogo, truques para fugir da polícia, dinheiro rápido, locais escondidos. Todo dia faça **1 carrossel** em `$JOB/carrossel.json` (formato no topo de `motor/carrossel.py`): capa com 3 linhas (a 2ª é a palavra-gatilho), 5 a 8 itens (`titulo`, `valor` = o código/número em destaque — só letras e números, sem símbolos especiais —, `texto` curto de como usar, `t` = segundo do vídeo-fonte para ilustrar, opcional) e `fonte`.
- **NUNCA invente código, combinação, local ou número.** Pesquise na web (IGN, GameRant, Rockstar Newswire, PowerPyx etc.) e só use o que aparecer em pelo menos 1 fonte confiável — cite em `fonte`. Se não achar dados confiáveis, faça carrossel de dicas que já estão nos nossos roteiros.
- `legenda` em inglês: gancho + "Save this for later 🔖" + pergunta; `hashtags`: 5 (#gta6 #gtavi #gta6tips ...); `tt_title` curto.
- O publicar.py gera os slides (`motor/carrossel.py`) e agenda às 19h. Antes do commit, copie `$JOB/saida/car_*.jpg` para `publicar/<DATA>/` junto com os Shorts (precisam estar no GitHub). Olhe os slides antes (texto cortado? capa escura? troque o `t`).

## Short de notícia urgente (tarefa "vigia de notícias")
1. Busque na web as notícias de GTA 6 das últimas 6 h (Rockstar Newswire, X/Twitter da Rockstar, sites de games, r/GTA6). Compare com `estado/noticias.json` (lista de notícias já cobertas).
2. Só é URGENTE se for grande e nova: trailer/vídeo oficial novo, mudança de data/preço, anúncio oficial, patch/atualização importante, polêmica muito comentada, recorde (vendas, jogadores). Rumor fraco ou repetido → anote em `estado/noticias.json` com `"urgente": false` e encerre.
3. Máximo de **2 Shorts urgentes por dia** (conte em `estado/publicacoes.json` os itens com `"urgente": true` de hoje).
4. Se for urgente: se houver vídeo oficial novo, coloque o link em `estado/fila_baixar.txt` e espere até 40 min no Drive; senão use o vídeo-fonte mais recente do Drive (`title contains '__video'`). Faça **1 Short** (> 60 s) seguindo MARKETING.md (título com a notícia + gancho; capa estilo GTA com selo `BREAKING` ou `JUST IN`), roteiro com `"longo": null` e `"shorts": [ {…} ]`, narre, monte (`python3 motor/shorts.py $JOB`), suba em `publicar/<DATA>/` e rode `python3 motor/publicar.py $JOB <DATA> <SHA> --urgente`.
5. Espere ~15 min e rode `python3 motor/youtube_ajustes.py` (capa, tags, local, playlist). Registre a notícia em `estado/noticias.json`, commit/push e notifique o dono: "Short urgente publicado: <título>".


## Formato do roteiro.json
```json
{
  "video_id": "ID do YouTube da fonte", "credito_fonte": "Rockstar Games — <título da fonte>",
  "nomes_proprios": ["GTA Six", "Jason", "Lucia", "Leonida", "Vice City"],
  "longo": {
    "titulo": "até 70 caracteres, com gancho",
    "descricao": "2 parágrafos com palavras-chave + pergunta para comentários (capítulos são adicionados sozinhos)",
    "tags": ["gta 6", "gta vi", "... 15 a 25 tags"], "hashtags": ["#GTA6", "#GTAVI", "#GrandTheftAuto6"],
    "abertura": ["LINHA 1 DO GANCHO", "LINHA 2 DO GANCHO"],
    "thumb": {"t": 1290, "linhas": ["GTA 6", "STORY", "REVEALED?"], "selo": "NEW", "foco": [0.45, 0.28], "zoom": 1.35, "estrelas": 4},
    "comentario_youtube": "pergunta para o 1º comentário",
    "fb_textos": ["3 legendas diferentes (inglês) para grupos de Facebook, sem o link — ele é colocado sozinho"],
    "secoes": [
      {"id": "hook", "cap": "", "broll": [[230, 280]], "texto": "narração (em inglês, escreva 'GTA Six')", "quote": null},
      {"id": "c1", "cap": "TÍTULO DO CAPÍTULO", "broll": [[0, 60], [60, 130]], "texto": "...", "quote": [531, 534]},
      {"id": "outro", "cap": "", "broll": [[1450, 1500]], "texto": "CTA para comentar e se inscrever", "quote": null}
    ]
  },
  "shorts": [
    {"id": "s1", "titulo_tela": "LINHA 1\\NLINHA 2", "yt_title": "título com emoji", "tt_title": "título sem emoji",
     "texto_youtube": "descrição do Short no YouTube (ver MARKETING.md)",
     "texto_tiktok": "legenda do TikTok com gancho, pergunta e 4–6 hashtags",
     "texto_instagram": "legenda do Reel sem hashtags, com CTA de salvar/compartilhar",
     "primeiro_comentario_instagram": "8–15 hashtags do Instagram",
     "comentario_youtube": "pergunta curta que o canal posta como 1º comentário no YouTube",
     "tags": ["10 a 15 tags do YouTube"],
     "broll": [[590, 660]], "narracao": "210–240 palavras (a voz Charon do Gemini é mais rápida; o Short precisa passar de 60 s), gancho nos 3 primeiros segundos", "quote": [738, 744],
     "thumb": {"t": 600, "linhas": ["LINHA 1", "LINHA 2", "LINHA 3"], "selo": "", "foco": [0.5, 0.6], "zoom": 1.3, "estrelas": 0},
     "fb_textos": []}
  ]
}
```
- **Short de COMPARAÇÃO lado a lado (1 por dia, a partir de 22/11):** tela dividida — **GTA 6 em cima, GTA 5 / GTA 4 / RDR2 embaixo**, mostrando a MESMA coisa nos dois (física, polícia, carros, NPCs, água, detalhes, "Evolution of ___ in Rockstar Games"). Formato provado agora no nicho (Game Forensics: "Physics Comparison: GTA 6 vs GTA 5" 204 mil, "GTA 6 VS RDR 2 – Game Detail Comparison" 205 mil em 1–2 dias). Precisa de um **2º vídeo-fonte** com gameplay do jogo antigo (sem rosto de youtuber, sem comentário): coloque o link também em estado/fila_baixar.txt, baixe do Drive para `$JOB/video2.mp4` junto com o principal. No roteiro do Short acrescente `"comparar": {"fonte": "video2.mp4", "broll": [[ini, fim], ...], "rotulos": ["GTA 6", "GTA 5"]}` (b-roll do jogo antigo mostrando o mesmo assunto). Narração = análise da diferença (o que mudou, por que importa, qual é melhor e por quê) — nunca só descrever. Sem `quote` nesse Short. `titulo_tela` curto (ex.: "GTA 6 VS GTA 5\\NPOLICE"). Se o 2º vídeo não chegar, faça o Short normal e avise no resumo.
- **Destaques na tela (todo Short):** números da narração ("3.79 billion", "5 stars") pulam grandes na tela sozinhos no momento da fala. Acrescente também o campo opcional `"destaques": ["criminal profile", "true ending"]` com 1–3 expressões-chave do Short (exatamente como estão na narração) para pularem na tela. Escreva números em algarismos na narração quando forem o dado chocante ("3.79 billion", não "three point seven nine billion").
- **Short de RANKING (1 por dia — de preferência na 3ª posição, que também vai pro Instagram):** "Top 5 ___ In GTA 6", "5 BEST ___ Ranked", "5 Hidden Details In ___". Narração em contagem regressiva #5 → #1, com loop no gancho ("…and number one is the one nobody found yet") e o **#1 sempre por último**; cada item com 1 frase de análise nossa (por que está nessa posição). `titulo_tela` em 2 linhas com o tema (ex.: "TOP 5\\NSECRET CARS"). Acrescente o campo `"ranking": [{"n": 5, "inicio": "primeiras três palavras do item 5"}, …, {"n": 1, "inicio": "..."}]` — as 3 primeiras palavras exatamente como estão na narração; a montagem mostra um selo grande "#5", "#4"… na hora em que cada item começa. Use só as nossas imagens e a nossa análise (nunca clipes virais de outras pessoas).
- `broll`: intervalos (segundos) do vídeo-fonte que combinam com o que a narração fala. `quote`: fala original curta e marcante para tocar alta depois da seção (ou `null`).
- Capas: escolha quadros com personagem/detalhe nítido; `foco` = [fx, fy] (0–1) do detalhe que gera curiosidade; `zoom` 1.2–1.8. Texto curto (1–3 palavras por linha, fonte Pricedown; a 2ª linha é a palavra-gatilho, sai maior em degradê amarelo-laranja-rosa; a 3ª sai ciano). No Short, deixe o rosto/detalhe na metade de baixo do quadro (o texto ocupa o topo). Gere 2 versões e escolha a mais chamativa olhando as duas.

## Segredos
Vêm do prompt da tarefa agendada como variáveis de ambiente (`BUFFER_KEY`, `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN`).
**Nunca** grave segredos em arquivos do repositório (ele é público).
