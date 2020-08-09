# -*- coding: utf-8 -*-

{
    'name': 'caiyong Customize',
    'version': '1.0.0.0',
    'author': 'Parson Li',
    'category': 'Productivity',
    'website': 'https://www.chemi-young.com',
    'license': 'LGPL-3',
    'sequence': 2,
    'summary': """    
    
    """,
    'description': """
自制的一些辅助软件与程序
    """,
    'images': [''],
    'depends': [
                'base', 'account', 'mrp', 'stock', 'sale',
    ],
    'data': [
            'views/cy_mrp_production_templates.xml',
            'views/res_partner_view_cy.xml',
            'views/stock_picking_cy.xml',
            'views/sale_order_view_cy.xml',
            'views/purchase_order_view_cy.xml',
            'views/account_invoice_view_cy.xml',
            'views/account_move_view_cy.xml',
            ],
    'qweb': [

    ],
    'demo': [],
    'test': [],
    'css': [],
    'js': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
