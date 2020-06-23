# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    def _get_invoice_reference_types(self):
        res = super(ResCompany, self)._get_invoice_reference_types()
        res.append(('fiscal_document', 'Fiscal Document'))
        return res
