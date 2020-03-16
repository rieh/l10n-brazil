# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# Copyright (C) 2019 - TODAY Raphaël Valyi - Akretion
# Copyright (C) 2020 - TODAY Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    SITUACAO_EDOC_EM_DIGITACAO,
)


class FiscalDocument(models.Model):
    _inherit = "l10n_br_fiscal.document"

    @api.depends('line_ids')
    def _compute_move_template_ids(self):
        for record in self:
            record.move_template_ids = record.line_ids.mapped('move_template_id')

    # the following fields collide with account.invoice fields so we use
    # related field alias to be able to write them through account.invoice
    fiscal_doc_partner_id = fields.Many2one(
        related="partner_id",
        string="Fiscal Doc Partner",
        readonly=False)

    fiscal_doc_date = fields.Datetime(
        related="date",
        string="Fiscal Doc Date",
        readonly=False)

    fiscal_doc_company_id = fields.Many2one(
        related="company_id",
        string="Fiscal Doc Company",
        readonly=False)

    fiscal_doc_currency_id = fields.Many2one(
        related="currency_id",
        string="Fiscal Doc Currency",
        readonly=False)

    fiscal_doc_state = fields.Selection(
        related="state",
        string="Fiscal Doc State",
        readonly=False)

    move_template_ids = fields.Many2many(
        comodel_name='l10n_br_account.move.template',
        compute='_compute_move_template_ids',
        readonly=True,
    )

    @api.multi
    def unlink(self):
        draft_documents = self.filtered(
            lambda d: d.state == SITUACAO_EDOC_EM_DIGITACAO)

        if draft_documents:
            UserError(_("You cannot delete a fiscal document "
                        "which is not draft state."))

        invoices = self.env['account.invoice'].search(
            [('fiscal_document_id', 'in', self.ids)])
        invoices.unlink()
        return super().unlink()
