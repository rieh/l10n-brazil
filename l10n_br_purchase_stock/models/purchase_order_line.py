# Copyright (C) 2009  Renato Lima - Akretion, Gabriel C. Stabel
# Copyright (C) 2012  Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, models


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.multi
    def _prepare_stock_moves(self, picking):
        """Prepare the stock moves data for one order line.
        This function returns a list of
        dictionary ready to be used in stock.move's create()
        """
        values = super()._prepare_stock_moves(picking)
        for v in values:
            v.update(self._prepare_br_fiscal_dict())
            if picking.invoice_state:
                v['invoice_state'] = picking.invoice_state
        return values
