from odoo import models, fields, api,  _ 
from odoo.exceptions import UserError, ValidationError
import logging


class WeheVoucherRequest(models.Model):
    _name = 'weha.voucher.request'
    
    company_id = fields.Many2one('res.company', 'Company')
    number = fields.Char(string='Order number', default="/",readonly=True)
    
    