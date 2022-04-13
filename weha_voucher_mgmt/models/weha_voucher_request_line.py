from odoo import models, fields, api,  _ 
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class VoucherRequestLine(models.Model):
    _name = 'weha.voucher.request.line'
    _description = 'Voucher Request Line'
    
    def calculate_total(self):
        for row in self:
            row.total_amount = row.voucher_amount * row.voucher_qty


    voucher_request_id = fields.Many2one(comodel_name='weha.voucher.request', string='Voucher Request')
    voucher_mapping_sku_id = fields.Many2one('weha.voucher.mapping.sku','Mapping SKU #',  required=True)
    voucher_code_id = fields.Many2one('weha.voucher.code', 'Voucher Code', required=False, readonly=True, related="voucher_mapping_sku_id.voucher_code_id", store=True)
    #voucher_code_id = fields.Many2one('weha.voucher.code', 'Voucher Code', required=True, readonly=False)
    voucher_amount = fields.Float('Amount', related='voucher_code_id.voucher_amount', readonly=True)
    voucher_qty = fields.Integer(string='Quantity Ordered', required=True)
    total_amount = fields.Float('Total', readonly=True, compute="calculate_total")
    _sql_constraints = [
        ('voucher_code_unique', 'unique (voucher_code_id)', 'Voucher Code already exist!')
    ]

class VoucherRequestAllocateLine(models.Model):
    _name = 'weha.voucher.request.allocate.line'
    
    voucher_request_id = fields.Many2one(comodel_name='weha.voucher.request', string='Voucher Request')
    voucher_allocate_id = fields.Many2one(comodel_name='weha.voucher.allocate', string='Voucher Allocate')
    voucher_order_line_id = fields.Many2one('weha.voucher.order.line', 'Voucher')
    voucher_code_id = fields.Many2one('weha.voucher.code', string="Voucher Code", related="voucher_order_line_id.voucher_code_id")
    year_id = fields.Many2one('weha.voucher.year', string="Year", related="voucher_order_line_id.year_id")
    voucher_promo_id = fields.Many2one('weha.voucher.promo', string="Voucher Promo", related="voucher_order_line_id.voucher_promo_id")
    state = fields.Selection([('open','Open'),('received','Received')], 'Status', default='open')
    
