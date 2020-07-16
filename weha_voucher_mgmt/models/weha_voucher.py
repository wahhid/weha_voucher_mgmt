# -*- coding: utf-8 -*-
import string
import random
from odoo import models, fields, api, _
from odoo.exceptions import UserError

AVAILABLE_STATES = [
    ('draft','New'),
    ('active','Active'),
    ('expired','Expired')]

class VoucherLine(models.Model):
    _name = 'weha.voucher.line'

    name = fields.Char(string="Name", required=True)
    code = fields.Char(
        string='Code',
        size=2,
        required=True
    )
    expired_date = fields.Date(string="Expired Date", required=True, help='The expiry date of Voucher.')
    state =  fields.Selection(AVAILABLE_STATES,'Status',size=16,readonly=True, default='active')


class Voucher(models.Model):
    _name = 'weha.voucher'

    name = fields.Char(string="Name", required=True)
    voucher_line_ids = fields.Many2one('weha.voucher.line', string="Voucher", required=True)
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    limit = fields.Integer(string="Total Available For Each User", default=1, help='Total Available For Each User')
    total_avail = fields.Integer(string="Total Available", default=1)
    voucher_val = fields.Float(string="Voucher Value", help='The amount for the voucher.')
    



