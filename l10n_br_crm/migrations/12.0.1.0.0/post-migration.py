# -*- coding: utf-8 -*-
# Copyright 2018 KMEE INFORMATICA LTDA - Gabriel Cardoso de Faria
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade

@openupgrade.migrate()
def migrate(env, version):
    cr = env.cr
    cr.execute(
        '''UPDATE crm_lead cl SET street_number=number;
        ''')
