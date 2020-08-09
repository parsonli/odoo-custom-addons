# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2018 Odoo IT now <http://www.odooitnow.com/>
# See LICENSE file for full copyright and licensing details.
#
##############################################################################
{
    'name': 'Delivery Status on Sales Order',
    'version': '12.0.1',
    'category': 'Extra Tools',
    'summary': 'Display Delivery Status on Sales Order Form and Tree view',
    'description': """
Display Delivery Status on Sales Order Form and Tree view
""",

    'author': "Odoo IT now",
    'website': "http://www.odooitnow.com/",
    'license': 'Other proprietary',

    'depends': ['sale_stock'],
    'data': [
        'views/sale_view.xml'
    ],
    'images': ['images/OdooITnow_screenshot.png'],

    'price': 10,
    'currency': 'EUR',

    'installable': True,
    'application': True,
    'auto_install': False
}
