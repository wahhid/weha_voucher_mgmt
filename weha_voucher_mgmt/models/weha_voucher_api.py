from odoo import models, fields, api,  _ 
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
import requests
from requests import ReadTimeout, ConnectTimeout, HTTPError, Timeout, ConnectionError
from ftplib import FTP
import os
import base64
from datetime import datetime
import csv
import logging
import io
import json

_logger = logging.getLogger(__name__)

ftp_url = "weha_voucher_mgmt.ftp_url"
ftp_username = "weha_voucher_mgmt.ftp_username"
ftp_password = "weha_voucher_mgmt.ftp_password"

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
                    voucher_promo_line_id = self.env['weha.voucher.promo.line'].search([('voucher_mapping_sku_id','=',mapping_sku_id.id)], limit=1)
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
                        _logger.info('Voucher number range id not found')
                else:
                    _logger.info('Mapping SKU not found')                    
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
                voucher_promo_line_id = self.env['weha.voucher.promo.line'].search([('voucher_mapping_sku_id','=',mapping_sku_id.id)], limit=1)
                #voucher_mapping_pos_id = mapping_sku_id.voucher_mapping_pos_id
                #if voucher_mapping_pos_id.pos_trx_type == 'Promo':
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

    def _auth_trust(self):
        url = "http://apiindev.trustranch.co.id/login"

        payload='barcode=3000030930&password=weha.ID!!2020'
        headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded',
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        #json_data = json.loads(response.text)
        str_json_data  = response.text.replace("'"," ")
        json_data = json.loads(str_json_data)
        #_logger.info(response.text)
        _logger.info(json_data['data']['api_token'])
        return json_data['data']['api_token']

    def send_data_to_trust(self):
        api_token = self._auth_trust()
        headers = {'content-type': 'text/plain', 'charset':'utf-8'}
        base_url = 'http://apiindev.trustranch.co.id'
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
            req = requests.post('{}/vms/get-voucher'.format(base_url), headers=headers ,data=data)
            _logger.info(req.text)
            
            #content = json.loads(req.content.decode('utf-8'))
            #headers.update(access-token=content.get('access_token'))
        except Exception as err:
            _logger.info(err)  
        finally:
            _logger.info("final")  

    def reserved_voucher(self):
        seq = self.env['ir.sequence']
        for voucher_trans_purchase_sku_id in self.voucher_trans_purchase_sku_ids:
            for i in range(1,voucher_trans_purchase_sku_id.quantity + 1):
                vals = {}
                vals.update({'member_id': self.member_id})
                vals.update({'operating_unit_id': 3})
                vals.update({'voucher_type': 'electronic'})
                vals.update({'voucher_sku': voucher_trans_purchase_sku_id.sku})
                vals.update({'voucher_trans_type': self.voucher_type})
                vals.update({'voucher_code_id': voucher_trans_purchase_sku_id.voucher_code_id.id})
                vals.update({'voucher_terms_id': voucher_trans_purchase_sku_id.voucher_code_id.voucher_terms_id.id})
                vals.update({'tender_type': self.tender_type})
                vals.update({'bank_category': self.bank_category})
                if voucher_trans_purchase_sku_id.voucher_promo_id:
                    vals.update({'voucher_promo_id': voucher_trans_purchase_sku_id.voucher_promo_id.id})
                    vals.update({'min_card_payment': voucher_trans_purchase_sku_id.voucher_promo_id.min_card_payment})
                    vals.update({'voucher_count_limit': voucher_trans_purchase_sku_id.voucher_promo_id.voucher_count_limit})

                #Get Current Year
                current_year = self.env['weha.voucher.year'].get_current_year()
                vals.update({'year_id': current_year.id})
                check_number = voucher_trans_purchase_sku_id.voucher_number_range_id.sequence_id.next_by_id()
                vals.update({'check_number': check_number})
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
                lines.append(voucher_trans_purchase_line_id.voucher_order_line_id.voucher_ean + "|" + voucher_trans_purchase_line_id.voucher_order_line_id.expired_date.strftime("%Y-%m-%d"))
                #lines.append(voucher_trans_purchase_line_id.voucher_order_line_id.voucher_ean)
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
    ref = fields.Char(string='Source Document', required=True)

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
        
        #Create Trans
        res = super(VoucherTransPurchase, self).create(vals)

        #Complete SKU List
        res.complete_sku()

        #Reserved Voucher
        if res.voucher_type == '4':
            for voucher_trans_purchase_line_id in self.voucher_trans_purchase_line_ids:
                voucher_trans_purchase_line_id.voucher_order_line_id.sudo().write({'state': 'activated'})
                voucher_trans_purchase_line_id.voucher_order_line_id.send_data_to_trust()
                voucher_trans_purchase_line_id.voucher_order_line_id.voucher_trans_type = False
        else:
            res.reserved_voucher()  

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

    def send_data_to_trust(self):
        api_token = self._auth_trust()
        headers = {'content-type': 'text/plain', 'charset':'utf-8'}
        base_url = 'http://apiindev.trustranch.co.id'
        try:
            vouchers = []
            for voucher_trans_purchase_line_id in self.voucher_trans_purchase_line_ids:
                vouchers.append(voucher_trans_purchase_line_id.voucher_order_line_id.voucher_ean + ';' + voucher_trans_purchase_line_id.voucher_order_line_id.expired_date.strftime('%Y-%m-%d')) 
            
            data = {
                'date': self.trans_date.strftime('%Y-%m-%d'),
                'time': self.trans_date.strftime('%H:%M:%S'),
                'receipt': self.receipt_number,
                'transactionId': self.t_id,
                'cashierId': self.cashier_id,
                'storeId': self.store_id,
                'memberId': self.member_id,
                'vouchers': '|'.join(vouchers)
            }
            _logger.info(data)
            headers = {'Authorization' : 'Bearer ' + api_token}
            req = requests.post('{}/vms/get-voucher'.format(base_url), headers=headers ,data=data)
            _logger.info(req.text)
            
            #content = json.loads(req.content.decode('utf-8'))
            #headers.update(access-token=content.get('access_token'))
        except Exception as err:
            _logger.info(err)  
        finally:
            _logger.info("final")  

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
                    if vals['process_type'] == 'reserved':
                        _logger.info(vals['process_type'])
                        voucher_order_line_id.sudo().write({'voucher_trans_type': '5','state': 'reserved'})
                        voucher_order_line_id.create_order_line_trans(self.name, 'RS')
                    elif vals['process_type'] == 'activated':
                        _logger.info(vals['process_type'])
                        voucher_order_line_id.sudo().write({'state': 'activated'})
                        if voucher_order_line_id.voucher_trans_type == '1':
                            voucher_order_line_id.send_data_to_trust()
                            voucher_order_line_id.voucher_trans_type = False
                        if voucher_order_line_id.voucher_trans_type == '2':
                            voucher_order_line_id.send_data_to_trust()
                            voucher_order_line_id.voucher_trans_type = False
                        if voucher_order_line_id.voucher_trans_type == '3':
                            voucher_order_line_id.send_data_to_trust()
                            voucher_order_line_id.voucher_trans_type = False
                        if voucher_order_line_id.voucher_trans_type == '4':
                            voucher_order_line_id.send_data_to_trust()
                            voucher_order_line_id.voucher_trans_type = False
                        if voucher_order_line_id.voucher_trans_type == '5':
                            pass
                        voucher_order_line_id.create_order_line_trans(self.name, 'AC')
                    elif vals['process_type'] == 'used':
                        _logger.info(vals['process_type'])
                        voucher_order_line_id.sudo().write({'state': 'used'})
                        voucher_order_line_id.send_used_notification_to_trust()
                        voucher_order_line_id.voucher_trans_type = False
                        voucher_order_line_id.create_order_line_trans(self.name, 'US')
                    elif vals['process_type'] == 'reopen':
                        _logger.info(vals['process_type'])
                        voucher_order_line_id.sudo().write({'state': 'open'})
                        voucher_order_line_id.create_order_line_trans(self.name, 'RO')
                        pass
                    else:
                        pass

    def procces_voucher_order_line_reopen(self, voucher_ean):
        pass                
    
    def get_json(self):
        data = {}
        if self.process_type == 'reserved':
            voucher_trans_status_line_id = self.voucher_trans_status_line_ids and self.voucher_trans_status_line_ids[0] or False
            if voucher_trans_status_line_id:
                voucher_order_line_id = voucher_trans_status_line_id.voucher_order_line_id
                data.update({'amount': voucher_order_line_id.voucher_code_id.voucher_amount})
                data.update({'tender_type': ''})
                data.update({'bank_category': ''})
                data.update({'min_card_payment': voucher_order_line_id.min_card_payment})
                data.update({'voucher_count_limit': voucher_order_line_id.voucher_count_limit})
                voucher_mapping_sku_id  = self.env['weha.voucher.mapping.sku'].search([('voucher_code_id','=', voucher_order_line_id.voucher_code_id.id)],limit=1)
                if voucher_mapping_sku_id:    
                    voucher_mapping_pos_id = voucher_mapping_sku_id.voucher_mapping_pos_id
                    if voucher_mapping_pos_id.pos_trx_type == 'Promo':
                        data.update({'tender_type': voucher_order_line_id.tender_type})
                        data.update({'bank_category': voucher_order_line_id.bank_category})
                        data.update({'min_card_payment': voucher_order_line_id.min_card_payment})
                        data.update({'voucher_count_limit': voucher_order_line_id.voucher_count_limit})
        return data
                
    name = fields.Char('Name', )
    trans_date = fields.Datetime("Transaction Date")
    receipt_number = fields.Char("Receipt #", size=5)
    t_id = fields.Char("Transaction #")
    cashier_id = fields.Char("Cashier #", size=5)
    store_id = fields.Char("Store #", size=4)
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

        res = super(VoucherTransStatus, self).create(vals)

        # arr_voucher_ean = vals['voucher_ean'].split("|")
        # voucher_ean_ids = []
        # for voucher_ean in arr_voucher_ean:

       
        if vals['process_type'] in ('reserved', 'activated', 'used'):
            res.process_voucher_order_line(vals) 
        else:
            #Process Voucher Order Line Reopen
            res.process_voucher_order_line(vals) 
        #Close Voucher Transaction Purchase
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

class VoucherTransFTP(models.Model):
    _name = "weha.voucher.trans.ftp"
     
    @api.model 
    def process_ftp(self):
        _logger.info("Process FTP")
        self.ftp_url = self.env.ref(ftp_url).sudo().value
        self.ftp_username = self.env.ref(ftp_username).sudo().value
        self.ftp_password = self.env.ref(ftp_password).sudo().value
        #Connect To FTP Server
        ftp = FTP()
        ftp.connect(self.ftp_url, 21)
        ftp.login(self.ftp_username, self.ftp_password)
        ftp.cwd('fail')
        _logger.info(ftp.pwd())
        files = []
        ftp.dir(files.append)  # Takes a callback for each file
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
                        print('Transfer complete')
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
                        #attachment_id = self.env['ir.attachment'].sudo().create({
                        #            'name': file_name,
                        #            'datas': base64.b64encode(data),
                        #            'store_fname': file_name,
                        #            'type': 'binary',
                        #            'res_model': 'weha.voucher.trans.ftp',
                        #            'res_id': res.id
                        #})
                        #res.write({'attachment_id': attachment_id.id})
                        keys = ['date', 'time','receipt_number','t_id','cashier_id','store_id', 'sku', 'qty', 'amount', 'voucher_type', 'member_id', 'status']                    
                        data = base64.decodebytes(res.file_csv)
                        file_input = io.StringIO(data.decode("utf-8"))
                        file_input.seek(0)
                        reader_info = []
                        reader = csv.reader(file_input, delimiter=';')
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
                                        res.write({'trans_purchase_id': trans_purchase_id.id, "voucher_type": values['voucher_type']})
                                    #res = self.env['weha.voucher.issuing.employee.line'].create(values)
                    else:
                        print('Error transferring. Local file may be incomplete or corrupt.')
            #f = open("demofile.txt", "r")
            
            #data = f.read()
            # request.env['ir.attachment'].sudo().create({
            #             'name': f.filename,
            #             'datas': base64.b64encode(data),
            #             'datas_fname': f.filename,
            #             'res_model': 'weha.voucher.trans.ftp',
            #             'res_id': res.id
            # })
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