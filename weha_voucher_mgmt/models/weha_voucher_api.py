from odoo import models, fields, api,  _ 
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class VoucherTransPurchase(models.Model):
    _name = "weha.voucher.trans.purchase"
    
    def issuing_voucher(self):
        domain=[
            ('voucher_code_id','=', self.voucher_code_id.id),
            ('state','=','open')
        ]
        voucher_order_line_ids = self.env['weha.voucher.order.line'].search(domain,order="check_number asc",limit=self.quantity)
        _logger.info(voucher_order_line_ids)
        #res = voucher_order_line_ids.write({'state':'activated'})
        for voucher_order_line_id in  voucher_order_line_ids:
            vals = {}
            vals.update({'voucher_trans_purchase_id': self.id})
            vals.update({'voucher_order_line_id': voucher_order_line_id.id})
            voucher_trans_purchase_line_id = self.env['weha.voucher.trans.purchase.line'].create(vals)
            voucher_order_line_id.write({'state':'activated'})

    name = fields.Char('Name', )
    trans_date = fields.Datetime("Transaction Date")
    receipt_number = fields.Char("Receipt #", size=5)
    t_id = fields.Char("Transaction #")
    cashier_id = fields.Char("Cashier #", size=5)
    store_id = fields.Char("Store #", size=4)
    member_id = fields.Char("Member #", size=10)
    sku = fields.Char("SKU", size=8)
    voucher_code_id = fields.Many2one("weha.voucher.code", "Voucher Code")
    year_id = fields.Many2one("weha.voucher.year", "Year")
    voucher_promo_id = fields.Many2one("weha.voucher.promo", "Voucher Promo")
    quantity = fields.Integer('Qty')
    amount = fields.Float('Amount', default="0.0")
    voucher_type = fields.Selection(
        [
            ('1', 'Sales'),
            ('2', 'Bank Promo'),
            ('3', 'Employee'),
        ],
        'Voucher Type'
    )
    voucher_trans_purchase_line_ids = fields.One2many('weha.voucher.trans.purchase.line','voucher_trans_purchase_id','Lines')
    state = fields.Selection(
        [  
            ('open', 'Open'),
            ('done', 'Close'),
            ('error', 'Error')
        ],
        'Status',
        default='open'
    )
    state_remark = fields.Char('Remark', size=250)

    @api.model
    def create(self, vals):
        #Create Trans #
        seq = self.env['ir.sequence']
        if 'company_id' in vals:
            seq = seq.with_context(force_company=vals['company_id'])
        vals['name'] = seq.next_by_code('weha.voucher.trans.purchase.sequence') or '/'
        domain = [
            ('code_sku','=', vals.get('sku')),
        ]
        mapping_sku_id = self.env['weha.voucher.mapping.sku'].search(domain, limit=1)
        vals['voucher_code_id'] = mapping_sku_id.voucher_code_id.id
        #Create Trans
        res = super(VoucherTransPurchase, self).create(vals)

        #Issuing Voucher
        res.issuing_voucher()

        

        return res    
    
    

class VoucherTransPurchaseLine(models.Model):
    _name = "weha.voucher.trans.purchase.line"

    voucher_trans_purchase_id = fields.Many2one('weha.voucher.trans.purchase', 'Purchase #')
    voucher_order_line_id = fields.Many2one('weha.voucher.order.line', 'Voucher #')


class VoucherTransPayment(models.Model):
    _name = "weha.voucher.trans.payment"

    

