import re
import ast
import functools
import logging
import json
from datetime import datetime
from datetime import date as dt
import werkzeug.wrappers
from odoo.exceptions import AccessError
from odoo.addons.weha_voucher_mgmt.common import invalid_response, valid_response

from odoo import http

from odoo.addons.weha_voucher_mgmt.common import (
    extract_arguments,
    invalid_response,
    valid_response,
)


from odoo.http import request

_logger = logging.getLogger(__name__)

def validate_token(func):
    """."""

    @functools.wraps(func)
    def wrap(self, *args, **kwargs):
        """."""
        access_token = request.httprequest.headers.get("access_token")
        if not access_token:
            return invalid_response("access_token_not_found", "missing access token in request header", 401)
        access_token_data = (
            request.env["api.access_token"].sudo().search([("token", "=", access_token)], order="id DESC", limit=1)
        )

        if access_token_data.find_one_or_create_token(user_id=access_token_data.user_id.id) != access_token:
            return invalid_response("access_token", "token seems to have expired or invalid", 401)

        request.session.uid = access_token_data.user_id.id
        request.uid = access_token_data.user_id.id
        return func(self, *args, **kwargs)

    return wrap


class VMSPromoController(http.Controller):
    
    @validate_token
    @http.route("/api/vms/v1.0/promo", type="http", auth="none", methods=["POST"], csrf=False)
    def vspromo(self, **post):
        
        date = post['date'] or False if 'date' in post else False
        time = post['time'] or False if 'time' in post else False
        receipt_number = post['receipt_number'] or False if 'receipt_number' in post else False
        t_id = post['t_id'] or False if 't_id' in post else False
        cashier_id = post['cashier_id'] or False if 'cashier_id' in post else False
        store_id = post['store_id'] or False if 'store_id' in post else False
        tender_type = post['tender_type'] or False if 'tender_type' in post else False
        bank_category = post['bank_category'] or False if 'bank_category' in post else False
        bin_number = post['bin_number'] or False if 'bin_number' in post else False
        sku = post['sku'] or False if 'sku' in post else False
        member_id = post['member_id'] or False  if 'member_id' in post else False
        voucher_type = post['voucher_type'] or False if 'voucher_type' in post else False

        _fields_includes_in_body = all([date, 
                                        time, 
                                        receipt_number, 
                                        t_id, 
                                        cashier_id, 
                                        store_id,
                                        tender_type,
                                        bank_category,
                                        bin_number,
                                        sku,
                                        voucher_type])

        if not _fields_includes_in_body:
                data =  {
                    "err": True,
                    "message": "Missing fields",
                    "data": []
                }
                return valid_response(data)

        if voucher_type != '2':
            return valid_response(
                {
                    "err": True,
                    "message": "Invalid Transaction",
                    "data": []
                }
            )
        
        skus = []
        is_available = True
        message = 'No Error'
        if ';' in sku:
            arr_skus = sku.split(';')
            _logger.info(arr_skus)
            total_amount = 0
            for str_sku in arr_skus:
                arr_sku  = str_sku.split('|')
                _logger.info(arr_sku)
                domain = [
                    ('code_sku', '=', arr_sku[0]),
                ]
                mapping_sku_id = http.request.env['weha.voucher.mapping.sku'].search(domain, limit=1)
                if not mapping_sku_id:
                    is_available = False
                    message = "SKU not found"
                    break
                    
                if mapping_sku_id.voucher_code_id and mapping_sku_id.voucher_code_id.voucher_type=='physical':
                    is_available = False
                    message = "P Voucher - Press Clear!"
                    break
                
                current_date = dt.today()
                _logger.info(current_date)
                
                domain = [
                    ('voucher_mapping_sku_id', '=' , mapping_sku_id.id),
                    ('voucher_promo_id','!=', False)
                ]

                _logger.info(domain)

                voucher_promo_line_id = http.request.env['weha.voucher.promo.line'].search(domain, limit=1)
                _logger.info(voucher_promo_line_id)
                if not voucher_promo_line_id:
                    message = "Promo Line not found"
                    is_available = False
                    break
                
                _logger.info(voucher_promo_line_id.voucher_promo_id.name)
                if not voucher_promo_line_id.voucher_promo_id:
                    message = f'Promo for {mapping_sku_id.code_sku} not found'
                    is_available = False
                    break
                
                if voucher_promo_line_id.voucher_promo_id.end_date:
                    if voucher_promo_line_id.voucher_promo_id.end_date < current_date:
                        message = "Promo Expired"
                        is_available = False  
                        break
                else:
                    message = f'Promo {voucher_promo_line_id.voucher_mapping_sku_id.name} need end date'
                    is_available = False  
                    break

                total_amount =  int(arr_sku[1]) * mapping_sku_id.voucher_code_id.voucher_amount
              
                if voucher_promo_line_id.voucher_promo_id.amount < voucher_promo_line_id.voucher_promo_id.current_amount + total_amount:
                    message = "Quota Exceeded"
                    is_available = False
                    break

            if not is_available:
                    response_data = {
                        "err": True,
                        "message": message,
                        "data": [
                            {'code': 'N'}
                        ]
                    }
                    return valid_response(response_data)

        else:
            arr_sku  = sku.split('|')
            _logger.info(arr_sku)
            domain = [
                ('code_sku', '=', arr_sku[0]),
            ]
            mapping_sku_id = http.request.env['weha.voucher.mapping.sku'].search(domain, limit=1)
            if not mapping_sku_id:
                message = "SKU not found"
                is_available = False

            if mapping_sku_id.voucher_code_id and mapping_sku_id.voucher_code_id.voucher_type=='physical':
                is_available = False
                message = "Physical Voucher Detected!"
            
            current_date = dt.today()
            _logger.info(current_date)

            domain = [
                    ('voucher_mapping_sku_id', '=' , mapping_sku_id.id),
                    ('voucher_promo_id.start_date', '<=',  current_date),
                    ('voucher_promo_id.end_date', '>=', current_date)
            ]
            _logger.info(domain)
            voucher_promo_line_id = http.request.env['weha.voucher.promo.line'].search(domain, limit=1)
            _logger.info(voucher_promo_line_id)
            _logger.info(voucher_promo_line_id.voucher_promo_id)
            if not voucher_promo_line_id:
                is_available = False
                message = "Promo not found or Already Expired"
            else:
                # current_date = dt.today()
                # if voucher_promo_line_id.voucher_promo_id.end_date < current_date:
                #     message = "Promo Expired"
                #     is_available = False
                
                total_amount =  int(arr_sku[1]) * mapping_sku_id.voucher_code_id.voucher_amount
                if voucher_promo_line_id.voucher_promo_id.amount < voucher_promo_line_id.voucher_promo_id.current_amount + total_amount:
                    message = "Quota Exceeded"
                    is_available = False
                
        if not is_available:
            response_data = {
                "err": True,
                "message": message,
                "data": [
                    {'code': 'N'}
                ]
            }
            return valid_response(response_data)

        values = {}
            
        # #Save Voucher Purchase Transaction
        voucher_trans_purchase_obj = http.request.env['weha.voucher.trans.purchase']
        trans_date = date  +  " "  + time + ":00"
        values.update({'trans_date': trans_date})
        values.update({'receipt_number': receipt_number})
        values.update({'t_id': t_id})
        values.update({'cashier_id': cashier_id})
        values.update({'store_id': store_id})
        values.update({'member_id': member_id})
        values.update({'sku': sku})
        values.update({'tender_type': tender_type})
        values.update({'bank_category': bank_category})
        values.update({'voucher_type': voucher_type})

        #values.update({'voucher_code_id': mapping_sku_id.voucher_code_id.id})

        #Save Data
        result = voucher_trans_purchase_obj.sudo().create(values)
        
        if not result:
            data =  {
                        "err": True,
                        "message": "Create Failed",
                        "data": []
                    }
            return valid_response(data)

        #Prepare Voucher Order Line List
        vouchers = result.get_json()
    
        data = {
            "err": False,
            "message": message,
            "data": [
                {
                    'code': 'Y',
                    'vouchers': vouchers
                }
            ]
        }
        return valid_response(data)

