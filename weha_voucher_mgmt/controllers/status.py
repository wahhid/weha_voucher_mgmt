import re
import ast
import functools
import logging
import json
from datetime import datetime, date
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


class VMSStatusController(http.Controller):
    
    @validate_token
    @http.route("/api/vms/v1.0/status", type="http", auth="none", methods=["POST"], csrf=False)
    def vssales(self, **post):
        
        trans_date = post['date'] or False if 'date' in post else False
        trans_time = post['time'] or False if 'time' in post else False
        receipt_number = post['receipt_number'] or False if 'receipt_number' in post else False
        t_id = post['t_id'] or False if 't_id' in post else False
        cashier_id = post['cashier_id'] or False  if 'cashier_id' in post else False
        store_id = post['store_id'] or False  if 'store_id' in post else False
        member_id = post['member_id'] or False  if 'member_id' in post else False
        voucher_ean = post['voucher_ean'] or False if 'voucher_ean' in post else False
        #voucher_type = post['voucher_type'] or False if 'voucher_type' in post else False
        process_type = post['process_type'] or False if 'process_type' in post else False

        if not process_type:
            data =  {
                "err": True,
                "message": "Missing fields",
                "data": []
            }
            return valid_response(data)
            
        if process_type == 'reserved':
            _logger.info("reserved")
            _fields_includes_in_body = all([trans_date, 
                                            trans_time, 
                                            #receipt_number,  optional
                                            t_id, 
                                            cashier_id, 
                                            store_id,
                                            # member_id, optional
                                            voucher_ean,
                                            process_type
                                            ])

        if process_type == 'used':
            _logger.info("used")
            _fields_includes_in_body = all([trans_date, 
                                            trans_time, 
                                            receipt_number, #mandatory
                                            t_id, 
                                            cashier_id, 
                                            store_id,
                                            #member_id, optional
                                            voucher_ean,
                                            process_type
                                            ])
        if process_type == 'activated':
            _logger.info("activated")
            _fields_includes_in_body = all([trans_date, 
                                            trans_time, 
                                            receipt_number,  #Mandatory
                                            t_id, 
                                            cashier_id, 
                                            store_id,
                                            #member_id, optional
                                            voucher_ean,
                                            process_type
                                            ])

        _logger.info(process_type)
        if not _fields_includes_in_body:
            data =  {
                "err": True,
                "message": "Missing fields",
                "data": []
            }
            return valid_response(data)
        
  
        is_available = True
        # if ';' in voucher_ean:
        #     arr_eans = voucher_ean.split(';')
        #     _logger.info(arr_eans)
        #     for str_ean in arr_eans:
        #         arr_ean  = str_ean.split('|')
        #         _logger.info(arr_ean)
        #         if process_type == 'reserved':
        #             domain = [
        #                 ('voucher_ean', '=', arr_ean),
        #                 ('state', '=', 'activated')
        #             ]
        #         elif process_type == 'used':
        #             domain = [
        #                 ('voucher_ean', '=', arr_ean),
        #                 ('state', '=', 'reserved')
        #             ]
        #         elif process_type == 'activated':
        #             domain = [
        #                 ('voucher_ean', '=', arr_ean),
        #                 ('state', '=', 'reserved')
        #             ]  
        #         else:
        #             is_available = False
        #         voucher_order_line_id = http.request.env['weha.voucher.order.line'].sudo().search(domain, limit=1)
        #         if not voucher_order_line_id:
        #             is_available = False
        # else:
        #     arr_ean  = voucher_ean.split('|')
        #     if process_type == 'reserved':
        #         domain = [
        #             ('voucher_ean', '=', arr_ean),
        #             ('state', '=', 'activated')
        #         ]
        #     elif process_type == 'used':
        #         domain = [
        #             ('voucher_ean', '=', arr_ean),
        #             ('state', '=', 'reserved')
        #         ]
        #     elif process_type == 'activated':
        #         domain = [
        #             ('voucher_ean', '=', arr_ean),
        #             ('state', '=', 'reserved')
        #         ]  
        #     else:
        #         is_available = False
        if process_type == 'reserved':
            domain = [
                ('voucher_ean', '=', voucher_ean),
                ('state', '=', 'activated')
            ]
        elif process_type == 'used':
            domain = [
                ('voucher_ean', '=', voucher_ean),
                ('state', '=', 'reserved')
            ]
        elif process_type == 'activated':
            domain = [
                ('voucher_ean', '=', voucher_ean),
                ('state', '=', 'reserved')
            ]
        else:
            response_data = {
                "err": True,
                "message": "Process Type not valid",
                "data": [
                    {'code': 'N'}
                ]
            }
            return valid_response(response_data)


        voucher_order_line_id = http.request.env['weha.voucher.order.line'].sudo().search(domain, limit=1)
        if not voucher_order_line_id:
            response_data = {
                "err": True,
                "message": "Vouchers not found",
                "data": [
                    {'code': 'N'}
                ]
            }
            return valid_response(response_data)

        if process_type == 'reserved':
            if voucher_order_line_id.expired_date <= date.today():
                response_data = {
                    "err": True,
                    "message": "Voucher expired",
                    "data": [
                        {'code': 'N'}
                    ]
                }
                return valid_response(response_data)
            

        values = {}
            
        # #Save Voucher Status Transaction
        voucher_trans_status_obj = http.request.env['weha.voucher.trans.status']
        trans_date = trans_date  +  " "  + trans_time + ":00"
        values.update({'trans_date': trans_date})
        values.update({'receipt_number': receipt_number})
        values.update({'t_id': t_id})
        values.update({'cashier_id': cashier_id})
        values.update({'store_id': store_id})
        values.update({'member_id': member_id})
        values.update({'voucher_ean': voucher_ean})
        values.update({'process_type': process_type})

        #Save Data
        result = voucher_trans_status_obj.sudo().create(values)
        
        if result:
            if process_type == 'reserved':
                add_data = result.get_json()
                data = {
                    "err": False,
                    "message": "Create Successfully",
                    "data": [
                        {
                            'code': 'Y',
                            'transaction_id': result.id,
                            'amount': add_data['amount'],
                            'tender_type': add_data['tender_type'],
                            'bank_category': add_data['bank_category'],
                        }
                    ]
                }
            if process_type == 'used':
                data = {
                    "err": False,
                    "message": "Create Successfully",
                    "data": [
                        {
                            'code': 'Y',
                            'transaction_id': result.id,
                        }
                    ]
                }          
            if process_type == 'activated':
                data = {
                    "err": False,
                    "message": "Create Successfully",
                    "data": [
                        {
                            'code': 'Y',
                            'transaction_id': result.id,
                        }
                    ]
                }
            return valid_response(data)
        else:
            data = {
                "err": True,
                "message": "Create Failed",
                "data": [
                    {
                        'code': 'N',
                    }
                ]
            }
            return valid_response(data)