# -*- coding: utf-8 -*-
# Copyright 2020 Kmee Informática LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import os
from uuid import uuid4
from py3o.template import Template
import sh
from lxml import objectify

DIRNAME = os.path.dirname(__file__)


def numero_formatado(NFe):
    num = str(NFe.infNFe.ide.nNF).zfill(9)
    num_formatado = '.'.join((num[0:3], num[3:6], num[6:9]))

    if str(NFe.infNFe.ide.mod) == '65':
        return 'nº ' + num_formatado
    elif str(NFe.infNFe.ide.mod) == '55':
        return 'Nº ' + num_formatado
    else:
        return num_formatado


def serie_formatada(NFe):
    if str(NFe.infNFe.ide.mod) == '65':
        return 'Série ' + str(NFe.infNFe.ide.serie).zfill(3)
    elif str(NFe.infNFe.ide.mod) == '55':
        return 'SÉRIE ' + str(NFe.infNFe.ide.serie).zfill(3)
    else:
        return str(NFe.infNFe.ide.serie).zfill(3)


class DanfeXml(object):

    def __init__(self):
        self.xml = open(
            DIRNAME + '/23200118386751000153550010000015991035334421-nfe.xml',
            'rb'
        ).read()
        self.object_xml = objectify.fromstring(self.xml)
        self.NFe = self.object_xml.NFe
        self.numero_formatado = numero_formatado(self.NFe)
        self.serie_formatada = serie_formatada(self.NFe)
        self.imprime_canhoto = True

    def _gera_pdf(self, template):
        arq_template = DIRNAME + '/' + uuid4().hex
        open(arq_template, 'wb').write(template.read())
        template.close()

        arq_temp = uuid4().hex
        arq_odt = DIRNAME + '/' + arq_temp + '.odt'
        arq_pdf = DIRNAME + '/' + arq_temp + '.pdf'

        t = Template(arq_template, arq_odt)
        t.render({'danfe': self})

        lo = sh.libreoffice('--headless', '--invisible', '--convert-to',
                            'pdf', '--outdir', DIRNAME, arq_odt, _bg=True)
        lo.wait()

        self.conteudo_pdf = open(arq_pdf, 'rb').read()

        os.remove(arq_template)
        os.remove(arq_odt)
        os.remove(arq_pdf)

    def gerar_danfe(self):
        template = open(os.path.join(DIRNAME, 'danfe.odt'), 'rb')
        self._gera_pdf(template)
        nome_arq = DIRNAME + \
            '/23200118386751000153550010000015991035334421' + '.pdf'
        open(nome_arq, 'wb').write(self.conteudo_pdf)
