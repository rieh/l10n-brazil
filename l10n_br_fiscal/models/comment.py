# Copyright (C) 2019  Renato Lima - Akretion
# Copyright (C) 2020  KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models
from odoo.osv import expression

from ..tools.misc import compute_message as cm
from ..constants.fiscal import COMMENT_TYPE, COMMENT_TYPE_DEFAULT


class Comment(models.Model):
    _name = "l10n_br_fiscal.comment"
    _description = "Comment"
    _order = "sequence"
    _rec_name = "comment"

    sequence = fields.Integer(string="Sequence", default=10)

    name = fields.Char(
        string="Name",
        required=True)

    comment = fields.Text(
        string="Comment",
        required=True)

    test_comment = fields.Text(string="Test Comment")

    comment_type = fields.Selection(
        selection=COMMENT_TYPE,
        string="Comment Type",
        default=COMMENT_TYPE_DEFAULT,
        required=True)

    object = fields.Selection(
        selection=[
            ("l10n_br_fiscal.document", "Fiscal Document"),
            ("l10n_br_fiscal.document.line", "Fiscal Document Line")],
        string="Object",
        required=True)

    date_begin = fields.Date(
        string="Initial Date")

    date_end = fields.Date(
        string="Final Date")

    @api.model
    def _name_search(self, name, args=None, operator="ilike",
                     limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = [
                "|",
                ("name", operator, name),
                ("comment", "ilike", "%" + name + "%"),
            ]
        recs = self._search(expression.AND([domain, args]),
                            limit=limit,
                            access_rights_uid=name_get_uid)

        return self.browse(recs).name_get()

    @api.multi
    def name_get(self):
        def truncate_name(name):
            if len(name) > 60:
                name = "{}...".format(name[:60])
            return name

        return [(r.id, "{}".format(truncate_name(r.name))) for r in self]

    @api.multi
    def object_selection_values(self):
        return [('l10n_br_fiscal.document', "Fiscal Document"),
                ('l10n_br_fiscal.document.line', "Fiscal Document Line")]

    object_id = fields.Reference(
        string='Reference',
        selection=lambda self: self.object_selection_values(),
        ondelete="set null"
    )

    def action_test_message(self):
        vals = {
            'user': self.env.user,
            'ctx': self._context,
            'doc': self.object_id
        }
        self.test_comment = cm(self, vals)

    def compute_message(self, vals):
        return cm(self, vals)
