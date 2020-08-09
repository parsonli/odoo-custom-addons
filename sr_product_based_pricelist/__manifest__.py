# -*- coding: utf-8 -*-
##############################################################################
#
#    This module uses OpenERP, Open Source Management Solution Framework.
#    Copyright (C) 2017-Today Sitaram
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

{
    'name': "Product Based On Pricelist",
    'version': "11.0.0.2",
    'summary': "This module allows you to select only those product which is assigned to the pricelist.",
    'category': 'Sale',
    'description': """
         This module allows you to select only those product which is assigned to the pricelist.
         sale pricelist
         product restricted with pricelist
         product select based on pricelist 
    """,
    'author': "Sitaram",
    'website': " ",
    'depends': ['base','sale_management','product'],
    'data': [
    ],
    'demo': [],
    "license": "AGPL-3",
    'images':['static/description/banner.png'],
    'live_test_url':'https://youtu.be/lZOpCcY734E',
    'installable': True,
    'application': True,
    'auto_install': False,
}
