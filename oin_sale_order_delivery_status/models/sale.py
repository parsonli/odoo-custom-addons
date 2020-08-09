# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2018 Odoo IT now <http://www.odooitnow.com/>
# See LICENSE file for full copyright and licensing details.
#
##############################################################################

from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.depends('picking_ids', 'picking_ids.move_ids_without_package.state')
    def _compute_order_status(self):
        for rec in self:
            if rec.picking_ids:
                states = rec.picking_ids.mapped('state')
                if all(state == 'done' for state in states):
                    rec.delivery_status = 'delivered'
                elif any(state == 'done' for state in states) \
                        and not any(state == 'draft' for state in states) \
                        and not any(state == 'waiting' for state in states) \
                        and not any(state == 'confirmed' for state in states) \
                        and not any(state == 'assigned' for state in states):
                    rec.delivery_status = 'delivered'
                elif any(state == 'done' for state in states):
                    rec.delivery_status = 'partially_deliver'
                elif all(state == 'waiting' for state in states):
                    rec.delivery_status = 'processing'
                elif any(state == 'waiting' for state in states):
                    rec.delivery_status = 'processing'
                elif all(state == 'cancel' for state in states):
                    rec.delivery_status = 'nothing_to_deliver'
                else:
                    rec.delivery_status = 'to_deliver'
            else:
                rec.delivery_status = 'nothing_to_deliver'

    delivery_status = fields.Selection([
        ('nothing_to_deliver', '无送货单'),
        ('to_deliver', '可送，或部分可送'),
        ('partially_deliver', '已送部分'),
        ('delivered', '送完'),
        ('processing', '等待生产'),
        ], string="送货状态", compute='_compute_order_status', store=False)
