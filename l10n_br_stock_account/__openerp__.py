# -*- coding: utf-8 -*-
###############################################################################
#
# Copyright (C) 2014  Renato Lima - Akretion
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

{
    'name': 'Brazilian Localization WMS Accounting',
    'category': 'Localisation',
    'license': 'AGPL-3',
    'author': 'Akretion, Odoo Community Association (OCA)',
    'website': 'http://odoo-brasil.org',
    'version': '8.0.1.0.1',
    'depends': [
        'l10n_br_account_product',
        'l10n_br_stock',
        'account_fiscal_position_rule_stock',
        'stock_account',
    ],
    'data': [
        'data/l10n_br_stock_account_data.xml',
        'views/stock_account_view.xml',
        'views/res_company_view.xml',
        'views/stock_view.xml',
        'wizard/stock_invoice_onshipping_view.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [],
    'test': [
        'test/stock_internal_picking.yml',
        'test/stock_return_internal_picking.yml',
    ],
    'installable': True,
    'auto_install': True,
}
