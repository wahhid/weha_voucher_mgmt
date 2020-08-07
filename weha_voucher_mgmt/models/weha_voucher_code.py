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
    