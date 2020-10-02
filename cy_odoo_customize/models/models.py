# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    # 客户编号（ref）自动大写，sql数据库控制unique
    @api.onchange('ref')
    def set_ref_upper(self):
        val = str(self.ref)
        self.ref = val.upper()

    _sql_constraints = [
        ('ref_unique', 'unique(ref)', '您输入的客户编号已经赋予了另一家客户，请查询后重新输入！')
    ]

    # 替换系统自带的function，删除company_id，应收总计现在可以叠加多个公司的应收账款
    @api.multi
    def _credit_debit_get(self):
        tables, where_clause, where_params = self.env['account.move.line'].with_context(state='posted')._query_get()
        where_params = [tuple(self.ids)] + where_params
        if where_clause:
            where_clause = 'AND ' + where_clause
        self._cr.execute("""SELECT account_move_line.partner_id, act.type, SUM(account_move_line.amount_residual)
                      FROM """ + tables + """
                      LEFT JOIN account_account a ON (account_move_line.account_id=a.id)
                      LEFT JOIN account_account_type act ON (a.user_type_id=act.id)
                      WHERE act.type IN ('receivable','payable')
                      AND account_move_line.partner_id IN %s
                      AND account_move_line.reconciled IS FALSE
                      """ + where_clause + """
                      GROUP BY account_move_line.partner_id, act.type
                      """, where_params)
        for pid, type, val in self._cr.fetchall():
            partner = self.browse(pid)
            if type == 'receivable':
                partner.credit = val
            elif type == 'payable':
                partner.debit = -val

    # 创建一个bool来控制，只允许sale manager来编辑credit limit。
    @api.one
    def credit_limit_change(self):
        self.able_credit_limit_change = self.env['res.users'].has_group('sales_team.group_sale_manager')

    able_credit_limit_change = fields.Boolean(compute=credit_limit_change)

    # 把company的 credit 传递给不是company的个人上,为了计算服务(is over credit)
    @api.one
    def credit_from_parent(self):
        if not self.is_company:
            self.parent_credit = self.parent_id.credit

    parent_credit = fields.Monetary(compute=credit_from_parent, readonly='True')


class SaleOrder(models.Model):
    _inherit = "sale.order"

    # 计算是否超过信用额度
    @api.depends('partner_invoice_id.credit', 'partner_invoice_id.parent_credit', 'partner_invoice_id.credit_limit')
    def is_over_credit(self):
        for record in self:
            if record.partner_invoice_id.is_company:
                # 公司
                record[('over_credit')] = record.partner_invoice_id.credit > record.partner_invoice_id.credit_limit
            else:
                # 个人
                record[('over_credit')] = record.partner_invoice_id.parent_credit > record.partner_invoice_id.credit_limit

    # bool用来控制是否显示确认按钮
    over_credit = fields.Boolean(compute=is_over_credit, readonly='True')

    @api.multi
    def action_invoice_create(self, grouped=False, final=False):
        if self.env.user.company_id.id != self.company_id.id:
            raise UserError(_("请切换公司后再创建发票"))
        res = super(SaleOrder, self).action_invoice_create()
        return res