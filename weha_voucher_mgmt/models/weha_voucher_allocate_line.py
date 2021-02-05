from odoo import models, fields, api,  _ 
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class VoucherAllocateRange(models.Model):  
    _name = 'weha.voucher.allocate.range'
    
    @api.depends('voucher_allocate_line_ids')
    def _calculate_voucher_count(self):
        for row in self:
            row.voucher_count = len(row.voucher_allocate_line_ids)
    
    @api.depends('voucher_allocate_line_ids')
    def _calculate_voucher_received(self):
        for row in self:
            row.voucher_received = len(row.voucher_allocate_line_ids.filtered(lambda r: r.state == 'received'))


    voucher_allocate_id = fields.Many2one(comodel_name='weha.voucher.allocate', string='Voucher Allocate')
    start_number = fields.Char("Start Number", size=13, required=True)
    start_check_number = fields.Integer("Start Check Number")
    end_number = fields.Char("End Number", size=13, required=True)  
    end_check_number = fields.Integer("End Check Number")
    voucher_count = fields.Integer(string="Voucher Count", compute="_calculate_voucher_count", readonly=True)
    voucher_received = fields.Integer(string="Voucher Received", compute="_calculate_voucher_received", readonly=True)
    voucher_allocate_line_ids = fields.One2many('weha.voucher.allocate.line','voucher_allocate_range_id','Allocate Lines')
    
    def unlink(self):
        range_id = self.id
        strSQL = """DELETE FROM weha_voucher_allocate_line WHERE voucher_allocate_range_id={}""".format(range_id)
        self.env.cr.execute(strSQL)
        super(VoucherAllocateRange, self).unlink()
       
    

class VoucherAllocateLine(models.Model):
    _name = 'weha.voucher.allocate.line'

    def check_voucher_order_line(self, voucher_allocate_id, voucher_order_line_id):
        domain = [
            ('voucher_order_line_id', '=', voucher_order_line_id),
            ('state', '=', 'open'),
        ]        
        voucher_allocate_line_ids = self.env['weha.voucher.allocate.line'].search(domain)
        if not voucher_allocate_line_ids:
            return False
        return True
        
    def create_allocate_line(self, voucher_allocated_id, voucher_order_line_id):
        vals = {
            'voucher_allocate_id': voucher_allocated_id,
            'voucher_order_line_id': voucher_order_line_id
        }
        self.env['weha.voucher.allocate.line'].create(vals)
        
    voucher_allocate_id = fields.Many2one(comodel_name='weha.voucher.allocate', string='Voucher Allocate')
    voucher_allocate_range_id = fields.Many2one('weha.voucher.allocate.range','Voucher Allocate')
    voucher_order_line_id = fields.Many2one('weha.voucher.order.line', 'Voucher')
    voucher_code_id = fields.Many2one('weha.voucher.code', string="Voucher Code", related="voucher_order_line_id.voucher_code_id")
    year_id = fields.Many2one('weha.voucher.year', string="Year", related="voucher_order_line_id.year_id")
    voucher_promo_id = fields.Many2one('weha.voucher.promo', string="Voucher Promo", related="voucher_order_line_id.voucher_promo_id")
    state = fields.Selection([('open','Open'),('received','Received'),('cancelled','Cancelled')], 'Status', default='open')
    

