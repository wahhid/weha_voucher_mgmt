from odoo import models, fields, api,  _ 
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class VoucherAllocateLine(models.Model):
    _name = 'weha.voucher.allocate.line'

    voucher_code_id = fields.Many2one('weha.voucher.code', 'Voucher Code', required=True)
    voucher_allocate_id = fields.Many2one(comodel_name='weha.voucher.allocate', string='Voucher Allocate')
    number_ranges_ids = fields.One2many(comodel_name='weha.voucher.number.ranges', inverse_name='allocate_line_id', string='Stock Transfer Range')
    amount = fields.Integer(string='Amount')