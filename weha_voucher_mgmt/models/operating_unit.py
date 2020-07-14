from odoo import models, fields, api,  _ 
from odoo.exceptions import UserError, ValidationError
import logging


_logger = logging.getLogger(__name__)


class OperatingUnit(models.Model):
    _name = 'operating.unit'
    _inherit = 'operating.unit'
    
    @api.depends('voucher_ids')
    def _compute_voucher_count(self):
        for record in self:
            record.voucher_count = len(record.voucher_ids)

    color = fields.Integer(string='Color Index')

    voucher_ids = fields.One2many(
        'weha.voucher.order.line',
        'operating_unit_id',
        string="Vouchers")
    
    voucher_count = fields.Integer(
        string="Number of Vouchers",
        compute='_compute_voucher_count')
    
    