#!/usr/bin/env python
# -*- coding: utf-8 -*-

import scraperwiki
import urllib2
from lxml.html import fromstring
from lxml.html.clean import clean_html

class CongressList(object):

    def __init__(self):
        self.start_url = 'http://www.congreso.es/portal/page/portal/Congreso/Congreso/Diputados?_piref73_1333056_73_1333049_1333049.next_page=\
        /wc/menuAbecedarioInicio&tipoBusqueda=completo&idLegislatura=11'
        self.headers = {'User-Agent' : 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.1.3) Gecko/20091020 Ubuntu/9.10 (karmic) Firefox/3.6.0'}
        self.result = []

    def start(self):
        pg = 1
        nexturl = self.start_url
        while nexturl:
            print 'Page', pg
            xmlroot = self.get_content(nexturl)
            nexturl = self.parse_and_save(xmlroot)
            pg = pg+1
        print 'FIN (%d páginas)' %pg

    def get_content(self, url):
        req = urllib2.Request(url, None, self.headers)
        html = urllib2.urlopen(req).read()
        html = clean_html(html)
        root = fromstring(html)
        return root.getroottree()

    def parse_and_save(self, root):
        urls = root.xpath('//div[@class="listado_1"]/ul/li/a/@href')
        names = root.xpath('//div[@class="listado_1"]/ul/li/a/text()')
        #import ipdb ; ipdb.set_trace()
        #print urls
        #print urls
        #assert(len(urls)==25)
        #assert(len(names)==25)
        for url, nombre in zip(urls, names):
            url = 'http://www.congreso.es' + url
            nombre = unicode(nombre.encode('latin-1'), "utf-8")
            ident = url.split('idDiputado=')[1].split('&')[0]
            resp = {'id':int(ident), 'nombre': nombre, 'url':url}
            self.result.append(resp)
            #scraperwiki.sqlite.save(['id'], {'id':int(id), 'nombre': unicode(nombre, "utf-8"), 'url':url})
            print nombre
        nsiguiente = root.xpath('count(//div[@class="paginacion"][1]/ul/a)')
        if nsiguiente == 2:
            return root.xpath('//div[@class="paginacion"][1]/ul/a[2]/@href')[0]
        elif nsiguiente == 1:
            if 'Siguiente' in root.xpath('//div[@class="paginacion"][1]/ul/a/text()')[0]:
                return root.xpath('//div[@class="paginacion"][1]/ul/a/@href')[0]
            else:
                print 'No hay más URLs'
                return None


class CongressData(object):

    def __init__(self):
        self.start_url = 'http://www.congreso.es/portal/page/portal/Congreso/Congreso/Diputados?_piref73_1333056_73_1333049_1333049\
                .next_page=/wc/menuAbecedarioInicio&tipoBusqueda=completo&idLegislatura=11'
        self.headers = {'User-Agent' : 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.1.3) Gecko/20091020 Ubuntu/9.10 (karmic) Firefox/3.6.0'}

    def start(self):
        scrape = CongressList()
        scrape.start()
        for s in scrape.result:
            url = s['url']
            ident = s['id']
            print ident, url
            xmlroot = self.get_content(url)
            self.parse_and_save(xmlroot, ident)
        print 'FIN'

    def get_content(self, url):
        req = urllib2.Request(url, None, self.headers)
        html = urllib2.urlopen(req).read()
        html = clean_html(html)
        root = fromstring(html)
        return root.getroottree()

    def convert_to_unicode(self, string): 
        return unicode(string.encode('latin-1'), "utf-8")

    def parse_and_save(self, root, ident):
        datos = {}
        datos['id'] = ident
        # --- div datos_diputado ---
        url_foto = root.xpath('//div[@id="datos_diputado"]/p[@class="logo_grupo"][1]/img/@src')[0]
        partido =  root.xpath('//div[@id="datos_diputado"]/p[@class="nombre_grupo"]/text()')[0]
        datos['url_foto'] = 'http://www.congreso.es' + url_foto
        datos['partido'] = partido
        #gif = root.xpath('substring-after(//div[@id="datos_diputado"]/p[@class="pos_hemiciclo"]/img/@src,"_")') # '100_2310.gif'
        #e = gif.split('100_')[1].split('.')[0] #3816
        #if len(e) == 4:
        #    #http://www.congreso.es/wc/htdocs/web/img/hemiciclo/hemi_100_3816.gif
        #    datos['pos_sector'] = e[0]
        #    datos['pos_fila'] = e[1]
        #    datos['pos_butaca'] = e[2:4]
        #elif len(e) == 1:
        #    #http://www.congreso.es/wc/htdocs/web/img/hemiciclo/hemi_100_3.gif
        #    datos['pos_sector'] = 6
        #    datos['pos_fila'] = 0
        #    datos['pos_butaca'] = e
        #else:
        #    print len(e), e
        #    assert(False)
        # --- div datos_diputado ---
        datos['legislatura'] = root.xpath('//div[@id="curriculum"]/div[@class="principal"]/text()')[0].strip()
        apellidos = root.xpath('substring-before(//div[@id="curriculum"]/div[@class="nombre_dip"]/text(),",")').strip()
        nombre = root.xpath('substring-after(//div[@id="curriculum"]/div[@class="nombre_dip"]/text(),",")').strip()
        datos['apellidos'] = self.convert_to_unicode(apellidos)
        datos['nombre'] = self.convert_to_unicode(nombre)
        # Ciprià: http://www.congreso.es/portal/page/portal/Congreso/Congreso/Diputados/BusqForm?_piref73_1333155_73_1333154_1333154.next_page=/wc/fichaDiputado?idDiputado=329&idLegislatura=11
        # Aixalà: http://www.congreso.es/portal/page/portal/Congreso/Congreso/Diputados/BusqForm?_piref73_1333155_73_1333154_1333154.next_page=/wc/fichaDiputado?idDiputado=190&idLegislatura=11
        #if 'Cipri' in datos['nombre']:
        #    datos['nombre'] = 'Cipria'
        #if 'Solsona Aixal' in datos['apellidos']:
        #    datos['apellidos'] = 'Solsona Aixala'
        cargo = root.xpath('normalize-space(//div[@id="curriculum"]/div[@class="texto_dip"][1]/ul/li/div[@class="dip_rojo"][1]/text())')
        datos['cargo'] = cargo[:cargo.find(' ')]
        datos['circunscripcion'] = cargo[cargo.rfind(' ')+1:][:-1]
        if datos['cargo'] not in ('Diputado', 'Diputada'):
            import ipdb ; ipdb.set_trace()
            print datos['cargo']
            assert(False)
        nacimiento = root.xpath('normalize-space(//div[@id="curriculum"]/div[@class="texto_dip"][2]/ul/li[1]/text())')[10:-2]
        cargos_anteriores = root.xpath('normalize-space(//div[@id="curriculum"]/div[@class="texto_dip"][2]/ul/li[2]/text())')
        estado_civil = root.xpath('normalize-space(//div[@id="curriculum"]/div[@class="texto_dip"][2]/ul/li[3]/text())')
        curriculum = " ".join(root.xpath('//div[@id="curriculum"]/div[@class="texto_dip"][2]/ul/li[3]/text()')[1:]).replace('\n','')
        datos['nacimiento'] = self.convert_to_unicode(nacimiento)
        datos['cargos_anteriores'] = self.convert_to_unicode(cargos_anteriores)
        datos['estado_civil'] = self.convert_to_unicode(estado_civil)
        datos['curriculum'] = self.convert_to_unicode(curriculum)
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
                print txt
                print url
                assert(False)
        datos['email'] = None
        datos['web'] = None
        personal_urls = root.xpath('//div[@id="curriculum"]/div[@class="texto_dip"][2]/ul/li/div[@class="webperso_dip"]/div[@class="webperso_dip_parte"]/a/@href')
        for url in personal_urls:
            if url.startswith('mailto:'):
                datos['email'] = url.split(':')[1]
            elif url.startswith('http'):
                url = url
                print 'http:', url
                if datos['web']:
                    datos['web'] += '; ' + url
                else:
                    datos['web'] = url
            else:
                if url.startswith('www.'):
                    datos['web'] = 'http://' + url
                else:
                    print url
                    assert(False)
        datos['twitter'] = None
        datos['facebook_url'] = None
        datos['flickr_url'] = None
        datos['linkedin_url'] = None
        datos['youtube_url'] = None
        datos['instagram_url'] = None
        personal_urls = root.xpath('//div[@id="curriculum"]/div[@class="texto_dip"][2]/ul/li/div[@class="webperso_dip"]/div[@class="webperso_dip_imagen"]/a/@href')
        for url in personal_urls:
            if 'twitter.com/' in url:
                datos['twitter'] = url[url.rfind('/')+1:]
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
                print url
                assert(False)
        """
        Twitter solo: http://www.congreso.es/portal/page/portal/Congreso/Congreso/Diputados/BusqForm?_piref73_1333155_73_1333154_1333154.next_page=/wc/fichaDiputado?idDiputado=191&idLegislatura=11
        Blog: http://www.congreso.es/portal/page/portal/Congreso/Congreso/Diputados/BusqForm?_piref73_1333155_73_1333154_1333154.next_page=/wc/fichaDiputado?idDiputado=246&idLegislatura=11
        Vimeo: http://www.congreso.es/portal/page/portal/Congreso/Congreso/Diputados/BusqForm?_piref73_1333155_73_1333154_1333154.next_page=/wc/fichaDiputado?idDiputado=282&idLegislatura=11
        Flickr: http://www.congreso.es/portal/page/portal/Congreso/Congreso/Diputados/BusqForm?_piref73_1333155_73_1333154_1333154.next_page=/wc/fichaDiputado?idDiputado=104&idLegislatura=11
        """
        datos['comisiones'] = "; ".join(root.xpath('//div[@id="curriculum"]/div[@class="listado_1"]/ul/li/a/text()'))
        print datos['apellidos'], datos['nombre']
        scraperwiki.sqlite.save(['id'], datos)


#s = CongressData()
#s.start()
scrape = CongressData()
scrape.start()
