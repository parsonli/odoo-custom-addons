# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import api, fields, models


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
    _order = "date asc, id desc"

    name = fields.Char('检测单号', required=True)
    date = fields.Datetime(string='日期', default=datetime.now(), track_visibility='onchange')
    product_id = fields.Many2one('product.product', string='产品变体', index=True)
    picking_id = fields.Many2one('stock.picking', string='相关源单据')
    origin = fields.Char(string='源单据',
                         help="Reference of the document that produced this alert.",
                         readonly=True)
    company_id = fields.Many2one('res.company', '公司',
                                 default=lambda self: self.env.user.company_id.id, index=1)
    user_id = fields.Many2one('res.users', string='创建人', default=lambda self: self.env.user.id)
    tests = fields.One2many('quality.test', 'alert_id', string="质检")
    final_status = fields.Selection(compute="_compute_status",
                                    selection=[('wait', '等待'),
                                               ('pass', '通过'),
                                               ('fail', '不合格')],
                                    store=True, string='状态',
                                    default='wait', track_visibility='onchange')

    @api.multi
    def generate_tests(self):
        quality_measure = self.env['quality.measure']
        measures = quality_measure.search([('product_id', '=', self.product_id.id),
                                           ('trigger_time', 'in', self.picking_id.picking_type_id.id)])
        for measure in measures:
            self.env['quality.test'].create({
                'quality_measure': measure.id,
                'alert_id': self.id,
            })

    @api.depends('tests', 'tests.test_status')
    def _compute_status(self):
        for alert in self:
            failed_tests = [test for test in alert.tests if test.test_status == 'fail']
            if not alert.tests:
                alert.final_status = 'wait'
            elif failed_tests:
                alert.final_status = 'fail'
            else:
                alert.final_status = 'pass'


class QualityTest(models.Model):
    _name = 'quality.test'
    _description = '检测报告明细'
    _inherit = ['mail.thread']
    _order = "id desc"

    alert_id = fields.Many2one('quality.alert', string="检测报告", track_visibility='onchange')
    name = fields.Char('Name', related="quality_measure.name", required=True)
    product_id = fields.Many2one('product.product', string='Product', related='alert_id.product_id')
    test_type = fields.Selection(related='quality_measure.type', string='Test Type', required=True, readonly=True)
    quantity_min = fields.Float(related='quality_measure.quantity_min', string='Min-Value', store=True, readonly=True)
    quantity_max = fields.Float(related='quality_measure.quantity_max', string='Max-Value', store=True, readonly=True)
    test_user_id = fields.Many2one('res.users', string='Assigned to', track_visibility='onchange')
    test_result = fields.Float(string='Result', track_visibility='onchange')
    test_result2 = fields.Selection([
        ('satisfied', 'Satisfied'),
        ('unsatisfied', 'Unsatisfied')], string='Result', track_visibility='onchange')
    test_status = fields.Selection(compute="_compute_status",
                                   selection=[('pass', 'Passed'),
                                              ('fail', 'Failed')],
                                   store=True, string='Status', track_visibility='onchange')

    @api.depends('test_result', 'test_result2')
    def _compute_status(self):
        for test in self:
            if test.test_type == 'quantity':
                if test.quantity_min <= test.test_result <= test.quantity_max:
                    test.test_status = 'pass'
                else:
                    test.test_status = 'fail'
            else:
                if test.test_result2 == 'satisfied':
                    test.test_status = 'pass'
                else:
                    test.test_status = 'fail'
