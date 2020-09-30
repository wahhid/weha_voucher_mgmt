from odoo import models, fields, api,  _ 
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class VoucherReturnLine(models.Model):
    _name = 'weha.voucher.return.line'

    voucher_return_id = fields.Many2one(comodel_name='weha.voucher.return', string='Voucher Return')
    voucher_order_line_id = fields.Many2one('weha.voucher.order.line', 'Voucher')
    voucher_code_id = fields.Many2one('weha.voucher.code', string="Voucher Code",
                                      related="voucher_order_line_id.voucher_code_id")
    year_id = fields.Many2one('weha.voucher.year', string="Year", related="voucher_order_line_id.year_id")
    voucher_promo_id = fields.Many2one('weha.voucher.promo', string="Voucher Promo",
                                       related="voucher_order_line_id.voucher_promo_id")
    state = fields.Selection([('open', 'Open'), ('received', 'Received')], 'Status', default='open')
    
    # voucher_code_id = fields.Many2one('weha.voucher.code', 'Voucher Code', required=True)
    # voucher_return_id = fields.Many2one(comodel_name='weha.voucher.return', string='Voucher Return')
    # number_ranges_ids = fields.One2many(comodel_name='weha.voucher.number.ranges', inverse_name='stock_transfer_line_id', string='Stock Transfer Range')
    # amount = fields.Integer(string='Amount')
    