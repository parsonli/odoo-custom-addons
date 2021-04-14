# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    strict_range = fields.Boolean(string='Use Strict Range', help='Use this if you want to show TB with retained earnings section')
    bucket_1 = fields.Integer(string='Bucket 1', required=True, default=30)
    bucket_2 = fields.Integer(string='Bucket 2', required=True, default=60)
    bucket_3 = fields.Integer(string='Bucket 3', required=True, default=90)
    bucket_4 = fields.Integer(string='Bucket 4', required=True, default=120)
    bucket_5 = fields.Integer(string='Bucket 5', required=True, default=180)
    date_range = fields.Selection(
        [('today', 'Today'),
         ('this_week', 'This Week'),
         ('this_month', 'This Month'),
         ('this_quarter', 'This Quarter'),
         ('this_financial_year', 'This financial Year'),
         ('yesterday', 'Yesterday'),
         ('last_week', 'Last Week'),
         ('last_month', 'Last Month'),
         ('last_quarter', 'Last Quarter'),
         ('last_financial_year', 'Last Financial Year')],
        string='Default Date Range', default='this_financial_year', required=True
    )
    financial_year = fields.Selection([
        ('april_march','1 April to 31 March'),
        ('july_june','1 july to 30 June'),
        ('january_december','1 Jan to 31 Dec')
        ], string='Financial Year', default='january_december', required=True)


class ResCurrency(models.Model):
    _inherit = 'res.currency'

    excel_format = fields.Char(string='Excel format', default='_ * #,##0.00_) ;_ * - #,##0.00_) ;_ * "-"??_) ;_ @_ ', required=True)

class ins_account_financial_report(models.Model):
    _name = "ins.account.financial.report"
    _description = "Account Report"

    @api.depends('parent_id', 'parent_id.level')
    def _get_level(self):
        '''Returns a dictionary with key=the ID of a record and value = the level of this
           record in the tree structure.'''
        for report in self:
            level = 0
            if report.parent_id:
                level = report.parent_id.level + 1
            report.level = level

    def _get_children_by_order(self):
        '''returns a recordset of all the children computed recursively, and sorted by sequence. Ready for the printing'''
        res = self
        children = self.search([('parent_id', 'in', self.ids)], order='sequence ASC')
        if children:
            for child in children:
                res += child._get_children_by_order()
        return res

    name = fields.Char('Report Name', required=True, translate=True)
    parent_id = fields.Many2one('ins.account.financial.report', 'Parent')
    children_ids = fields.One2many('ins.account.financial.report', 'parent_id', 'Account Report')
    sequence = fields.Integer('Sequence')
    level = fields.Integer(compute='_get_level', string='Level', store=True)
    type = fields.Selection([
        ('sum', 'View'),
        ('accounts', 'Accounts'),
        ('account_type', 'Account Type'),
        ('account_report', 'Report Value'),
        ], 'Type', default='sum')
    account_ids = fields.Many2many('account.account', 'ins_account_account_financial_report', 'report_line_id', 'account_id', 'Accounts')
    account_report_id = fields.Many2one('ins.account.financial.report', 'Report Value')
    account_type_ids = fields.Many2many('account.account.type', 'ins_account_account_financial_report_type', 'report_id', 'account_type_id', 'Account Types')
    sign = fields.Selection([('-1', 'Reverse balance sign'), ('1', 'Preserve balance sign')], 'Sign on Reports', required=True, default='1',
                            help='For accounts that are typically more debited than credited and that you would like to print as negative amounts in your reports, you should reverse the sign of the balance; e.g.: Expense account. The same applies for accounts that are typically more credited than debited and that you would like to print as positive amounts in your reports; e.g.: Income account.')
    display_detail = fields.Selection([
        ('no_detail', 'No detail'),
        ('detail_flat', 'Display children flat'),
        ('detail_with_hierarchy', 'Display children with hierarchy')
        ], 'Display details', default='detail_flat')
    style_overwrite = fields.Selection([
        ('0', 'Automatic formatting'),
        ('1', 'Main Title 1 (bold, underlined)'),
        ('2', 'Title 2 (bold)'),
        ('3', 'Title 3 (bold, smaller)'),
        ('4', 'Normal Text'),
        ('5', 'Italic Text (smaller)'),
        ('6', 'Smallest Text'),
        ], 'Financial Report Style', default='0',
        help="You can set up here the format you want this record to be displayed. If you leave the automatic formatting, it will be computed based on the financial reports hierarchy (auto-computed field 'level').")
    date_from = fields.Date(string='开始日期')
    date_to = fields.Date(string='结束日期')
    enable_filter = fields.Boolean(string='启用比较', default=False)
    date_from_cmp = fields.Date(string='开始日期')
    date_to_cmp = fields.Date(string='结束日期')
    label_filter = fields.Char(string='列标签')

class AccountAccount(models.Model):
    _inherit = 'account.account'

    def get_cashflow_domain(self):
        cash_flow_id = self.env.ref('account_dynamic_reports.ins_account_financial_report_cash_flow0')
        if cash_flow_id:
            return [('parent_id.id', '=', cash_flow_id.id)]

    cash_flow_category = fields.Many2one('ins.account.financial.report', string="Cash Flow type", domain=get_cashflow_domain)

    @api.onchange('cash_flow_category')
    def onchange_cash_flow_category(self):
        # Add account to cash flow record to account_ids
        if self._origin and self._origin.id:
            self.cash_flow_category.write({'account_ids': [(4, self._origin.id)]})
            self.env.ref(
                'account_dynamic_reports.ins_account_financial_report_cash_flow0').write(
                {'account_ids': [(4, self._origin.id)]})
        # Remove account from previous category
        # In case of changing/ removing category
        if self._origin.cash_flow_category:
            self._origin.cash_flow_category.write({'account_ids': [(3, self._origin.id)]})
            self.env.ref(
                'account_dynamic_reports.ins_account_financial_report_cash_flow0').write(
                {'account_ids': [(3, self._origin.id)]})
