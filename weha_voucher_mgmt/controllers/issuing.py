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



class VMSIssuingContoller(http.Controller):
    
    @validate_token
    @http.route("/api/vms/v1.0/issuing", type="http", auth="none", methods=["POST"], csrf=False)
    def crmbooking(self, **post):
        message = "Booking Successfully"
        date = post['date'] or False if 'date' in post else False
        time = post['time'] or False if 'time' in post else False
        ref = post['ref'] or False  if 'ref' in post else False
        store_id = post['store_id'] or False  if 'store_id' in post else False
        member_id = post['member_id'] or False  if 'member_id' in post else False
        voucher_ean = post['voucher_ean'] or False  if 'voucher_ean' in post else False


        _fields_includes_in_body = all([date, 
                                        time, 
                                        store_id,
                                        ref,
                                        member_id,
                                        voucher_ean])

        if not _fields_includes_in_body:
                data =  {
                    "err": True,
                    "message": "Missing fields",
                    "data": []
                }
                return valid_response(data)

        # if voucher_type != 'physical':
        #     return valid_response(
        #         {
        #             "err": True,
        #             "message": "Only Physical Voucher Allowed",
        #             "data": []
        #         }
        #     )

        
        operating_unit_id = http.request.env['operating.unit'].search([('code','=',store_id)])
        if not operating_unit_id:
            response_data = {
                "err": True,
                "message": "Operating Unit not found",
                "data": [
                    {'code': 'N'}
                ]
            }
            return valid_response(response_data)

        

        #Check Vouche by SKU on store
        voucher_eans = []
        is_error = False
        err_message = ''
        arr_voucher_ean  = voucher_ean.split('|')
        _logger.info(arr_voucher_ean)
        for ean in arr_voucher_ean:
            domain = [
                ('voucher_ean', '=', ean),
                ('operating_unit_id', '=', operating_unit_id.id)
            ]

            voucher_ean_id = http.request.env['weha.voucher.order.line'].search(domain, limit=1)
            if not voucher_ean_id:
                is_error = True
                err_message = f'{ean} not found'
                break
        
        if is_error:
            response_data = {
                "err": True,
                "message": err_message,
                "data": []
                }
            return valid_response(response_data)

        # if mapping_sku_id.voucher_code_id.voucher_type != 'physical':
        #     response_data = {
        #         "err": True,
        #         "message": "Voucher type not allowed",
        #         "data": []
        #     }
        #     return valid_response(response_data)

        values = {}
            
        # #Save Voucher Booking Transaction
        voucher_issuing_obj = http.request.env['weha.voucher.issuing']
        values.update({'issuing_date': datetime.now().strftime("%Y-%m-%d")})
        values.update({'operating_unit_id':operating_unit_id.id})
        values.update({'user_id': })
        values.update({'ref': })

        #Save Data
        result = voucher_trans_booking_obj.sudo().create(values)
        
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

    @validate_token
    @http.route("/api/vms/v1.0/bookingconfirm", type="http", auth="none", methods=["POST"], csrf=False)
    def bookingconfirm(self, **post):
        message = "Booking Confirm Successfully"
        date = post['date'] or False if 'date' in post else False
        time = post['time'] or False if 'time' in post else False
        store_id = post['store_id'] or False  if 'store_id' in post else False
        member_id = post['member_id'] or False  if 'member_id' in post else False
        voucher_ean = post['voucher_ean'] or False  if 'voucher_ean' in post else False

        _fields_includes_in_body = all([date, 
                                        time, 
                                        store_id,
                                        member_id,
                                        voucher_ean])
        if not _fields_includes_in_body:
                data =  {
                    "err": True,
                    "message": "Missing fields",
                    "data": []
                }
                return valid_response(data)
                
        operating_unit_id = http.request.env['operating.unit'].search([('code','=',store_id)])
        if not operating_unit_id:
            response_data = {
                "err": True,
                "message": "Operating Unit not found",
                "data": [
                    {'code': 'N'}
                ]
            }
            return valid_response(response_data)

        domain = [
            ('operating_unit_id','=', operating_unit_id.id),
            ('voucher_ean','=', voucher_ean),
            ('member_id','=', member_id)
        ]

        _logger.info(domain)

        voucher_order_line_id = http.request.env['weha.voucher.order.line'].sudo().search(domain, limit=1)
        
        if not voucher_order_line_id:
            response_data = {
                "err": True,
                "message": "Voucher not found",
                "data": [
                    {'code': 'N'}
                ]
            }
            return valid_response(response_data)

        voucher_order_line_id.write({'state': 'activated'})

        data = {
            "err": False,
            "message": "Booking Confirm Successfully",
            "data": []
        }
        return valid_response(data)