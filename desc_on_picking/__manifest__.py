# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Sale/Purchase order Line Description to Pickings(Shipment/Delivery)',
    'version': '12.0.0.2',
    'category': 'Warehouse',
    'summary': 'This module helps add description on shipment and delivery order from sales and purchase',
    'description': """
      Sale Line Description to Picking
      purchase Line Description to Pickings
      Sales Line Description to Picking
      purchases Line Description to Pickings
      Sale order Line Description to Picking
      purchase order Line Description to Pickings
      Sales order Line Description to Picking
      Sale Line Description to delivery order
      purchase Line Description to incoming shipment
      picking description from sales
      picking description from purchase  
      picking description from sales order
      picking description from purchase order
	  Description on Picking report
	Description on delivery order ,Description on delivery order report, Description on delivery report, Description on shipment, shipping description 
	  Sale Description to Picking
      purchase Description to Pickings
      Sales Description to Picking
      purchases Description to Pickings
      purchase line Description on picking
      purchase order line Description on picking
      sale order line Description on picking
      sale order line Description on picking
      SO line Description on picking
       SO Description on picking
        PO line Description on picking
         SO Description on picking

	
     
""",
    'author': 'BrowseInfo',
    'website': 'http://www.browseinfo.in/',
    'depends': ['base','stock','sale_management','purchase'],
    'data': [
        'views/stock_view.xml',
    ],
    'demo': [],
    "price": 19,
    "currency": 'EUR',
    'js': [],
    'qweb': [],
    'installable': True,
    'auto_install': False,
    "live_test_url":'https://youtu.be/LcQQyQ-xm3A',
    "images":['static/description/Banner.png'],
}
