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


class VMSPromoController(http.Controller):
    
    @validate_token
    @http.route("/api/vms/v1.0/promo", type="http", auth="none", methods=["POST"], csrf=False)
    def vspromo(self, **post):
        
        date = post['date']
        time = post['time']
        receipt_number = post['receipt_number']
        t_id = post['t_id']
        cashier_id = post['cashier_id']
        store_id = post['store_id']
        tender_type = post['tender_type']
        bank_categgory = post['bank_category']
        bin_number = post['bin_number']
        sku = post['sku']
        member_id = post['member_id'] or False  if 'member_id' in post else False
        voucher_type = post['voucher_type']

        _fields_includes_in_body = all([date, 
                                        time, 
                                        receipt_number, 
                                        t_id, 
                                        cashier_id, 
                                        store_id,
                                        tender_type,
                                        bank_categgory,
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
                domain = [
                    ('voucher_mapping_sku_id', '=' , mapping_sku_id.id)
                ]
                voucher_promo_line_id = http.request.env['weha.voucher.promo.line'].search(domain, limit=1)
                if not voucher_promo_line_id:
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
            domain = [
                    ('voucher_mapping_sku_id', '=' , mapping_sku_id.id)
            ]
            voucher_promo_line_id = http.request.env['weha.voucher.promo.line'].search(domain, limit=1)
            if not voucher_promo_line_id:
                is_available = False
            
        
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
        #values.update({'quantity': quantity})
        #values.update({'amount': amount})
        values.update({'voucher_type': voucher_type})
        #values.update({'voucher_code_id': mapping_sku_id.voucher_code_id.id})

        #Save Data
        result = voucher_trans_purchase_obj.create(values)
        
        #Prepare Voucher Order Line List
        vouchers = []
        for voucher_trans_purchase_line_id in result.voucher_trans_purchase_line_ids:
            vouchers.append(voucher_trans_purchase_line_id.voucher_order_line_id.voucher_ean)
        

        if result:

            data =  {
                        "err": False,
                        "message": "Create Successfully",
                        "data": []
                    }
            return valid_response(data)
        else:
            data =  {
                        "err": True,
                        "message": "Create Failed",
                        "data": []
                    }
            return valid_response(data)

