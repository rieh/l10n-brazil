# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields


class FiscalPaymentLine(models.Model):
    _name = 'l10n_br_fiscal.payment.line'
    _inherit = ["l10n_br_fiscal.payment.line", "nfe.40.dup"]

    nfe40_nDup = fields.Char(related='communication')
    nfe40_dVenc = fields.Date(related='date_maturity')
    nfe40_vDup = fields.Monetary(related='amount')
