# Vault Clips — rotina diária de produção (para o Claude)

Canal: **HQ Vault Clips** (YouTube) · TikTok **@thevaultclipsof** · Instagram **@hqvaultclips**. Tudo em **inglês**.
Meta diária (horário de Brasília): **12h vídeo longo** + Shorts em **13h · 16h · 21h**.
**Semana de lançamento do GTA 6 (19 a 25/11/2026): 7 Shorts por dia — 9h · 11h · 13h · 16h · 18h · 20h · 22h** (no Instagram só os de 13h, 18h e 22h: coloque os 3 Shorts mais fortes nessas posições do roteiro — 3ª, 5ª e 7ª). Confira com `python3 motor/publicar.py --slots <DATA>` quantos Shorts fazer.

## Regras de conteúdo (do dono do canal)
- Tema: **GTA 6** (hype). Vídeos-fonte **só com o jogo** (trailers, gameplay, extended look, compilações sem facecam/sem pessoa reagindo). React só se não houver outra fonte, e só para Shorts.
- **Shorts/Reels/TikToks com mais de 60 s** (narração de 175–210 palavras + citação opcional).
- **Vídeo longo de 8 a 10 min** (narração de 1.150–1.400 palavras), 16:9, roteiro **original** com análise/opinião — nunca só repostar.
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
1. **Setup**: `bash motor/setup.sh`. Depois rode `python3 motor/relatorio.py` e leia `estado/RELATORIO.md`: repita o assunto/formato dos vídeos que mais deram views por dia (com ângulo novo) e evite o estilo dos piores.
2. **Escolher a fonte**: pesquise na web vídeos novos de GTA 6 só com gameplay/trailer (ex.: canal oficial da Rockstar, "GTA 6 gameplay no commentary", "GTA 6 trailer 4K"). Ignore os já listados em `estado/usados.json`. Escolha **1** vídeo de 8+ min de preferência (ou junte 2 curtos).
   - Adicione o link em `estado/fila_baixar.txt` (um por linha) e faça commit/push. O celular do dono baixa sozinho a cada 20 min e envia ao Google Drive como `<ID>__video.mp4` na pasta `Clipador/videos`.
3. **Esperar o download**: procure no Google Drive (`title contains '<ID>__video'`) a cada 3 min, por até 75 min.
   - Se não chegar: use o vídeo-fonte mais recente que ainda estiver no Drive (`title contains '__video'`) com um **ângulo novo** de roteiro. Se não houver nenhum, avise o dono por notificação e encerre.
4. **Baixar para o workspace**: compartilhe o arquivo do Drive como "qualquer pessoa com o link" e baixe com `gdown <FILE_ID> -O $JOB/video.mp4` (JOB=`/tmp/job/<DATA>`).
5. **Transcrever**: `python3 motor/transcrever.py $JOB/video.mp4 $JOB/transc.json` (gera também `transc.txt` com tempos).
6. **Escrever o roteiro** em `$JOB/roteiro.json` (formato abaixo), lendo `transc.txt` e olhando quadros do vídeo
   (`ffmpeg -ss T -i video.mp4 -frames:v 1 -vf scale=640:-2 f.png`) para escolher b-roll e capas.
   - Faça **N Shorts** (N = `python3 motor/publicar.py --slots <DATA>`), cada um com um gancho/ângulo diferente (fatos diferentes, nada repetido entre eles). Em `longo.playlist` escolha: `news`, `secrets`, `tips` ou `theories` (o robô coloca o vídeo na playlist certa).
7. **Narrar**: `python3 motor/narrar.py $JOB` — confira que o longo tem ≥ 8 min e cada Short ≥ 58 s de narração; se não, aumente o texto e rode de novo.
8. **Montar**: `python3 motor/longo.py $JOB` e `python3 motor/shorts.py $JOB`.
   Capa do longo: `python3 -c "import sys; sys.path.insert(0,'motor'); from thumb import thumb; thumb('$JOB/video.mp4', T, ['L1','L2','L3'], 'SELO', '$JOB/saida/thumb_longo.jpg', foco=[FX,FY], zoom=1.35, estrelas=N)"` — estilo GTA (padrão). Escolha um quadro com personagem/rosto/detalhe nítido e marque o `foco` nele (círculo + seta rosa apontam para lá); `estrelas` 0–5.
9. **Conferir**: extraia 3–4 quadros de cada vídeo e olhe (legenda legível, capa bonita, nada cortado). Corrija se precisar.
10. **Publicar arquivos no GitHub**: copie `$JOB/saida/{longo.mp4,short_*.mp4,thumb_*.jpg}` para `publicar/<DATA>/`, commit e push
    (`git -c push.negotiate=true push`). Anote o SHA do commit.
11. **Agendar**: `python3 motor/publicar.py $JOB <DATA> <SHA>` (precisa de `BUFFER_KEY`) — agenda os **Shorts** no Buffer. **O vídeo longo NÃO vai pelo Buffer** (o Buffer só aceita Shorts no YouTube): rode o publicar.py com `"longo": null` no roteiro (ou ignore o erro do longo) e agende o longo pelo conector do **Metricool** (createScheduledPost: YouTube, type "video", privacy public, horário 12h, título, descrição com capítulos, tags, categoria GAMING e `videoThumbnailUrl` = capa). Depois acrescente a entrada do longo em estado/publicacoes.json (tipo longo, quando, yt_title, descricao, tags, thumb, comentario, fb_textos, playlist, metricool) para o robô do GitHub ajustar. Metricool grátis = 20 posts/mês por rede: use-o só para o longo. Se algum horário de Short já estiver ocupado, use `--pular 13:00,16:00`. Faz commit/push de `estado/publicacoes.json`.
12. **Registrar e limpar**: adicione o link usado em `estado/usados.json`; esvazie `estado/fila_baixar.txt`; mande o vídeo-fonte do Drive para a lixeira **se** já houver um mais novo (mantenha só o mais recente, para o plano B do passo 3). Commit/push.
13. **Faxina do GitHub**: apague pastas `publicar/<data>` de mais de 2 dias e reescreva o histórico para não acumular espaço:
    `git checkout --orphan novo && git add -A && git commit -m "faxina" && git branch -D main && git branch -m main && git push -f origin main`.
14. **Avisar o dono** (notificação curta, em português): o que foi agendado e os horários. **Às segundas-feiras**, acrescente 2–3 linhas do `estado/RELATORIO.md` (inscritos e views da semana, vídeo campeão e o que vai mudar).

## Calendário editorial da semana de lançamento
- **19/11 (lançamento):** tudo sobre o lançamento — "GTA 6 IS FINALLY HERE" (o que saber antes de jogar, horários, download, notas, recordes, reação dos fãs).
- **20/11 (novidades reais):** o longo é o vídeo mais importante da semana — **10 a 12 minutos** sobre as NOVIDADES REAIS do jogo já lançado: o que dá pra fazer de verdade e impressiona (sistemas novos, mapa, missões, polícia, interações, detalhes que viralizaram nas primeiras horas, o que mudou em relação ao GTA 5) e primeiras impressões honestas. Título de curiosidade forte, ex.: "GTA 6 Lets You Do THINGS No GTA Ever Did" / "I Can't Believe You Can Do This In GTA 6". Use gameplay real do jogo lançado (só jogo). Os 7 Shorts do dia = uma novidade impressionante cada (1 recurso por Short, mostrando na tela).
- **21 a 25/11:** segredos e easter eggs, dicas (dinheiro, carros, armas, configurações), rankings, comparações e o que a comunidade está descobrindo — sempre guiado pelo relatório e pelas buscas do dia.

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
     "broll": [[590, 660]], "narracao": "175–210 palavras, gancho nos 3 primeiros segundos", "quote": [738, 744],
     "thumb": {"t": 600, "linhas": ["LINHA 1", "LINHA 2", "LINHA 3"], "selo": "", "foco": [0.5, 0.6], "zoom": 1.3, "estrelas": 0},
     "fb_textos": []}
  ]
}
```
- `broll`: intervalos (segundos) do vídeo-fonte que combinam com o que a narração fala. `quote`: fala original curta e marcante para tocar alta depois da seção (ou `null`).
- Capas: escolha quadros com personagem/detalhe nítido; `foco` = [fx, fy] (0–1) do detalhe que gera curiosidade; `zoom` 1.2–1.8. Texto curto (1–3 palavras por linha, fonte Pricedown; a 2ª linha é a palavra-gatilho, sai maior em degradê amarelo-laranja-rosa; a 3ª sai ciano). No Short, deixe o rosto/detalhe na metade de baixo do quadro (o texto ocupa o topo). Gere 2 versões e escolha a mais chamativa olhando as duas.

## Segredos
Vêm do prompt da tarefa agendada como variáveis de ambiente (`BUFFER_KEY`, `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN`).
**Nunca** grave segredos em arquivos do repositório (ele é público).
