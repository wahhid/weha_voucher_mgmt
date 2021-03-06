from odoo import models, fields, api,  _ 
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class VoucherRequestLine(models.Model):
    _name = 'weha.voucher.request.line'
    
    voucher_code_id = fields.Many2one('weha.voucher.code', 'Voucher Code', required=True)
    amount = fields.Integer(string='Amount')
    voucher_request_id = fields.Many2one(comodel_name='weha.voucher.request', string='Voucher Request')
    number_ranges_ids = fields.One2many(comodel_name='weha.voucher.number.ranges', inverse_name='request_line_id', string='Voucher Ranges')
    