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

from odoo import api, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        pricelist_id = self._context.get('pricelist')
        if not args:
            args = []
        # case 1 both name and price list
        if name and pricelist_id:
            pricelist = self.env['product.pricelist'].browse(pricelist_id)
            product_list = []
            for record in pricelist.item_ids:
                if record.applied_on == '0_product_variant':
                    product_list.append(record.product_id.id)

            product_ids = self._search(args + [('id', '=', product_list), ('default_code', operator, name)], limit=limit)
            if not limit or len(product_ids) < limit:
                limit2 = (limit - len(product_ids)) if limit else False
                product2_ids = self._search(args + [('id', '=', product_list), ('name', operator, name), ('id', 'not in', product_ids)], limit=limit2)
                product_ids.extend(product2_ids)
            return self.browse(product_ids).name_get()
        # case 2 only price list
        # case 3 only name
        # case 4 no name or price list but its a sales order
        elif pricelist_id or pricelist_id != None:
            pricelist = self.env['product.pricelist'].browse(pricelist_id)
            product_list = []
            for record in pricelist.item_ids:
                if record.applied_on == '0_product_variant':
                    product_list.append(record.product_id.id)
            return self.browse(product_list).name_get()
        # case 5 no name or price list and its not a sales order
        else:
            return super(ProductProduct, self)._name_search(name, args, operator, limit=limit)
