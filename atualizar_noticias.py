#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
atualizar_noticias.py  -  baixa as últimas notícias dos jornais do jogo e grava
o arquivo  noticias.js  na MESMA pasta do olimpo-do-codigo.html.

Uso:
    python3 atualizar_noticias.py              # atualiza todas as fontes
    python3 atualizar_noticias.py --so "BBC News" --so "Folha de S.Paulo"
    python3 atualizar_noticias.py --n 6        # 6 notícias por fonte (padrão 5)
    python3 atualizar_noticias.py --og         # busca a foto (og:image) das notícias sem imagem
    python3 atualizar_noticias.py --teste      # testa os leitores de feed, sem internet

Só usa a biblioteca padrão do Python 3 (nada para instalar).

Estratégia por fonte:
  1) RSS/Atom oficial do jornal (traz manchete, link e, quase sempre, foto);
  2) se falhar, ou se o jornal não tem RSS aberto: RSS público do Google Notícias
     filtrado pelo site (manchete e link; sem foto, a não ser com --og).
Fontes pagas ou sem RSS recebem o botão "Arquivar" no jogo, que abre o archive.ph
já com o endereço da notícia preenchido.
"""
import argparse, base64, gzip, html, json, os, re, sys, time
import urllib.request, urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

UA = ("Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0")
TIMEOUT = 15

# nome (igual ao do jogo) -> (lista de feeds, domínio, idioma, pago/sem RSS aberto)
S = {
 "Financial Times": (["https://www.ft.com/rss/home"], "ft.com", "en", True),
 "The Economist": (["https://www.economist.com/the-world-this-week/rss.xml", "https://www.economist.com/finance-and-economics/rss.xml"], "economist.com", "en", True),
 "Bloomberg": (["https://feeds.bloomberg.com/markets/news.rss"], "bloomberg.com", "en", True),
 "Wall Street Journal": (["https://feeds.a.dj.com/rss/RSSMarketsMain.xml", "https://feeds.a.dj.com/rss/RSSWorldNews.xml"], "wsj.com", "en", True),
 "Valor Econômico": (["https://pox.globo.com/rss/valor"], "valor.globo.com", "pt", True),
 "InfoMoney": (["https://www.infomoney.com.br/feed/"], "infomoney.com.br", "pt", False),
 "Exame": (["https://exame.com/feed/"], "exame.com", "pt", False),
 "Bloomberg Línea": ([], "bloomberglinea.com.br", "pt", True),
 "Morning Brew": ([], "morningbrew.com", "en", False),
 "Visual Capitalist": (["https://www.visualcapitalist.com/feed/"], "visualcapitalist.com", "en", False),
 "Indie Hackers": ([], "indiehackers.com", "en", False),
 "Reddit r/investimentos": (["https://www.reddit.com/r/investimentos/.rss"], "reddit.com/r/investimentos", "pt", False),
 "Reddit r/personalfinance": (["https://www.reddit.com/r/personalfinance/.rss"], "reddit.com/r/personalfinance", "en", False),
 "Reuters": ([], "reuters.com", "en", True),
 "Associated Press": ([], "apnews.com", "en", False),
 "BBC News": (["https://feeds.bbci.co.uk/news/world/rss.xml"], "bbc.com", "en", False),
 "Al Jazeera": (["https://www.aljazeera.com/xml/rss/all.xml"], "aljazeera.com", "en", False),
 "The Guardian": (["https://www.theguardian.com/world/rss"], "theguardian.com", "en", False),
 "Foreign Affairs": (["https://www.foreignaffairs.com/rss.xml"], "foreignaffairs.com", "en", True),
 "Foreign Policy": (["https://foreignpolicy.com/feed/"], "foreignpolicy.com", "en", True),
 "Deutsche Welle": (["https://rss.dw.com/xml/rss-br-all"], "dw.com", "pt", False),
 "Folha de S.Paulo": (["https://feeds.folha.uol.com.br/emcimadahora/rss091.xml"], "folha.uol.com.br", "pt", True),
 "Estadão": ([], "estadao.com.br", "pt", True),
 "Gazeta do Povo": (["https://www.gazetadopovo.com.br/feed/rss/"], "gazetadopovo.com.br", "pt", True),
 "CartaCapital": (["https://www.cartacapital.com.br/feed/"], "cartacapital.com.br", "pt", True),
 "Nexo Jornal": ([], "nexojornal.com.br", "pt", True),
 "Agência Brasil": (["https://agenciabrasil.ebc.com.br/rss/ultimasnoticias/feed.xml"], "agenciabrasil.ebc.com.br", "pt", False),
 "Poder360": (["https://www.poder360.com.br/feed/"], "poder360.com.br", "pt", False),
 "Aeon": (["https://aeon.co/feed.rss"], "aeon.co", "en", False),
 "The Marginalian": (["https://www.themarginalian.org/feed/"], "themarginalian.org", "en", False),
 "Open Culture": (["https://www.openculture.com/feed"], "openculture.com", "en", False),
 "Smithsonian Magazine": (["https://www.smithsonianmag.com/rss/latest_articles/"], "smithsonianmag.com", "en", False),
 "The Atlantic": (["https://www.theatlantic.com/feed/all/"], "theatlantic.com", "en", True),
 "Arts & Letters Daily": (["https://www.aldaily.com/feed/"], "aldaily.com", "en", False),
 "Reddit r/AskHistorians": (["https://www.reddit.com/r/AskHistorians/.rss"], "reddit.com/r/AskHistorians", "en", False),
 "Piauí": (["https://piaui.folha.uol.com.br/feed/"], "piaui.folha.uol.com.br", "pt", True),
 "Hacker News": (["https://news.ycombinator.com/rss"], "news.ycombinator.com", "en", False),
 "MIT Technology Review": (["https://www.technologyreview.com/feed/"], "technologyreview.com", "en", True),
 "Ars Technica": (["https://feeds.arstechnica.com/arstechnica/index"], "arstechnica.com", "en", False),
 "Tecnoblog": (["https://tecnoblog.net/feed/"], "tecnoblog.net", "pt", False),
 "freeCodeCamp News": (["https://www.freecodecamp.org/news/rss/"], "freecodecamp.org", "en", False),
 "Examine": ([], "examine.com", "en", False),
 "Harvard Health": (["https://www.health.harvard.edu/blog/feed"], "health.harvard.edu", "en", False),
 "Our World in Data": (["https://ourworldindata.org/atom.xml"], "ourworldindata.org", "en", False),
 "Nature News": (["https://www.nature.com/nature.rss"], "nature.com", "en", False),
 "Superinteressante": (["https://super.abril.com.br/feed/"], "super.abril.com.br", "pt", False),
 "News in Levels": ([], "newsinlevels.com", "en", False),
 "VOA Learning English": ([], "learningenglish.voanews.com", "en", False),
 "BBC Learning English": ([], "bbc.co.uk/learningenglish", "en", False),
 "Simple English Wikipedia": ([], "simple.wikipedia.org", "en", False),
 "Breaking News English": ([], "breakingnewsenglish.com", "en", False),
}

NS = {"media": "http://search.yahoo.com/mrss/", "atom": "http://www.w3.org/2005/Atom",
      "content": "http://purl.org/rss/1.0/modules/content/", "dc": "http://purl.org/dc/elements/1.1/"}


def get(url, limit=None):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*", "Accept-Encoding": "gzip, identity"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        data = r.read(limit) if limit else r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            try:
                data = gzip.decompress(data)
            except Exception:
                pass
        return data


def limpa(t):
    t = re.sub(r"<[^>]+>", " ", t or "")
    return re.sub(r"\s+", " ", html.unescape(t)).strip()


def tem_img(txt):
    m = re.search(r"<img[^>]+src=[\"']([^\"']+)[\"']", txt or "", re.I)
    return html.unescape(m.group(1)) if m else ""


def data_iso(txt):
    if not txt:
        return ""
    try:
        d = parsedate_to_datetime(txt)
    except Exception:
        try:
            d = datetime.fromisoformat(txt.replace("Z", "+00:00"))
        except Exception:
            return ""
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone.utc).isoformat()


def txt(el, path):
    f = el.find(path, NS)
    return "".join(f.itertext()).strip() if f is not None else ""


def parse_feed(data):
    """Lê RSS 2.0, RSS 1.0 (RDF) ou Atom. Devolve [{t,u,i,d}]."""
    root = ET.fromstring(data)
    out = []
    itens = root.findall(".//item") or root.findall("{http://purl.org/rss/1.0/}item") or root.findall(".//atom:entry", NS)
    for it in itens:
        titulo = limpa(txt(it, "title") or txt(it, "{http://purl.org/rss/1.0/}title") or txt(it, "atom:title"))
        link = txt(it, "link") or txt(it, "{http://purl.org/rss/1.0/}link")
        if not link:
            for l in it.findall("atom:link", NS):
                if l.get("rel", "alternate") == "alternate" and l.get("href"):
                    link = l.get("href"); break
        if not link:
            g = it.find("guid")
            if g is not None and (g.text or "").startswith("http"):
                link = g.text.strip()
        img = ""
        for tag in ("media:thumbnail", "media:content"):
            for m in it.findall(tag, NS):
                u = m.get("url")
                if u and (tag.endswith("thumbnail") or "image" in (m.get("medium", "") + m.get("type", "image"))):
                    img = u; break
            if img:
                break
        if not img:
            for e in it.findall("enclosure"):
                if "image" in (e.get("type") or "") and e.get("url"):
                    img = e.get("url"); break
        if not img:
            cuerpo = txt(it, "content:encoded") or txt(it, "description") or txt(it, "atom:content") or txt(it, "atom:summary")
            img = tem_img(cuerpo)
        d = data_iso(txt(it, "pubDate") or txt(it, "dc:date") or txt(it, "atom:updated") or txt(it, "atom:published"))
        if titulo and link:
            out.append({"t": titulo, "u": link.strip(), "i": img, "d": d})
    return out


def decodifica_google(link):
    """Links do Google Notícias antigos trazem a URL real em base64. Se não der, devolve ''."""
    m = re.search(r"/articles/([^?]+)", link)
    if not m:
        return ""
    tok = m.group(1)
    try:
        raw = base64.urlsafe_b64decode(tok + "=" * (-len(tok) % 4)).decode("latin-1")
    except Exception:
        return ""
    mm = re.search(r"https?://[^\s\x00-\x1f\"<>\\^`{|}]+", raw)
    return mm.group(0) if mm else ""


def via_google(dominio, idioma):
    hl, gl, ceid = ("pt-BR", "BR", "BR:pt-419") if idioma == "pt" else ("en-US", "US", "US:en")
    q = urllib.parse.quote("site:%s when:2d" % dominio)
    url = "https://news.google.com/rss/search?q=%s&hl=%s&gl=%s&ceid=%s" % (q, hl, gl, ceid)
    itens = parse_feed(get(url))
    for it in itens:
        it["t"] = re.sub(r"\s+-\s+[^-]{2,40}$", "", it["t"])      # tira " - Nome do jornal"
        real = decodifica_google(it["u"])
        it["r"] = real                                              # URL real (se der para descobrir)
    return itens


def og_image(url):
    try:
        pag = get(url, limit=250000).decode("utf-8", "ignore")
    except Exception:
        return ""
    for pad in (r'property=["\']og:image["\'][^>]*content=["\']([^"\']+)', r'content=["\']([^"\']+)["\'][^>]*property=["\']og:image'):
        m = re.search(pad, pag, re.I)
        if m:
            return html.unescape(m.group(1))
    return ""


def processa(nome, n, usar_og):
    feeds, dominio, idioma, pago = S[nome]
    erro, via, itens = "", "", []
    for f in feeds:
        try:
            itens = parse_feed(get(f)); via = "rss"
            if itens:
                break
        except Exception as e:
            erro = "%s: %s" % (f.split("/")[2], str(e)[:60])
    if not itens:
        try:
            itens = via_google(dominio, idioma); via = "google"
        except Exception as e:
            erro = (erro + " | google: " + str(e)[:60]).strip(" |")
    itens.sort(key=lambda x: x["d"], reverse=True)
    itens = itens[:n]
    if usar_og:
        for it in itens:
            if not it["i"]:
                it["i"] = og_image(it.get("r") or it["u"])
                time.sleep(0.4)
    arquivar = pago or via == "google" or not feeds
    return {"via": via, "items": itens, "archive": bool(arquivar), "err": "" if itens else (erro or "sem itens")}


def teste():
    rss = b"""<?xml version='1.0'?><rss version='2.0' xmlns:media='http://search.yahoo.com/mrss/' xmlns:content='http://purl.org/rss/1.0/modules/content/'>
<channel><item><title>Primeira &amp; <b>teste</b></title><link>https://ex.com/a</link><pubDate>Sat, 17 Oct 2026 10:00:00 GMT</pubDate><media:thumbnail url='https://ex.com/a.jpg'/></item>
<item><title>Segunda</title><link>https://ex.com/b</link><pubDate>Sat, 17 Oct 2026 12:00:00 GMT</pubDate><description>&lt;p&gt;&lt;img src="https://ex.com/b.png"&gt;texto&lt;/p&gt;</description></item>
<item><title>Terceira</title><link>https://ex.com/c</link><enclosure url='https://ex.com/c.jpg' type='image/jpeg'/></item></channel></rss>"""
    r = parse_feed(rss)
    assert [x["t"] for x in r] == ["Primeira & teste", "Segunda", "Terceira"], r
    assert r[0]["i"] == "https://ex.com/a.jpg" and r[1]["i"] == "https://ex.com/b.png" and r[2]["i"] == "https://ex.com/c.jpg"
    assert r[1]["d"].startswith("2026-10-17T12:00")
    atom = b"""<feed xmlns='http://www.w3.org/2005/Atom'><entry><title>Atom 1</title><link rel='alternate' href='https://ex.com/x'/><updated>2026-10-17T09:00:00Z</updated><content type='html'>&lt;img src='https://ex.com/x.jpg'&gt;</content></entry></feed>"""
    a = parse_feed(atom)
    assert a[0]["t"] == "Atom 1" and a[0]["u"] == "https://ex.com/x" and a[0]["i"] == "https://ex.com/x.jpg", a
    url = "https://www.exemplo.com/mundo/2026/noticia-boa"
    tok = base64.urlsafe_b64encode(b"\x08\x13\x22" + bytes([len(url)]) + url.encode()).decode().rstrip("=")
    assert decodifica_google("https://news.google.com/rss/articles/%s?oc=5" % tok) == url
    assert decodifica_google("https://news.google.com/rss/articles/AU_yqLxyz?oc=5") == ""
    print("OK: leitores de RSS, Atom e link do Google funcionando.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--so", action="append", help="atualiza só esta fonte (pode repetir)")
    ap.add_argument("--n", type=int, default=5)
    ap.add_argument("--og", action="store_true")
    ap.add_argument("--teste", action="store_true")
    a = ap.parse_args()
    if a.teste:
        return teste()
    nomes = a.so or list(S)
    pasta = os.path.dirname(os.path.abspath(__file__))
    destino = os.path.join(pasta, "noticias.js")
    antigo = {}
    if a.so and os.path.exists(destino):               # mantém o que já existia ao atualizar só algumas fontes
        try:
            antigo = json.loads(open(destino, encoding="utf-8").read().split("=", 1)[1].rstrip("; \n"))["sources"]
        except Exception:
            antigo = {}
    res = dict(antigo)
    ok = falhou = 0
    for nome in nomes:
        if nome not in S:
            print("  ? fonte desconhecida:", nome); continue
        r = processa(nome, a.n, a.og)
        res[nome] = r
        if r["items"]:
            ok += 1; print("  ✔ %-28s %d notícias (%s)" % (nome, len(r["items"]), r["via"]))
        else:
            falhou += 1; print("  ✘ %-28s %s" % (nome, r["err"]))
    saida = {"updated": datetime.now(timezone.utc).isoformat(), "sources": res}
    tmp = destino + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write("window.NEWS=" + json.dumps(saida, ensure_ascii=False) + ";\n")
    os.replace(tmp, destino)
    print("\nPronto: %d fontes com notícias, %d sem. Arquivo gravado em %s" % (ok, falhou, destino))


if __name__ == "__main__":
    main()
