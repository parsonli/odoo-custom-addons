# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class Bukcirra(models.Model):

    _inherit = 'stock.picking'

    @api.depends('partner_id.user_id', 'partner_id.commercial_partner_id.user_id')
    def _compute_user_id(self):
        for record in self:
            record.user_id = record.partner_id.user_id or record.partner_id.commercial_partner_id.user_id

    user_id = fields.Many2one('res.users', string='销售员', compute='_compute_user_id', store=True)