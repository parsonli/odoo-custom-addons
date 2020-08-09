# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import tools
from odoo import api, fields, models


class SaleReport(models.Model):
    _name = "piece.work.report"
    _description = "计件分报告"
    _auto = False

    name = fields.Char(string='台账编号', readonly=True)
    produced_date = fields.Date(string='生产日期', readonly=True)
    worker_id = fields.Many2one('hr.employee', string='姓名', readonly=True)
    production_id = fields.Many2one('mrp.production', string='生产任务单号', readonly=True)
    produced_quantity = fields.Float(string='数量求和', readonly=True)
    over_work_char = fields.Char(string='加班', readonly=True)
    product_id = fields.Many2one('product.product', string='产品', readonly=True)
    product_uom = fields.Many2one('uom.uom', string='单位', readonly=True)
    piece_credit_total = fields.Float(string='计件分求和', readonly=True)
    note = fields.Char(string='备注', readonly=True)

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        with_ = ("WITH %s" % with_clause) if with_clause else ""

        select_ = """
            min(l.id) as id,
            w.name as name,
            w.produced_date as produced_date,
            w.worker_id as worker_id,
            l.production_id as production_id,
            sum(l.produced_quantity) as produced_quantity,
            l.product_id as product_id,
            l.product_uom as product_uom,
            sum(l.piece_credit_subtotal) as piece_credit_total,
            l.over_work_char as over_work_char,
            l.note as note
        """

        for field in fields.values():
            select_ += field

        from_ = """
                piece_work_line l
                      join piece_work w on (l.work_id=w.id)
                      join hr_employee h on (w.worker_id = h.id)
                        left join product_product p on (l.product_id=p.id)
                    left join uom_uom u on (u.id=l.product_uom)
                    left join mrp_production m on (m.id=l.production_id)
                %s
        """ % from_clause

        groupby_ = """
            l.product_id,
            l.production_id,
            l.product_uom,
            l.note,
            w.name,
            w.worker_id,
            w.produced_date,
            l.over_work_char %s
        """ % (groupby)

        return '%s (SELECT %s FROM %s WHERE w.worker_id IS NOT NULL GROUP BY %s)' % (with_, select_, from_, groupby_)

    @api.model_cr
    def init(self):
        # self._table = sale_report
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (%s)""" % (self._table, self._query()))

