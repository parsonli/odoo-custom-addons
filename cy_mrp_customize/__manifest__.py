# -*- coding: utf-8 -*-

{
    'name': 'caiyong mrp Customize',
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
            'views/mrp_view_cy.xml',
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
