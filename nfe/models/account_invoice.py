# -*- coding: utf-8 -*-
###############################################################################
#
# Copyright (C) 2013  Danimar Ribeiro 26/06/2013
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
###############################################################################

import os
import logging
import datetime
import base64

from odoo.tools.translate import _
from odoo import models, fields, api
from odoo.exceptions import RedirectWarning

from odoo.addons.nfe.sped.nfe.nfe_factory import NfeFactory
from odoo.addons.nfe.sped.nfe.validator.xml import XMLValidator
from odoo.addons.nfe.sped.nfe.processing.xml import send, cancel
from odoo.addons.nfe.sped.nfe.processing.xml import monta_caminho_nfe
from odoo.addons.nfe.sped.nfe.processing.xml import check_key_nfe
from odoo.addons.nfe.sped.nfe.validator.config_check import \
    validate_nfe_configuration, validate_invoice_cancel

_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    """account_invoice overwritten methods"""
    _inherit = 'account.invoice'

    cce_document_event_ids = fields.One2many(
        'l10n_br_account.invoice.cce', 'invoice_id', u'Eventos')
    is_danfe_printed = fields.Boolean(
        string="Danfe Impresso",
        readonly=True,
    )

    @api.multi
    def attach_file_event(self, seq, att_type, ext):
        """
        Implemente esse metodo na sua classe de manipulação de arquivos
        :param cr:
        :param uid:
        :param ids:
        :param seq:
        :param att_type:
        :param ext:
        :param context:
        :return:
        """
        if seq is None:
            seq = 1

        for inv in self:
            company = inv.company_id
            nfe_key = inv.nfe_access_key

            if att_type != 'nfe' and att_type is not None:
                str_aux = nfe_key + '-%02d-%s.%s' % (seq, att_type, ext)
                save_dir = os.path.join(
                    monta_caminho_nfe(
                        company,
                        chave_nfe=nfe_key) +
                    str_aux)

            elif att_type is None and ext == 'pdf':
                str_aux = nfe_key + '.%s' % (ext)
                save_dir = os.path.join(
                    monta_caminho_nfe(
                        company,
                        chave_nfe=nfe_key) +
                    str_aux)

            elif att_type == 'nfe' and ext == 'xml':
                str_aux = nfe_key + '-%s.%s' % (att_type, ext)
                save_dir = os.path.join(
                    monta_caminho_nfe(
                        company,
                        chave_nfe=nfe_key) +
                    str_aux)


            try:
                file_attc = open(save_dir, 'r')
                attc = file_attc.read()

                self.env['ir.attachment'].create({
                    'name': str_aux.format(nfe_key),
                    'datas': base64.b64encode(attc),
                    'datas_fname': str_aux.format(nfe_key),
                    'description': '' or _('No Description'),
                    'res_model': 'account.invoice',
                    'res_id': inv.id,
                    'type': 'binary',
                })
            except IOError:
                pass
            else:
                file_attc.close()

        return True

    def action_confirm_invoice(self):
        self.nfe_check()
        self.action_date_assign()
        self.action_number()
        self.action_move_create()
        self.nfe_export()
        return True

    def action_invoice_sent(self, cr, uid, ids, context=None):

        assert len(ids) == 1, \
            'This option should only be used for a single id at a time.'
        ir_model_data = self.pool.get('ir.model.data')
        attach_obj = self.pool.get('ir.attachment')
        attachment_ids = attach_obj.search(
            cr, uid, [
                ('res_model', '=', 'account.invoice'),
                ('res_id', '=', ids[0])], context=context)
        try:
            template_id = ir_model_data.get_object_reference(
                cr,
                uid,
                'nfe_attach',
                'email_template_nfe')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference(
                cr,
                uid,
                'mail',
                'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict(context)
        ctx.update({
            'default_model': 'account.invoice',
            'default_res_id': ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_invoice_as_sent': True,
            'attachment_ids': [(6, 0, attachment_ids)],
        })
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    def _get_nfe_factory(self, nfe_version):
        return NfeFactory().get_nfe(nfe_version)

    @api.multi
    def nfe_export(self):

        for inv in self:

            validate_nfe_configuration(inv.company_id)

            nfe_obj = self._get_nfe_factory(inv.nfe_version)

            # nfe_obj = NFe310()
            nfes = nfe_obj.get_xml(inv, int(inv.company_id.nfe_environment))

            for nfe in nfes:
                # erro = nfe_obj.validation(nfe['nfe'])
                erro = XMLValidator.validation(nfe['nfe'], nfe_obj)
                nfe_key = nfe['key'][3:]
                if erro:
                    raise RedirectWarning(
                        erro, _(u'Erro na validaço da NFe!'))

                inv.write({'nfe_access_key': nfe_key})
                save_dir = os.path.join(
                    monta_caminho_nfe(
                        inv.company_id,
                        chave_nfe=nfe_key) +
                    'tmp/')
                nfe_file = nfe['nfe'].encode('utf8')

                file_path = save_dir + nfe_key + '-nfe.xml'
                try:
                    if not os.path.exists(save_dir):
                        os.makedirs(save_dir)
                    f = open(file_path, 'w')
                except IOError:
                    raise RedirectWarning(
                        _(u'Erro!'), _(u"""Não foi possível salvar o arquivo
                            em disco, verifique as permissões de escrita
                            e o caminho da pasta"""))
                else:
                    f.write(nfe_file)
                    f.close()

                    event_obj = self.env['l10n_br_account.document_event']
                    event_obj.create({
                        'type': '0',
                        'company_id': inv.company_id.id,
                        'origin': '[NF-E]' + inv.fiscal_number,
                        'file_sent': file_path,
                        'create_date': datetime.datetime.now(),
                        'state': 'draft',
                        'document_event_ids': inv.id
                    })
                    inv.write({'state': 'sefaz_export'})

    @api.multi
    def action_invoice_send_nfe(self):

        for inv in self:

            event_obj = self.env['l10n_br_account.document_event']
            event = max(
                event_obj.search([('document_event_ids', '=', inv.id),
                                  ('type', '=', '0')]))
            arquivo = event.file_sent
            nfe_obj = self._get_nfe_factory(inv.nfe_version)

            nfe = []
            results = []
            protNFe = {}
            protNFe["state"] = 'sefaz_exception'
            protNFe["status_code"] = ''
            protNFe["message"] = ''
            protNFe["nfe_protocol_number"] = ''
            try:
                nfe.append(nfe_obj.set_xml(arquivo))
                for processo in send(inv.company_id, nfe):
                    vals = {
                        'type': str(processo.webservice),
                        'status': processo.resposta.cStat.valor,
                        'response': '',
                        'company_id': inv.company_id.id,
                        'origin': '[NF-E]' + inv.fiscal_number,
                        # TODO: Manipular os arquivos manualmente
                        # 'file_sent': processo.arquivos[0]['arquivo'],
                        # 'file_returned': processo.arquivos[1]['arquivo'],
                        'message': processo.resposta.xMotivo.valor,
                        'state': 'done',
                        'document_event_ids': inv.id}
                    results.append(vals)
                    if processo.webservice == 1:
                        for prot in processo.resposta.protNFe:
                            protNFe["status_code"] = prot.infProt.cStat.valor
                            protNFe["nfe_protocol_number"] = \
                                prot.infProt.nProt.valor
                            protNFe["message"] = prot.infProt.xMotivo.valor
                            vals["status"] = prot.infProt.cStat.valor
                            vals["message"] = prot.infProt.xMotivo.valor
                            if prot.infProt.cStat.valor in ('100', '150'):
                                protNFe["state"] = 'open'
                            elif prot.infProt.cStat.valor in ('110', '301',
                                                              '302'):
                                protNFe["state"] = 'sefaz_denied'
                        self.attach_file_event(None, 'nfe', 'xml')
                        self.attach_file_event(None, None, 'pdf')
            except Exception as e:
                _logger.error(e.message, exc_info=True)
                vals = {
                    'type': '-1',
                    'status': '000',
                    'response': 'response',
                    'company_id': self.company_id.id,
                    'origin': '[NF-E]' + inv.fiscal_number,
                    'file_sent': 'False',
                    'file_returned': 'False',
                    'message': 'Erro desconhecido ' + str(e),
                    'state': 'done',
                    'document_event_ids': inv.id
                }
                results.append(vals)
            finally:
                for result in results:
                    if result['type'] == '0':
                        event_obj.write(result)
                    else:
                        event_obj.create(result)

                self.write({
                    'nfe_status': protNFe["status_code"] + ' - ' +
                    protNFe["message"],
                    'nfe_date': datetime.datetime.now(),
                    'state': protNFe["state"],
                    'nfe_protocol_number': protNFe["nfe_protocol_number"],
                })
        return True

    @api.multi
    def button_cancel(self):

        document_serie_id = self.document_serie_id
        fiscal_document_id = self.document_serie_id.fiscal_document_id
        electronic = self.document_serie_id.fiscal_document_id.electronic
        nfe_protocol = self.nfe_protocol_number
        emitente = self.issuer

        if ((document_serie_id and fiscal_document_id and not electronic) or
                not nfe_protocol) or emitente == u'1':
            return self.action_cancel()
        else:
            result = self.env['ir.actions.act_window'].for_xml_id(
                'nfe',
                'action_nfe_invoice_cancel_form')
            return result

    @api.multi
    def cancel_invoice_online(self, justificative):
        event_obj = self.env['l10n_br_account.document_event']

        for inv in self:
            if inv.state in ('open', 'paid'):

                validate_nfe_configuration(self.company_id)
                validate_invoice_cancel(inv)

                results = []
                try:
                    processo = cancel(
                        self.company_id,
                        inv.nfe_access_key,
                        inv.nfe_protocol_number,
                        justificative)
                    vals = {
                        'type': str(processo.webservice),
                        'status': processo.resposta.cStat.valor,
                        'response': '',
                        'company_id': self.company_id.id,
                        'origin': '[NF-E] {0}'.format(inv.fiscal_number),
                        'message': processo.resposta.xMotivo.valor,
                        'state': 'done',
                        'document_event_ids': inv.id}

                    self.attach_file_event(None, 'can', 'xml')

                    for prot in processo.resposta.retEvento:
                        vals["status"] = prot.infEvento.cStat.valor
                        vals["message"] = prot.infEvento.xEvento.valor
                        if vals["status"] in (
                                '101',  # Cancelamento de NF-e
                                # homologado
                                '128',
                                # Loto do evento processado
                                '135',  # Evento registrado e
                                # vinculado a NFC-e
                                '151',  # Cancelamento de NF-e
                                # homologado fora de prazo
                                '155'):  # Cancelamento homologado fora prazo
                            # Fixme:
                            result = super(AccountInvoice, self)\
                                .action_cancel()
                            if result:
                                self.write({'state': 'sefaz_cancelled',
                                            'nfe_status': vals["status"] +
                                            ' - ' + vals["message"]
                                            })
                                obj_cancel = self.env[
                                    'l10n_br_account.invoice.cancel']
                                obj = obj_cancel.create({
                                    'invoice_id': inv.id,
                                    'justificative': justificative,
                                })
                                vals['cancel_document_event_id'] = obj.id
                    results.append(vals)
                except Exception as e:
                    _logger.error(e.message, exc_info=True)
                    vals = {
                        'type': '-1',
                        'status': '000',
                        'response': 'response',
                        'company_id': self.company_id.id,
                        'origin': '[NF-E] {0}'.format(inv.fiscal_number),
                        'file_sent': 'OpenFalse',
                        'file_returned': 'False',
                        'message': 'Erro desconhecido ' + e.message,
                        'state': 'done',
                        'document_event_ids': inv.id
                    }
                    results.append(vals)
                finally:
                    for result in results:
                        event_obj.create(result)

            elif inv.state in ('sefaz_export', 'sefaz_exception'):
                _logger.error(
                    _(u'Invoice in invalid state to cancel online'),
                    exc_info=True)
                # TODO
        return

    @api.multi
    def invoice_print(self):

        for inv in self:

            document_serie_id = inv.document_serie_id
            fiscal_document_id = inv.document_serie_id.fiscal_document_id
            electronic = inv.document_serie_id.fiscal_document_id.electronic

            if document_serie_id and fiscal_document_id and not electronic:
                return super(AccountInvoice, self).invoice_print()

            assert len(inv.ids) == 1, 'This option should only be ' \
                                      'used for a single id at a time.'

            self.write({'sent': True})
            datas = {
                'ids': inv.ids,
                'model': 'account.invoice',
                'form': self.read()
            }

            return {
                'type': 'ir.actions.report.xml',
                'report_name': 'danfe_account_invoice',
                'datas': datas,
                'nodestroy': True
            }

    @api.multi
    def action_check_nfe(self):
        for inv in self:

            event_obj = self.env['l10n_br_account.document_event']
            # event = max(
            #     event_obj.search([('document_event_ids', '=', inv.id),
            #                       ('type', '=', '0')]))
            # arquivo = event.file_sent
            nfe_obj = self._get_nfe_factory(inv.nfe_version)

            nfe = []
            results = []
            protNFe = {}
            protNFe["state"] = 'sefaz_exception'
            protNFe["status_code"] = ''
            protNFe["message"] = ''
            protNFe["nfe_protocol_number"] = ''
            try:
                file_xml = monta_caminho_nfe(
                    inv.company_id, inv.nfe_access_key)
                # if inv.state not in (
                # 'open', 'paid', 'sefaz_cancelled'):
                #     file_xml = os.path.join(file_xml, 'tmp/')
                arquivo = os.path.join(
                    file_xml, inv.nfe_access_key + '-nfe.xml')
                nfe = nfe_obj.set_xml(arquivo)
                nfe.monta_chave()
                processo = check_key_nfe(inv.company_id, nfe.chave, nfe)
                vals = {
                    'type': str(processo.webservice),
                    'status': processo.resposta.cStat.valor,
                    'response': '',
                    'company_id': inv.company_id.id,
                    'origin': '[NF-E]' + inv.fiscal_number,
                    # TODO: Manipular os arquivos manualmente
                    # 'file_sent': processo.arquivos[0]['arquivo'],
                    # 'file_returned': processo.arquivos[1]['arquivo'],
                    'message': processo.resposta.xMotivo.valor,
                    'state': 'done',
                    'document_event_ids': inv.id}
                results.append(vals)
                if processo.webservice == 4:
                    prot = processo.resposta.protNFe
                    protNFe["status_code"] = prot.infProt.cStat.valor
                    protNFe["nfe_protocol_number"] = \
                        prot.infProt.nProt.valor
                    protNFe["message"] = prot.infProt.xMotivo.valor
                    vals["status"] = prot.infProt.cStat.valor
                    vals["message"] = prot.infProt.xMotivo.valor
                    if prot.infProt.cStat.valor in ('100', '150'):
                        protNFe["state"] = 'open'
                        inv.invoice_validate()
                    elif prot.infProt.cStat.valor in ('110', '301',
                                                      '302'):
                        protNFe["state"] = 'sefaz_denied'
                    self.attach_file_event(None, 'nfe', 'xml')
                    self.attach_file_event(None, None, 'pdf')
            except Exception as e:
                _logger.error(e.message, exc_info=True)
                vals = {
                    'type': '-1',
                    'status': '000',
                    'response': 'response',
                    'company_id': self.company_id.id,
                    'origin': '[NF-E]' + inv.fiscal_number,
                    'file_sent': 'False',
                    'file_returned': 'False',
                    'message': 'Erro desconhecido ' + str(e),
                    'state': 'done',
                    'document_event_ids': inv.id
                }
                results.append(vals)
            finally:
                for result in results:
                    if result['type'] == '0':
                        event_obj.write(result)
                    else:
                        event_obj.create(result)

                self.write({
                    'nfe_status': protNFe["status_code"] + ' - ' +
                    protNFe["message"],
                    'nfe_date': datetime.datetime.now(),
                    'state': protNFe["state"],
                    'nfe_protocol_number': protNFe["nfe_protocol_number"],
                })
        return True
