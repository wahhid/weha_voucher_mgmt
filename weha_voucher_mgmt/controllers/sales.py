import re
import ast
import functools
import logging
import json
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


class VMSSalesController(http.Controller):
    
    @validate_token
    @http.route("/api/vms/v1.0/sales", type="http", auth="none", methods=["POST"], csrf=False)
    def vssales(self, **post):
        message = "Create Successfully"
        date = post['date'] or False if 'date' in post else False
        time = post['time'] or False if 'time' in post else False
        receipt_number = post['receipt_number'] or False if 'receipt_number' in post else False
        t_id = post['t_id'] or False if 't_id' in post else False
        cashier_id = post['cashier_id'] or False  if 'cashier_id' in post else False
        store_id = post['store_id'] or False  if 'store_id' in post else False
        member_id = post['member_id'] or False  if 'member_id' in post else False
        sku = post['sku'] or False  if 'sku' in post else False
        #quantity = post['quantity'] or False  if 'quantity' in post else False
        #amount = post['amount'] or False  if 'amount' in post else False
        voucher_type = post['voucher_type'] or False if 'voucher_type' in post else False

        _fields_includes_in_body = all([date, 
                                        time, 
                                        receipt_number, 
                                        t_id, 
                                        cashier_id, 
                                        store_id,
                                        member_id,
                                        sku,
                                        #quantity,
                                        #amount,
                                        voucher_type])
        if not _fields_includes_in_body:
                data =  {
                    "err": True,
                    "message": "Missing fields",
                    "data": []
                }
                return valid_response(data)

        if voucher_type != '1':
            return valid_response(
                {
                    "err": True,
                    "message": "Invalid Transaction",
                    "data": []
                }
            )

        skus = []
        is_available = True
        if ';' in sku:
            arr_skus = sku.split(';')
            _logger.info(arr_skus)
            for str_sku in arr_skus:
                arr_sku  = str_sku.split('|')
                _logger.info(arr_sku)
                domain = [
                    ('code_sku', '=', arr_sku[0]),
                ]
                mapping_sku_id = http.request.env['weha.voucher.mapping.sku'].search(domain, limit=1)
                if not mapping_sku_id:
                    is_available = False
        else:
            arr_sku  = sku.split('|')
            _logger.info(arr_sku)
            domain = [
                ('code_sku', '=', arr_sku[0]),
            ]
            mapping_sku_id = http.request.env['weha.voucher.mapping.sku'].search(domain, limit=1)
            if not mapping_sku_id:
                is_available = False
        
        #domain = [
        #    ('code_sku', '=', sku),
        #]


        if not is_available:
            response_data = {
                "err": True,
                "message": "SKU not found",
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
        values.update({'voucher_type': voucher_type})        

        #Save Data
        result = voucher_trans_purchase_obj.sudo().create(values)
        
        if not result:
            data =  {
                        "err": True,
                        "message": "Create Failed",
                        "data": []
                    }
            return valid_response(data)

        #Validate Data
        #result.write({'state','done'})
        
        #Prepare Voucher Order Line List
        vouchers = result.get_json()
        
        #if validate set return_code = Y

        #if not validate set return_code = N

        #if return code not receive by VS send file to FTP
        #VMSyyyymmdd_Success 
        #VMSyyyymmdd_Fail 
    
        data = {
            "err": False,
            "message": message,
            "data": [
                {
                    'code': 'Y',
                    'transaction_id': result.id,
                    'vouchers': vouchers
                }
            ]
        }
        return valid_response(data)
