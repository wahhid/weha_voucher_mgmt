from odoo import models, fields, api,  _ 
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
import requests
from requests import ReadTimeout, ConnectTimeout, HTTPError, Timeout, ConnectionError

import logging

_logger = logging.getLogger(__name__)

class VoucherTransPurchase(models.Model):
    _name = "weha.voucher.trans.purchase"

    def trans_error(self):
        super(VoucherTransPurchase, self).write({'state': 'error'})

    def trans_close(self):
        super(VoucherTransPurchase, self).write({'state': 'done'})

    def complete_sku(self):
        mapping_sku = []
        if ';' in self.sku:
            arr_skus = self.sku.split(';')
            _logger.info(arr_skus)
            for str_sku in arr_skus: 
                vals = {}
                arr_sku  = str_sku.split('|')
                vals['voucher_trans_purchase_id'] = self.id
                vals['sku'] = arr_sku[0]
                vals['quantity'] = arr_sku[1]
                #vals['amount'] = arr_sku[2]
                _logger.info(arr_sku)
                domain = [
                    ('code_sku', '=', arr_sku[0]),
                ]
                mapping_sku_id = self.env['weha.voucher.mapping.sku'].search(domain, limit=1)
                if mapping_sku_id:
                    voucher_number_range_id = self.env['weha.voucher.number.ranges'].sudo().search([('voucher_code_id','=',mapping_sku_id.voucher_code_id.id)], limit=1)
                    _logger.info(voucher_number_range_id)
                    _logger.info(voucher_number_range_id.sequence_id)
                    if voucher_number_range_id:
                        vals['voucher_number_range_id'] = voucher_number_range_id.id
                        vals['voucher_code_id']  = voucher_number_range_id.voucher_code_id.id
                        vals['voucher_terms_id']  = voucher_number_range_id.voucher_code_id.voucher_terms_id.id
                        vals['year_id'] =  voucher_number_range_id.year_id.id
                        vals['voucher_mapping_sku_id'] = mapping_sku_id.id
                        vals['amount'] = int(vals['quantity']) * voucher_number_range_id.voucher_code_id.voucher_amount
                        self.env['weha.voucher.trans.purchase.sku'].create(vals)

        else:
            vals = {}
            arr_sku  = self.sku.split('|')
            vals['voucher_trans_purchase_id'] = self.id
            vals['sku'] = arr_sku[0]
            vals['quantity'] = arr_sku[1]
            #vals['amount'] = arr_sku[2]
            _logger.info(arr_sku)
            domain = [
                ('code_sku', '=', arr_sku[0]),
            ]
            mapping_sku_id = self.env['weha.voucher.mapping.sku'].search(domain, limit=1)
            if mapping_sku_id:
                voucher_mapping_pos_id = mapping_sku_id.voucher_mapping_pos_id
                #if voucher_mapping_pos_id.pos_trx_type == 'Promo':
                voucher_number_range_id = self.env['weha.voucher.number.ranges'].sudo().search([('voucher_code_id','=',mapping_sku_id.voucher_code_id.id)], limit=1)
                _logger.info(voucher_number_range_id)
                _logger.info(voucher_number_range_id.sequence_id)
                if voucher_number_range_id:
                   vals['voucher_number_range_id'] = voucher_number_range_id.id
                   vals['voucher_code_id']  = voucher_number_range_id.voucher_code_id.id
                   vals['voucher_terms_id']  = voucher_number_range_id.voucher_code_id.voucher_terms_id.id
                   vals['year_id'] =  voucher_number_range_id.year_id.id
                   vals['voucher_mapping_sku_id'] = mapping_sku_id.id
                   vals['amount'] = int(vals['quantity']) * voucher_number_range_id.voucher_code_id.voucher_amount
                self.env['weha.voucher.trans.purchase.sku'].create(vals)
                   
    def send_data_to_trust(self):
        headers = {'content-type': 'text/plain', 'charset':'utf-8'}
        base_url = 'http://localhost:5000'
        try:
            vouchers = []
            for voucher_trans_purchase_line_id in self.voucher_trans_purchase_line_ids:
                vouchers.append(voucher_trans_purchase_line_id.voucher_order_line_id.voucher_ean)
            data = {
                'date': self.trans_date.strftime('%Y-%m-%d'),
                'time': self.trans_date.strftime('%H:%M:%S'),
                'receipt_number': self.receipt_number,
                't_id': self.trans_date,
                'cashier_id': self.cashier_id,
                'store_id': self.store_id,
                'member_id': self.member_id,
                'vouchers': vouchers
            }
            _logger.info(data)
            eq = requests.post('{}/vs'.format(base_url), data=data)
            _logger.info(eq)
                #content = json.loads(req.content.decode('utf-8'))
                #headers.update(access-token=content.get('access_token'))
        except Exception as err:
            _logger.info(err)  
        finally:
            _logger.info("final")  

    def issuing_voucher(self):
        seq = self.env['ir.sequence']
        for voucher_trans_purchase_sku_id in self.voucher_trans_purchase_sku_ids:
            for i in range(1,voucher_trans_purchase_sku_id.quantity + 1):
                vals = {}
                vals.update({'member_id': self.member_id})
                vals.update({'operating_unit_id': 3})
                vals.update({'voucher_type': 'electronic'})
                vals.update({'voucher_code_id': voucher_trans_purchase_sku_id.voucher_code_id.id})
                vals.update({'voucher_terms_id': voucher_trans_purchase_sku_id.voucher_code_id.voucher_terms_id.id})
                vals.update({'tender_type': self.tender_type})
                vals.update({'bank_category': self.bank_category})
                if voucher_trans_purchase_sku_id.voucher_promo_id:
                    vals.update({'voucher_promo_id': voucher_trans_purchase_sku_id.voucher_promo_id.id})
                
                vals.update({'year_id': voucher_trans_purchase_sku_id.year_id.id})
                check_number = voucher_trans_purchase_sku_id.voucher_number_range_id.sequence_id.next_by_id()
                vals.update({'check_number': check_number})
                voucher_order_line_id = self.env['weha.voucher.order.line'].sudo().create(vals)            
                if not voucher_order_line_id:
                    raise ValidationError("Can't Generate voucher order line, contact administrator!")
                voucher_order_line_id.write({'state': 'activated'})
                voucher_order_line_id.create_order_line_trans(self.name, 'AC')

                vals = {
                    'voucher_trans_purchase_id': self.id,
                    'voucher_trans_purchase_sku_id': voucher_trans_purchase_sku_id.id,
                    'voucher_order_line_id': voucher_order_line_id.id
                }
                self.env['weha.voucher.trans.purchase.line'].create(vals)

    def get_json(self):
        vouchers = []
        #for voucher_trans_purchase_line_id in result.voucher_trans_purchase_line_ids:
        #    vouchers.append(voucher_trans_purchase_line_id.voucher_order_line_id.voucher_ean)
        for voucher_trans_purchase_sku_id in self.voucher_trans_purchase_sku_ids:
            lines = []
            for  voucher_trans_purchase_line_id in voucher_trans_purchase_sku_id.voucher_trans_purchase_line_ids:
                lines.append(voucher_trans_purchase_line_id.voucher_order_line_id.voucher_ean)
            vouchers.append({'sku': voucher_trans_purchase_sku_id.sku, 'vouchers' : lines})
        return vouchers

    name = fields.Char('Name', )
    trans_type = fields.Char('Trans Type', size=10)
    trans_date = fields.Datetime("Transaction Date")
    receipt_number = fields.Char("Receipt #", size=10)
    t_id = fields.Char("Terminal #")
    cashier_id = fields.Char("Cashier #", size=10)
    store_id = fields.Char("Store #", size=10)
    member_id = fields.Char("Member #", size=20)
    sku = fields.Char("SKU", size=255)

    # additional field for bank promo    
    tender_type = fields.Char('Tender Type')
    bank_category = fields.Char('Bank Category')
    bin_number = fields.Char("BIN")

    point_redeem = fields.Integer('Point Redeem')
    voucher_type = fields.Selection(
        [
            ('1', 'Sales'),
            ('2', 'Bank Promo'),
            ('3', 'Redeem'),
            ('4', 'Employee'),
        ],
        'Voucher Type',
        index=True
    )
    voucher_trans_purchase_line_ids = fields.One2many('weha.voucher.trans.purchase.line','voucher_trans_purchase_id','Lines')
    voucher_trans_purchase_sku_ids = fields.One2many('weha.voucher.trans.purchase.sku','voucher_trans_purchase_id','Skus')

    state = fields.Selection(
        [  
            ('open', 'Open'),
            ('done', 'Close'),
            ('error', 'Error')
        ],
        'Status',
        default='open',
        index=True
    )
    state_remark = fields.Char('Remark', size=250)

    @api.model
    def create(self, vals):
        #Create Trans #
        seq = self.env['ir.sequence']
        if 'company_id' in vals:
            seq = seq.with_context(force_company=vals['company_id'])
        vals['name'] = seq.next_by_code('weha.voucher.trans.purchase.sequence') or '/'
        
        if vals.get('voucher_type') == '1' or vals.get('voucher_type') == '3':
            pass     

        if vals.get('voucher_type') == '2':
            pass


        #Create Trans
        res = super(VoucherTransPurchase, self).create(vals)

        #Complete SKU List
        res.complete_sku()
            
        #Issuing Voucher
        res.issuing_voucher()

        #Update CRM
        res.send_data_to_trust()
        
        res.trans_close()

        return res    
    
    
class VoucheTransPurchaseSku(models.Model):
    _name = "weha.voucher.trans.purchase.sku"

    voucher_trans_purchase_id = fields.Many2one('weha.voucher.trans.purchase', 'Purchase #')
    voucher_mapping_sku_id = fields.Many2one('weha.voucher.mapping.sku', 'Mapping SKU #')
    sku = fields.Char("SKU", size=8)
    quantity = fields.Integer('Qty')
    amount = fields.Float('Amount', default="0.0")
    voucher_number_range_id = fields.Many2one('weha.voucher.number.ranges','Number Range')
    voucher_code_id = fields.Many2one("weha.voucher.code", "Voucher Code")
    voucher_terms_id = fields.Many2one("weha.voucher.terms", "Voucher Terms")
    year_id = fields.Many2one("weha.voucher.year", "Year")
    voucher_promo_id = fields.Many2one("weha.voucher.promo", "Voucher Promo")
    voucher_trans_purchase_line_ids = fields.One2many('weha.voucher.trans.purchase.line','voucher_trans_purchase_sku_id','Lines')
    state = fields.Selection(
        [  
            ('open', 'Open'),
            ('done', 'Close'),
            ('error', 'Error')
        ],
        'Status',
        default='open',
        index=True
    )

class VoucherTransPurchaseLine(models.Model):
    _name = "weha.voucher.trans.purchase.line"

    voucher_trans_purchase_id = fields.Many2one('weha.voucher.trans.purchase', 'Purchase #')
    voucher_trans_purchase_sku_id = fields.Many2one('weha.voucher.trans.purchase.sku', 'Purchase SKU #')
    voucher_order_line_id = fields.Many2one('weha.voucher.order.line', 'Voucher #')
    voucher_code_id = fields.Many2one('weha.voucher.code', string="Voucher Code", related="voucher_order_line_id.voucher_code_id")
    year_id = fields.Many2one('weha.voucher.year', string="Year", related="voucher_order_line_id.year_id")
    voucher_promo_id = fields.Many2one('weha.voucher.promo', string="Voucher Promo", related="voucher_order_line_id.voucher_promo_id")
    state = fields.Selection(
        [  
            ('open', 'Open'),
            ('done', 'Close'),
            ('error', 'Error')
        ],
        'Status',
        default='open',
        index=True
    )

class VoucherTransPayment(models.Model):
    _name = "weha.voucher.trans.payment"


    def trans_error(self):
        super(VoucherTransPayment, self).sudo().write({'state': 'error'})

    def trans_close(self):
        super(VoucherTransPayment, self).sudo().write({'state': 'done'})

    name = fields.Char('Name', )
    trans_date = fields.Datetime("Transaction Date")
    receipt_number = fields.Char("Receipt #", size=5)
    t_id = fields.Char("Transaction #")
    cashier_id = fields.Char("Cashier #", size=5)
    store_id = fields.Char("Store #", size=4)
    member_id = fields.Char("Member #", size=10)
    voucher_ean = fields.Char("Voucher Ean", size=20)
    voucher_order_line_id = fields.Many2one('weha.voucher.order.line','Voucher #')
    voucher_code_id = fields.Many2one("weha.voucher.code", "Voucher Code")
    year_id = fields.Many2one("weha.voucher.year", "Year")
    voucher_promo_id = fields.Many2one("weha.voucher.promo", "Voucher Promo")
    state = fields.Selection(
        [  
            ('open', 'Open'),
            ('done', 'Close'),
            ('error', 'Error')
        ],
        'Status',
        default='open',
        index=True
    )
    state_remark = fields.Char('Remark', size=250)

    @api.model 
    def create(self, vals):
        #Create Trans #
        seq = self.env['ir.sequence']
        if 'company_id' in vals:
            seq = seq.with_context(force_company=vals['company_id'])
        vals['name'] = seq.next_by_code('weha.voucher.trans.payment.sequence') or '/'

        res = super(VoucherTransPayment, self).create(vals)
        voucher_order_line_id = res.voucher_order_line_id
        voucher_order_line_id.sudo().write({'state':'reserved'})
        voucher_order_line_id.create_order_line_trans(res.name, 'RS')
        res.trans_close()
        return res
  
class VoucheTransPaymentSku(models.Model):
    _name = "weha.voucher.trans.payment.sku"

    voucher_trans_purchase_id = fields.Many2one('weha.voucher.trans.payment', 'Payment #')
    sku = fields.Char("SKU", size=8)
    quantity = fields.Integer('Qty')
    amount = fields.Float('Amount', default="0.0")
    voucher_number_range_id = fields.Many2one('weha.voucher.number.ranges','Number Range')
    voucher_code_id = fields.Many2one("weha.voucher.code", "Voucher Code")
    voucher_terms_id = fields.Many2one("weha.voucher.terms", "Voucher Terms")
    year_id = fields.Many2one("weha.voucher.year", "Year")
    voucher_promo_id = fields.Many2one("weha.voucher.promo", "Voucher Promo")
    state = fields.Selection(
        [  
            ('open', 'Open'),
            ('done', 'Close'),
            ('error', 'Error')
        ],
        'Status',
        default='open',
        index=True
    )

class VoucherTransStatus(models.Model):
    _name = "weha.voucher.trans.status"

    def trans_error(self):
        super(VoucherTransStatus, self).sudo().write({'state': 'error'})

    def trans_close(self):
        super(VoucherTransStatus, self).sudo().write({'state': 'done'})

    def get_json(self):
        data = {}
        if self.process_type == 'reserved':
            voucher_trans_status_line_id = self.voucher_trans_status_line_ids and self.voucher_trans_status_line_ids[0] or False
            if voucher_trans_status_line_id:
                voucher_order_line_id = voucher_trans_status_line_id.voucher_order_line_id
                data.update({'amount': voucher_order_line_id.voucher_code_id.voucher_amount})
                voucher_mapping_sku_id  = self.env['weha.voucher.mapping.sku'].search([('voucher_code_id','=', voucher_order_line_id.voucher_code_id.id)],limit=1)
                if voucher_mapping_sku_id:    
                    voucher_mapping_pos_id = voucher_mapping_sku_id.voucher_mapping_pos_id
                    if voucher_mapping_pos_id.pos_trx_type == 'Promo':
                        data.update({'tender_type': voucher_order_line_id.tender_type})
                        data.update({'bank_category': voucher_order_line_id.bank_category})
                    else:
                        data.update({'tender_type': ''})
                        data.update({'bank_category': ''})
        return data 
                
    name = fields.Char('Name', )
    trans_date = fields.Datetime("Transaction Date")
    receipt_number = fields.Char("Receipt #", size=5)
    t_id = fields.Char("Transaction #")
    cashier_id = fields.Char("Cashier #", size=5)
    store_id = fields.Char("Store #", size=4)
    member_id = fields.Char("Member #", size=10)
    voucher_ean = fields.Char("Voucher Ean", size=20)
    voucher_code_id = fields.Many2one("weha.voucher.code", "Voucher Code")
    year_id = fields.Many2one("weha.voucher.year", "Year")
    voucher_promo_id = fields.Many2one("weha.voucher.promo", "Voucher Promo")
    voucher_ean = fields.Char('Vouchers', size=250)
    voucher_trans_status_line_ids = fields.One2many('weha.voucher.trans.status.line','voucher_trans_status_id','Lines')
    state = fields.Selection(
        [  
            ('open', 'Open'),
            ('done', 'Close'),
            ('error', 'Error')
        ],
        'Status',
        default='open',
        index=True
    )
    state_remark = fields.Char('Remark', size=250)
    process_type = fields.Selection(
        [  
            ('reserved', 'Reserved'),
            ('activated', 'Activated'),
            ('used', 'Used'),
            
        ],
        'Process Type',
        index=True
    )

    @api.model 
    def create(self, vals):
       
        #Create Trans #
        seq = self.env['ir.sequence']
        if 'company_id' in vals:
            seq = seq.with_context(force_company=vals['company_id'])
        vals['name'] = seq.next_by_code('weha.voucher.trans.status.sequence') or '/'

        res = super(VoucherTransStatus, self).create(vals)
        order_line_trans_obj = self.env['weha.voucher.order.line.trans']

        # arr_voucher_ean = vals['voucher_ean'].split("|")
        # voucher_ean_ids = []
        # for voucher_ean in arr_voucher_ean:
        domain = [
            ('voucher_ean','=', vals['voucher_ean']),
            ('state','=', 'activated')
        ]
        voucher_order_line_id = self.env['weha.voucher.order.line'].sudo().search(domain, limit=1)
        _logger.info(voucher_order_line_id)
        if voucher_order_line_id:
            data = {
                'voucher_trans_status_id': res.id,
                'voucher_order_line_id': voucher_order_line_id.id,   
            }
            result = self.env['weha.voucher.trans.status.line'].sudo().create(data)
            if result:
                if vals['process_type'] == 'reserved':
                    voucher_order_line_id.sudo().write({'state': 'reserved'})
                    voucher_order_line_id.create_order_line_trans(res.name, 'RS')
                elif vals['process_type'] == 'activated':
                    voucher_order_line_id.sudo().write({'state': 'activated'})
                    vals = {}
                    voucher_order_line_id.create_order_line_trans(res.name, 'AC')
                elif vals['process_type'] == 'used':
                    voucher_order_line_id.sudo().write({'state': 'used'})
                    voucher_order_line_id.create_order_line_trans(res.name, 'US')
                else:
                    pass
                    
        res.trans_close()
        return res
  
class VoucheTransStatusLine(models.Model):
    _name = "weha.voucher.trans.status.line"

    voucher_trans_status_id = fields.Many2one('weha.voucher.trans.status', 'Status #')
    voucher_order_line_id = fields.Many2one('weha.voucher.order.line', 'Voucher #')
    voucher_code_id = fields.Many2one("weha.voucher.code", "Voucher Code")
    voucher_terms_id = fields.Many2one("weha.voucher.terms", "Voucher Terms")
    year_id = fields.Many2one("weha.voucher.year", "Year")
    voucher_promo_id = fields.Many2one("weha.voucher.promo", "Voucher Promo")
    amount = fields.Float('Amount', default="0.0")
    state = fields.Selection(
        [  
            ('open', 'Open'),
            ('done', 'Close'),
            ('error', 'Error')
        ],
        'Status',
        default='open',
        index=True
    )