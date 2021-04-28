from odoo import models, fields, api,  _ 
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class VoucherScrapLine(models.Model):
    _name = 'weha.voucher.scrap.line'
    
    def check_voucher_order_line(self, voucher_scrap_id, voucher_order_line_id):
        domain = [
            ('voucher_order_line_id', '=', voucher_order_line_id),
            ('state', '=', 'open'),
        ]        
        voucher_scrap_line_ids = self.env['weha.voucher.scrap.line'].search(domain)
        if not voucher_scrap_line_ids:
            return False
        return True

    
    voucher_scrap_id = fields.Many2one(comodel_name='weha.voucher.scrap', string='Voucher Scrap')
    voucher_order_line_id = fields.Many2one('weha.voucher.order.line', 'Voucher')
    voucher_code_id = fields.Many2one('weha.voucher.code', string="Voucher Code", related="voucher_order_line_id.voucher_code_id")
    year_id = fields.Many2one('weha.voucher.year', string="Year", related="voucher_order_line_id.year_id")
    voucher_promo_id = fields.Many2one('weha.voucher.promo', string="Voucher Promo", related="voucher_order_line_id.voucher_promo_id")
    state = fields.Selection([('open','Open'),('cancelled','Cancelled'),('damaged','Scrap')], 'Status', default='open')
    