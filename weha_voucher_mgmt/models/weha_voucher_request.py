from odoo import models, fields, api,  _ 
from odoo.exceptions import UserError, ValidationError
import logging


class WeheVoucherRequest(models.Model):
    _name = 'weha.voucher.request'
    _rec_name = 'number'
    _order = 'number desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    company_id = fields.Many2one('res.company', 'Company')
    number = fields.Char(string='Request number', default="/",readonly=True)
    date_request = fields.Date('Date Request')
    user_id = fields.Many2one('res.users', 'Requester')
    operating_unit_id = fields.Many2one('operating.unit', 'Store')
    

        
    