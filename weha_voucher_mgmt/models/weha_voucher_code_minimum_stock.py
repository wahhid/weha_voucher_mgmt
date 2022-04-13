from odoo import models, fields, api,  _ 
from odoo.exceptions import UserError, ValidationError

import logging
_logger = logging.getLogger(__name__)

class VoucherCodeMinimumStock(models.Model):
    _name = 'weha.voucher.code.minimum.stock'
    _description = 'Voucher Code Minimum Stock'

    voucher_code_id = fields.Many2one('weha.voucher.code', 'Voucher Code', required=False)
    operating_unit_id = fields.Many2one('operating.unit', 'Store', required=True)
    quantity = fields.Integer(string='Minimum Stock', default=0,)