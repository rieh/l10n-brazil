# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api
from odoo.addons.spec_driven_model.models import spec_models


class FiscalPayment(spec_models.StackedModel):
    _name = "l10n_br_fiscal.payment"
    _inherit = ["l10n_br_fiscal.payment", "nfe.40.detpag"]
    _spec_module = 'odoo.addons.l10n_br_nfe_spec.models.v4_00.leiauteNFe'
    _stacked = "nfe.40.detpag"

    nfe40_tPag = fields.Selection(related='forma_pagamento')
    nfe40_vPag = fields.Monetary(related='amount')
    nfe40_indPag = fields.Selection(compute='_compute_ind_pag')
    nfe40_tpIntegra = fields.Selection(related='integracao_cartao')
    nfe40_tBand = fields.Selection(related='bandeira_cartao')

    @api.depends('line_ids')
    def _compute_ind_pag(self):
        for record in self:
            if len(record.line_ids) == 1 and \
                    record.payment_term_id.line_ids.days == 0:
                record.nfe40_indPag = '0'
            else:
                record.nfe40_indPag = '1'

    def _export_field(self, xsd_field, class_obj, member_spec):
        if xsd_field == 'nfe40_CNPJ':
            return self.cnpj_cpf.replace(
                        '.', '').replace('/', '').replace('-', '')
        return super(FiscalPayment, self)._export_field(
            xsd_field, class_obj, member_spec)
