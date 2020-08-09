# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockMove(models.Model):
    _inherit = "stock.move"

    def _compute_price_total(self):
        for record in self:
            record.price_total = record.price_unit * record.product_uom_qty

    price_total = fields.Float('小计', compute="_compute_price_total")

    def _get_price_unit(self):
        """ Returns the unit price to store on the quant """
        return not self.company_id.currency_id.is_zero(self.price_unit) and self.price_unit or self.production_id.bom_price


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    def _compute_bom_price_total(self):
        for record in self:
            total_price = 0
            if self.move_raw_ids.ids:
                for item in record.move_raw_ids:
                    total_price += item.quantity_done * item.price_unit
                record.bom_price_total = abs(total_price)

    bom_price_total = fields.Float('BOM总价', compute='_compute_bom_price_total')

    def compute_production_uom_factor(self):
        if self.product_uom_id.uom_type == 'smaller':
            factor = self.product_uom_id.factor
        elif self.product_uom_id.uom_type == 'bigger':
            factor = 1/self.product_uom_id.factor
        else:
            factor = 1
        return factor

    def _compute_bom_price(self):
        if self.finished_move_line_ids.id:
            self.bom_price = self.bom_price_total / self.finished_move_line_ids[0].qty_done * self.compute_production_uom_factor()

    bom_price = fields.Float('成品单价', compute='_compute_bom_price')

