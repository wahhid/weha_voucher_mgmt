from odoo import models, fields, api,  _ 
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class VoucherAllocateLine(models.Model):
    _name = 'weha.voucher.allocate.line'

    voucher_allocate_id = fields.Many2one(comodel_name='weha.voucher.allocate', string='Voucher Allocate')
    voucher_order_line_id = fields.Many2one('weha.voucher.order.line', 'Voucher')