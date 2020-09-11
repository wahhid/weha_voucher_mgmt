from odoo import models, fields, api,  _ 
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class VoucherScrapLine(models.Model):
    _name = 'weha.voucher.scrap.line'

    voucher_code_id = fields.Many2one('weha.voucher.code', 'Voucher Code', required=True)
    voucher_scrap_id = fields.Many2one(comodel_name='weha.voucher.scrap', string='Voucher Scrap')
    number_ranges_ids = fields.One2many(comodel_name='weha.voucher.number.ranges', inverse_name='stock_transfer_line_id', string='Stock Transfer Range')
    amount = fields.Integer(string='Amount')
    