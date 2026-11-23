# HQ Vault — guia do robô social media (posts de imagem: carrossel, 2 páginas, estático)

Escrito em 23/11/2026 a partir de pesquisa (estudos de Instagram 2026 + o que os sites e perfis de GTA 6 estão publicando
na semana do lançamento). Vale para Instagram e TikTok modo foto. Tudo que é publicado: INGLÊS americano.

## 1. Quem é o público
- Jogadores de GTA 6 nos EUA e Reino Unido (os dados do nosso Instagram mostram a maior parte das views vindo de lá),
  homens 16–34, jogando no PS5/Xbox desde 19/11.
- O que eles querem AGORA (primeiras semanas do jogo): **atalhos e vantagens** (cheats de D-pad, códigos de cofre,
  dinheiro rápido, fugir da polícia), **comparar com o GTA 5** (nostalgia + discussão) e **se identificar** (Jason/Lucia,
  "seu parceiro de crime").
- Eles salvam o que vão usar no jogo e mandam para o amigo com quem jogam. **Salvar e enviar por DM são os sinais mais
  fortes do Instagram em 2026** — o post tem que ser útil (salvar) ou provocar (mandar para o amigo / comentar).

## 2. Formatos (campo "formato" no carrossel.json — ver motor/carrossel.py)
| formato | o que é | objetivo | quando |
|---|---|---|---|
| `lista` | capa + 5–8 itens + "save this/follow" (7–10 slides é o que mais rende) | SALVAR | 3x/semana — cheats, códigos de cofre, locais, dinheiro |
| `vs` | GTA V x GTA VI lado a lado ("LIKE = V • COMMENT = VI"), 1 página ou com 2–4 comparações | COMENTAR/DEBATER | 2x/semana |
| `tag` | "Tag your partner in crime / your Lucia / the friend who..." (1–3 páginas) | ENVIAR/MARCAR | 1x/semana |
| `teaser` | 2 páginas: gancho/pergunta → resposta ("swipe for the answer") | DESLIZAR + SALVAR | 1x/semana |
| `unico` | 1 imagem: enquete/pergunta forte ("driver, shooter or the planner?") | COMENTAR | quando sobrar espaço |
Até **2 posts de imagem por dia** (10h30 e 19h). Varie o formato — nunca 2 iguais no mesmo dia.

### Itens com controle (cheats)
Use `"setas": ["Up","Right","Down",...]` — o robô desenha as setas do D-pad (visual nosso, mais fácil de entender que texto).
Sempre diga como ativar (hold L1+R1 / LB+RB) e o requisito para desbloquear (ex.: "finish the story").

## 3. Regra anti-fake news (OBRIGATÓRIA)
1. Todo dado (código, combinação, sequência de cheat, local, número, requisito) precisa aparecer em **pelo menos 2 fontes
   confiáveis que concordem** (ex.: GamesRadar, IGN, GTABase, KeenGamer, PowerPyx, Rockstar Newswire). Se as fontes
   discordam ou dizem "TBA/not discovered", NÃO publique aquele item.
2. Escreva as fontes em `"fonte"` (aparece no último slide da lista).
3. Opinião e enquete (vs, tag, unico) podem ser livres, mas os FATOS citados nelas seguem a regra 1.
4. Nunca rumor como fato. Nada de vazamento.

## 4. O que está engajando (como descobrir todo dia)
- Pesquise na web: "GTA 6 cheats", "GTA 6 safe codes", "GTA 6 money", "GTA 6 vs GTA 5", "GTA 6 tips" + notícias do dia.
  Assunto que aparece em vários sites grandes nas últimas 48 h = assunto que o público está procurando.
- Olhe `estado/REDES.md` e `estado/CONTROLE.md`: os posts e Reels nossos que mais renderam no Instagram mostram o tema
  certo — repita o tema com outro formato (ex.: Reel de cofre bombou → carrossel de códigos de cofre).
- Refaça do NOSSO jeito: identidade GTA (Pricedown, neon rosa/ciano, Vice City) + marca HQ VAULT + setas/cards nossos.
  Nunca copie a arte de outro perfil.

## 5. Legenda (inglês)
Linha 1 = gancho que pede a ação ("Save this before your next robbery 🔖" / "Comment V or VI 👇" / "Tag your getaway driver").
Linha 2 = 1 frase de valor. Linha 3 = pergunta. Depois 5 hashtags (#gta6 #gtavi + 3 do tema). Máx. 2 emojis.
