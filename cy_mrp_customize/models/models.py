# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockMove(models.Model):
    _inherit = "stock.move"

    @api.depends('price_unit', 'quantity_done')
    def _compute_price_total(self):
        for record in self:
            #record.price_unit = record.product_id.standard_price
            record.price_total = record.product_id.standard_price * record.quantity_done

    price_total = fields.Float('小计', compute="_compute_price_total", store=True)

    @api.multi
    def _get_price_unit(self):
        self.ensure_one()
        if self.production_id:
            price_unit = self.production_id.bom_price
            return price_unit
        return super(StockMove, self)._get_price_unit()


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    @api.depends('state', 'move_raw_ids', 'finished_move_line_ids')
    def _compute_bom_price_total(self):
        for record in self:
            total_price = 0
            if record.move_raw_ids.ids:
                for item in record.move_raw_ids:
                    total_price += item.price_total
                record.bom_price_total = abs(total_price)

    bom_price_total = fields.Float('BOM总价', compute='_compute_bom_price_total', store=True)

    def compute_production_uom_factor(self):
        if self.product_uom_id.uom_type == 'smaller':
            factor = self.product_uom_id.factor
        elif self.product_uom_id.uom_type == 'bigger':
            factor = 1/self.product_uom_id.factor
        else:
            factor = 1
        return factor

    @api.depends('state', 'bom_price_total', 'finished_move_line_ids')
    def _compute_bom_price(self):
        for record in self:
            if record.finished_move_line_ids.id and record.finished_move_line_ids[0].qty_done != 0:
                record.bom_price = (record.bom_price_total / record.finished_move_line_ids[0].qty_done) * record.compute_production_uom_factor()
            else:
                record.bom_price = 0

    bom_price = fields.Float('成品单价', compute='_compute_bom_price', store=True)

