from odoo import models, fields, api,  _ 
from odoo.exceptions import UserError, ValidationError

import logging
_logger = logging.getLogger(__name__)

class VoucherCode(models.Model):
    _name = 'weha.voucher.code'

    name = fields.Char(
        string='Name',
        size=200,
        required=True
    )
    
    code = fields.Char(
        string='Code',
        size=2,
        required=True
    )
    
    voucher_type = fields.Selection(
        string='Voucher Type',
        selection=[('physical', 'Physical'), ('electronic', 'Electronic')],
        default='physical'
    )
    
    voucher_amount = fields.Float('Denom', default=0.0)
    

    voucher_minimum_stock_ids = fields.One2many(comodel_name='weha.voucher.code.minimum.stock', inverse_name='voucher_code_id', string='Voucher Code ID')
    
    
    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Code already exists!')
    ]