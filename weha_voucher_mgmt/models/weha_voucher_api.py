from odoo import models, fields, api,  _ 
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
import requests
from requests import ReadTimeout, ConnectTimeout, HTTPError, Timeout, ConnectionError
from ftplib import FTP
import os
import base64
from datetime import datetime
from datetime import date as dt
import csv
import logging
import io
import json
import string
import random

_logger = logging.getLogger(__name__)

ftp_url = "weha_voucher_mgmt.ftp_url"
ftp_username = "weha_voucher_mgmt.ftp_username"
ftp_password = "weha_voucher_mgmt.ftp_password"

class VoucherTransPurchase(models.Model):
    _name = "weha.voucher.trans.purchase"
    _description = 'Voucher Transaction Purchase (API)'

    def trans_error(self):
        super(VoucherTransPurchase, self).write({'state': 'error'})

    def trans_close(self):
        super(VoucherTransPurchase, self).write({'state': 'done'})

    def process_and_complete_sku(self):
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
                    current_date = dt.today()
                    _logger.info(current_date)
                    domain = [
                        ('voucher_mapping_sku_id', '=' , mapping_sku_id.id),
                        ('voucher_promo_id.start_date', '<=',  current_date),
                        ('voucher_promo_id.end_date', '>=', current_date)
                    ]
                    _logger.info(domain)
        
                    voucher_promo_line_id = self.env['weha.voucher.promo.line'].search(domain, limit=1)
                    _logger.info(voucher_promo_line_id)
                    current_year = self.env['weha.voucher.year'].get_current_year()
                    voucher_number_range_id = self.env['weha.voucher.number.ranges'].sudo().search([('voucher_code_id','=',mapping_sku_id.voucher_code_id.id),('year_id','=', current_year.id)], limit=1)
                    _logger.info(voucher_number_range_id)
                    _logger.info(voucher_number_range_id.sequence_id)
                    if voucher_number_range_id:
                        vals['voucher_number_range_id'] = voucher_number_range_id.id
                        vals['voucher_code_id']  = voucher_number_range_id.voucher_code_id.id
                        vals['voucher_terms_id']  = voucher_number_range_id.voucher_code_id.voucher_terms_id.id
                        vals['year_id'] =  voucher_number_range_id.year_id.id
                        vals['voucher_mapping_sku_id'] = mapping_sku_id.id
                        if voucher_promo_line_id:
                            vals['voucher_promo_id'] = voucher_promo_line_id.voucher_promo_id.id
                        vals['amount'] = int(vals['quantity']) * voucher_number_range_id.voucher_code_id.voucher_amount
                    self.env['weha.voucher.trans.purchase.sku'].create(vals)  
                else:
                    _logger.info("Mappign SKU not Found")                
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
                current_date = dt.today()
                _logger.info(current_date)
                domain = [
                    ('voucher_mapping_sku_id', '=' , mapping_sku_id.id),
                    ('voucher_promo_id.start_date', '<=',  current_date),
                    ('voucher_promo_id.end_date', '>=', current_date)
                ]
                _logger.info(domain)
    
                voucher_promo_line_id = self.env['weha.voucher.promo.line'].search(domain, limit=1)
                _logger.info(voucher_promo_line_id)
                current_year = self.env['weha.voucher.year'].get_current_year()
                voucher_number_range_id = self.env['weha.voucher.number.ranges'].sudo().search([('voucher_code_id','=',mapping_sku_id.voucher_code_id.id),('year_id','=', current_year.id)], limit=1)
                _logger.info(voucher_number_range_id)
                _logger.info(voucher_number_range_id.sequence_id)
                if voucher_number_range_id:
                   vals['voucher_number_range_id'] = voucher_number_range_id.id
                   vals['voucher_code_id']  = voucher_number_range_id.voucher_code_id.id
                   vals['voucher_terms_id']  = voucher_number_range_id.voucher_code_id.voucher_terms_id.id
                   vals['year_id'] =  voucher_number_range_id.year_id.id
                   vals['voucher_mapping_sku_id'] = mapping_sku_id.id
                   if voucher_promo_line_id:
                        vals['voucher_promo_id'] = voucher_promo_line_id.voucher_promo_id.id
                   vals['amount'] = int(vals['quantity']) * voucher_number_range_id.voucher_code_id.voucher_amount
                self.env['weha.voucher.trans.purchase.sku'].create(vals)
            else:
                _logger.info("Mappign SKU not Found")

    def _auth_trust(self):
        config_parameter_obj = self.env['ir.config_parameter'].sudo()
        crm_api_url = config_parameter_obj.get_param('crm_api_url')
        _logger.info(crm_api_url)
        crm_api_username = config_parameter_obj.get_param('crm_api_username')
        crm_api_password = config_parameter_obj.get_param('crm_api_password')

        #url = "http://apiindev.trustranch.co.id/login"
        #payload='barcode=3000030930&password=weha.ID!!2020'

        payload=f'barcode={crm_api_username}&password={crm_api_password}'
        
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        try:
            response = requests.request("POST", crm_api_url + "/login", headers=headers, data=payload)
            #json_data = json.loads(response.text)
            str_json_data  = response.text.replace("'"," ")
            json_data = json.loads(str_json_data)
            #_logger.info(response.text)
            _logger.info(json_data['data']['api_token'])
            return json_data['data']['api_token']
        except Exception as err:
            _logger.info(err)  

    def send_data_to_trust(self):
        config_parameter_obj = self.env['ir.config_parameter'].sudo()
        crm_api_url = config_parameter_obj.get_param('crm_api_url')
   
        api_token = self._auth_trust()
        headers = {'content-type': 'text/plain', 'charset':'utf-8'}
        #base_url = 'http://apiindev.trustranch.co.id'
        try:
            vouchers = []
            for voucher_trans_purchase_line_id in self.voucher_trans_purchase_line_ids:
                vouchers.append(voucher_trans_purchase_line_id.voucher_order_line_id.voucher_ean + ';' + voucher_trans_purchase_line_id.voucher_order_line_id.expired_date.strftime('%Y-%m-%d') + ";" + voucher_trans_purchase_line_id.voucher_trans_purchase_sku_id.sku  ) 
            data = {
                'date': self.trans_date.strftime('%Y-%m-%d'),
                'time': self.trans_date.strftime('%H:%M:%S'),
                'receipt': self.receipt_number,
                'transactionId': self.t_id,
                'cashierId': self.cashier_id,
                'storeId': self.store_id,   
                #'memberId': '3000000183',
                'memberId': self.member_id,
                'vouchers': '|'.join(vouchers)
            }
            _logger.info(data)
            headers = {'Authorization' : 'Bearer ' + api_token}
            req = requests.post('{}/vms/get-voucher'.format(crm_api_url), headers=headers ,data=data)
            _logger.info(req.text)
            
            #content = json.loads(req.content.decode('utf-8'))
            #headers.update(access-token=content.get('access_token'))
        except Exception as err:
            _logger.info(err)  
        finally:
            _logger.info("final")   

    def create_and_reserved_voucher(self):
        seq = self.env['ir.sequence']
        operating_unit_id = self.env['operating.unit'].search([('code','=', self.store_id)],limit=1)
        for voucher_trans_purchase_sku_id in self.voucher_trans_purchase_sku_ids:
            for i in range(1,voucher_trans_purchase_sku_id.quantity + 1):
                vals = {}
                vals.update({'batch_id': self.batch_id})
                vals.update({'member_id': self.member_id})
                vals.update({'operating_unit_id': operating_unit_id.id})
                vals.update({'voucher_type': 'electronic'})
                vals.update({'voucher_sku': voucher_trans_purchase_sku_id.sku})
                vals.update({'receipt_number': self.receipt_number})
                vals.update({'t_id': self.t_id})
                #Set Voucher Trans Type for API#4 and Empty after API#4 confirm
                vals.update({'voucher_trans_type': self.voucher_type})
                vals.update({'voucher_code_id': voucher_trans_purchase_sku_id.voucher_code_id.id})
                vals.update({'voucher_terms_id': voucher_trans_purchase_sku_id.voucher_code_id.voucher_terms_id.id})
                vals.update({'tender_type': self.tender_type})
                vals.update({'bank_category': self.bank_category})
                #Voucher Promo Process
                if voucher_trans_purchase_sku_id.voucher_promo_id:
                    vals.update({'voucher_promo_id': voucher_trans_purchase_sku_id.voucher_promo_id.id})
                    vals.update({'min_card_payment': voucher_trans_purchase_sku_id.voucher_promo_id.min_card_payment})
                    vals.update({'voucher_count_limit': voucher_trans_purchase_sku_id.voucher_promo_id.voucher_count_limit})

                #Get Current Year
                current_year = self.env['weha.voucher.year'].get_current_year()
                vals.update({'year_id': current_year.id})

                check_number = voucher_trans_purchase_sku_id.voucher_number_range_id.sequence_id.next_by_id()
                vals.update({'check_number': check_number})

                #Create Voucher Order Line
                voucher_order_line_id = self.env['weha.voucher.order.line'].sudo().create(vals)            
                if not voucher_order_line_id:
                    raise ValidationError("Can't Generate voucher order line, contact administrator!")
                voucher_order_line_id.write({'state': 'reserved'})
                voucher_order_line_id.create_order_line_trans(self.name, 'RS')

                vals = {
                    'voucher_trans_purchase_id': self.id,
                    'voucher_trans_purchase_sku_id': voucher_trans_purchase_sku_id.id,
                    'voucher_order_line_id': voucher_order_line_id.id
                }
                self.env['weha.voucher.trans.purchase.line'].create(vals)

    def get_json(self):
        vouchers = []
        for voucher_trans_purchase_sku_id in self.voucher_trans_purchase_sku_ids:
            lines = []
            for  voucher_trans_purchase_line_id in voucher_trans_purchase_sku_id.voucher_trans_purchase_line_ids:
                lines.append(voucher_trans_purchase_line_id.voucher_order_line_id.voucher_ean + "|" + voucher_trans_purchase_line_id.voucher_order_line_id.expired_date.strftime("%Y-%m-%d"))
            vouchers.append({'sku': voucher_trans_purchase_sku_id.sku, 'vouchers' : lines})
        return vouchers

    def get_json_v2(self):
        return {'batch_id', self.batch_id}

    name = fields.Char('Name', )
    batch_id = fields.Char('Batch #', size=10, readonly=True)
    trans_type = fields.Char('Trans Type', size=10)
    trans_date = fields.Datetime("Transaction Date")
    receipt_number = fields.Char("Receipt #", size=10)
    t_id = fields.Char("Terminal #")
    cashier_id = fields.Char("Cashier #", size=10)
    store_id = fields.Char("Store #", size=10)
    member_id = fields.Char("Member #", size=20)
    sku = fields.Char("SKU", size=255)
    ref = fields.Char(string='Source Document', required=False)

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
        
        batch_id = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
        _logger.info(batch_id)
        vals['batch_id'] = batch_id
        
        #Create Trans
        res = super(VoucherTransPurchase, self).create(vals)

        #Process SKU List
        res.process_and_complete_sku()

        #Reserved Voucher
        if res.voucher_type == '4':
            #if voucher for employee
            for voucher_trans_purchase_line_id in self.voucher_trans_purchase_line_ids:
                err , message = voucher_trans_purchase_line_id.voucher_order_line_id.send_data_to_trust()
                if not err:
                    voucher_trans_purchase_line_id.voucher_order_line_id.sudo().write({'state': 'activated'})
                    voucher_trans_purchase_line_id.voucher_order_line_id.voucher_trans_type = False
        else:
            res.create_and_reserved_voucher()  

        #Close Purchase Transaction
        res.trans_close()

        return res    
      
class VoucheTransPurchaseSku(models.Model):
    _name = "weha.voucher.trans.purchase.sku"
    _description = 'Voucher Transaction Purchase SKU (API)'

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
    _description = 'Voucher Transaction Purchase Line (API)'

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
    _description = 'Voucher Transaction Payment (API)'


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
    _description = 'Voucher Transaction Payment SKU (API)'

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
    _description = 'Voucher Transaction Status (API)'

    def trans_error(self):
        super(VoucherTransStatus, self).sudo().write({'state': 'error'})

    def trans_close(self):
        super(VoucherTransStatus, self).sudo().write({'state': 'done'})

    def process_voucher_order_line_reserved(self, vals):
        arr_ean = vals['voucher_ean'].split('|')
        for voucher_ean in arr_ean:
            domain = [
                ('voucher_ean', '=', voucher_ean),
                ('state', '=', 'activated')
            ]
            voucher_order_line_id = self.env['weha.voucher.order.line'].sudo().search(domain, limit=1)
            _logger.info(voucher_order_line_id)
            if voucher_order_line_id:
                data = {
                    'voucher_trans_status_id': self.id,
                    'voucher_order_line_id': voucher_order_line_id.id,   
                }
                result = self.env['weha.voucher.trans.status.line'].sudo().create(data)
                if result:
                    vals = {}
                    vals.update({'voucher_trans_type': '5'})
                    vals.update({'state': 'reserved'})
                    vals.update({'t_id': self.t_id})
                    vals.update({'receipt_number': self.receipt_number})
                    voucher_order_line_id.sudo().write(vals)

                    _logger.info('Update Voucher Order Line Status to Reserved')
                    voucher_order_line_id.create_order_line_trans(self.name, 'RS')

    def process_voucher_order_line_used(self, vals):
        arr_ean = vals['voucher_ean'].split('|')
        for voucher_ean in arr_ean:
            domain = [
                ('voucher_ean', '=', voucher_ean),
                ('state', '=', 'reserved')
            ]
            voucher_order_line_id = self.env['weha.voucher.order.line'].sudo().search(domain, limit=1)
            _logger.info(voucher_order_line_id)
            if voucher_order_line_id:
                data = {
                    'voucher_trans_status_id': self.id,
                    'voucher_order_line_id': voucher_order_line_id.id,   
                }
                result = self.env['weha.voucher.trans.status.line'].sudo().create(data)
                if result:
                    vals = {}
                    vals.update({'voucher_trans_type': '5'})
                    vals.update({'state': 'reserved'})
                    vals.update({'t_id': self.t_id})
                    vals.update({'receipt_number': self.receipt_number})
                    vals.update({'used_operating_unit_id' : self.operating_unit_id.id})
                    voucher_order_line_id.sudo().write(vals)

                    _logger.info('Update Voucher Order Line Status to Used')
                    voucher_order_line_id.create_order_line_trans(self.name, 'RS')

    def process_voucher_order_line(self, vals):
        arr_ean = vals['voucher_ean'].split('|')
        _logger.info(arr_ean)
        for voucher_ean in arr_ean:
            if vals['process_type'] == 'reserved':
                domain = [
                    ('voucher_ean', '=', voucher_ean),
                    ('state', '=', 'activated')
                ]
            elif vals['process_type'] == 'used':
                domain = [
                    ('voucher_ean', '=', voucher_ean),
                    ('state', '=', 'reserved')
                ]
            elif vals['process_type'] == 'activated':
                domain = [
                    ('voucher_ean', '=', voucher_ean),
                    ('state', 'in', ['reserved','used'])
                ]
            elif vals['process_type'] == 'reopen':
                domain = [
                    ('voucher_ean', '=', voucher_ean),
                    ('state', 'in', ['reserved','activated','used'])
                ]
            else:
                raise ValidationError("Process Type not valid")
            
            voucher_order_line_id = self.env['weha.voucher.order.line'].sudo().search(domain, limit=1)
            _logger.info(voucher_order_line_id)
            if voucher_order_line_id:
                data = {
                    'voucher_trans_status_id': self.id,
                    'voucher_order_line_id': voucher_order_line_id.id,   
                }
                result = self.env['weha.voucher.trans.status.line'].sudo().create(data)
                if result:
                    _logger.info('Create Voucher Trans Status Line')
                    if vals['process_type'] == 'reserved':
                        _logger.info(vals['process_type'])
                        vals = {}
                        vals.update({'voucher_trans_type': '5'})
                        vals.update({'state': 'reserved'})

                        voucher_order_line_id.sudo().write(vals)
                        _logger.info('Update Voucher Order Line Status to Reserved')
                        voucher_order_line_id.create_order_line_trans(self.name, 'RS')
                    elif vals['process_type'] == 'activated':
                        _logger.info(vals['process_type'])
                        voucher_order_line_id.sudo().write({'state': 'activated', 'issued_on': datetime.now()})
                        voucher_order_line_id.voucher_trans_type = False
                        voucher_order_line_id.create_order_line_trans(self.name, 'AC')                   
                    elif vals['process_type'] == 'used':
                        _logger.info(vals['process_type'])
                        pass
                    elif vals['process_type'] == 'reopen':
                        _logger.info(vals['process_type'])
                        voucher_order_line_id.sudo().write({'state': 'open'})
                        voucher_order_line_id.create_order_line_trans(self.name, 'RO')
                        pass
                    else:
                        pass

    def process_voucher_order_line_by_batch(self, vals):
        arr_ean = vals['voucher_ean'].split('|')
        _logger.info(arr_ean)
        for voucher_ean in arr_ean:
            if vals['process_type'] == 'reserved':
                domain = [
                    ('voucher_ean', '=', voucher_ean),
                    ('state', '=', 'activated')
                ]
            elif vals['process_type'] == 'used':
                domain = [
                    ('voucher_ean', '=', voucher_ean),
                    ('state', '=', 'reserved')
                ]
            elif vals['process_type'] == 'activated':
                domain = [
                    ('voucher_ean', '=', voucher_ean),
                    ('state', 'in', ['reserved','used'])
                ]
            elif vals['process_type'] == 'reopen':
                domain = [
                    ('voucher_ean', '=', voucher_ean),
                    ('state', 'in', ['reserved','activated','used'])
                ]
            else:
                raise ValidationError("Process Type not valid")
            
            voucher_order_line_id = self.env['weha.voucher.order.line'].sudo().search(domain, limit=1)
            _logger.info(voucher_order_line_id)
            if voucher_order_line_id:
                data = {
                    'voucher_trans_status_id': self.id,
                    'voucher_order_line_id': voucher_order_line_id.id,   
                }
                result = self.env['weha.voucher.trans.status.line'].sudo().create(data)
                if result:
                    _logger.info('')

    def _auth_trust(self):
        _logger.info("_auth_trust")
        config_parameter_obj = self.env['ir.config_parameter'].sudo()
        crm_api_url = config_parameter_obj.get_param('crm_api_url')
        crm_api_username = config_parameter_obj.get_param('crm_api_username')
        crm_api_password = config_parameter_obj.get_param('crm_api_password')

        #url = "http://apiindev.trustranch.co.id/login"
        #payload='barcode=3000030930&password=weha.ID!!2020'

        payload=f'barcode={crm_api_username}&password={crm_api_password}'
        _logger.info(payload)
        
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        try:
            response = requests.request("POST", crm_api_url + "/login", headers=headers, data=payload)
            #json_data = json.loads(response.text)
            str_json_data  = response.text.replace("'"," ")
            json_data = json.loads(str_json_data)
            #_logger.info(response.text)
            _logger.info(json_data['data']['api_token'])
            return json_data['data']['api_token']
        except Exception as err:
            _logger.info("Error Auth Trust")
            _logger.info(err)  

    #API for Sales
    def send_data_to_trust(self):
        _logger.info("Send Data To Trust")
        config_parameter_obj = self.env['ir.config_parameter'].sudo()
        crm_api_url = config_parameter_obj.get_param('crm_api_url')
   
        trans_line_id = self.get_last_trans_line()
        _logger.info(trans_line_id.name)
        if self.voucher_trans_type in ('1','2','3'):
            trans_purchase_id = self.env['weha.voucher.trans.purchase'].search([('name','=',trans_line_id.name)], limit=1)

        api_token = self._auth_trust()
        if not api_token:
            self.is_send_to_crm = False
            self.send_to_crm_message = "Error Authentication"
            self.message_post(body="Send Notification to CRM Failed (Error Authentication)")
            return True, "Error CRM"

        headers = {'content-type': 'text/plain', 'charset':'utf-8'}
        #base_url = 'http://apiindev.trustranch.co.id'
        try:
            vouchers = []
            vouchers.append(self.voucher_ean + ';' + self.expired_date.strftime('%Y-%m-%d') + ";" + self.voucher_sku)
            data = {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'time': datetime.now().strftime('%H:%M:%S'),
                'receipt': trans_purchase_id.receipt_number,
                'transaction_id': trans_purchase_id.t_id,
                'cashier_id': trans_purchase_id.cashier_id,
                'store_id': trans_purchase_id.store_id,
                'member_id': self.member_id,
                'vouchers': '|'.join(vouchers)
            }
            _logger.info(data)
            headers = {'Authorization' : 'Bearer ' + api_token}
            req = requests.post('{}/vms/send-voucher'.format(crm_api_url), headers=headers ,data=data)
            if req.status_code == 200:
                #Success
                response_json = req.json()
                self.is_send_to_crm = True
                self.message_post(body="Send Notification to CRM Successfully")
                _logger.info("Send Notification to CRM Successfully")
                return False, "Success"                
            else:
                #Error
                _logger.info(f'Error : {req.status_code}')
                _logger.info("Send Notification to CRM Error")
                if req.json():
                    response_json = req.json()                
                    _logger.info(f'Error Message: {response_json["message"]}')
                    self.is_send_to_crm = False
                    self.send_to_crm_message = response_json["message"]
                    self.message_post(body=response_json["message"])
                else:
                    self.is_send_to_crm = False
                    self.send_to_crm_message = f'Error : {req.status_code}'

                return True, self.send_to_crm_message

        except requests.exceptions.Timeout:
            # Maybe set up for a retry, or continue in a retry loop
            self.is_send_to_crm = False
            self.send_to_crm_message = "Error "
            self.message_post(body="Send Notification to CRM Failed (Timeout)")
            return True, "Error CRM"
        except requests.exceptions.TooManyRedirects:
            # Tell the user their URL was bad and try a different one
            self.is_send_to_crm = False
            self.send_to_crm_message = "Error Too Many Redirects"
            self.message_post(body="Send Notification to CRM Failed (TooManyRedirects)")
            return True, "Error CRM"
        except requests.exceptions.RequestException as e:
            _logger.info(e)
            self.is_send_to_crm = False
            self.send_to_crm_message = "Error Request"
            self.message_post(body=e)
            self.message_post(body="Send Notification to CRM Failed (Exception)")
            return True, "Error CRM"

    def send_to_trust_by_batch_id(self):
        _logger.info("send_to_trust_by_batch_id")
       
        api_token = self._auth_trust()
        if not api_token:
            self.is_send_to_crm = False
            self.send_to_crm_message = "Error Authentication"
            return True, "Error CRM Authentication"

        config_parameter_obj = self.env['ir.config_parameter'].sudo()
        crm_api_url = config_parameter_obj.get_param('crm_api_url')
    
        headers = {'content-type': 'text/plain', 'charset':'utf-8'}
        base_url = 'http://apiindev.trustranch.co.id'
        try:
            vouchers = []
            for voucher_trans_status_line_id in self.voucher_trans_status_line_ids:
                voucher_order_line_id = voucher_trans_status_line_id.voucher_order_line_id
                vouchers.append(voucher_order_line_id.voucher_ean + ';' + voucher_order_line_id.expired_date.strftime('%Y-%m-%d') + ";" + voucher_order_line_id.voucher_sku)

            data = {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'time': datetime.now().strftime('%H:%M:%S'),
                'receipt': self.receipt_number,
                'transaction_id': self.t_id,
                'cashier_id': self.cashier_id,
                'store_id': self.store_id,
                'member_id': self.member_id,
                'vouchers': '|'.join(vouchers)
            }
            _logger.info(data)
            headers = {'Authorization' : 'Bearer ' + api_token}
            req = requests.post('{}/vms/send-voucher'.format(crm_api_url), headers=headers ,data=data)
            if req.status_code == 200:
                #Success
                response_json = req.json()
                self.is_send_to_crm = True
                #self.message_post(body="Send Notification to CRM Successfully")
                _logger.info("Send Notification to CRM Successfully")
                for voucher_trans_status_line_id in self.voucher_trans_status_line_ids:
                    voucher_order_line_id = voucher_trans_status_line_id.voucher_order_line_id
                    voucher_order_line_id.sudo().is_send_to_crm = True
                    voucher_order_line_id.sudo().write({'state': 'activated', 'issued_on': datetime.now()})
                    voucher_order_line_id.voucher_trans_type = False
                    voucher_order_line_id.create_order_line_trans(self.name, 'AC')
                return False, "Success"                
            else:
                #Error
                _logger.info(f'Error : {req.status_code}')
                _logger.info("Send Notification to CRM Error")
                if req.json():
                    response_json = req.json()                
                    _logger.info(f'Error Message: {response_json["message"]}')
                    self.is_send_to_crm = False
                    self.send_to_crm_message = response_json["message"]
                    #self.message_post(body=response_json["message"])
                else:
                    self.is_send_to_crm = False
                    self.send_to_crm_message = f'Error : {req.status_code}'

                return True, "Error CRM"

        except requests.exceptions.Timeout:
            # Maybe set up for a retry, or continue in a retry loop
            self.is_send_to_crm = False
            self.send_to_crm_message = "Error "
            #self.message_post(body="Send Notification to CRM Failed (Timeout)")
            return True, "Error CRM Timeout" 
        except requests.exceptions.TooManyRedirects:
            # Tell the user their URL was bad and try a different one
            self.is_send_to_crm = False
            self.send_to_crm_message = "Error Too Many Redirects"
            #self.message_post(body="Send Notification to CRM Failed (TooManyRedirects)")
            return True, "Error CRM  Too Many Redirects"
        except requests.exceptions.RequestException as e:
            _logger.info(e)
            self.is_send_to_crm = False
            self.send_to_crm_message = "Error Request"
            #self.message_post(body=e)
            #self.message_post(body="Send Notification to CRM Failed (Exception)")
            return True, "Error CRM Request"

    def send_to_trust(self):
        _logger.info("Send To Trust")
        config_parameter_obj = self.env['ir.config_parameter'].sudo()
        crm_api_url = config_parameter_obj.get_param('crm_api_url')
     
        api_token = self._auth_trust()
        if not api_token:
            self.is_send_to_crm = False
            self.send_to_crm_message = "Error Authentication"
            self.message_post(body="Send Notification to CRM Failed (Error Authentication)")
            return True, "Error CRM"

        headers = {'content-type': 'text/plain', 'charset':'utf-8'}
        base_url = 'http://apiindev.trustranch.co.id'
        try:
            vouchers = []
            for voucher_trans_status_line_id in self.voucher_trans_status_line_ids:
                voucher_order_line_id = voucher_trans_status_line_id.voucher_order_line_id
                vouchers.append(voucher_order_line_id.voucher_ean + ';' + voucher_order_line_id.expired_date.strftime('%Y-%m-%d') + ";" + voucher_order_line_id.voucher_sku)

            data = {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'time': datetime.now().strftime('%H:%M:%S'),
                'receipt': self.receipt_number,
                'transaction_id': self.t_id,
                'cashier_id': self.cashier_id,
                'store_id': self.store_id,
                'member_id': self.member_id,
                'vouchers': '|'.join(vouchers)
            }
            _logger.info(data)
            headers = {'Authorization' : 'Bearer ' + api_token}
            req = requests.post('{}/vms/send-voucher'.format(crm_api_url), headers=headers ,data=data)
            if req.status_code == 200:
                #Success
                response_json = req.json()
                self.is_send_to_crm = True
                #self.message_post(body="Send Notification to CRM Successfully")
                _logger.info("Send Notification to CRM Successfully")
                for voucher_trans_status_line_id in self.voucher_trans_status_line_ids:
                    voucher_order_line_id = voucher_trans_status_line_id.voucher_order_line_id
                    voucher_order_line_id.sudo().is_send_to_crm = True
                    voucher_order_line_id.sudo().write({'state': 'activated'})
                    voucher_order_line_id.voucher_trans_type = False
                    voucher_order_line_id.create_order_line_trans(self.name, 'AC')
                
                return False, "Success"                
            else:
                #Error
                _logger.info(f'Error : {req.status_code}')
                _logger.info("Send Notification to CRM Error")
                if req.json():
                    response_json = req.json()                
                    _logger.info(f'Error Message: {response_json["message"]}')
                    self.is_send_to_crm = False
                    self.send_to_crm_message = response_json["message"]
                    #self.message_post(body=response_json["message"])
                else:
                    self.is_send_to_crm = False
                    self.send_to_crm_message = f'Error : {req.status_code}'

                return True, "Error CRM"

        except requests.exceptions.Timeout:
            # Maybe set up for a retry, or continue in a retry loop
            self.is_send_to_crm = False
            self.send_to_crm_message = "Error "
            #self.message_post(body="Send Notification to CRM Failed (Timeout)")
            return True, "Error CRM"
        except requests.exceptions.TooManyRedirects:
            # Tell the user their URL was bad and try a different one
            self.is_send_to_crm = False
            self.send_to_crm_message = "Error Too Many Redirects"
            #self.message_post(body="Send Notification to CRM Failed (TooManyRedirects)")
            return True, "Error CRM"
        except requests.exceptions.RequestException as e:
            _logger.info(e)
            self.is_send_to_crm = False
            self.send_to_crm_message = "Error Request"
            #self.message_post(body=e)
            #self.message_post(body="Send Notification to CRM Failed (Exception)")
            return True, "Error CRM"

    def send_promo_to_trust(self):
        _logger.info("Send Promo To Trust")
        config_parameter_obj = self.env['ir.config_parameter'].sudo()
        crm_api_url = config_parameter_obj.get_param('crm_api_url')
     
        #trans_line_id = self.get_last_trans_line()
        #_logger.info(trans_line_id.name)
        #if self.voucher_trans_type in ('1','2','3'):
        #    trans_purchase_id = self.env['weha.voucher.trans.purchase'].search([('name','=',trans_line_id.name)], limit=1)

        api_token = self._auth_trust()
        if not api_token:
            self.is_send_to_crm = False
            self.send_to_crm_message = "Error Authentication"
            self.message_post(body="Send Notification to CRM Failed (Error Authentication)")
            return True, "Error CRM"

        headers = {'content-type': 'text/plain', 'charset':'utf-8'}
        base_url = 'http://apiindev.trustranch.co.id'
        try:
            vouchers = []
            for voucher_trans_status_line_id in self.voucher_trans_status_line_ids:
                voucher_order_line_id = voucher_trans_status_line_id.voucher_order_line_id
                vouchers.append(voucher_order_line_id.voucher_ean + ';' + voucher_order_line_id.expired_date.strftime('%Y-%m-%d') + ";" + voucher_order_line_id.voucher_sku)
            data = {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'time': datetime.now().strftime('%H:%M:%S'),
                'receipt': self.receipt_number,
                'transaction_id': self.t_id,
                'cashier_id': self.cashier_id,
                'store_id': self.store_id,
                'member_id': self.member_id,
                'vouchers': '|'.join(vouchers)
            }
            _logger.info(data)
            headers = {'Authorization' : 'Bearer ' + api_token}
            req = requests.post('{}/vms/send-voucher'.format(crm_api_url), headers=headers ,data=data)
            if req.status_code == 200:
                #Success
                response_json = req.json()
                self.is_send_to_crm = True
                #self.message_post(body="Send Notification to CRM Successfully")
                _logger.info("Send Notification to CRM Successfully")
                for voucher_trans_status_line_id in self.voucher_trans_status_line_ids:
                    voucher_trans_status_line_id.voucher_order_line_id.state = 'activated'
                return False, "Success"                
            else:
                #Error
                _logger.info(f'Error : {req.status_code}')
                _logger.info("Send Notification to CRM Error")
                if req.json():
                    response_json = req.json()                
                    _logger.info(f'Error Message: {response_json["message"]}')
                    self.is_send_to_crm = False
                    self.send_to_crm_message = response_json["message"]
                    #self.message_post(body=response_json["message"])
                else:
                    self.is_send_to_crm = False
                    #self.send_to_crm_message = f'Error : {req.status_code}'

                return True, self.send_to_crm_message

        except requests.exceptions.Timeout:
            # Maybe set up for a retry, or continue in a retry loop
            self.is_send_to_crm = False
            self.send_to_crm_message = "Error "
            #self.message_post(body="Send Notification to CRM Failed (Timeout)")
            return True, "Error CRM"
        except requests.exceptions.TooManyRedirects:
            # Tell the user their URL was bad and try a different one
            self.is_send_to_crm = False
            self.send_to_crm_message = "Error Too Many Redirects"
            #self.message_post(body="Send Notification to CRM Failed (TooManyRedirects)")
            return True, "Error CRM"
        except requests.exceptions.RequestException as e:
            _logger.info(e)
            self.is_send_to_crm = False
            self.send_to_crm_message = "Error Request"
            #self.message_post(body=e)
            #self.message_post(body="Send Notification to CRM Failed (Exception)")
            return True, "Error CRM"

    #API for Used
    def send_used_notification_to_trust_partial(self): 
        
        #Change Voucher Order Line status to Used
        for voucher_trans_status_line_id in self.voucher_trans_status_line_ids:
            voucher_order_line_id = voucher_trans_status_line_id.voucher_order_line_id
            #voucher_order_line_id.sudo().is_send_to_crm = True
            vals = {}
            vals.update({'state': 'used'})
            vals.update({'used_on': datetime.now()})
            vals.update({'receipt_number': self.receipt_number})
            vals.update({'t_id': self.t_id})
            vals.update({'used_operating_unit_id': self.operating_unit_id.id})
            _logger.info(vals)
            voucher_order_line_id.sudo().write(vals)

        #Check All Voucher Already Change to Used State
        domain = [
            ('receipt_number','=', self.receipt_number),
            ('t_id', '=', self.t_id)        
        ]
        voucher_order_line_reserved_ids = self.env['weha.voucher.order.line'].search(domain)
        _logger.info(len(voucher_order_line_reserved_ids))
        _logger.info(voucher_order_line_reserved_ids)
        domain = [
            ('receipt_number','=', self.receipt_number),
            ('t_id', '=', self.t_id),
            ('state', '=', 'used')
        ]
        voucher_order_line_used_ids = self.env['weha.voucher.order.line'].search(domain)
        _logger.info(len(voucher_order_line_reserved_ids))
        _logger.info(voucher_order_line_used_ids)

    
        used_status = True
        if len(voucher_order_line_reserved_ids) != len(voucher_order_line_used_ids):
            used_status = False
        
        # for voucher_order_line_id in voucher_order_line_ids:
        #     if voucher_order_line_id.state != 'used':
        #         used_status = False
        #         break
            
        if used_status:
            _logger.info("Count Match")
            vouchers = []
            physical_vouchers = []
            for voucher_order_line_id in voucher_order_line_used_ids:
                if voucher_order_line_id.voucher_type != 'physical':
                    vouchers.append(voucher_order_line_id.voucher_ean)
                else:
                    physical_vouchers.append(voucher_order_line_id.voucher_ean)
            
            _logger.info(vouchers)
            if len(vouchers) > 0:
                _logger.info("Send Used Notifcation")
                config_parameter_obj = self.env['ir.config_parameter'].sudo()
                crm_api_url = config_parameter_obj.get_param('crm_api_url')
           
                api_token = self._auth_trust()
                if not api_token:
                    self.is_send_to_crm = False
                    self.send_to_crm_message = "Error Authentication"
                    #self.message_post(body="Send Notification to CRM Failed (Error Authentication)")
                    return True, "Error CRM"

                data = {
                    'store_id': self.store_id,
                    'member_id': self.member_id,
                    'vouchers': '|'.join(vouchers)
                }
                _logger.info(data)
  

                base_url = 'http://apiindev.trustranch.co.id'
                headers = {'Authorization' : 'Bearer ' + api_token}
                req = requests.post('{}/vms/use-voucher'.format(crm_api_url), headers=headers ,data=data)
                if req.status_code == 200:
                    #Success
                    response_json = req.json()
                    self.is_send_to_crm = True
                    #self.message_post(body="Send Notification to CRM Successfully")
                    _logger.info("Send Notification to CRM Successfully")
                    for voucher_trans_status_line_id in self.voucher_trans_status_line_ids:
                        voucher_order_line_id = voucher_trans_status_line_id.voucher_order_line_id
                        voucher_order_line_id.sudo().is_send_to_crm = True
                        voucher_order_line_id.voucher_trans_type = False
                        voucher_order_line_id.create_order_line_trans(self.name, 'US')
                    #return False, "Success"
                    return False, "Success"                
                else:
                    #Error
                    _logger.info(f'Error : {req.status_code}')
                    if req.json():
                        response_json = req.json()                
                        _logger.info(f'Error Message: {response_json["message"]}')
                        self.is_send_to_crm = False
                        self.send_to_crm_message = response_json["message"]
                        #self.message_post(body=response_json["message"])
                    else:
                        self.is_send_to_crm = False
                        self.send_to_crm_message = f'Error : {req.status_code}'
                    return True, self.send_to_crm_message
            else:
                return False, "Success"                 
        else:
            return False, "Success" 
    
    def send_used_notification_to_trust(self):  
        _logger.info("Send Used Notifcation")
        config_parameter_obj = self.env['ir.config_parameter'].sudo()
        crm_api_url = config_parameter_obj.get_param('crm_api_url')
    
        api_token = self._auth_trust()
        if not api_token:
            self.is_send_to_crm = False
            self.send_to_crm_message = "Error Authentication"
            #self.message_post(body="Send Notification to CRM Failed (Error Authentication)")
            return True, "Error CRM"

        headers = {'content-type': 'text/plain', 'charset':'utf-8'}
        base_url = 'http://apiindev.trustranch.co.id'
        try:
            vouchers = []
            physical_vouchers = []
            for voucher_trans_status_line_id in self.voucher_trans_status_line_ids:
                voucher_order_line_id = voucher_trans_status_line_id.voucher_order_line_id
                if voucher_order_line_id.voucher_type != 'physical':
                    vouchers.append(voucher_order_line_id.voucher_ean)
                else:
                    physical_vouchers.append(voucher_order_line_id.voucher_ean)

            _logger.info(vouchers)
            if len(vouchers) > 0:
                data = {
                    'store_id': self.store_id,
                    'member_id': self.member_id,
                    'vouchers': '|'.join(vouchers)
                }
                _logger.info(data)
                headers = {'Authorization' : 'Bearer ' + api_token}
                req = requests.post('{}/vms/use-voucher'.format(crm_api_url), headers=headers ,data=data)
                if req.status_code == 200:
                    #Success
                    response_json = req.json()
                    self.is_send_to_crm = True
                    #self.message_post(body="Send Notification to CRM Successfully")
                    _logger.info("Send Notification to CRM Successfully")
                    for voucher_trans_status_line_id in self.voucher_trans_status_line_ids:
                        voucher_order_line_id = voucher_trans_status_line_id.voucher_order_line_id
                        voucher_order_line_id.sudo().is_send_to_crm = True
                        vals = {}
                        vals.update({'state': 'used'})
                        vals.update({'used_on': datetime.now()})
                        vals.update({'receipt_number': self.receipt_number})
                        vals.update({'t_id': self.t_id})
                        vals.update({'used_operating_unit_id': self.operating_unit_id.id})
                        _logger.info(vals)
                        voucher_order_line_id.sudo().write(vals)
                        voucher_order_line_id.voucher_trans_type = False
                        voucher_order_line_id.create_order_line_trans(self.name, 'US')
                    #return False, "Success"
                    return False, "Success"                
                else:
                    #Error
                    _logger.info(f'Error : {req.status_code}')
                    if req.json():
                        response_json = req.json()                
                        _logger.info(f'Error Message: {response_json["message"]}')
                        self.is_send_to_crm = False
                        self.send_to_crm_message = response_json["message"]
                        #self.message_post(body=response_json["message"])
                    else:
                        self.is_send_to_crm = False
                        self.send_to_crm_message = f'Error : {req.status_code}'

                    return True, self.send_to_crm_message
            else:
                for voucher_trans_status_line_id in self.voucher_trans_status_line_ids:
                    voucher_order_line_id = voucher_trans_status_line_id.voucher_order_line_id
                    voucher_order_line_id.sudo().is_send_to_crm = True
                    vals = {}
                    vals.update({'state': 'used'})
                    vals.update({'used_on': datetime.now()})
                    vals.update({'receipt_number': self.receipt_number})
                    vals.update({'t_id': self.t_id})
                    vals.update({'used_operating_unit_id': self.operating_unit_id.id})
                    _logger.info(vals)
                    voucher_order_line_id.sudo().write(vals)
                    voucher_order_line_id.voucher_trans_type = False
                    voucher_order_line_id.create_order_line_trans(self.name, 'US')
                return False, "Success" 
            
        except Exception as err:
            _logger.info(err)  
            self.is_send_to_crm = False
            self.send_to_crm_message = "Error Request"
            #self.message_post(body=err)
            #self.message_post(body="Send Notification to CRM Failed (Exception)")
            return True, "Error CRM"


    def _used_notifcation_to_trust(self, vouchers):
        _logger.info("Send Used Notifcation")
        config_parameter_obj = self.env['ir.config_parameter'].sudo()
        crm_api_url = config_parameter_obj.get_param('crm_api_url')
   
        api_token = self._auth_trust()
        if not api_token:
            self.is_send_to_crm = False
            self.send_to_crm_message = "Error Authentication"
            #self.message_post(body="Send Notification to CRM Failed (Error Authentication)")
            return True, "Error CRM"

        data = {
            'store_id': self.store_id,
            'member_id': self.member_id,
            'vouchers': '|'.join(vouchers)
        }
        _logger.info(data)


        base_url = 'http://apiindev.trustranch.co.id'
        headers = {'content-type': 'text/plain', 'charset':'utf-8', 'Authorization' : 'Bearer ' + api_token}
        req = requests.post('{}/vms/use-voucher'.format(crm_api_url), headers=headers ,data=data)
        if req.status_code == 200:
            #Success
            response_json = req.json()
            self.is_send_to_crm = True
            #self.message_post(body="Send Notification to CRM Successfully")
            _logger.info("Send Notification to CRM Successfully")
            for voucher_trans_status_line_id in self.voucher_trans_status_line_ids:
                voucher_order_line_id = voucher_trans_status_line_id.voucher_order_line_id
                voucher_order_line_id.sudo().is_send_to_crm = True
                #voucher_order_line_id.sudo().write(vals)
                voucher_order_line_id.voucher_trans_type = False
                voucher_order_line_id.create_order_line_trans(self.name, 'US')
            #return False, "Success"
            return False, "Success"                
        else:
            #Error
            _logger.info(f'Error : {req.status_code}')
            if req.json():
                response_json = req.json()                
                _logger.info(f'Error Message: {response_json["message"]}')
                self.is_send_to_crm = False
                self.send_to_crm_message = response_json["message"]
                #self.message_post(body=response_json["message"])
            else:
                self.is_send_to_crm = False
                self.send_to_crm_message = f'Error : {req.status_code}'

            return True, self.send_to_crm_message


    def procces_voucher_order_line_reopen(self, voucher_ean):
        pass                
    
    #API for Promo
    def get_json(self):
        data = {}
        if self.process_type == 'reserved':
            _logger.info('Get Json - reserved')
            voucher_trans_status_line_id = self.voucher_trans_status_line_ids and self.voucher_trans_status_line_ids[0] or False
            if voucher_trans_status_line_id:
                voucher_order_line_id = voucher_trans_status_line_id.voucher_order_line_id
                data.update({'err': False})
                data.update({'amount': voucher_order_line_id.voucher_code_id.voucher_amount})
                data.update({'tender_type': ''})
                data.update({'bank_category': ''})
                data.update({'min_card_payment': voucher_order_line_id.min_card_payment})
                data.update({'voucher_count_limit': voucher_order_line_id.voucher_count_limit})
                if voucher_order_line_id.voucher_promo_id:
                    data.update({'tender_type': voucher_order_line_id.tender_type})
                    data.update({'bank_category': voucher_order_line_id.bank_category})
                    data.update({'min_card_payment': voucher_order_line_id.min_card_payment})
                    data.update({'voucher_count_limit': voucher_order_line_id.voucher_count_limit})
            else:
                data.update({'err': True})
                data.update({'message': "Transaction not found"})

        if self.process_type == 'activated':
            _logger.info('Get Json - activated')
            self.send_promo_to_trust()
            data.update({'err': False})
            data.update({'message': "Transaction Create Successfully"})
        
        return data

    def get_json_batch(self):
        data = {}
        data.update({'err': False})
        data.update({'message': ""})
        return data
                
    name = fields.Char('Name', )
    batch_id = fields.Char('Batch #', size=10, readonly=True)
    trans_date = fields.Datetime("Transaction Date")
    receipt_number = fields.Char("Receipt #", size=50)
    t_id = fields.Char("Transaction #")
    cashier_id = fields.Char("Cashier #", size=5)
    store_id = fields.Char("Store #", size=4)
    operating_unit_id = fields.Many2one("operating.unit", "Operating Unit")
    member_id = fields.Char("Member #", size=10)
    voucher_ean = fields.Char("Voucher Ean", size=250)
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
            ('reopen', 'Re-Open')
            
        ],
        'Process Type',
        index=True
    )
    void = fields.Boolean('Void', default=False)

    @api.model 
    def create(self, vals):
       
        #Create Trans #
        seq = self.env['ir.sequence']
        if 'company_id' in vals:
            seq = seq.with_context(force_company=vals['company_id'])
        vals['name'] = seq.next_by_code('weha.voucher.trans.status.sequence') or '/'

        operating_unit_id = self.env['operating.unit'].search([('code','=', vals['store_id'])], limit=1)
        _logger.info(operating_unit_id)
        if operating_unit_id:
            vals['operating_unit_id'] = operating_unit_id.id
        
        res = super(VoucherTransStatus, self).create(vals)
       
        if vals['process_type'] in ('reserved', 'activated', 'used'):
            if vals['batch_id']:
                _logger.info("Process by Batch")
                res.process_voucher_order_line_by_batch(vals) 
            else:   
                _logger.info("Process without Batch")
                if vals['process_type'] == 'activated':
                    res.process_voucher_order_line(vals)
                if vals['process_type'] == 'used':
                    res.process_voucher_order_line_used(vals)
                if vals['process_type'] == 'reserved':
                    res.process_voucher_order_line_reserved(vals)
        else:
            res.process_voucher_order_line(vals) 
        
        # #Close Voucher Transaction Purchase
        # res.trans_close()
        return res
  
class VoucheTransStatusLine(models.Model):
    _name = "weha.voucher.trans.status.line"
    _description = 'Voucher Transaction Status Line (API)'

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

class VoucherTransFTP(models.Model):
    _name = "weha.voucher.trans.ftp"
    _description = 'Voucher Transaction FTP (API)'
     
    @api.model 
    def process_ftp(self):
        _logger.info("Process FTP")
        self.ftp_url = self.env.ref(ftp_url).sudo().value
        _logger.info(self.ftp_url)
        self.ftp_username = self.env.ref(ftp_username).sudo().value
        _logger.info(self.ftp_username)
        self._password = self.env.ref(ftp_password).sudo().value
        _logger.info(self.ftp_password)
        #Connect To FTP Server
        ftp = FTP()
        ftp.connect(self.ftp_url, 21)
        ftp.login(self.ftp_username, self.ftp_password)
        ftp.set_pasv(False)
        #ftp.cwd('fail')
        _logger.info(ftp.pwd())
        files = []
        #ftp.dir(files.append)  # Takes a callback for each file
        for file_name in ftp.nlst():
            _logger.info(file_name)
            try:
                ftp.cwd(file_name)
            except Exception:
                #do the code for folder not exists
                file_csv = io.BytesIO()
                with open("/tmp/" + file_name, 'wb') as local_file:  # Open local file for writing
                    response = ftp.retrbinary('RETR ' + file_name, file_csv.write)
                    if response.startswith('226'):  # Transfer complete
                        print('Transfer complete - ' + file_name)
                        ftp.rename(file_name, "old/" + file_name)
                        #Create Ir Attachment
                        data = file_csv.getvalue()
                        vals = {
                            'file_csv': base64.encodebytes(data),
                            'file_csv_filename': file_name,
                        }
                        _logger.info(vals)
                        #Create Trans Ftp
                        res = self.env['weha.voucher.trans.ftp'].create(vals)
                        keys = ['date', 'time','receipt_number','t_id','cashier_id','store_id','api_name', 'sku', 'voucher_ean', 'qty', 'amount', 'voucher_type', 'member_id', 'status']                    
                        data = base64.decodebytes(res.file_csv)
                        file_input = io.StringIO(data.decode("utf-8"))
                        file_input.seek(0)
                        reader_info = []
                        reader = csv.reader(file_input, delimiter=',')
                        try:
                            reader_info.extend(reader)
                        except Exception:
                            raise exceptions.Warning(_("Not a valid file!"))
                        values = {}
                        for i in range(len(reader_info)):
                            field = list(map(str, reader_info[i]))
                            values = dict(zip(keys, field))
                            if values:
                                if i == 0:
                                    continue
                                else:
                                    _logger.info(values)
                                    if values['api_name'] == 'API#1':
                                        _logger.info('API#1')
                                        if values['voucher_type'] == '1':
                                            vals = {}
                                            # #Save Voucher Purchase Transaction
                                            voucher_trans_purchase_obj = self.env['weha.voucher.trans.purchase']
                                            trans_date = values['date']  +  " "  + values['time'] + ":00"
                                            vals.update({'trans_date': trans_date})
                                            vals.update({'receipt_number': values['receipt_number']})
                                            vals.update({'t_id': values['t_id']})
                                            vals.update({'cashier_id': values['cashier_id']})
                                            vals.update({'store_id': values['store_id']})
                                            vals.update({'member_id': values['member_id']})
                                            vals.update({'sku': values['sku'] + "|" + values['qty']})
                                            vals.update({'voucher_type': values['voucher_type']})        
                                            #Save Data
                                            trans_purchase_id = voucher_trans_purchase_obj.sudo().create(vals)
                                            if not trans_purchase_id:
                                                _logger.info("error")  
                                            else:
                                                res.write({'trans_purchase_id': trans_purchase_id.id, "voucher_type": values['voucher_type']})
                                                #Save Voucher Status Transaction
                                                vals = {}
                                                voucher_trans_status_obj = self.env['weha.voucher.trans.status']
                                                trans_date = values['date']  +  " "  + values['time'] + ":00"
                                                vals.update({'trans_date': trans_date})
                                                vals.update({'receipt_number': values['receipt_number']})
                                                vals.update({'t_id': values['t_id']})
                                                vals.update({'cashier_id': values['cashier_id']})
                                                vals.update({'store_id': values['store_id']})
                                                vals.update({'member_id': values['member_id']})
                                                voucher_eans = ""
                                                for voucher_trans_purchase_line_id in trans_purchase_id.voucher_trans_purchase_line_ids:
                                                    voucher_eans = voucher_eans + "|" + voucher_trans_purchase_line_id.voucher_order_line_id.voucher_ean
                                                vals.update({'voucher_ean': voucher_eans})
                                                vals.update({'process_type': "activated"})
                                                trans_status_id = voucher_trans_status_obj.sudo().create(vals)

                                    if values['api_name'] == 'API#4':
                                        _logger.info('API#4')
                                        #Save Voucher Status Transaction
                                        vals = {}
                                        voucher_trans_status_obj = self.env['weha.voucher.trans.status']
                                        trans_date = values['date']  +  " "  + values['time'] + ":00"
                                        vals.update({'trans_date': trans_date})
                                        vals.update({'receipt_number': values['receipt_number']})
                                        vals.update({'t_id': values['t_id']})
                                        vals.update({'cashier_id': values['cashier_id']})
                                        vals.update({'store_id': values['store_id']})
                                        vals.update({'member_id': values['member_id']})
                                        vals.update({'voucher_ean': values['voucher_ean']})
                                        vals.update({'process_type': "activated"})
                                        trans_status_id = voucher_trans_status_obj.sudo().create(vals)                                        
                    else:
                        print('Error transferring. Local file may be incomplete or corrupt.')
        #Close FTP Connection
        ftp.close()        

    name = fields.Char('Name', )
    trans_date = fields.Datetime("Transaction Date",  default=datetime.now())    
    file_csv = fields.Binary('File')
    file_csv_filename = fields.Char("Filename")
    attachment_id = fields.Many2one('ir.attachment','CSV File')
    trans_purchase_id = fields.Many2one("weha.voucher.trans.purchase", "Purchase #")
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

    @api.model 
    def create(self, vals):
        #Create Trans #
        seq = self.env['ir.sequence']
        if 'company_id' in vals:
            seq = seq.with_context(force_company=vals['company_id'])
        vals['name'] = seq.next_by_code('weha.voucher.trans.ftp.sequence') or '/'
        res = super(VoucherTransFTP, self).create(vals)
        return res

class VoucherTransBooking(models.Model):
    _name = "weha.voucher.trans.booking" 
    _description = 'Voucher Transaction Booking (API)'

    def complete_sku(self):
        mapping_sku = []
        if ';' in self.sku:
            arr_skus = self.sku.split(';')
            _logger.info(arr_skus)
            for str_sku in arr_skus: 
                vals = {}
                arr_sku  = str_sku.split('|')
                vals['voucher_trans_booking_id'] = self.id
                vals['sku'] = arr_sku[0]
                vals['quantity'] = arr_sku[1]
                #vals['amount'] = arr_sku[2]
                _logger.info(arr_sku)
                domain = [
                    ('code_sku', '=', arr_sku[0]),
                ]
                mapping_sku_id = self.env['weha.voucher.mapping.sku'].search(domain, limit=1)
                if mapping_sku_id:
                    _logger.info("Mapping SKU Exist")
                    vals['voucher_code_id']  = mapping_sku_id.voucher_code_id.id
                    vals['voucher_terms_id']  = mapping_sku_id.voucher_code_id.voucher_terms_id.id
                    current_year = self.env['weha.voucher.year'].get_current_year()
                    vals['year_id'] =  current_year.id
                    vals['voucher_mapping_sku_id'] = mapping_sku_id.id
                    vals['amount'] = int(vals['quantity']) * mapping_sku_id.voucher_code_id.voucher_amount
                    self.env['weha.voucher.trans.booking.sku'].create(vals)

        else:
            vals = {}
            arr_sku  = self.sku.split('|')
            vals['voucher_trans_booking_id'] = self.id
            vals['sku'] = arr_sku[0]
            vals['quantity'] = arr_sku[1]
            #vals['amount'] = arr_sku[2]
            _logger.info(arr_sku)
            domain = [
                ('code_sku', '=', arr_sku[0]),
            ]

            mapping_sku_id = self.env['weha.voucher.mapping.sku'].search(domain, limit=1)
            if mapping_sku_id:
                _logger.info("Mapping SKU Exist")
                voucher_mapping_pos_id = mapping_sku_id.voucher_mapping_pos_id
                _logger.info(mapping_sku_id.voucher_code_id)
                vals['voucher_code_id']  = mapping_sku_id.voucher_code_id.id
                vals['voucher_terms_id']  = mapping_sku_id.voucher_code_id.voucher_terms_id.id
                current_year = self.env['weha.voucher.year'].get_current_year()
                vals['year_id'] = current_year.id
                vals['voucher_mapping_sku_id'] = mapping_sku_id.id
                vals['amount'] = int(vals['quantity']) * mapping_sku_id.voucher_code_id.voucher_amount
                self.env['weha.voucher.trans.booking.sku'].create(vals)

    def issuing_voucher(self):
        seq = self.env['ir.sequence']
        for voucher_trans_booking_sku_id in self.voucher_trans_booking_sku_ids:
            store_id  = voucher_trans_booking_sku_id.voucher_trans_booking_id.store_id
            operating_unit_id = self.env['operating.unit'].search([('code','=', store_id)], limit=1)

            for i in range(1,voucher_trans_booking_sku_id.quantity + 1):

                domain = [
                    ('operating_unit_id','=',operating_unit_id.id),
                    ('voucher_type','=', 'physical'),
                    ('voucher_code_id', '=', voucher_trans_booking_sku_id.voucher_code_id.id),
                    #('voucher_terms_id', '=',  voucher_trans_booking_sku_id.voucher_code_id.voucher_terms_id.id),
                    ('year_id', '=', voucher_trans_booking_sku_id.year_id.id),
                    ('state','=', 'open')
                ]
                _logger.info(domain)
                voucher_order_line_id = self.env['weha.voucher.order.line'].search(domain, limit=1)
                _logger.info(voucher_order_line_id)
                vals = {
                    'voucher_trans_booking_id': self.id,
                    'voucher_trans_booking_sku_id': voucher_trans_booking_sku_id.id,
                    'voucher_order_line_id': voucher_order_line_id.id
                }
                result = self.env['weha.voucher.trans.booking.line'].create(vals)
                if result:
                    voucher_order_line_id.write(
                        {
                            'member_id': self.member_id,
                            'booking_expired_date': datetime.now() + timedelta(days=1),
                            'state': 'booking'
                        }
                    )
                    voucher_order_line_id.create_order_line_trans(self.name, 'BO')

    def get_json(self):
        vouchers = []
        #for voucher_trans_purchase_line_id in result.voucher_trans_purchase_line_ids:
        #    vouchers.append(voucher_trans_purchase_line_id.voucher_order_line_id.voucher_ean)
        for voucher_trans_booking_sku_id in self.voucher_trans_booking_sku_ids:
            lines = []
            for  voucher_trans_booking_line_id in voucher_trans_booking_sku_id.voucher_trans_booking_line_ids:
                #_logger.info(voucher_trans_booking_line_id.voucher_order_line_id.voucher_ean)
                #_logger.info(voucher_trans_booking_line_id.voucher_order_line_id.expired_date.strftime("%Y-%m-%d"))
                #voucher_ean = voucher_trans_booking_line_id.voucher_order_line_id.voucher_ean
                #lines.append(voucher_trans_booking_line_id.voucher_order_line_id.voucher_ean + "|" + voucher_trans_booking_line_id.voucher_order_line_id.expired_date.strftime("%Y-%m-%d"))
                _logger.info(voucher_trans_booking_line_id.voucher_order_line_id)
                lines.append(voucher_trans_booking_line_id.voucher_order_line_id.voucher_ean)
            vouchers.append({'sku': voucher_trans_booking_sku_id.sku, 'vouchers' : lines})
        return vouchers

    def trans_close(self):
        super(VoucherTransBooking, self).write({'state': 'done'})

    name = fields.Char('Name', )
    trans_type = fields.Char('Trans Type', size=10)
    trans_date = fields.Datetime("Transaction Date")
    receipt_number = fields.Char("Receipt #", size=10)
    t_id = fields.Char("Terminal #")
    cashier_id = fields.Char("Cashier #", size=10)
    store_id = fields.Char("Store #", size=10)
    member_id = fields.Char("Member #", size=20)
    sku = fields.Char("SKU", size=255)

    voucher_trans_booking_line_ids = fields.One2many('weha.voucher.trans.booking.line','voucher_trans_booking_id','Lines')
    voucher_trans_booking_sku_ids = fields.One2many('weha.voucher.trans.booking.sku','voucher_trans_booking_id','Skus')

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
        vals['name'] = seq.next_by_code('weha.voucher.trans.booking.sequence') or '/'
        
        #Create Trans
        res = super(VoucherTransBooking, self).create(vals)

        #Complete SKU List
        res.complete_sku()
            
        #Issuing Voucher
        res.issuing_voucher()

        #Update CRM
        #res.send_data_to_trust()
        
        res.trans_close()

        return res    

class VoucheTransBookingSku(models.Model):
    _name = "weha.voucher.trans.booking.sku"
    _description = 'Voucher Transaction Booking SKU (API)'

    voucher_trans_booking_id = fields.Many2one('weha.voucher.trans.booking', 'Booking #')
    voucher_mapping_sku_id = fields.Many2one('weha.voucher.mapping.sku', 'Mapping SKU #')
    sku = fields.Char("SKU", size=8)
    quantity = fields.Integer('Qty')
    amount = fields.Float('Amount', default="0.0")
    voucher_number_range_id = fields.Many2one('weha.voucher.number.ranges','Number Range')
    voucher_code_id = fields.Many2one("weha.voucher.code", "Voucher Code")
    voucher_terms_id = fields.Many2one("weha.voucher.terms", "Voucher Terms")
    year_id = fields.Many2one("weha.voucher.year", "Year")
    voucher_promo_id = fields.Many2one("weha.voucher.promo", "Voucher Promo")
    voucher_trans_booking_line_ids = fields.One2many('weha.voucher.trans.booking.line','voucher_trans_booking_sku_id','Lines')
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

class VoucherTransBookingLine(models.Model):
    _name = "weha.voucher.trans.booking.line"
    _description = 'Voucher Transaction Booking Line (API)'

    voucher_trans_booking_id = fields.Many2one('weha.voucher.trans.booking', 'Purchase #')
    voucher_trans_booking_sku_id = fields.Many2one('weha.voucher.trans.booking.sku', 'Purchase SKU #')
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

class VoucherChangeMember(models.Model):
    _name = "weha.voucher.change.member"

    def process_voucher_order_line_reserved(self, vals):
        arr_ean = vals['voucher_ean'].split('|')
        for voucher_ean in arr_ean:
            domain = [
                ('voucher_ean', '=', voucher_ean),
                ('member_id', '=', self.old_member_id)
            ]
            voucher_order_line_id = self.env['weha.voucher.order.line'].sudo().search(domain, limit=1)
            if voucher_order_line_id:
                line_id = self.env['weha.voucher.change.member.line'].create(
                    {
                        'voucher_change_member_id': self.id,
                        'voucher_order_line_id': voucher_order_line_id.id,
                    }
                )

    def complete_change_member_line(self):
        for voucher_change_member_line_id in self.voucher_change_member_line_ids:
            voucher_change_member_line_id.voucher_order_line_id.member_id = self.new_member_id
            voucher_change_member_line_id.state = 'done'



    name = fields.Char('Name', )
    trans_date = fields.Datetime("Transaction Date", default=datetime.now())
    trx_no = fields.Char('Trx No', size=50)
    old_member_id = fields.Char("Old Member #", size=20)
    new_member_id = fields.Char("New Member #", size=20)
    voucher_ean = fields.Char("Voucher Ean", size=250)

    voucher_change_member_line_ids = fields.One2many('weha.voucher.change.member.line','voucher_change_member_id','Lines')

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

    @api.model
    def create(self, vals):
        #Create Trans #
        seq = self.env['ir.sequence']
        if 'company_id' in vals:
            seq = seq.with_context(force_company=vals['company_id'])
        vals['name'] = seq.next_by_code('weha.voucher.change.member.sequence') or '/'
        
        #Create Trans
        res = super(VoucherChangeMember, self).create(vals)

        res.process_voucher_order_line_reserved(vals)
        res.complete_change_member_line()
        res.state = 'done'

        return res    

class VoucherChangeMemberLine(models.Model):
    _name = "weha.voucher.change.member.line"

    voucher_change_member_id = fields.Many2one('weha.voucher.change.member', 'Change Member #')
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