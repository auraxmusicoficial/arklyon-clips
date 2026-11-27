"""PRODUÇÃO DIÁRIA DO GTA 6 SEM CLAUDE (roda no GitHub Actions — 27/11/2026).
Faz sozinho o que a tarefa agendada do Claude fazia:
 1. escolhe a fonte (vídeo só de jogo) e pede ao celular baixar (estado/fila_baixar.txt -> Drive Clipador/videos);
 2. baixa do Drive (rclone), o Gemini olha quadros do vídeo e descreve as cenas com os tempos;
 3. escolhe os temas do dia (ESTUDO/BUSCAS/notícias/APRENDIZADOS, sem repetir) e PESQUISA os fatos na web (Groq
    browser_search, 2+ fontes — nunca inventar);
 4. o Gemini escreve roteiro.json (Shorts) e carrossel.json (2 posts de imagem) seguindo INSTRUCOES/MARKETING/SOCIAL;
 5. narra (Charon), monta (shorts.py, carrossel.py), confere durações;
 6. sobe os arquivos numa GitHub Release do dia (pub-AAAA-MM-DD) — nada de vídeo no histórico do git;
 7. agenda (publicar.py), registra, faz a faxina (releases > 3 dias, vídeo-fonte velho do Drive) e avisa no ntfy.
Uso: python3 motor/produzir.py [AAAA-MM-DD] [--teste]   (--teste = gera tudo mas não publica)
Precisa de: GEMINI_KEY, GROQ_KEY, BUFFER_KEY, YT_CLIENT_ID/SECRET/REFRESH_TOKEN, NTFY_TOPIC, rclone configurado, GH_TOKEN."""
import base64, glob, json, os, re, subprocess, sys, time, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
RAIZ = Path(__file__).resolve().parent.parent
EST = RAIZ / "estado"
BRT = timezone(timedelta(hours=-3))
REPO = "auraxmusicoficial/arklyon-clips"
MODELOS_GEMINI = ["gemini-3.8-flash", "gemini-flash-latest", "gemini-3-flash-preview"]
TESTE = "--teste" in sys.argv
REMOTO = None


def log(*a):
    print(*a, flush=True)


def avisar(msg):
    topico = os.environ.get("NTFY_TOPIC")
    log("AVISO:", msg)
    if topico and not TESTE:
        try:
            urllib.request.urlopen(urllib.request.Request("https://ntfy.sh/" + topico, msg.encode(), {"Title": "HQ Vault Clips"}), timeout=20)
        except Exception as e:
            log("ntfy falhou:", e)


def sh(cmd, **kw):
    return subprocess.run(cmd, shell=isinstance(cmd, str), check=True, text=True, capture_output=True, **kw).stdout


def ler(p, padrao=None):
    try:
        return json.loads(Path(p).read_text())
    except Exception:
        return padrao


# ---------------------------------------------------------------- IAs grátis
def gemini(partes, json_saida=False, max_saida=16000, temp=0.8):
    k = os.environ["GEMINI_KEY"]
    corpo = {"contents": [{"role": "user", "parts": partes}],
             "generationConfig": {"maxOutputTokens": max_saida, "temperature": temp, "mediaResolution": "MEDIA_RESOLUTION_LOW",
                                  **({"responseMimeType": "application/json"} if json_saida else {})}}
    ultimo = None
    for m in MODELOS_GEMINI:
        for tent in range(3):
            req = urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={k}",
                                         json.dumps(corpo).encode(), {"Content-Type": "application/json"})
            try:
                d = json.load(urllib.request.urlopen(req, timeout=400))
                txt = "".join(p.get("text", "") for p in d["candidates"][0]["content"].get("parts", [])).strip()
                if txt:
                    return txt
                ultimo = f"{m}: vazio"
            except urllib.error.HTTPError as e:
                ultimo = f"{m}: HTTP {e.code} {e.read()[:200]!r}"
                if e.code in (429, 500, 503) and tent < 2:
                    time.sleep(30 * (tent + 1)); continue
            except Exception as e:
                ultimo = f"{m}: {e}"
                if tent < 1:
                    time.sleep(10); continue
            break
    raise RuntimeError("Gemini falhou: " + str(ultimo))


def json_de(txt):
    txt = txt.strip()
    txt = re.sub(r"^```(json)?|```$", "", txt, flags=re.M).strip()
    i = min([x for x in (txt.find("{"), txt.find("[")) if x >= 0] or [0])
    return json.loads(txt[i:txt.rfind("}" if txt[i] == "{" else "]") + 1])


def pesquisar(pergunta):
    """Groq com busca na web embutida (grátis). Devolve texto com fatos e fontes."""
    for modelo in ("openai/gpt-oss-120b", "openai/gpt-oss-20b"):
        corpo = {"model": modelo, "tools": [{"type": "browser_search"}], "reasoning_effort": "medium",
                 "messages": [{"role": "user", "content": pergunta}], "max_tokens": 3000}
        for t in range(2):
            try:
                req = urllib.request.Request("https://api.groq.com/openai/v1/chat/completions", json.dumps(corpo).encode(), {
                    "Authorization": "Bearer " + os.environ["GROQ_KEY"], "Content-Type": "application/json", "User-Agent": "vault-clips"})
                r = json.load(urllib.request.urlopen(req, timeout=200))["choices"][0]["message"].get("content") or ""
                if r.strip():
                    return r.strip()
            except Exception as e:
                log("pesquisa falhou:", modelo, str(e)[:150]); time.sleep(25)
    return ""


# ---------------------------------------------------------------- 1. fonte
def yt_token():
    import youtube_ajustes as ya
    return ya.token()


def drive_videos():
    out = sh(["rclone", "lsjson", f"{REMOTO}Clipador/videos", "--files-only"])
    return sorted(json.loads(out or "[]"), key=lambda x: x["ModTime"], reverse=True)


def escolher_fonte():
    usados = set(ler(EST / "usados.json", []))
    usados_ids = {re.split(r"[/=]", u)[-1][:11] for u in usados}
    tok = yt_token()
    depois = (datetime.now(timezone.utc) - timedelta(days=6)).strftime("%Y-%m-%dT%H:%M:%SZ")
    ruim = re.compile(r"react|live|stream|podcast|facecam|reaction|my thoughts|first impressions|#shorts|rumou?r|leak|mod\b", re.I)
    cands = []
    for q in ("GTA 6 gameplay no commentary", "GTA 6 4K gameplay walkthrough", "GTA VI gameplay no commentary PS5", "Rockstar Games GTA VI"):
        url = ("https://www.googleapis.com/youtube/v3/search?part=snippet&type=video&maxResults=15&order=viewCount&videoDuration=long"
               f"&publishedAfter={depois}&relevanceLanguage=en&q={urllib.parse.quote(q)}")
        try:
            r = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"Authorization": "Bearer " + tok}), timeout=30))
        except Exception as e:
            log("busca de fonte falhou:", e); continue
        for it in r.get("items", []):
            vid, t = it["id"]["videoId"], it["snippet"]["title"]
            if vid in usados_ids or ruim.search(t) or not re.search(r"gta ?(6|vi)", t, re.I):
                continue
            cands.append((vid, t, it["snippet"]["channelTitle"]))
    vistos, lista = set(), []
    for c in cands:
        if c[0] not in vistos:
            vistos.add(c[0]); lista.append(c)
    return lista


def pedir_download(vid):
    fila = EST / "fila_baixar.txt"
    fila.write_text(f"https://youtu.be/{vid}\n")
    if not TESTE:
        git_salvar(f"robô produção: pedir download {vid}")


def obter_fonte(job):
    """Pede um vídeo novo ao celular e espera até 70 min no Drive; senão usa o mais recente que já está lá."""
    ja = drive_videos()
    hoje_cedo = datetime.now(timezone.utc) - timedelta(hours=20)
    recentes = [f for f in ja if f["Name"].endswith("__video.mp4")]
    escolhido = None
    lista = escolher_fonte()
    log("candidatos de fonte:", [c[1][:50] for c in lista[:5]])
    if lista:
        vid, titulo, canal = lista[0]
        pedir_download(vid)
        limite = time.time() + (5 * 60 if TESTE else 70 * 60)
        while time.time() < limite:
            achou = [f for f in drive_videos() if f["Name"].startswith(vid + "__video")]
            if achou:
                time.sleep(60)   # deixa terminar o envio
                escolhido = (achou[0], titulo, canal); break
            time.sleep(180)
    if not escolhido:
        if not recentes:
            raise RuntimeError("nenhum vídeo-fonte no Drive (o celular não baixou) — produção cancelada hoje")
        f = recentes[0]
        escolhido = (f, "", "")
        log("usando o vídeo-fonte mais recente do Drive:", f["Name"], "(novo não chegou)")
        avisar("O celular não baixou o vídeo-fonte novo a tempo — usei o mais recente do Drive com ângulos novos.")
    f, titulo, canal = escolhido
    sh(["rclone", "copyto", f"{REMOTO}Clipador/videos/{f['Name']}", str(job / "video.mp4")])
    vid = f["Name"].split("__")[0]
    return vid, titulo, canal


# ---------------------------------------------------------------- 2. cenas
def cenas(job):
    from PIL import Image, ImageDraw, ImageFont
    from comum import dur
    v = job / "video.mp4"; d = dur(v)
    passo = max(6, d / 96)
    fr = job / "quadros"; fr.mkdir(exist_ok=True)
    sh(["ffmpeg", "-v", "error", "-y", "-i", str(v), "-vf", f"fps=1/{passo:.2f},scale=320:-2", str(fr / "q%04d.jpg")])
    arqs = sorted(fr.glob("q*.jpg"))
    tempos = [i * passo for i in range(len(arqs))]
    fonte = ImageFont.truetype(str(RAIZ / "motor" / "fontes" / "Anton-Regular.ttf"), 28)
    folhas, partes = [], []
    for k in range(0, len(arqs), 16):
        grupo = arqs[k:k + 16]
        im0 = Image.open(grupo[0]); w, h = im0.size
        folha = Image.new("RGB", (w * 4, h * 4))
        for j, a in enumerate(grupo):
            im = Image.open(a); folha.paste(im, ((j % 4) * w, (j // 4) * h))
            dr = ImageDraw.Draw(folha)
            t = tempos[k + j]; x, y = (j % 4) * w + 6, (j // 4) * h + 4
            dr.rectangle((x - 4, y, x + 92, y + 36), fill=(0, 0, 0)); dr.text((x, y), f"{int(t)}s", font=fonte, fill=(255, 255, 0))
        p = job / f"folha{k // 16}.jpg"; folha.save(p, quality=80); folhas.append(p)
        partes.append({"inline_data": {"mime_type": "image/jpeg", "data": base64.b64encode(p.read_bytes()).decode()}})
    pedido = ("These are contact sheets of frames from a GTA 6 gameplay video; each frame is labeled with its time in seconds. "
              f"Video length: {int(d)} s. For EVERY labeled frame return one entry. JSON only: "
              '{"cenas": [{"t": 12, "desc": "short concrete description (place, vehicle, action, characters, police, weather, UI/menu)", '
              '"tags": ["car","police","beach","interior","menu","map","character","gunfight","night","city","water","phone"], '
              '"capa": 0-10 (how good as a thumbnail: sharp character/vehicle/detail, not menu/black), "foco": [x, y] (0-1, the most interesting detail)}]}')
    try:
        r = json_de(gemini(partes + [{"text": pedido}], json_saida=True, temp=0.3))
        cs = [c for c in r.get("cenas", []) if 0 <= float(c.get("t", -1)) < d]
    except Exception as e:
        log("AVISO: Gemini não descreveu as cenas:", e)
        cs = [{"t": round(t), "desc": "gameplay", "tags": [], "capa": 5, "foco": [0.5, 0.5]} for t in tempos]
    json.dump({"dur": d, "passo": passo, "cenas": cs}, open(job / "cenas.json", "w"), ensure_ascii=False)
    return d, passo, cs


# ---------------------------------------------------------------- 3. temas + pesquisa
def secao(txt, titulo_re, limite=4000):
    m = re.search(titulo_re, txt, re.I | re.M)
    if not m:
        return ""
    resto = txt[m.start():]
    fim = re.search(r"^#{1,2} ", resto[3:], re.M)
    return resto[: (fim.start() + 3) if fim else limite][:limite]


def contexto_canal():
    pub = ler(EST / "publicacoes.json", [])
    titulos = [p.get("yt_title") or (p.get("legenda") or "")[:80] for p in pub[-70:] if isinstance(p, dict)]
    titulos = [t for t in titulos if t][-60:]
    noticias = [n for n in ler(EST / "noticias.json", []) if isinstance(n, dict)][-12:]
    rd = lambda n: (EST / n).read_text() if (EST / n).exists() else ""
    return {"titulos": titulos, "noticias": noticias, "estudo": rd("ESTUDO.md")[:9000], "buscas": rd("BUSCAS.md")[:3500],
            "aprendizados": rd("APRENDIZADOS.md")[:3500], "redes": rd("REDES.md")[:2500], "analytics": rd("YT_ANALYTICS.md")[:2500]}


def escolher_temas(n_shorts, ctx, cenas_txt):
    pedido = f"""You plan today's content for "HQ Vault Clips", a GTA 6 tips/secrets channel (game released 19 Nov 2026; audience US/UK).
Pick {n_shorts} Short topics and 2 image-post topics. Rules:
- Topics people actively SEARCH/want now (use HOT TOPICS, real searches, news, what worked for us). Prefer high-score gaps.
- Every Short gives usable value: a tip, steps, a ranking, a comparison, a hidden detail. One Short must be a TOP 5 RANKING.
- NOTHING repeated from our recent titles below (no same subject/angle).
- Must be illustratable with generic GTA 6 gameplay (scene list below).
- Image posts: 2 DIFFERENT formats among: lista (cheats/codes/locations/money methods), vs (GTA V vs GTA VI), tag (tag a friend), teaser (2 pages), unico (single image). Only topics with checkable facts.
- Any unprocessed URGENT news (urgente true, produzido false) becomes Short #1.
Return JSON only: {{"shorts": [{{"tema": "...", "angulo": "hook/angle", "tipo": "dica|ranking|segredo|noticia|comparacao", "pesquisa": "web search question in English to verify the facts"}}],
 "posts": [{{"tema": "...", "formato": "lista|vs|tag|teaser|unico", "pesquisa": "..."}}]}}

HOT TOPICS / STUDY (our daily study):
{ctx['estudo']}

REAL SEARCHES (YouTube autocomplete):
{ctx['buscas']}

WHAT WORKED FOR US:
{ctx['aprendizados']}
{ctx['redes']}

NEWS LOG: {json.dumps(ctx['noticias'], ensure_ascii=False)[:2500]}

OUR RECENT TITLES (do not repeat): {json.dumps(ctx['titulos'], ensure_ascii=False)}

SCENES AVAILABLE IN TODAY'S FOOTAGE: {cenas_txt[:2500]}"""
    return json_de(gemini([{"text": pedido}], json_saida=True, max_saida=4000))


def fatos(tema, pergunta):
    q = (f"GTA 6 (Grand Theft Auto VI, released November 19, 2026). Research this for a short video: {tema}. {pergunta}\n"
         "Search the web (game guides like IGN, GameSpot, Polygon, PC Gamer, Eurogamer, Rockstar Newswire, Reddit r/GTA6, wikis). "
         "Return a bullet list of 6-12 concrete, VERIFIED facts (exact names, numbers, steps, locations, codes) — only facts that at least 2 "
         "sources agree on; mark anything with a single source as [1 SOURCE]. Under each fact list the source sites. If you can't verify, say so. English.")
    return pesquisar(q)


# ---------------------------------------------------------------- 4. roteiro
def regras_texto():
    ins = (RAIZ / "INSTRUCOES.md").read_text()
    mk = (RAIZ / "MARKETING.md").read_text()
    soc = (RAIZ / "SOCIAL.md").read_text()
    partes = [secao(ins, r"^## ⚠️ ORIGINALIDADE", 3000), secao(ins, r"^## 🇺🇸 IDIOMA", 800), secao(ins, r"^## Direitos autorais", 900),
              secao(ins, r"^## Formato do roteiro", 9000),
              secao(mk, r"^## 🏆", 2500), secao(mk, r"^## 1c\.", 5000), secao(mk, r"^## 3\. YouTube Shorts", 2500),
              secao(mk, r"^## 4\. TikTok", 1500), secao(mk, r"^## 5\. Instagram", 1500), secao(mk, r"^## 5b\.", 2000),
              soc[:3800]]
    return "\n\n".join(p for p in partes if p)


ESQUEMA = """OUTPUT: one JSON object {"roteiro": {...}, "carrossel": {"carrosseis": [...]}}.
roteiro = {"video_id": "<source id>", "credito_fonte": "<credit>", "nomes_proprios": [...], "longo": null, "shorts": [ ... ]}
Each Short object MUST have exactly these keys:
 id ("s1","s2",...), titulo_tela ("LINE 1\\\\NLINE 2", max 2 short lines), yt_title (with 1 emoji, true and catchy, <=70 chars),
 tt_title (no emoji), texto_youtube, texto_tiktok (hook + question + 4-6 hashtags), texto_instagram (no hashtags, CTA save/share),
 primeiro_comentario_instagram (8-15 hashtags), comentario_youtube (short question), tags (10-15),
 narracao (210-240 words, English, write 'GTA Six' instead of GTA 6, numbers in digits when they are the shocking data, hook in first 3 s,
   curiosity loops, >=40% own analysis/opinion, ends with a follow CTA), trilha ("acao"|"noite"|"sol"),
 broll: [[start,end], ...] 5-8 ranges in seconds from the SCENE LIST that match what is said (each 6-15 s, all different, inside the video),
 quote: null, cartoes: 3-5 objects {"quando": "first 2-4 words of the narration sentence where it appears, EXACTLY as written in narracao", "texto": "LINE1\\\\NLINE2" (<=22 chars per line)},
 destaques: 1-3 expressions copied exactly from narracao,
 thumb: {"t": <scene time with high capa score>, "linhas": ["L1","L2","L3"] (1-3 words each), "selo": "" or short badge, "foco": [x,y], "zoom": 1.3, "estrelas": 0-5},
 fb_textos: [].
The ranking Short also has "ranking": [{"n":5,"inicio":"first three words of item 5 exactly as in narracao"}, ... down to n 1], countdown #5 -> #1, #1 last.
Use the 'cartoes' to carry our original info (tip, number, step) — never repeat the title.
carrossel.carrosseis = exactly 2 posts (first goes out 19:00, second 10:30), each:
 {"id": "c1"/"c2", "formato": "...", "capa": ["L1","L2","L3"], "selo": "SAVE THIS" (or similar), "fundo": {"video": "video.mp4", "t": <scene time>},
  "itens": [{"titulo": "...", "valor": "...", "texto": "..."}] (format rules in SOCIAL.md / carrossel.py), "fonte": "sites the facts came from",
  "legenda": "English caption per SOCIAL.md", "tt_title": "...", "hashtags": "#gta6 #gtavi ... (5)"}
Fields per format: lista -> itens [{"titulo","valor" (code/number, optional),"setas" (D-pad list like ["Up","Right"], ONLY if verified),"texto","t" (scene time, optional)}] 4-8 items;
 vs -> itens [{"titulo": aspect, "a": "GTA V fact", "b": "GTA VI fact"}] 3-6 items, plus "pergunta"; tag -> itens [{"texto": funny relatable line, "img": {"video":"video.mp4","t":<scene>}}] 1-3 items, capa[1] = who to tag (e.g. "GETAWAY DRIVER");
 teaser -> "img": {"video":"video.mp4","t":..}, capa = the question/hook lines, "resposta": the answer text; unico -> "img": {...}, capa = 1-3 lines with one strong fact.
ABSOLUTE RULE: every fact (names, numbers, codes, steps, locations) must come from the RESEARCH notes below (2+ sources). If a fact is marked [1 SOURCE] or missing, don't state it as fact — use analysis/opinion instead. Never invent cheat codes or button sequences.
All published text in American English. No markdown, no labels like "Hook:" in captions."""


def escrever(temas, pesquisas, cenas_txt, video_id, credito, n):
    regras = regras_texto()
    notas = "\n\n".join(f"### RESEARCH for: {t}\n{p}" for t, p in pesquisas)
    pedido = f"""You are the producer of the GTA 6 channel "HQ Vault Clips". Write today's {n} Shorts and 2 image posts.

CHANNEL RULES (Portuguese/English notes from the owner — follow them):
{regras}

{ESQUEMA}

TODAY'S PLAN: {json.dumps(temas, ensure_ascii=False)}

{notas}

SCENE LIST of the source video (time s: description; capa = thumbnail score):
{cenas_txt}

source video id: {video_id}; credit: {credito}"""
    return json_de(gemini([{"text": pedido}], json_saida=True, max_saida=30000, temp=0.75))


def palavras(s):
    return re.findall(r"[a-z0-9']+", s.lower())


def contem(narr, trecho):
    a, b = palavras(narr), palavras(trecho)
    return bool(b) and any(a[i:i + len(b)] == b for i in range(len(a) - len(b) + 1))


def validar(saida, n, d):
    """Confere e conserta o que dá; devolve lista de problemas que precisam de reescrita."""
    prob = []
    r = saida.get("roteiro") or {}
    sh_ = r.get("shorts") or []
    if len(sh_) < n:
        prob.append(f"only {len(sh_)} shorts, need {n}")
    for i, s in enumerate(sh_):
        s["id"] = f"s{i + 1}"
        faltam = [k for k in ("titulo_tela", "yt_title", "tt_title", "texto_youtube", "texto_tiktok", "texto_instagram", "narracao", "broll", "thumb", "tags") if not s.get(k)]
        if faltam:
            prob.append(f"{s['id']}: missing {faltam}"); continue
        npal = len(palavras(s["narracao"]))
        if npal < 200 or npal > 260:
            prob.append(f"{s['id']}: narracao has {npal} words, must be 210-240")
        br = []
        for a, b in s["broll"]:
            a, b = max(0, float(a)), min(d - 1, float(b))
            if b - a >= 2:
                br.append([round(a, 1), round(b, 1)])
        if not br:
            br = [[round(d * k / 7, 1), round(d * k / 7 + 10, 1)] for k in range(1, 6)]
        s["broll"] = br
        s["quote"] = None
        s["cartoes"] = [c for c in s.get("cartoes", []) if c.get("quando") and contem(s["narracao"], c["quando"])]
        if len(s["cartoes"]) < 3:
            prob.append(f"{s['id']}: needs 3-5 cartoes whose 'quando' is copied EXACTLY from narracao")
        s["destaques"] = [x for x in s.get("destaques", []) if contem(s["narracao"], x)]
        if s.get("ranking"):
            ok = [x for x in s["ranking"] if contem(s["narracao"], x.get("inicio", ""))]
            if len(ok) < len(s["ranking"]):
                prob.append(f"{s['id']}: ranking 'inicio' must be the exact first 3 words of each item in narracao")
            s["ranking"] = ok
        th = s["thumb"]; th["t"] = min(max(0, float(th.get("t", d / 2))), d - 1)
        th.setdefault("linhas", ["GTA 6"]); th.setdefault("foco", [0.5, 0.55]); th.setdefault("zoom", 1.3)
        for k in ("texto_youtube", "texto_tiktok", "texto_instagram"):
            s[k] = re.sub(r"\*\*|__|^#+ |^(Hook|Caption|CTA|Description)\s*:\s*", "", s[k], flags=re.M | re.I).strip()
    cs = (saida.get("carrossel") or {}).get("carrosseis") or []
    if len(cs) < 2:
        prob.append("carrossel needs exactly 2 posts")
    for j, c in enumerate(cs[:2]):
        c["id"] = f"c{j + 1}"
        if (not c.get("itens") and c.get("formato") not in ("teaser", "unico", "vs")) or not c.get("capa") or not c.get("legenda"):
            prob.append(f"{c['id']}: missing itens/capa/legenda")
        f = c.get("fundo") or {}
        if f:
            c["fundo"] = {"video": "video.mp4", "t": min(max(0, float(f.get("t", d / 3))), d - 1)}
    return prob


def corrigir(saida, prob):
    pedido = ("Fix this JSON so it satisfies ALL the problems listed. Keep everything else the same; return the full corrected JSON only.\n"
              f"PROBLEMS: {json.dumps(prob)}\nJSON:\n{json.dumps(saida, ensure_ascii=False)}")
    return json_de(gemini([{"text": pedido}], json_saida=True, max_saida=30000, temp=0.4))


# ---------------------------------------------------------------- 6. release + git
def git_salvar(msg):
    subprocess.run(["python3", "-c", f"import sincronizar; sincronizar.main({msg!r})"], cwd=RAIZ / "motor", check=False)


def release(data, arquivos):
    tag = f"pub-{data}"
    env = dict(os.environ)
    if subprocess.run(["gh", "release", "view", tag, "-R", REPO], capture_output=True, env=env).returncode != 0:
        sh(["gh", "release", "create", tag, "-R", REPO, "--title", f"Publicações {data}", "--notes",
            "Arquivos temporários do robô (apagados depois de 3 dias).", "--latest=false"], env=env)
    for a in arquivos:
        sh(["gh", "release", "upload", tag, str(a), "-R", REPO, "--clobber"], env=env)
    return f"https://github.com/{REPO}/releases/download/{tag}"


def limpar_releases(dias=3):
    lim = (datetime.now(BRT) - timedelta(days=dias)).strftime("%Y-%m-%d")
    out = sh(["gh", "release", "list", "-R", REPO, "--limit", "100", "--json", "tagName"])
    for r in json.loads(out or "[]"):
        t = r["tagName"]
        if t.startswith("pub-") and t[4:] < lim:
            subprocess.run(["gh", "release", "delete", t, "-R", REPO, "--yes", "--cleanup-tag"], capture_output=True)
            log("release apagada:", t)


def limpar_drive():
    vs = [f for f in drive_videos() if f["Name"].endswith("__video.mp4")]
    for f in vs[1:]:   # fica só o mais recente (plano B do dia seguinte)
        subprocess.run(["rclone", "deletefile", f"{REMOTO}Clipador/videos/{f['Name']}"], capture_output=True)
        log("Drive: apagado", f["Name"])


# ---------------------------------------------------------------- principal
def main():
    global REMOTO
    for k, v in json.loads(os.environ.get("VAULT_SECRETS", "{}")).items():
        os.environ.setdefault(k, v)
    data = next((a for a in sys.argv[1:] if re.fullmatch(r"\d{4}-\d{2}-\d{2}", a)), datetime.now(BRT).strftime("%Y-%m-%d"))
    REMOTO = sh(["rclone", "listremotes"]).split()[0]
    import publicar
    agora = datetime.now(BRT)
    slots = [h for h in publicar.slots_shorts(data) if publicar.quando(data, h)[1] > agora + timedelta(minutes=50)]
    pub = ler(EST / "publicacoes.json", [])
    ja = [p for p in pub if isinstance(p, dict) and p.get("tipo") == "short" and str(p.get("quando", "")).startswith(data) and not p.get("urgente")]
    if ja and not TESTE:
        log("já tem Shorts agendados para", data, "— nada a fazer"); return
    n = len(slots) if not TESTE else max(1, len(slots))
    if n == 0:
        log("sem horários livres hoje"); return
    job = Path(f"/tmp/job/{data}"); job.mkdir(parents=True, exist_ok=True)
    log(f"== produção {data}: {n} Shorts + 2 posts")

    vid, titulo, canal = obter_fonte(job)
    credito = f"{canal} — {titulo}" if titulo else "Rockstar Games — GTA VI gameplay"
    d, passo, cs = cenas(job)
    cenas_txt = "\n".join(f"{int(float(c['t']))}s: {c.get('desc', '')} [capa {c.get('capa', 5)}]" for c in cs)
    log(f"fonte {vid} ({d / 60:.1f} min), {len(cs)} cenas")

    ctx = contexto_canal()
    temas = escolher_temas(n, ctx, cenas_txt)
    log("temas:", json.dumps(temas, ensure_ascii=False)[:1500])
    pesquisas = []
    for t in (temas.get("shorts", [])[:n] + temas.get("posts", [])[:2]):
        p = fatos(t["tema"], t.get("pesquisa", ""))
        pesquisas.append((t["tema"], p or "NO VERIFIED FACTS FOUND — use only analysis/opinion, no specific claims."))
        log("pesquisa:", t["tema"][:60], len(p), "chars")
        time.sleep(8)

    saida = escrever(temas, pesquisas, cenas_txt, vid, credito, n)
    for tent in range(3):
        prob = validar(saida, n, d)
        if not prob:
            break
        log("corrigindo:", prob)
        saida = corrigir(saida, prob)
    prob = validar(saida, n, d)
    if prob:
        log("AVISO: problemas restantes (seguindo assim mesmo):", prob)
    r = saida["roteiro"]; r["shorts"] = r["shorts"][:n]; r["longo"] = None
    r["video_id"] = vid; r["credito_fonte"] = credito
    r.setdefault("nomes_proprios", ["GTA Six", "Jason", "Lucia", "Leonida", "Vice City"])
    json.dump(r, open(job / "roteiro.json", "w"), ensure_ascii=False, indent=1)
    json.dump({"carrosseis": saida["carrossel"]["carrosseis"][:2]}, open(job / "carrossel.json", "w"), ensure_ascii=False, indent=1)
    json.dump(pesquisas, open(job / "pesquisas.json", "w"), ensure_ascii=False, indent=1)
    json.dump({"palavras": []}, open(job / "transc.json", "w"))   # sem citações do áudio original (quote: null)

    M = RAIZ / "motor"
    for passo_cmd in (["narrar.py", str(job)], ["shorts.py", str(job)], ["carrossel.py", str(job)]):
        log("rodando", passo_cmd[0])
        subprocess.run(["python3", str(M / passo_cmd[0])] + passo_cmd[1:], check=True, cwd=RAIZ)

    saida_dir = job / "saida"
    from comum import dur
    curtos = [s["id"] for s in r["shorts"] if dur(saida_dir / f"short_{s['id']}.mp4") < 58]
    if curtos:
        log("AVISO: Shorts com menos de 58 s:", curtos)
    arquivos = sorted(glob.glob(str(saida_dir / "short_*.mp4")) + glob.glob(str(saida_dir / "thumb_*.jpg"))
                      + glob.glob(str(saida_dir / "car_*.jpg")) + glob.glob(str(saida_dir / "reel_*.mp4")))
    if TESTE:
        log("TESTE: arquivos gerados", [Path(a).name for a in arquivos]); return

    base = release(data, arquivos)
    os.environ["PUB_BASE"] = base
    publicar.main(job, data, "release")

    usados = ler(EST / "usados.json", [])
    usados.append(f"https://youtu.be/{vid}")
    (EST / "usados.json").write_text(json.dumps(usados, ensure_ascii=False, indent=1))
    (EST / "fila_baixar.txt").write_text("")
    try:
        limpar_releases(); limpar_drive()
    except Exception as e:
        log("faxina falhou:", e)
    git_salvar(f"robô produção {data}: {n} Shorts + 2 posts (sem Claude)")

    pl = [p for p in ler(EST / "publicacoes.json", []) if isinstance(p, dict) and str(p.get("quando", "")).startswith(data)]
    linhas = []
    for p in pl:
        h = datetime.fromisoformat(p["quando"]).astimezone(BRT).strftime("%Hh%M")
        linhas.append(f"• {h} {'Short' if p.get('tipo') == 'short' else 'Post'}: {(p.get('yt_title') or p.get('legenda') or '')[:55]}")
    avisar(f"Robô produziu {data} sozinho (sem Claude) ✅\n" + "\n".join(linhas))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback; traceback.print_exc()
        avisar(f"⚠️ Produção do GTA falhou hoje: {str(e)[:200]}")
        sys.exit(1)
