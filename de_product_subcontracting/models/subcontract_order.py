# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.addons import decimal_precision as dp


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    subcontract_id = fields.Many2one('purchase.subcontract.order', 'Subcontract Order', ondelete='cascade')
    delivery_count = fields.Integer(string='Delivery Orders', compute='_compute_picking_ids')

    @api.depends('subcontract_id')
    def _compute_picking_ids(self):
        for order in self:
            order.delivery_count = len(order.subcontract_id.picking_ids) - len(order.picking_ids)

    @api.multi
    def action_view_delivery(self):
        '''
        This function returns an action that display existing delivery orders
        of given sales order ids. It can either be a in a list or in a form
        view, if there is only one delivery order to show.
        '''
        action = self.env.ref('stock.action_picking_tree_all').read()[0]

        pickings = self.mapped('subcontract_id.picking_ids')

        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings.ids), ('id', 'not in', self.picking_ids.ids)]
        elif pickings:
            action['views'] = [(self.env.ref('stock.view_picking_form').id, 'form')]
            action['res_id'] = pickings.id
        return action


class Picking(models.Model):
    _inherit = 'stock.picking'

    subcontract_id = fields.Many2one('purchase.subcontract.order', 'Subcontract Order', ondelete='cascade')


class PurchaseSubcontracting(models.Model):
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _name = 'purchase.subcontract.order'
    _description = "Subcontracting Order"
    _order = 'date_order desc, id desc'

    @api.depends('product_id', 'quantity', 'order_lines', 'price_unit', 'taxes_id')
    def _get_product_current_price_unit(self):
        for record in self:
            price_total = 0
            if record.order_lines:
                for price in record.order_lines:
                    price_total += price.total_price
            if record.taxes_id and record.quantity != 0:
                record.product_current_price_unit = record.price_unit / (
                            1 + record.taxes_id[0].amount * record.taxes_id[0].price_include / 100) + (
                                                                price_total / record.quantity)
            elif record.quantity != 0:
                record.product_current_price_unit = record.price_unit + (price_total / record.quantity)

    @api.depends('product_current_price_unit', 'order_lines')
    def _check_price_unit(self):
        for record in self:
            if record.product_id:
                val = 1
                for line in record.order_lines:
                    val *= line.check_price_unit
                record.check_price_unit = (record.product_current_price_unit != 0) * val

    name = fields.Char('Order Reference', required=True, index=True, copy=False, default='New')
    date_order = fields.Datetime('Order Date', required=True, index=True, copy=False, default=fields.Datetime.now,
                                 help="Depicts the date where the Quotation should be validated and converted into a purchase order.")
    date_approve = fields.Date('Approval Date', readonly=1, index=True, copy=False)
    date_planned = fields.Datetime(string='Scheduled Date', required=True, index=True)

    partner_id = fields.Many2one('res.partner', string='Vendor', required=True,
                                 change_default=True, track_visibility='always',
                                 default=lambda self: self.env['res.partner'].search([('name', '=', '上海强宏包装材料有限公司')],
                                                                                         limit=1),
                                 help="You can find a vendor by its Name, TIN, Email or Internal Reference.")
    user_id = fields.Many2one('res.users',
                              string='Purchase Representative',
                              index=True,
                              track_visibility='onchange',
                              track_sequence=2,
                              default=lambda self: self.env.user)
    location_id = fields.Many2one('stock.location', string='Subcontracting Location', required=True,
                                  default=lambda self: self.env['stock.location'].search([('usage', '=', 'inventory')], limit=1),
                                  help="The vendor location for subcontracting process")

    service_id = fields.Many2one('product.product', string='Service', required=True,
                                 default=lambda self: self.env['product.product'].search([('name', '=', '委外加工费（重量）')], limit=1))

    company_id = fields.Many2one('res.company', 'Company', required=True, index=True,
                                 default=lambda self: self.env.user.company_id.id)

    product_id = fields.Many2one(comodel_name="product.product", string="Product", required=True)
    product_uom_id = fields.Many2one('uom.uom', 'UOM', related='product_id.uom_id', readonly=True)

    quantity = fields.Float(string="Quantity",required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('subcontract', 'Subcontracting Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled')
    ], string='Status', readonly=True, index=True, copy=False, default='draft', track_visibility='onchange')
    order_lines = fields.One2many('purchase.subcontract.line', 'order_id', string='Order Lines',
                                 states={'cancel': [('readonly', True)], 'done': [('readonly', True)]}, copy=True)
    picking_ids = fields.One2many('stock.picking', 'subcontract_id', string='Pickings')
    delivery_count = fields.Integer(string='Delivery Orders', compute='_compute_picking_ids')
    price_unit = fields.Float(string='加工费单价', digits=dp.get_precision('Product Price'))
    purchase_ids = fields.One2many('purchase.order', 'subcontract_id', string='Purchase Order')
    purchase_count = fields.Integer(string='Purchase', compute='_compute_purchase_ids')
    taxes_id = fields.Many2many('account.tax', string='税率',
                                domain=['|', ('active', '=', False), ('active', '=', True)])
    check_price_unit = fields.Boolean(compute='_check_price_unit')
    product_current_price_unit = fields.Float(string='当前订单单价', digits=dp.get_precision('Product Price'), compute='_get_product_current_price_unit', store=True)

    @api.multi
    def unlink(self):
        for order in self:
            if not order.state == 'cancel':
                raise UserError(_('请先取消后，再删除'))
        return super(PurchaseSubcontracting, self).unlink()

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('purchase.subcontract.order') or '/'
        return super(PurchaseSubcontracting, self).create(vals)

    @api.depends('purchase_ids')
    def _compute_purchase_ids(self):
        for order in self:
            order.purchase_count = len(order.purchase_ids)

    @api.depends('picking_ids')
    def _compute_picking_ids(self):
        for order in self:
            order.delivery_count = len(order.picking_ids)

    @api.multi
    def action_confirm(self):
        for order in self:
            order.write({'state': 'subcontract'})
            # Creating Purchase Order Vals
            purchase_vals = {
                'partner_id': order.partner_id.id,
                'company_id': self.env.user.company_id.id,
                'currency_id': order.partner_id.property_purchase_currency_id.id or self.env.user.company_id.currency_id.id,
                'origin': order.name,
                'payment_term_id': order.partner_id.property_supplier_payment_term_id.id,
                'date_order': str(datetime.now()),
                'subcontract_id': order.id,
            }
            purchase_rec = self.env['purchase.order'].create(purchase_vals)
            purchase_rec.button_confirm()
            # Creating Purchase Order Line Vals
            line_data = {
                'name': order.product_id.display_name,
                'product_qty': order.quantity,
                'product_id': order.service_id.id or False,
                'product_uom': order.service_id.uom_po_id.id,
                'price_unit': order.price_unit or 0.0,
                'company_id': self.env.user.company_id.id,
                'order_id': purchase_rec.id,
                'date_planned': order.date_planned,
                'taxes_id': [(6, 0, order.taxes_id.ids)] or False,
            }
            purchase_rec_line = self.env['purchase.order.line'].create(line_data)

            delivery_picking_type = self.env['stock.picking.type'].search([('name', '=', 'Subcontract')])
            location = self.env.ref('stock.stock_location_stock', raise_if_not_found=False)



            # Creating Raw Material out Delivery Document
            delivery_vals = {
                'picking_type_id': delivery_picking_type.id,
                'partner_id': order.partner_id.id,
                'date': str(datetime.now()),
                'origin': order.name,
                'location_id': location.id,
                'location_dest_id': order.location_id.id,
                'company_id': self.env.user.company_id.id,
                'subcontract_id': order.id,
            }
            delivery_rec = self.env['stock.picking'].create(delivery_vals)
            # Creating the stock move vals for raw materials
            for line in order.order_lines:
                stock_move_vals = {
                    'name': delivery_rec.name or '',
                    'product_id': line.product_id.id,
                    'product_uom': line.product_id.uom_po_id.id,
                    'date': str(datetime.now()),
                    'date_expected': str(datetime.now()),
                    'location_id': location.id,
                    'location_dest_id': order.location_id.id,
                    'partner_id': order.partner_id.id,
                    'state': 'confirmed',
                    'company_id': self.env.user.company_id.id,
                    'price_unit': line.product_id.standard_price or 0.0,
                    'origin': order.name,
                    'product_uom_qty': line.product_qty
                }
                stock_move_vals.update({
                    'picking_type_id': delivery_rec.picking_type_id.id,
                    'picking_id': delivery_rec.id
                })
                self.env['stock.move'].create(stock_move_vals)

            # Creating Finish Product Receipt Document
            delivery_vals = {
                'picking_type_id': delivery_picking_type.id,
                'partner_id': order.partner_id.id,
                'date': str(datetime.now()),
                'origin': order.name,
                'location_id': order.location_id.id,
                'location_dest_id': location.id,
                'company_id': self.env.user.company_id.id,
                'subcontract_id': order.id,
            }
            delivery_rec = self.env['stock.picking'].create(delivery_vals)
            # Creating the stock move vals for Finish Product
            stock_move_vals = {
                'name': delivery_rec.name or '',
                'product_id': order.product_id.id,
                'product_uom': order.product_id.uom_po_id.id,
                'date': str(datetime.now()),
                'date_expected': order.date_planned,
                'location_id': order.location_id.id,
                'location_dest_id': location.id,
                'partner_id': order.partner_id.id,
                'state': 'confirmed',
                'company_id': self.env.user.company_id.id,
                'price_unit': order.product_current_price_unit or order.product_id.standard_price,
                'origin': order.name,
                'product_uom_qty': order.quantity,
                'purchase_line_id': purchase_rec_line.id
            }

            stock_move_vals.update({
                'picking_type_id': delivery_rec.picking_type_id.id,
                'picking_id': delivery_rec.id
            })
            self.env['stock.move'].create(stock_move_vals)
        self.env.user.notify_info('成功创建1张采购单，2张调拨单', title='信息', sticky=False)

    @api.multi
    def action_draft(self):
        self.write({'state': 'draft'})
        return {}

    @api.multi
    def action_done(self):
        return self.write({'state': 'done'})

    @api.multi
    def action_unlock(self):
        self.write({'state': 'subcontract'})

    @api.multi
    def action_cancel(self):
        for order in self:
            for pick in order.picking_ids:
                if pick.state == 'done':
                    raise UserError(
                        _('已经有库存移动，无法取消 %s ') % (
                            order.name))
            if order.state in ('draft', 'subcontract'):
                for pick in order.picking_ids.filtered(lambda r: r.state != 'cancel'):
                    pick.action_cancel()
                for purchase_order in order.purchase_ids.filtered(lambda r: r.state != 'cancel'):
                    purchase_order.button_cancel()
        return self.write({'state': 'cancel'})

    @api.multi
    def action_view_delivery(self):
        '''
        This function returns an action that display existing delivery orders
        of given sales order ids. It can either be a in a list or in a form
        view, if there is only one delivery order to show.
        '''
        action = self.env.ref('stock.action_picking_tree_all').read()[0]

        pickings = self.mapped('picking_ids')
        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings.ids)]
        elif pickings:
            action['views'] = [(self.env.ref('stock.view_picking_form').id, 'form')]
            action['res_id'] = pickings.id
        return action


    @api.multi
    def action_view_purchase(self):
        action = self.env.ref('purchase.purchase_rfq').read()[0]

        purchases = self.mapped('purchase_ids')
        if len(purchases) > 1:
            action['domain'] = [('id', 'in', purchases.ids)]
        elif purchases:
            action['views'] = [(self.env.ref('purchase.purchase_order_form').id, 'form')]
            action['res_id'] = purchases.id
        return action


class PurchaseSubcontractingLine(models.Model):
    _name = 'purchase.subcontract.line'
    _description = 'Subcontract Order Line'
    _order = 'order_id, id'

    @api.depends('product_id')
    def _get_price_unit(self):
        for line in self:
            line.price_unit = line.product_id.standard_price

    @api.depends('price_unit', 'product_qty')
    def get_total_price(self):
        for line in self:
            line.total_price = line.product_qty * line.price_unit

    @api.depends('price_unit')
    def _check_price_unit(self):
        for record in self:
            if record.product_id:
                record.check_price_unit = record.price_unit != 0

    order_id = fields.Many2one('purchase.subcontract.order', string='Order Reference', index=True, required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', change_default=True, required=True)
    product_uom_id = fields.Many2one('uom.uom', 'UOM', related='product_id.uom_id', readonly=True)
    product_qty = fields.Float(string='Quantity', required=True)
    price_unit = fields.Float(string='单价', digits=dp.get_precision('Product Price'), compute='_get_price_unit', store=True)
    total_price = fields.Float(string='小计', compute='get_total_price')
    check_price_unit = fields.Boolean(compute='_check_price_unit')