#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import scraperwiki
from urllib.request import Request, urlopen
from lxml.html import fromstring
from lxml.html.clean import clean_html

import os
# https://github.com/otherchirps/nsw_gov_docs/commit/f162b1dc8409dc4724a27b5c82280d5f56745a8d
# morph.io requires this db filename, but scraperwiki doesn't nicely
# expose a way to alter this. So we'll fiddle our environment ourselves
# before our pipeline modules load.
os.environ['SCRAPERWIKI_DATABASE_NAME'] = 'sqlite:///data.sqlite'


USER_AGENT = 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.1.3) Gecko/20091020 Ubuntu/9.10 (karmic) Firefox/3.6.0'
LEGISLATURE = '12'


def get_content(url):
    req = Request(url)
    req.add_header('User-Agent', USER_AGENT)
    html = urlopen(req).read()
    html = clean_html(html)
    root = fromstring(html)
    return root.getroottree()


class CongressList(object):

    def __init__(self):
        self.start_url = 'http://www.congreso.es/portal/page/portal/Congreso/Congreso/Diputados?_piref73_1333056_73_1333049_1333049.next_page=/wc/menuAbecedarioInicio&tipoBusqueda=completo&idLegislatura=' + LEGISLATURE
        self.result = []

    def start(self):
        pg = 1
        nexturl = self.start_url
        while nexturl:
            xmlroot = get_content(nexturl)
            nexturl = self.parse_and_save(xmlroot)
            pg += 1

    def parse_and_save(self, root):
        urls = root.xpath('//div[@class="listado_1"]/ul/li/a/@href')
        names = root.xpath('//div[@class="listado_1"]/ul/li/a/text()')
        for url, nombre in zip(urls, names):
            url = 'http://www.congreso.es' + url
            ident = url.split('idDiputado=')[1].split('&')[0]
            resp = {'id': int(ident), 'nombre': nombre, 'url': url}
            self.result.append(resp)
        nsiguiente = root.xpath('count(//div[@class="paginacion"][1]/ul/a)')
        if nsiguiente == 2:
            return root.xpath('//div[@class="paginacion"][1]/ul/a[2]/@href')[0]
        elif nsiguiente == 1:
            if 'Siguiente' in root.xpath('//div[@class="paginacion"][1]/ul/a/text()')[0]:
                return root.xpath('//div[@class="paginacion"][1]/ul/a/@href')[0]
            else:
                return None


class CongressData(object):

    def __init__(self):
        self.start_url = 'http://www.congreso.es/portal/page/portal/Congreso/Congreso/Diputados?_piref73_1333056_73_1333049_1333049.next_page=/wc/menuAbecedarioInicio&tipoBusqueda=completo&idLegislatura=' + LEGISLATURE

    def start(self):
        scrape = CongressList()
        scrape.start()
        for s in scrape.result:
            url = s['url']
            ident = s['id']
            xmlroot = get_content(url)
            self.parse_and_save(url, xmlroot, ident)

    def parse_and_save(self, url, root, ident):
        datos = {}
        datos['url'] = url
        datos['id'] = ident
        # --- div datos_diputado ---
        ext = root.xpath('//div[@id="datos_diputado"]/p[@class="logo_grupo"][1]/img/@src')
        if len(ext) == 1:
            url_foto = ext[0]
        else:
            url_foto = "/missing.png"
        datos['url_foto'] = 'http://www.congreso.es' + url_foto
        datos['partido'] = root.xpath('//div[@id="datos_diputado"]/p[@class="nombre_grupo"]/text()')[0]
        datos['legislatura'] = root.xpath('//div[@id="curriculum"]/div[@class="principal"]/text()')[0].strip()
        datos['apellidos'] = root.xpath('substring-before(//div[@id="curriculum"]/div[@class="nombre_dip"]/text(),",")').strip()
        datos['nombre'] = root.xpath('substring-after(//div[@id="curriculum"]/div[@class="nombre_dip"]/text(),",")').strip()
        cargo = root.xpath('normalize-space(//div[@id="curriculum"]/div[@class="texto_dip"][1]/ul/li/div[@class="dip_rojo"][1]/text())')
        datos['cargo'] = cargo[:cargo.find(' ')]
        datos['circunscripcion'] = cargo[cargo.rfind(' ') + 1:][:-1]
        if datos['cargo'] not in ('Diputado', 'Diputada'):
            assert(False)
        datos['nacimiento'] = root.xpath('normalize-space(//div[@id="curriculum"]/div[@class="texto_dip"][2]/ul/li[1]/text())')[10:-2]
        datos['cargos_anteriores'] = root.xpath('normalize-space(//div[@id="curriculum"]/div[@class="texto_dip"][2]/ul/li[2]/text())')
        datos['estado_civil'] = root.xpath('normalize-space(//div[@id="curriculum"]/div[@class="texto_dip"][2]/ul/li[3]/text())')
        datos['curriculum'] = " ".join(root.xpath('//div[@id="curriculum"]/div[@class="texto_dip"][2]/ul/li[3]/text()')[1:]).replace('\n', '')
        dec_txts = root.xpath('//div[@id="curriculum"]/div[@class="texto_dip"][2]/ul/li[@class="regact_dip"]/a/text()')
        dec_urls = root.xpath('//div[@id="curriculum"]/div[@class="texto_dip"][2]/ul/li[@class="regact_dip"]/a/@href')
        assert(len(dec_urls) == len(dec_txts))
        datos['declaracion_bienes_url'] = None
        datos['declaracion_actividades_url'] = None
        for url, txt in zip(dec_urls, dec_txts):
            url = 'http://www.congreso.es' + url
            if 'Actividades' in txt:
                datos['declaracion_actividades_url'] = url
            elif 'Bienes' in txt:
                datos['declaracion_bienes_url'] = url
            else:
                assert(False)
        datos['email'] = None
        datos['web'] = None
        personal_urls = root.xpath('//div[@id="curriculum"]/div[@class="texto_dip"][2]/ul/li/div[@class="webperso_dip"]/div[@class="webperso_dip_parte"]/a/@href')
        for url in personal_urls:
            if url.startswith('mailto:'):
                datos['email'] = url.split(':')[1]
            elif url.startswith('http'):
                url = url
                if datos['web']:
                    datos['web'] += '; ' + url
                else:
                    datos['web'] = url
            else:
                if url.startswith('www.'):
                    datos['web'] = 'http://' + url
                else:
                    assert(False)
        datos['twitter'] = None
        datos['facebook_url'] = None
        datos['flickr_url'] = None
        datos['linkedin_url'] = None
        datos['youtube_url'] = None
        datos['instagram_url'] = None
        datos['personal_url'] = None
        personal_urls = root.xpath('//div[@id="curriculum"]/div[@class="texto_dip"][2]/ul/li/div[@class="webperso_dip"]/div[@class="webperso_dip_imagen"]/a/@href')
        for url in personal_urls:
            if 'twitter.com/' in url:
                datos['twitter'] = url[url.rfind('/') + 1:]
            elif 'facebook.com/' in url:
                datos['facebook_url'] = url
            elif 'flickr.com/' in url:
                datos['flickr_url'] = url
            elif 'linkedin.com/' in url:
                datos['linkedin_url'] = url
            elif 'youtube.com/' in url:
                datos['youtube_url'] = url
            elif 'instagram.com/' in url:
                datos['instagram_url'] = url
            else:
                datos['personal_url'] = url
        """
        Twitter solo: http://www.congreso.es/portal/page/portal/Congreso/Congreso/Diputados/BusqForm?_piref73_1333155_73_1333154_1333154.next_page=/wc/fichaDiputado?idDiputado=191&idLegislatura=11
        Blog: http://www.congreso.es/portal/page/portal/Congreso/Congreso/Diputados/BusqForm?_piref73_1333155_73_1333154_1333154.next_page=/wc/fichaDiputado?idDiputado=246&idLegislatura=11
        Vimeo: http://www.congreso.es/portal/page/portal/Congreso/Congreso/Diputados/BusqForm?_piref73_1333155_73_1333154_1333154.next_page=/wc/fichaDiputado?idDiputado=282&idLegislatura=11
        Flickr: http://www.congreso.es/portal/page/portal/Congreso/Congreso/Diputados/BusqForm?_piref73_1333155_73_1333154_1333154.next_page=/wc/fichaDiputado?idDiputado=104&idLegislatura=11
        """
        datos['comisiones'] = "; ".join(root.xpath('//div[@id="curriculum"]/div[@class="listado_1"]/ul/li/a/text()'))
        scraperwiki.sqlite.save(['id'], datos)


scrape = CongressData()
scrape.start()
