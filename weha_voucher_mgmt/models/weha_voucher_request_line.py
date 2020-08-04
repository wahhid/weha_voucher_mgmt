from odoo import models, fields, api,  _ 
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class VoucherRequestLine(models.Model):
    _name = 'weha.voucher.request.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    voucher_code_id = fields.Many2one('weha.voucher.code', 'Voucher Code', required=True)
    amount = fields.Integer(string='Amount')
    voucher_request_id = fields.Many2one(comodel_name='weha.voucher.request', string='Voucher Request')
    request_line_range_ids = fields.One2many(comodel_name='weha.voucher.request.line.ranges', inverse_name='request_line_id', string='')
    

class VoucherRequestLineRanges(models.Model):
    _name = 'weha.voucher.request.line.ranges'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    start_num = fields.Integer(string='Start Number')
    end_num = fields.Integer(string='End Number')
    request_line_id = fields.Many2one(comodel_name='weha.voucher.request.line', string='Request Line')
    
    
    