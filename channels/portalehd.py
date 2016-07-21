# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# streamondemand.- XBMC Plugin
# Canal para portalehd
# http://blog.tvalacarta.info/plugin-xbmc/streamondemand.
# ------------------------------------------------------------
import re
import time
import urllib
import urlparse

from core import config
from core import logger
from core import scrapertools
from core.item import Item
from servers import servertools

__channel__ = "portalehd"
__category__ = "F"
__type__ = "generic"
__title__ = "Portalehd (IT)"
__language__ = "IT"

DEBUG = config.get_setting("debug")

host = "http://www.24hd.online"

headers = [
    ['User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:38.0) Gecko/20100101 Firefox/38.0'],
    ['Accept-Encoding', 'gzip, deflate'],
    ['Referer', host]
]


def isGeneric():
    return True


def mainlist(item):
    logger.info("streamondemand.portalehd mainlist")
    itemlist = [Item(channel=__channel__,
                     title="[COLOR azure]Novita'[/COLOR]",
                     action="peliculas",
                     url=host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=__channel__,
                     title="[COLOR azure]Categorie[/COLOR]",
                     action="categorias",
                     url=host,
                     thumbnail="https://raw.githubusercontent.com/orione7/Pelis_images/master/General_Popular/most%20used/genres_2.png"),
                Item(channel=__channel__,
                     title="[COLOR yellow]Cerca...[/COLOR]",
                     action="search",
                     thumbnail="http://dc467.4shared.com/img/fEbJqOum/s7/13feaf0c8c0/Search")]

    return itemlist


def categorias(item):
    logger.info("streamondemand.portalehd categorias")
    itemlist = []

    data = scrapertools.cache_page(item.url, headers=headers)

    # Narrow search by selecting only the combo
    patron = '<ul class="sub-menu">(.*?)</ul>'
    bloque = scrapertools.find_single_match(data, patron)

    # The categories are the options for the combo
    patron = '<li id=[^=]+="menu-item menu-item-type-taxonomy[^>]+><a href="([^"]+)">(.*?)</a></li>'
    matches = re.compile(patron, re.DOTALL).findall(bloque)

    for scrapedurl, scrapedtitle in matches:
        scrapedurl = urlparse.urljoin(item.url, scrapedurl)
        scrapedthumbnail = ""
        scrapedplot = ""
        if (DEBUG): logger.info(
            "title=[" + scrapedtitle + "], url=[" + scrapedurl + "], thumbnail=[" + scrapedthumbnail + "]")
        itemlist.append(
            Item(channel=__channel__,
                 action="peliculas",
                 title="[COLOR azure]" + scrapedtitle + "[/COLOR]",
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 plot=scrapedplot))

    return itemlist


def search(item, texto):
    logger.info("[portalehd.py] " + item.url + " search " + texto)
    item.url = host + "/?s=" + texto
    try:
        return peliculas(item)
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def peliculas(item):
    logger.info("streamondemand.portalehd peliculas")
    itemlist = []

    # Descarga la pagina
    data = anti_cloudflare(item.url)

    # ------------------------------------------------
    cookies = ""
    matches = re.compile('(.24hd.online.*?)\n', re.DOTALL).findall(config.get_cookie_data())
    for cookie in matches:
        name = cookie.split('\t')[5]
        value = cookie.split('\t')[6]
        cookies += name + "=" + value + ";"
    headers.append(['Cookie', cookies[:-1]])
    _headers = urllib.urlencode(dict(headers))
    # ------------------------------------------------

    # Extrae las entradas (carpetas)
    patron = '<li><img src=".*?src="([^"]+)".*?<a href="([^"]+)".*?class="title">([^<]+)</a>.*?</li>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedthumbnail, scrapedurl, scrapedtitle in matches:
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        scrapedplot = ""
        # ------------------------------------------------
        scrapedthumbnail += "|" + _headers
        # ------------------------------------------------
        if (DEBUG): logger.info(
            "title=[" + scrapedtitle + "], url=[" + scrapedurl + "], thumbnail=[" + scrapedthumbnail + "]")
        tmdbtitle1 = scrapedtitle.split("Sub ")[0]
        tmdbtitle = tmdbtitle1.split("(")[0]
        year = scrapertools.find_single_match(scrapedtitle, '\((\d+)\)')
        try:
            plot, fanart, poster, extrameta = info(tmdbtitle, year)

            itemlist.append(
                Item(channel=__channel__,
                     thumbnail=poster,
                     fanart=fanart if fanart != "" else poster,
                     extrameta=extrameta,
                     plot=str(plot),
                     action="findvideos",
                     title="[COLOR azure]" + scrapedtitle + "[/COLOR]",
                     url=scrapedurl,
                     fulltitle=scrapedtitle,
                     show=scrapedtitle,
                     folder=True))
        except:
            itemlist.append(
                Item(channel=__channel__,
                     action="findvideos",
                     fulltitle=scrapedtitle,
                     show=scrapedtitle,
                     title="[COLOR azure]" + scrapedtitle + "[/COLOR]",
                     url=scrapedurl,
                     thumbnail=scrapedthumbnail,
                     plot=scrapedplot,
                     folder=True))

    # Extrae el paginador
    patronvideos = '<a class="nextpostslink" rel="next" href="([^"]+)">Avanti »</a>'
    matches = re.compile(patronvideos, re.DOTALL).findall(data)

    if len(matches) > 0:
        scrapedurl = urlparse.urljoin(item.url, matches[0])
        itemlist.append(
            Item(channel=__channel__,
                 action="HomePage",
                 title="[COLOR yellow]Torna Home[/COLOR]",
                 folder=True)),
        itemlist.append(
            Item(channel=__channel__,
                 action="peliculas",
                 title="[COLOR orange]Successivo >>[/COLOR]",
                 url=scrapedurl,
                 thumbnail="http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png",
                 folder=True))

    return itemlist


def findvideos(item):
    logger.info("[portalehd.py] findvideos")

    # Descarga la página
    data = anti_cloudflare(item.url)

    itemlist = servertools.find_video_items(data=data)

    for videoitem in itemlist:
        videoitem.title = "".join([item.title, '[COLOR green][B]' + videoitem.title + '[/B][/COLOR]'])
        videoitem.fulltitle = item.fulltitle
        videoitem.show = item.show
        videoitem.thumbnail = item.thumbnail
        videoitem.channel = __channel__

    return itemlist


def parseJSString(s):
    try:
        offset = 1 if s[0] == '+' else 0
        val = int(eval(s.replace('!+[]', '1').replace('!![]', '1').replace('[]', '0').replace('(', 'str(')[offset:]))
        return val
    except:
        pass


def anti_cloudflare(url):
    result = scrapertools.cache_page(url, headers=headers)
    try:
        jschl = re.compile('name="jschl_vc" value="(.+?)"/>').findall(result)[0]
        init = re.compile('setTimeout\(function\(\){\s*.*?.*:(.*?)};').findall(result)[0]
        builder = re.compile(r"challenge-form\'\);\s*(.*)a.v").findall(result)[0]
        decrypt_val = parseJSString(init)
        lines = builder.split(';')

        for line in lines:
            if len(line) > 0 and '=' in line:
                sections = line.split('=')
                line_val = parseJSString(sections[1])
                decrypt_val = int(eval(str(decrypt_val) + sections[0][-1] + str(line_val)))

        urlsplit = urlparse.urlsplit(url)
        h = urlsplit.netloc
        s = urlsplit.scheme

        answer = decrypt_val + len(h)

        query = '%s/cdn-cgi/l/chk_jschl?jschl_vc=%s&jschl_answer=%s' % (url, jschl, answer)

        if 'type="hidden" name="pass"' in result:
            passval = re.compile('name="pass" value="(.*?)"').findall(result)[0]
            query = '%s/cdn-cgi/l/chk_jschl?pass=%s&jschl_vc=%s&jschl_answer=%s' % (
            s + '://' + h, urllib.quote_plus(passval), jschl, answer)
            time.sleep(5)

        scrapertools.get_headers_from_response(query, headers=headers)
        return scrapertools.cache_page(url, headers=headers)
    except:
        return result


def HomePage(item):
    import xbmc
    xbmc.executebuiltin("ReplaceWindow(10024,plugin://plugin.video.streamondemand-pureita-master)")


def info(title, year):
    logger.info("streamondemand.portalehd info")
    try:
        from core.tmdb import Tmdb
        oTmdb = Tmdb(texto_buscado=title, year=year, tipo="movie", include_adult="false", idioma_busqueda="it")
        if oTmdb.total_results > 0:
            extrameta = {"Year": oTmdb.result["release_date"][:4],
                         "Genre": ", ".join(oTmdb.result["genres"]),
                         "Rating": float(oTmdb.result["vote_average"])}
            fanart = oTmdb.get_backdrop()
            poster = oTmdb.get_poster()
            plot = oTmdb.get_sinopsis()
            return plot, fanart, poster, extrameta
    except:
        pass
