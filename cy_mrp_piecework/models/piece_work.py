# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class MrpProduction(models.Model):
    _inherit = 'mrp.production'
    _order = 'name desc'


class PieceWork(models.Model):
    _name = 'piece.work'
    _description = '计件'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _order = 'produced_date desc, id desc'

    name = fields.Char(string='台账编号', required=True, copy=False, readonly=True,
                       index=True, default=lambda self: _('New'))
    produced_date = fields.Date(string='生产日期', required=True, inverse='_set_produced_date')
    worker_id = fields.Many2one('hr.employee', string='姓名', required=True, inverse='_set_worker_id')
    work_line = fields.One2many('piece.work.line', 'work_id', string='计件分行', auto_join=True)
    amount_credit = fields.Float(string='白班总计', store=True, readonly=True, compute='_amount_all',
                                 track_visibility='always', track_sequence=1)
    amount_overwork_credit = fields.Float(string='加班总计', store=True, readonly=True, compute='_amount_all',
                                 track_visibility='always', track_sequence=2)

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('piece.work') or _('New')

        result = super(PieceWork, self).create(vals)
        return result

    @api.depends('work_line.piece_credit_subtotal', 'work_line.over_work')
    def _amount_all(self):
        for record in self:
            amount_credit = amount_overwork_credit = 0.0
            for line in record.work_line:
                if line.over_work:
                    amount_overwork_credit += line.piece_credit_subtotal
                else:
                    amount_credit += line.piece_credit_subtotal
            record.update({
                'amount_credit': amount_credit,
                'amount_overwork_credit': amount_overwork_credit,
            })

    @api.one
    def _set_produced_date(self):
        self.work_line.write({'produced_date': self.produced_date})

    @api.one
    def _set_worker_id(self):
        self.work_line.write({'worker_id': self.worker_id.id})


class PieceWorkLine(models.Model):
    _name = 'piece.work.line'
    _description = '计件分行'

    work_id = fields.Many2one('piece.work', string='计件分行号', required=True, ondelete='cascade', index=True, copy=False, readonly=True)
    production_id = fields.Many2one('mrp.production', string='生产任务单号')
    produced_quantity = fields.Float(string='数量', digits=(12, 4))
    produced_quantity_uom = fields.Float(string='数量', compute='compute_quantity_uom', digits=(12, 4), store=True)
    over_work = fields.Boolean(string='加班')
    product_id = fields.Many2one('product.product', string='产品')
    product_uom = fields.Many2one('uom.uom', string='单位')
    piece_credit = fields.Float(string='计件分', digits=(12, 4))
    piece_credit_subtotal = fields.Float(string='小计', compute='_compute_amount', digits=(12, 4), store=True)
    over_work_char = fields.Char(string='加班', compute='compute_over_work_char', store=True)
    amount_remain = fields.Float(string='剩余数量', compute='compute_amount_remain', digits=(12, 4), store=True)
    note = fields.Char(string='备注')
    produced_date = fields.Date(string='生产日期', readonly=True, compute='_get_produced_date', store=True)
    worker_id = fields.Many2one('hr.employee', string='姓名', readonly=True, compute='_get_worker_id', store=True)
    origin = fields.Char(string='销售订单',  readonly=True, compute='_get_origin', store=True)

    @api.depends('production_id')
    def _get_origin(self):
        for rec in self:
            rec.origin = rec.production_id.origin

    @api.depends('work_id')
    def _get_produced_date(self):
        for rec in self:
            rec.produced_date = rec.work_id.produced_date

    @api.depends('work_id')
    def _get_worker_id(self):
        for rec in self:
            rec.worker_id = rec.work_id.worker_id

    @api.depends('produced_quantity', 'product_uom')
    def compute_quantity_uom(self):
        for rec in self:
            rec.produced_quantity_uom = rec.produced_quantity / rec.compute_uom_factor()

    def compute_uom_factor(self):
        if self.product_uom.uom_type == 'smaller':
            factor = self.product_uom.factor
        elif self.product_uom.uom_type == 'bigger':
            factor = 1/self.product_uom.factor
        else:
            factor = 1
        return factor

    def compute_production_uom_factor(self):
        if self.production_id.product_uom_id.uom_type == 'smaller':
            factor = self.production_id.product_uom_id.factor
        elif self.production_id.product_uom_id.uom_type == 'bigger':
            factor = 1/self.production_id.product_uom_id.factor
        else:
            factor = 1
        return factor

    @api.depends('production_id', 'produced_quantity', 'product_uom')
    def compute_amount_remain(self):
        for rec in self:
            rec.amount_remain = rec.compute_amount_remain_function()

    def compute_amount_remain_function(self):
        if not self.production_id:
            res = 0.0
        else:
            for line in self:
                self._cr.execute("""SELECT SUM(l.produced_quantity_uom) 
                                    FROM piece_work_line l 
                                     WHERE l.production_id = %s""", line.production_id.ids)
                for res in self._cr.fetchall():
                    if res[0]:
                        res = (line.production_id.product_qty / line.compute_production_uom_factor() - res[0]) * line.compute_uom_factor()
                    else:
                        res = line.production_id.product_qty / line.compute_production_uom_factor() * line.compute_uom_factor()
        return res

    @api.depends('produced_quantity', 'piece_credit')
    def _compute_amount(self):
        for line in self:
            subtotal = line.produced_quantity * line.piece_credit
            line.update({
                'piece_credit_subtotal': subtotal,
            })

    @api.multi
    @api.depends('over_work')
    def compute_over_work_char(self):
        for rec in self:
            if rec.over_work:
                rec.over_work_char = '加班分'
            else:
                rec.over_work_char = '白班分'

    @api.multi
    @api.onchange('production_id')
    def production_id_change(self):
        vals = {}
        if not self.production_id:
            vals['product_id'] = ()
            domain = {'product_id': []}
        else:
            vals['product_id'] = self.production_id.product_id
            domain = {'product_id': [('id', '=', self.production_id.product_id.id)]}
        self.update(vals)
        result = {'domain': domain}
        return result


    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        if not self.product_id:
            vals = {}
            vals['product_uom'] = ()
            vals['piece_credit'] = 0
            vals['production_id'] = ()
            self.update(vals)
            return {'domain': {'product_uom': []}}

        vals = {}
        domain = {'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
        if not self.product_uom or (self.product_id.uom_id.id != self.product_uom.id):
            vals['product_uom'] = self.production_id.product_uom_id
        if not self.product_id.variant_bom_ids:
            self.piece_credit = 0
            self.update(vals)
            return {
                'warning': {
                    'title': '',
                    'message': '产品的物料清单没有定义，或者产品已归档，请联系管理员'}
            }
        else:
            bom_id = self.product_id.variant_bom_ids.id
            vals['piece_credit'] = self.env['mrp.bom.line'].search([('product_id', '=', 1774), ('bom_id', '=', bom_id)])[0].product_qty

        self.update(vals)

        result = {'domain': domain}
        return result

    @api.multi
    @api.onchange('product_uom')
    def product_uom_change(self):
        vals = {}
        if not self.product_uom:
            vals['piece_credit'] = 0

        elif self.product_id.uom_id.category_id != self.product_uom.category_id or not self.product_id.variant_bom_ids:
            vals['piece_credit'] = 0
            self.update(vals)
            return {
                'warning': {
                    'title': '',
                    'message': '选择的单位与产品的单位不是一个类别，请重新选择产品，可以刷新单位'}
            }

        else:
            bom_id = self.product_id.variant_bom_ids.id
            credit = self.env['mrp.bom.line'].search([('product_id', '=', 1774), ('bom_id', '=', bom_id)])[
                0].product_qty
            vals['piece_credit'] = credit / self.compute_uom_factor()
            vals['amount_remain'] = self.compute_amount_remain_function()
        self.update(vals)
