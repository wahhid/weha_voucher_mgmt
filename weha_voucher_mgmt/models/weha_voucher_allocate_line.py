from odoo import models, fields, api,  _ 
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class VoucherAllocateLine(models.Model):
    _name = 'weha.voucher.allocate.line'

    voucher_allocate_id = fields.Many2one(comodel_name='weha.voucher.allocate', string='Voucher Allocate')
    voucher_order_line_id = fields.Many2one('weha.voucher.order.line', 'Voucher')
    voucher_code_id = fields.Many2one('weha.voucher.code', string="Voucher Code", related="voucher_order_line_id.voucher_code_id")
    year_id = fields.Many2one('weha.voucher.year', string="Year", related="voucher_order_line_id.year_id")
    voucher_promo_id = fields.Many2one('weha.voucher.promo', string="Voucher Promo", related="voucher_order_line_id.voucher_promo_id")
    