# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import api, fields, models, _


class QualityMeasure(models.Model):
    _name = 'quality.measure'
    _description = '检测产品及控制点'
    _inherit = ['mail.thread']
    _order = "sequence,id"

    name = fields.Char('名称', required=True)
    product_id = fields.Many2one('product.product', string='产品变体')
    product_template_id = fields.Many2one('product.template', string='产品', related='product_id.product_tmpl_id')
    type = fields.Many2many('quality.type', string='检测项目')
    trigger_time = fields.Many2many('stock.picking.type', string='控制点激活')
    active = fields.Boolean('有效', default=True, track_visibility='onchange')
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env.user.company_id.id, index=1)
    sequence = fields.Integer(required=True, default=1)


class QualityType(models.Model):
    _name = 'quality.type'
    _description = '检测项目'
    _order = 'sequence,id'

    name = fields.Char('名称', required=True)
    measure = fields.Char('检测指标', required=True)
    active = fields.Boolean('有效', default=True, track_visibility='onchange')
    sequence = fields.Integer(required=True, default=1)


class QualityAlert(models.Model):
    _name = 'quality.alert'
    _description = '检测报告'
    _inherit = ['mail.thread']
    _order = "id desc"

    name = fields.Char('检测单号', required=True, copy=False, readonly=True,
                       index=True, default=lambda self: _('New'))
    date = fields.Datetime(string='日期', default=datetime.now(), track_visibility='onchange')
    product_id = fields.Many2one('product.product', string='产品变体', index=True)
    picking_id = fields.Many2one('stock.picking', string='相关源单据', ondelete="cascade")
    origin = fields.Char(string='源单据',
                         help="Reference of the document that produced this alert.",
                         readonly=True)
    company_id = fields.Many2one('res.company', '公司',
                                 default=lambda self: self.env.user.company_id.id, index=1)
    user_id = fields.Many2one('res.users', string='创建人', default=lambda self: self.env.user.id)
    tests = fields.One2many('quality.test', 'alert_id', string="质检")
    state = fields.Selection(selection=[('wait', '等待'),
                                        ('pass', '通过'),
                                        ('fail', '不合格')],
                             string='状态', default='wait', track_visibility='onchange')

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('quality.alert') or _('New')

        result = super(QualityAlert, self).create(vals)
        return result

    @api.multi
    def btn_pass(self):
        self.state = 'pass'

    @api.multi
    def btn_fail(self):
        self.state = 'fail'

    @api.multi
    def generate_tests(self):
        quality_measure = self.env['quality.measure']
        measures = quality_measure.search([('product_id', '=', self.product_id.id),
                                           ('trigger_time', 'in', self.picking_id.picking_type_id.id)])
        res = []
        for record in self.tests:
            res.append(record.name)

        for measure in measures:
            for types in measure.type:
                if types.name not in res:
                    self.env['quality.test'].create({
                        'quality_measure': measure.id,
                        'alert_id': self.id,
                        'name': types.name,
                        'test_type': types.measure,

                    })


class QualityTest(models.Model):
    _name = 'quality.test'
    _description = '检测报告明细'
    _order = "id asc"

    quality_measure = fields.Many2one('quality.measure', string='Measure', index=True, ondelete='cascade', track_visibility='onchange')
    alert_id = fields.Many2one('quality.alert', string="检测报告",ondelete='cascade', track_visibility='onchange')
    name = fields.Char('项目')
    product_id = fields.Many2one('product.product', string='产品变体', related='alert_id.product_id')
    test_type = fields.Char(string='标准')
    test_result = fields.Char(string='结果')

