from odoo import models, fields, api,  _ 
from odoo.exceptions import UserError, ValidationError
import requests
from requests import ReadTimeout, ConnectTimeout, HTTPError, Timeout, ConnectionError
from ftplib import FTP
import os
import base64
import csv
import logging
import io
import json
import logging
from random import randrange
from datetime import datetime, timedelta, date
import pytz
from functools import reduce

_logger = logging.getLogger(__name__)

import math
import re


class VoucherOrderLine(models.Model):
    _name = 'weha.voucher.order.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    def calc_check_digit(self, number):
        """Calculate the EAN check digit for 13-digit numbers. The number passed
        should not have the check bit included."""
        return str((10 - sum((3, 1)[i % 2] * int(n)
                            for i, n in enumerate(reversed(number)))) % 10)

    def generate_12_numbers(self, voucher_type, voucher_code_id, year_id, check_number):

        c_code = str(self.env.user.default_operating_unit_id.company_id.res_company_code)

        voucher_code = self.env['weha.voucher.code'].browse(voucher_code_id)
        v_code = voucher_code.code
        
        year = self.env['weha.voucher.year'].browse(year_id)
        year_code = str(year.year)[2:4]
        
        if voucher_type == 'physical':
            classifi = '1'
        else:
            classifi = '2'

        number = str(check_number).zfill(6)
    
        code12 = c_code + v_code + year_code + classifi + number
        _logger.info("CODE 12 = " + str(code12))
        _logger.info("CODE 12 = " + str(code12))
        
        return code12

    def ean_checksum(self, eancode):
        """returns the checksum of an ean string of length 13, returns -1 if
        the string has the wrong length"""
        if len(eancode) != 13:
            return -1
        oddsum = 0
        evensum = 0
        eanvalue = eancode
        reversevalue = eanvalue[::-1]
        finalean = reversevalue[1:]

        for i in range(len(finalean)):
            if i % 2 == 0:
                oddsum += int(finalean[i])
            else:
                evensum += int(finalean[i])
        total = (oddsum * 3) + evensum

        check = int(10 - math.ceil(total % 10.0)) % 10
        return check

    def check_ean(self, eancode):
        """returns True if eancode is a valid ean13 string, or null"""
        if not eancode:
            return True
        if len(eancode) != 13:
            return False
        try:
            int(eancode)
        except:
            return False
        return self.ean_checksum(eancode) == int(eancode[-1])

    def generate_ean(self, ean):
        """Creates and returns a valid ean13 from an invalid one"""
        if not ean:
            return "0000000000000"
        ean = re.sub("[A-Za-z]", "0", ean)
        ean = re.sub("[^0-9]", "", ean)
        ean = ean[:13]
        if len(ean) < 13:
            ean = ean + '0' * (13 - len(ean))
        return ean[:-1] + str(self.ean_checksum(ean))

    def calculate_expired(self):
        if self.voucher_type == 'physical':
            self.expired_date = datetime.now() + timedelta(days=self.expired_days)
        else:
            self.expired_date = datetime.now() + timedelta(days=self.voucher_code_id.voucher_terms_id.number_of_days)

    def process_voucher_booking(self):
        cur_date_time = datetime.now()
        next_date_time = cur_date_time + timedelta(minutes=5)
        domain = [
            ('booking_expired_date','<', cur_date_time),
            ('state','=','booking')
        ]
        voucher_order_line_ids = self.env['weha.voucher.order.line'].search(domain)
        for voucher_order_line_id in  voucher_order_line_ids:
            #_logger.info(f"Scheduler : {len(voucher_order_line_ids)} vouhcers change to open ")
            voucher_order_line_id.write({'state': 'open'})
            voucher_order_line_id.create_order_line_trans(voucher_order_line_id.name, "RO")

    def process_voucher_scrap(self):
        _logger.info("Process Voucher Scrap")
        cur_date_time = datetime.now()
        next_date_time = cur_date_time + timedelta(minutes=5)
        domain = [
            ('expired_date','<', cur_date_time),
            ('state','=','activated')
        ]
        voucher_order_line_ids = self.env['weha.voucher.order.line'].search(domain)
        _logger.info(voucher_order_line_ids)
        for voucher_order_line_id in  voucher_order_line_ids:
            #_logger.info(f"Scheduler : {len(voucher_order_line_ids)} vouhcers change to open ")
            voucher_order_line_id.write({'state': 'scrap'})
            voucher_order_line_id.create_order_line_trans(voucher_order_line_id.name, "DM")

    def postgresql_create(self, vals):
        #Generate 12 Digit
        voucher_12_digit = self.generate_12_numbers(vals.get('voucher_type'), vals.get('voucher_code_id'), vals.get('year_id'), vals.get('check_number'))
        #Check Digit and Generate EAN 13
        _logger.info("Calc Check Digit")
        ean = voucher_12_digit + self.calc_check_digit(voucher_12_digit)
        _logger.info("INSERT 1")
        vals['voucher_12_digit'] = voucher_12_digit
        vals['voucher_ean'] = ean
        vals['name'] = ean
        _logger.info("INSERT")
        strSQL = """INSERT INTO weha_voucher_order_line 
            (voucher_12_digit,voucher_ean, name, operating_unit_id,voucher_type,
             voucher_order_id, voucher_sku, voucher_code_id,voucher_terms_id,year_id,check_number,voucher_amount,state,create_date,create_uid)
            VALUES ('{}','{}','{}',{},'{}',{},'{}',{},{},{},{},{},'{}','{}',{}) RETURNING id""".format(
                vals['voucher_12_digit'],
                vals['voucher_ean'],
                vals['name'],
                vals['operating_unit_id'],
                vals['voucher_type'],
                vals['voucher_order_id'],
                vals['voucher_sku'],
                vals['voucher_code_id'],
                vals['voucher_terms_id'],
                vals['year_id'],
                vals['check_number'],
                vals['voucher_amount'],
                'inorder',
                datetime.now().astimezone(pytz.utc),
                self.env.uid
            )
        self.env.cr.execute(strSQL)
        voucher_id = self.env.cr.fetchone()[0]
        voucher_order_name  = vals['voucher_order_name']
        vals = {}
        vals.update({'name': voucher_order_name})
        vals.update({'voucher_order_line_id': voucher_id})
        vals.update({'trans_date': datetime.now()})
        vals.update({'trans_type': 'OR'})
        self.env['weha.voucher.order.line.trans'].sudo().create(vals)

    def postgresql_create_legacy(self, vals):
        _logger.info("INSERT 1")
        vals['voucher_12_digit'] = vals['voucher_ean'][:12]
        vals['name'] = vals['voucher_ean']
        if vals['expired_date']:
            strSQL = """INSERT INTO weha_voucher_order_line 
                (voucher_12_digit,voucher_ean, name, operating_unit_id,voucher_type,
                voucher_code_id,voucher_terms_id,year_id,voucher_amount,is_legacy,state, create_date, create_uid, voucher_sku, expired_date)
                VALUES ('{}','{}','{}',{},'{}',{},{},{},{},{},'{}','{}',{},'{}','{}') RETURNING id""".format(
                    vals['voucher_12_digit'],
                    vals['voucher_ean'],
                    vals['name'],
                    vals['operating_unit_id'],
                    vals['voucher_type'],
                    vals['voucher_code_id'],
                    vals['voucher_terms_id'],
                    vals['year_id'],
                    vals['voucher_amount'],
                    vals['is_legacy'],
                    vals['state'],
                    datetime.now().astimezone(pytz.utc),
                    self.env.uid,
                    vals['voucher_sku'],
                    vals['expired_date'] if vals['expired_date'] else 'NULL'
                )
        else:
            strSQL = """INSERT INTO weha_voucher_order_line 
                (voucher_12_digit,voucher_ean, name, operating_unit_id,voucher_type,
                voucher_code_id,voucher_terms_id,year_id,voucher_amount,is_legacy,state, create_date, create_uid, voucher_sku)
                VALUES ('{}','{}','{}',{},'{}',{},{},{},{},{},'{}','{}',{},'{}') RETURNING id""".format(
                    vals['voucher_12_digit'],
                    vals['voucher_ean'],
                    vals['name'],
                    vals['operating_unit_id'],
                    vals['voucher_type'],
                    vals['voucher_code_id'],
                    vals['voucher_terms_id'],
                    vals['year_id'],
                    vals['voucher_amount'],
                    vals['is_legacy'],
                    vals['state'],
                    datetime.now().astimezone(pytz.utc),
                    self.env.uid,
                    vals['voucher_sku']
                )
        self.env.cr.execute(strSQL)
        voucher_id = self.env.cr.fetchone()[0]

        strSQL = """INSERT INTO weha_voucher_order_line_trans 
                (name, voucher_order_line_id, trans_date, trans_type, create_date, create_uid) 
                VALUES ('{}',{},'{}','{}','{}',{})""".format(
                    'Import',
                    voucher_id,
                    datetime.now(),
                    'OP',
                    datetime.now().astimezone(pytz.utc),
                    self.env.uid,
                )
        self.env.cr.execute(strSQL)

        # vals = {}
        # vals.update({'name': "Import"})
        # vals.update({'voucher_order_line_id': voucher_id})
        # vals.update({'trans_date': datetime.now()})
        # vals.update({'trans_type': 'OP'})
        # self.env['weha.voucher.order.line.trans'].sudo().create(vals)

    def get_voucher_expired(self):
        is_expired = False
        for row in self:
            if row.expired_date:
                if row.expired_date < date.today():
                    is_expired = True
            row.is_expired = is_expired

    def get_last_trans_line(self):
        trans_line_id = self.env['weha.voucher.order.line.trans'].search([('voucher_order_line_id','=', self.id)],limit=1)
        return trans_line_id

    def _auth_trust(self):
        try:
            url = "http://apiindev.trustranch.co.id/login"
            payload='barcode=3000030930&password=weha.ID!!2020'
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/x-www-form-urlencoded',
            }
            response = requests.request("POST", url, headers=headers, data=payload)
            str_json_data  = response.text.replace("'"," ")
            json_data = json.loads(str_json_data)
            _logger.info(json_data['data']['api_token'])
            return json_data['data']['api_token']
        except Exception as err:
            return False

    #API for Sales
    def send_data_to_trust(self):
        _logger.info("Send Data")
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
        base_url = 'http://apiindev.trustranch.co.id'
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
            req = requests.post('{}/vms/send-voucher'.format(base_url), headers=headers ,data=data)
            if req.status_code == 200:
                #Success
                response_json = req.json()
                self.is_send_to_crm = True
                self.message_post(body="Send Notification to CRM Successfully")
                return False, "Success"                
            else:
                #Error
                _logger.info(f'Error : {req.status_code}')
                if req.json():
                    response_json = req.json()                
                    _logger.info(f'Error Message: {response_json["message"]}')
                    self.is_send_to_crm = False
                    self.send_to_crm_message = response_json["message"]
                    self.message_post(body=response_json["message"])
                else:
                    self.is_send_to_crm = False
                    self.send_to_crm_message = f'Error : {req.status_code}'

                return True, "Error CRM"

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
            _logger.info(err)
            self.is_send_to_crm = False
            self.send_to_crm_message = "Error Request"
            self.message_post(body=err)
            self.message_post(body="Send Notification to CRM Failed (Exception)")
            return True, "Error CRM"
 

    #API for Used
    def send_used_notification_to_trust(self):  
        _logger.info("Send Used Notifcation")
        
        trans_line_id = self.get_last_trans_line()
        _logger.info(trans_line_id.name)

        if self.voucher_trans_type == '5':
            trans_status_id = self.env['weha.voucher.trans.status'].search([('name','=',trans_line_id.name)], limit=1)

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
            vouchers.append(self.voucher_ean)
            data = {
                'store_id': trans_status_id.store_id,
                'member_id': self.member_id,
                'vouchers': '|'.join(vouchers)
            }
            _logger.info(data)
            headers = {'Authorization' : 'Bearer ' + api_token}
            req = requests.post('{}/vms/use-voucher'.format(base_url), headers=headers ,data=data)
            if req.status_code == 200:
                #Success
                response_json = req.json()
                self.is_send_to_crm = True
                self.message_post(body="Send Notification to CRM Successfully")
                return False, "Success"                
            else:
                #Error
                _logger.info(f'Error : {req.status_code}')
                if req.json():
                    response_json = req.json()                
                    _logger.info(f'Error Message: {response_json["message"]}')
                    self.is_send_to_crm = False
                    self.send_to_crm_message = response_json["message"]
                    self.message_post(body=response_json["message"])
                else:
                    self.is_send_to_crm = False
                    self.send_to_crm_message = f'Error : {req.status_code}'

                return True, "Error CRM"

            
        except Exception as err:
            _logger.info(err)  
            self.is_send_to_crm = False
            self.send_to_crm_message = "Error Request"
            self.message_post(body=err)
            self.message_post(body="Send Notification to CRM Failed (Exception)")
            return True, "Error CRM"

    #API for Employee Voucher
    def send_employee_data_to_trust(self):
        _logger.info("Send Employee Data")
        trans_line_id = self.get_last_trans_line()
        _logger.info(trans_line_id.name)
        if self.voucher_trans_type == '4':
            voucher_issuing_id = self.env['weha.voucher.issuing'].search([('number','=',trans_line_id.name)], limit=1)
    
        api_token = self._auth_trust()
        headers = {'content-type': 'text/plain', 'charset':'utf-8'}
        base_url = 'http://apiindev.trustranch.co.id'
        try:
            vouchers = []
            vouchers.append(self.voucher_ean + ';' + self.expired_date.strftime('%Y-%m-%d') + ";" + self.voucher_sku)
            data = {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'time': datetime.now().strftime('%H:%M:%S'),
                'receipt': voucher_issuing_id.number,
                'transaction_id': voucher_issuing_id.number,
                'cashier_id': voucher_issuing_id.number,
                'store_id': 'H-100',
                #'member_id': trans_purchase_id.member_id,
                'member_id': self.member_id,
                'vouchers': '|'.join(vouchers)
            }
            _logger.info(data)
            headers = {'Authorization' : 'Bearer ' + api_token}
            req = requests.post('{}/vms/send-voucher'.format(base_url), headers=headers ,data=data)
            _logger.info(req.text)
            if req.status_code != '200':
                _logger.info(f'Error : {req.status_code}')
                response_json = req.json()
                _logger.info(f'Error Message: {response_json}')

            response_json = req.json()
            _logger.info(f'Success : {req.status_code}')
            _logger.info(f'Data: {response_json}')

        except Exception as err:
            _logger.error(err)  


    @api.model
    def create_order_line_trans(self, name, trans_type):
        for row in self:
            order_line_trans_obj = self.env['weha.voucher.order.line.trans']
            vals = {} 
            vals.update({'name': name})
            vals.update({'trans_date': datetime.now()})
            vals.update({'voucher_order_line_id': self.id})
            vals.update({'trans_type': trans_type})
            result = order_line_trans_obj.sudo().create(vals)            
            if not result:
                raise ValidationError("Can't create voucher order line trans, contact administrator!")

    name = fields.Char('Name', )
    
    #Customer Code
    customer_id = fields.Many2one('res.partner', 'Customer')
    member_id = fields.Char("Member #", size=20, index=True)
    
    #Operating Unit
    operating_unit_id = fields.Many2one(
        string='Operating Unit',
        comodel_name='operating.unit',
        ondelete='restrict',
        index=True
    )
    #Voucher Type
    voucher_type = fields.Selection(
        string='Type',
        selection=[('physical', 'Physical'), ('electronic', 'Electronic')],
        default='physical',
        index=True
    )

    #Voucher Trans Type
    voucher_trans_type = fields.Selection(
        string='Trans Type',
        selection=[('1', 'Sales'),('2','Promo'),('3','Redeem'),('4','Employee'),('5','Payment')],
        index=True
    )
    #Last Voucher Transaction Number
    #voucher_trans_number = fields.Char('Voucher Trans Number', size=200, readonly=True)

    #P-Voucher or E-Voucher
    voucher_code = fields.Char(string='Voucher Code')
    voucher_code_id = fields.Many2one(comodel_name='weha.voucher.code', string='Voucher Code ID', index=True)
    voucher_amount = fields.Float("Amount", related="voucher_code_id.voucher_amount", store=True)
    
    #Voucher Term (Expired Date)
    voucher_terms_id = fields.Many2one(comodel_name='weha.voucher.terms', string='Voucher Terms', index=True)
    
    #Voucher Promo
    voucher_promo_id = fields.Many2one('weha.voucher.promo','Promo', index=True)
    is_voucher_promo = fields.Boolean('Is Promo Voucher', default=False, readonly=True)
    tender_type_id = fields.Many2one('weha.voucher.tender.type', 'Tender Type')
    min_card_payment = fields.Float('Min Payment', default=0.0)
    voucher_count_limit = fields.Integer('Max Voucher Count', default=0)
    #tender_type_id = fields.Many2one('weha.voucher.tender.type', 'Tender Type', related='voucher_promo_id.tender_type_id', store=True)
    tender_type = fields.Char('Tender Type', size=20)
    bank_category_id = fields.Many2one('weha.voucher.bank.category', 'Bank Category')
    #bank_category_id = fields.Many2one('weha.voucher.bank.category', 'Bank Category', related='voucher_promo_id.bank_category_id', store=True)
    bank_category = fields.Char('Bank Category', size=20)

    #Check Number Voucher
    check_number = fields.Integer(string='Check Number', group_operator=False)
    #Voucher 12 Digit
    voucher_12_digit = fields.Char('Code 12', size=12)
    #Voucher EAN
    voucher_ean = fields.Char('Code', size=13)
    #Voucher SKU
    voucher_sku = fields.Char('SKU', size=20)
    #Loc Fr
    operating_unit_loc_fr_id = fields.Many2one(string='Loc.Fr', comodel_name='operating.unit', ondelete='restrict',)
    #Loc To
    operating_unit_loc_to_id = fields.Many2one(string='Loc.To', comodel_name='operating.unit', ondelete='restrict',)
    
    #Expired Date Voucher & Year
    expired_days =fields.Integer('Expired Days', default=0)
    expired_date = fields.Date(string='Expired Date')
    booking_expired_date = fields.Datetime(string='Booking Expired Date')
    year_id = fields.Many2one('weha.voucher.year',string='Year', index=True)
    
    #Send CRM Status
    is_send_to_crm = fields.Boolean('Send to CRM', default=False)
    send_to_crm_retry_count = fields.Integer('Send to CRM Retry', default=0)
    send_to_crm_message = fields.Char("Send to CRM Message", size=255)

    #Many2one relation
    voucher_order_id = fields.Many2one(
        string='Voucher Order',
        comodel_name='weha.voucher.order',
        ondelete='cascade',
    )

    voucher_request_id = fields.Many2one(
       string='Request id',
       comodel_name='weha.voucher.request',
       ondelete='restrict',
       index=True
    )
    voucher_allocate_id = fields.Many2one(
       string='Allocate id',
       comodel_name='weha.voucher.allocate',
       ondelete='restrict',
       index=True
    )
    voucher_stock_transfer_id = fields.Many2one(
       string='Stock Transfer id',
       comodel_name='weha.voucher.stock.transfer',
       ondelete='restrict',
       index=True
    )
    voucher_return_id = fields.Many2one(
       string='Stock Transfer id',
       comodel_name='weha.voucher.return',
       ondelete='restrict',
       index=True
    )
    voucher_order_id = fields.Many2one(
       string='Order id',
       comodel_name='weha.voucher.order',
       ondelete='restrict',
       index=True
    )
    voucher_order_line_trans_ids = fields.One2many(
        string='Voucher Trans',
        comodel_name='weha.voucher.order.line.trans',
        inverse_name='voucher_order_line_id',
        readonly=True,
    )
    
    is_expired = fields.Boolean('Is Expired', compute="get_voucher_expired")
    is_legacy = fields.Boolean('Is Legacy', default=False)

    #State Voucher
    state = fields.Selection(
        string='Status',
        selection=[
            ('draft', 'New'), 
            ('inorder', 'In-Order'),
            ('open', 'Open'), 
            ('deactivated','Deactivated'),
            ('activated','Activated'), 
            ('damage', 'Scrap'),
            ('transferred','Transferred'),
            ('intransit', 'In-Transit'),
            ('booking', 'Booking'),
            ('reserved', 'Reserved'),
            ('used', 'Used'),
            ('return', 'Return'),
            ('exception', 'Exception Request'),
            ('done','Close'),
            ('scrap','Scrap')
        ],
        default='inorder',
        index=True
    )

    _sql_constraints = [('voucher_ean_unique', 'unique(voucher_ean)', 'Voucher already exists.')]

    @api.model
    def create(self, vals):
        #Generate 12 Digit
        voucher_12_digit = self.generate_12_numbers(vals.get('voucher_type'), vals.get('voucher_code_id'), vals.get('year_id'), vals.get('check_number'))
        #Check Digit and Generate EAN 13
        ean = voucher_12_digit + self.calc_check_digit(voucher_12_digit)
        
        vals['voucher_12_digit'] = voucher_12_digit
        vals['voucher_ean'] = ean
        vals['name'] = ean
        res = super(VoucherOrderLine, self).create(vals)

        if vals.get('voucher_type') == 'electronic':
            res.calculate_expired()

        res.create_order_line_trans(res.name, 'OP')
        return res
    
class VoucherOrderLineTrans(models.Model):
    _name = 'weha.voucher.order.line.trans'
    _order = "trans_date desc"

    def open_form_view(self):
        self.ensure_one()
        if self.trans_type == 'US':
            voucher_trans_status_id = self.env['weha.voucher.trans.status'].search([('name','=', self.name)], limit=1)
            if voucher_trans_status_id:
                form_view = self.env.ref('weha_voucher_mgmt.view_weha_voucher_trans_status_form')
                return {
                    'name': _('Voucher Transaction - Status'),
                    'res_model': 'weha.voucher.trans.status',
                    'res_id': voucher_trans_status_id.id,
                    'views': [(form_view.id, 'form'), ],
                    'type': 'ir.actions.act_window',
                    'target': 'new',
                    'store':False,
                    'create':False,
                    'edit':False  
                }

    name = fields.Char(
        string='Voucher Trans ID', readonly=True
    )
    
    trans_date = fields.Datetime('Date and Time')
    
    voucher_order_line_id = fields.Many2one(
        string='Voucher Order Line',
        comodel_name='weha.voucher.order.line',
        ondelete='cascade', required=False,
    )
            
    trans_type = fields.Selection(
        string='Transaction Type', 
        selection=[
            ('OR', 'Order'),
            ('OP', 'Open'), 
            ('RV', 'Received'), 
            ('DV', 'Delivery'),
            ('ST', 'Stock Transfer'), 
            ('IC', 'Issued Customer'), 
            ('RT', 'Return'), 
            ('AC', 'Activated'), 
            ('RS', 'Reserved'), 
            ('US', 'Used'), 
            ('DM', 'Scrap'),
            ('CL', 'Cancel'),
            ('RO', 'Re-Open'),
            ('BO', 'Booking'),
        ],
        default='OP'
    )

    #Loc Fr
    operating_unit_loc_fr_id = fields.Many2one(string='Loc.Fr', comodel_name='operating.unit', ondelete='restrict',)
    #Loc To
    operating_unit_loc_to_id = fields.Many2one(string='Loc.To', comodel_name='operating.unit', ondelete='restrict',)

    #User    
    user_id = fields.Many2one('res.users', 'User')
