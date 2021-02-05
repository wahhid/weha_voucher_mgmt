from odoo import models, fields, api,  _ 
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class VoucherIssuingLine(models.Model):
    _name = 'weha.voucher.issuing.line'
    
    def check_voucher_order_line(self, voucher_issuing_id, voucher_order_line_id):
        domain = [
            ('voucher_order_line_id', '=', voucher_order_line_id),
            ('state', '=', 'open'),
        ]        
        voucher_issuing_line_ids = self.env['weha.voucher.issuing.line'].search(domain)
        if not voucher_issuing_line_ids:
            return False
        return True

    def trans_close(self):
        super(VoucherIssuingLine, self).write({'state': 'issued'})


    voucher_issuing_id = fields.Many2one(comodel_name='weha.voucher.issuing', string='Voucher Allocate')
    voucher_order_line_id = fields.Many2one('weha.voucher.order.line', 'Voucher')
    voucher_code_id = fields.Many2one('weha.voucher.code', string="Voucher Code", related="voucher_order_line_id.voucher_code_id")
    year_id = fields.Many2one('weha.voucher.year', string="Year", related="voucher_order_line_id.year_id")
    voucher_promo_id = fields.Many2one('weha.voucher.promo', string="Voucher Promo", related="voucher_order_line_id.voucher_promo_id")
    member_id = fields.Char('Member #', size=20)
    state = fields.Selection([('open','Open'),('issued','Issued'),('cancelled','Cancelled')], 'Status', default='open')


class VoucherIssuingEmployeeLine(models.Model):
    _name = 'weha.voucher.issuing.employee.line'
    

    def trans_close(self):
        super(VoucherIssuingEmployeeLine, self).write({'state': 'issued'})

    voucher_issuing_id = fields.Many2one(comodel_name='weha.voucher.issuing', string='Voucher Allocate')
    voucher_trans_purchase_id = fields.Many2one('weha.voucher.trans.payment', 'Payment #')
    employee_name = fields.Char("Employee", size=100)
    employee_nik = fields.Char("NIK", size=50)
    member_id = fields.Char("Member #", size=20)
    sku = fields.Char("SKU #", size=20)
    quantity = fields.Integer('Qty')
    file_line_id = fields.Many2one('weha.voucher.issuing.file.line', 'File #')
    state = fields.Selection([('open','Open'),('issued','Issued'),('cancelled','Cancelled')], 'Status', default='open')


class VoucherAllocateFileLine(models.Model):
    _name = 'weha.voucher.issuing.file.line'
    _rec_name = 'file_attachment_name'

    def delete_lines(self):
        self.env.cr.execute('DELETE FROM weha_voucher_issuing_employee_line WHERE file_line_id=' + str(self.id))
   
    voucher_issuing_id = fields.Many2one(comodel_name='weha.voucher.issuing', string='Voucher Issuing')
    file_attachment = fields.Binary('File')
    file_attachment_name = fields.Char('Filename', )
    voucher_issuing_employee_line_ids = fields.One2many(
        comodel_name='weha.voucher.issuing.employee.line', 
        inverse_name='file_line_id', 
        string='Employee Lines',
    )

    def unlink(self):
        self.delete_lines()
        super(VoucherAllocateFileLine, self).unlink()
