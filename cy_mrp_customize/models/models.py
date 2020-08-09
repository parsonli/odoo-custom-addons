# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductionMRP(models.Model):
    _inherit = "mrp.production"

    @api.depends('bom_id')
    def _compute_finished_product_price(self):
        for record in self:
            parts_cost = 0
            for parts in record.bom_id.bom_line_ids:
                parts_cost += parts.product_id.standard_price * parts.product_qty
            record[('finished_product_price')] = parts_cost

    finished_product_price = fields.Float('Cost', compute=_compute_finished_product_price)
