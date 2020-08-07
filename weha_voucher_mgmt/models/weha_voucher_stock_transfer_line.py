from odoo import models, fields, api,  _ 
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class VoucherStockTransferLine(models.Model):
    _name = 'weha.voucher.stock.transfer.line'

    voucher_code_id = fields.Many2one('weha.voucher.code', 'Voucher Code', required=True)
    voucher_transfer_id = fields.Many2one(comodel_name='weha.voucher.stock.transfer', string='Voucher Request')
    voucher_order_line_ids = fields.Many2many('weha.voucher.order.line', string="Voucher Line")
    amount = fields.Integer(string='Amount')
    