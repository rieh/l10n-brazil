# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2009  Renato Lima - Akretion, Gabriel C. Stabel               #
#                                                                             #
#This program is free software: you can redistribute it and/or modify         #
#it under the terms of the GNU Affero General Public License as published by  #
#the Free Software Foundation, either version 3 of the License, or            #
#(at your option) any later version.                                          #
#                                                                             #
#This program is distributed in the hope that it will be useful,              #
#but WITHOUT ANY WARRANTY; without even the implied warranty of               #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                #
#GNU Affero General Public License for more details.                          #
#                                                                             #
#You should have received a copy of the GNU Affero General Public License     #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.        #
###############################################################################

from osv import osv, fields

FISCAL_POSITION_COLUMNS = {
    'cfop_id': fields.many2one('l10n_br_account.cfop', 'CFOP'),
    'fiscal_category_id': fields.many2one('l10n_br_account.fiscal.category',
                                          'Categoria Fiscal'),
    'type': fields.selection([('input', 'Entrada'), ('output', 'Saida')],
                             'Tipo'),
    'type_tax_use': fields.selection([('sale','Sale'),
                                      ('purchase','Purchase'),
                                      ('all','All')], 'Tax Application'),
    'fiscal_category_journal_type': fields.related(
        'fiscal_category_id', 'journal_type', type='char', readonly=True,
        relation='l10n_br_account.fiscal.category', store=True,
        string='Journal Type'),
    'fiscal_category_fiscal_type': fields.related(
        'fiscal_category_id', 'fiscal_type', type='char', readonly=True,
        relation='l10n_br_account.fiscal.category', store=True,
        string='Fiscal Type'),
    'refund_fiscal_category_id': fields.many2one(
        'l10n_br_account.fiscal.category', 'Categoria Fiscal de Devolução'),
    'inv_copy_note': fields.boolean('Copiar Observação na Nota Fiscal'),
    'asset_operation': fields.boolean('Operação de Aquisição de Ativo',
                                      help="Caso seja marcada essa opção, \
                                        será incluido o IPI na base de \
                                        calculo do ICMS.")}


class account_fiscal_position_template(osv.osv):
    _inherit = 'account.fiscal.position.template'
    _columns = FISCAL_POSITION_COLUMNS
    
    def onchange_type(self, cr, uid, ids, type=False, context=None):
        type_tax = {'input': 'purhcase', 'output': 'sale'}
        return {'value': {'type_tax_use': type_tax.get(type, 'all'), 'tax_ids': False}}

    def onchange_fiscal_category_id(self, cr, uid, ids,
                                    fiscal_category_id=False, context=None):
        print fiscal_category_id
        if fiscal_category_id:
             fiscal_category_fields = self.pool.get(
                'l10n_br_account.fiscal.category').read(
                    cr, uid, fiscal_category_id, ['fiscal_type',
                                                  'journal_type'], context=context)
        return {'value': 
            {'fiscal_category_fiscal_type':  fiscal_category_fields['fiscal_type'],
             'fiscal_category_journal_type': fiscal_category_fields['journal_type']}}

account_fiscal_position_template()


class account_fiscal_position_tax_template(osv.osv):
    _inherit = 'account.fiscal.position.tax.template'
    _columns = {
        'tax_src_domain': fields.related('tax_src_id', 'domain',
                                         type='char'),
        'tax_code_dest_id': fields.many2one('account.tax.code.template',
                                            'Replacement Tax Code')}

    def onchange_tax_src_id(self, cr, uid, ids, tax_src_id=False, context=None):
        tax_domain = False
        if tax_src_id:
            tax_domain = self.pool.get('account.tax.template').read(
                cr, uid, tax_src_id, ['domain'], context=context)['domain']
        return {'value': {'tax_src_domain': tax_domain}}

account_fiscal_position_tax_template()


class account_fiscal_position(osv.osv):
    _inherit = 'account.fiscal.position'
    _columns = FISCAL_POSITION_COLUMNS
    
    def onchange_type(self, cr, uid, ids, type=False, context=None):
        type_tax = {'input': 'purchase', 'output': 'sale'}
        return {'value': {'type_tax_use': type_tax.get(type, 'all'), 'tax_ids': False}}
    
    def onchange_fiscal_category_id(self, cr, uid, ids,
                                    fiscal_category_id=False, context=None):
        fiscal_category_fields = False
        if fiscal_category_id:
             fiscal_category_fields = self.pool.get(
                'l10n_br_account.fiscal.category').read(
                    cr, uid, fiscal_category_id, ['fiscal_type',
                                                  'journal_type'], context=context)
        return {'value': 
            {'fiscal_category_fiscal_type':  fiscal_category_fields['fiscal_type'],
             'fiscal_category_journal_type': fiscal_category_fields['journal_type']}}

account_fiscal_position()


class account_fiscal_position_tax(osv.osv):
    _inherit = 'account.fiscal.position.tax'
    _columns = {
        'tax_src_domain': fields.related('tax_src_id', 'domain',
                                         type='char'),
        'tax_code_dest_id': fields.many2one('account.tax.code',
                                            'Replacement Tax Code')}

    def onchange_tax_src_id(self, cr, uid, ids, tax_src_id=False, context=None):
        tax_domain = False
        if tax_src_id:
            tax_domain = self.pool.get('account.tax').read(
                cr, uid, tax_src_id, ['domain'], context=context)['domain']
        return {'value': {'tax_src_domain': tax_domain}}

account_fiscal_position_tax()


class res_partner(osv.osv):
    _inherit = 'res.partner'
    _columns = {
        'partner_fiscal_type_id': fields.many2one(
            'l10n_br_account.partner.fiscal.type',
            'Tipo Fiscal do Parceiro',
            domain="[('tipo_pessoa','=',tipo_pessoa)]")}

res_partner()
