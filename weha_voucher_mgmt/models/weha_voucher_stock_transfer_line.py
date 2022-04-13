from odoo import models, fields, api,  _ 
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class VoucherStockTransferLine(models.Model):
    _name = 'weha.voucher.stock.transfer.line'
    _description = 'Voucher Stock Transfer Line'

    voucher_code_id = fields.Many2one('weha.voucher.code', 'Voucher Code', required=True)
    voucher_transfer_id = fields.Many2one(comodel_name='weha.voucher.stock.transfer', string='Voucher Request')
    # number_ranges_ids = fields.One2many(comodel_name='weha.voucher.number.ranges', inverse_name='stock_transfer_line_id', string='Stock Transfer Range')
    amount = fields.Integer(string='Amount')
    