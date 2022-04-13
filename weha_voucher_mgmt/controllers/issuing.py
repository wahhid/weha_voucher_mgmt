import re
import ast
import functools
from datetime import datetime, date
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

        #Check Store ID
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
        #Check Submitted Voucher
        for ean in arr_voucher_ean:
            domain = [
                ('voucher_ean', '=', ean),
                ('operating_unit_id', '=', operating_unit_id.id),
                ('voucher_type','=','physical'),
                ('state', '=', 'open'),
            ]
            _logger.info(domain)
            voucher_ean_id = http.request.env['weha.voucher.order.line'].sudo().search(domain, limit=1)
            if not voucher_ean_id:
                is_error = True
                err_message = f'{ean} not found or already activated or make sure is physical voucher'
                break
        #If any error send error Response
        if is_error:
            response_data = {
                "err": True,
                "message": err_message,
                "data": []
                }
            return valid_response(response_data)

        values = {}
            
        # Prepare Vouche Issuing Transaction Data
        voucher_issuing_obj = http.request.env['weha.voucher.issuing']
        values.update({'issuing_date': datetime.now().strftime("%Y-%m-%d")})
        values.update({'operating_unit_id':operating_unit_id.id})
        values.update({'user_id': http.request.env.uid})
        values.update({'ref': ref})

        # Create Vouche Issuing Transaction
        result = voucher_issuing_obj.sudo().sudo().create(values)
        
        #Return Error Response
        if not result:
            data =  {
                "err": True,
                "message": "Create Failed",
                "data": []
            }
            return valid_response(data)

        #Repeat and Create All Voucher Issuing Line
        for ean in arr_voucher_ean:
            domain  = [
                ('voucher_ean', '=', ean),
                ('operating_unit_id', '=', operating_unit_id.id),
                ('voucher_type','=','physical'),
                ('state', '=', 'open'),
            ]
            
            voucher_ean_id = http.request.env['weha.voucher.order.line'].sudo().search(domain, limit=1)
            if not voucher_ean_id:
                _logger.error('Voucher not found')
            else:
                vals = {
                    'voucher_issuing_id': result.id,
                    'voucher_order_line_id': voucher_ean_id.id
                }
                http.request.env['weha.voucher.issuing.line'].sudo().create(vals)
        
        #Issuing All Voucher
        result.action_issuing_voucher()
        #Close Voucher Issuing Transaction
        result.trans_close()

        #Return Successfull Response
        data = {
            "err": False,
            "message": message,
            "data": [
                {
                    'code': 'Y',
                    'transaction_id': result.id,
                    'vouchers': []
                }
            ]
        }
        return valid_response(data)

    @validate_token
    @http.route("/api/vms/v1.0/pos_issuing", type="http", auth="none", methods=["POST"], csrf=False)
    def pos_issuing(self, **post):
        message = "Issuing Successfully"
        date = post['date'] or False if 'date' in post else False
        time = post['time'] or False if 'time' in post else False
        ref = post['ref'] or False  if 'ref' in post else False
        store_id = post['store_id'] or False  if 'store_id' in post else False
        #member_id = post['member_id'] or False  if 'member_id' in post else False
        voucher_ean = post['voucher_ean'] or False  if 'voucher_ean' in post else False


        _fields_includes_in_body = all([date, 
                                        time, 
                                        store_id,
                                        ref,
                                        #member_id,
                                        voucher_ean])

        if not _fields_includes_in_body:
                data =  {
                    "err": True,
                    "message": "Missing fields",
                    "data": []
                }
                return valid_response(data)

        #Check Store ID
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
        #Check Submitted Voucher
        for ean in arr_voucher_ean:
            domain = [
                ('voucher_ean', '=', ean),
                ('operating_unit_id', '=', operating_unit_id.id),
                ('voucher_type','=','physical'),
                ('state', '=', 'open'),
            ]
            _logger.info(domain)
            voucher_ean_id = http.request.env['weha.voucher.order.line'].sudo().search(domain, limit=1)
            if not voucher_ean_id:
                is_error = True
                err_message = f'{ean} not found or already activated or make sure is physical voucher'
                break
        #If any error send error Response
        if is_error:
            response_data = {
                "err": True,
                "message": err_message,
                "data": []
                }
            return valid_response(response_data)

        values = {}
            
        # Prepare Vouche Issuing Transaction Data
        voucher_issuing_obj = http.request.env['weha.voucher.issuing']
        values.update({'issuing_date': datetime.now().strftime("%Y-%m-%d")})
        values.update({'operating_unit_id':operating_unit_id.id})
        values.update({'user_id': http.request.env.uid})
        values.update({'ref': ref})

        # Create Vouche Issuing Transaction
        result = voucher_issuing_obj.sudo().sudo().create(values)
        
        #Return Error Response
        if not result:
            data =  {
                "err": True,
                "message": "Create Failed",
                "data": []
            }
            return valid_response(data)

        #Repeat and Create All Voucher Issuing Line
        for ean in arr_voucher_ean:
            domain  = [
                ('voucher_ean', '=', ean),
                ('operating_unit_id', '=', operating_unit_id.id),
                ('voucher_type','=','physical'),
                ('state', '=', 'open'),
            ]
            
            voucher_ean_id = http.request.env['weha.voucher.order.line'].sudo().search(domain, limit=1)
            if not voucher_ean_id:
                _logger.error('Voucher not found')
            else:
                vals = {
                    'voucher_issuing_id': result.id,
                    'voucher_order_line_id': voucher_ean_id.id
                }
                http.request.env['weha.voucher.issuing.line'].sudo().create(vals)
        
        #Issuing All Voucher
        result.action_issuing_voucher()
        #Close Voucher Issuing Transaction
        result.trans_close()

        #Return Successfull Response
        data = {
            "err": False,
            "message": message,
            "data": [
                {
                    'code': 'Y',
                    'transaction_id': result.id,
                    'vouchers': []
                }
            ]
        }
        return valid_response(data)