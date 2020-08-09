# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.


from odoo import models, fields, osv, api
from odoo.exceptions import Warning
from collections import namedtuple

from dateutil.relativedelta import relativedelta
from datetime import  datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_is_zero, float_compare


class StockRule(models.Model):
    _inherit = 'stock.rule'
    
    def _get_stock_move_values(self, product_id, product_qty, product_uom, location_id, name, origin, values, group_id):
        result = super(StockRule, self)._get_stock_move_values(product_id, product_qty, product_uom, location_id, name, origin, values, group_id)
        
        result.update({
                'product_description':values.get('product_description',0),
            })
        return result



class stock_picking(models.Model):

    _inherit = 'stock.picking'

    def _prepare_pack_ops(self, quants, forced_qties):
        """ Prepare pack_operations, returns a list of dict to give at create """
        # TDE CLEANME: oh dear ...
        valid_quants = quants.filtered(lambda quant: quant.qty > 0)
        _Mapping = namedtuple('Mapping', ('product' , 'package', 'owner', 'location', 'location_dst_id'))

        all_products = valid_quants.mapped('product_id') | self.env['product.product'].browse(p.id for p in forced_qties.keys()) | self.move_lines.mapped('product_id')
        computed_putaway_locations = dict(
            (product, self.location_dest_id.get_putaway_strategy(product) or self.location_dest_id.id) for product in all_products)

        product_to_uom = dict((product.id, product.uom_id) for product in all_products)
        picking_moves = self.move_lines.filtered(lambda move: move.state not in ('done', 'cancel'))
        for move in picking_moves:
            # If we encounter an UoM that is smaller than the default UoM or the one already chosen, use the new one instead.
            if move.product_uom != product_to_uom[move.product_id.id] and move.product_uom.factor > product_to_uom[move.product_id.id].factor:
                product_to_uom[move.product_id.id] = move.product_uom
        if len(picking_moves.mapped('location_id')) > 1:
            raise UserError(_('The source location must be the same for all the moves of the picking.'))
        if len(picking_moves.mapped('location_dest_id')) > 1:
            raise UserError(_('The destination location must be the same for all the moves of the picking.'))

        pack_operation_values = []
        # find the packages we can move as a whole, create pack operations and mark related quants as done
        top_lvl_packages = valid_quants._get_top_level_packages(computed_putaway_locations)
        for pack in top_lvl_packages:
            pack_quants = pack.get_content()
            pack_operation_values.append({
                'picking_id': self.id,
                'package_id': pack.id,
                'product_qty': 1.0,
                'location_id': pack.location_id.id,
                'location_dest_id': computed_putaway_locations[pack_quants[0].product_id],
                'owner_id': pack.owner_id.id,
            })
            valid_quants -= pack_quants

        # Go through all remaining reserved quants and group by product, package, owner, source location and dest location
        # Lots will go into pack operation lot object
        qtys_grouped = {}
        lots_grouped = {}
        for quant in valid_quants:
            key = _Mapping(quant.product_id, quant.package_id, quant.owner_id, quant.location_id, computed_putaway_locations[quant.product_id])
            qtys_grouped.setdefault(key, 0.0)
            qtys_grouped[key] += quant.qty
            if quant.product_id.tracking != 'none' and quant.lot_id:
                lots_grouped.setdefault(key, dict()).setdefault(quant.lot_id.id, 0.0)
                lots_grouped[key][quant.lot_id.id] += quant.qty
        # Do the same for the forced quantities (in cases of force_assign or incomming shipment for example)
        for product, qty in forced_qties.items():
            if qty <= 0.0:
                continue
            key = _Mapping(product, self.env['stock.quant.package'], self.owner_id, self.location_id, computed_putaway_locations[product])
            qtys_grouped.setdefault(key, 0.0)
            qtys_grouped[key] += qty

        # Create the necessary operations for the grouped quants and remaining qtys
        Uom = self.env['product.uom']
        product_id_to_vals = {}  # use it to create operations using the same order as the picking stock moves
        for mapping, qty in qtys_grouped.items():
            uom = product_to_uom[mapping.product.id]
            val_dict = {
                'picking_id': self.id,
                'product_qty': mapping.product.uom_id._compute_quantity(qty, uom),
                'product_id': mapping.product.id,
                'package_id': mapping.package.id,
                'owner_id': mapping.owner.id,
                'location_id': mapping.location.id,
                'location_dest_id': mapping.location_dst_id,
                'product_uom_id': uom.id,
                'pack_lot_ids': [
                    (0, 0, {'lot_id': lot, 'qty': 0.0, 'qty_todo': lots_grouped[mapping][lot]})
                    for lot in lots_grouped.get(mapping, {}).keys()],
            }
            product_id_to_vals.setdefault(mapping.product.id, list()).append(val_dict)

        for move in self.move_lines.filtered(lambda move: move.state not in ('done', 'cancel')):
		
            values = product_id_to_vals.pop(move.product_id.id, [])
            if values and values[0]:
               values[0].update({'product_description':move.product_description})	
            pack_operation_values += values
        return pack_operation_values


    
class SaleOrderLine(models.Model):
    
    _inherit = 'sale.order.line'
    
    
 
    @api.multi
    def _prepare_procurement_values(self,group_id):
	    res = super(SaleOrderLine,self)._prepare_procurement_values(group_id=group_id)
	    res.update({
            'product_description':self.name,
            })
	    return res

    product_description = fields.Char(string="Description")



class stock_move(models.Model):

    _inherit = 'stock.move'

    product_description = fields.Char(string="Description")



class purchase_order(models.Model):

    _inherit = 'purchase.order.line'


    @api.multi
    def _create_stock_moves(self, picking):
       moves = self.env['stock.move']
       done = self.env['stock.move'].browse()
       for line in self:
           for val in line._prepare_stock_moves(picking):
               val.update({
						'product_description':line.name,
					})
				
               done += moves.create(val)
       return done






    
