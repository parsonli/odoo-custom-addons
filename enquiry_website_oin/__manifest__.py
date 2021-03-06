# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2018 Odoo IT now <http://www.odooitnow.com/>
# See LICENSE file for full copyright and licensing details.
#
##############################################################################
{
    'name': "Website Shop: Product Enquiry",
    'category': 'Website',
    'version': '12.0.1',
    'summary': 'Make an Enquiry instead of Add t cart in website.',

    'description': """
Website Shop: Product Enquiry
=============================
Enquiry from product instead of add to cart and create a lead from enquiry.
""",

    'author': 'Odoo IT now',
    'website': 'http://www.odooitnow.com/',
    'license': 'Other proprietary',

    'depends': [
        'website_sale',
        'crm',
    ],
    'data': [
        'data/enquiry_data.xml',
        'views/templates.xml'
    ],
    'images': ['images/OdooITnow_screenshot.png'],

    'price': 15.0,
    'currency': 'EUR',

    'installable': True,
    'application': False,
    'auto_install': False
}
