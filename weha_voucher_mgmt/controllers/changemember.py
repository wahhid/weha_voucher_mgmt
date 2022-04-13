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



class VMSChangeMemberContoller(http.Controller):
    
    @validate_token
    @http.route("/api/vms/v1.0/changemember", type="http", auth="none", methods=["POST"], csrf=False)
    def crmbooking(self, **post):
        message = "Change Member Successfully"
        trx_no = post['trx_no'] or False if 'trx_no' in post else False
        old_member = post['old_member'] or False if 'old_member' in post else False
        new_member = post['new_member'] or False  if 'new_member' in post else False
        voucher_ean = post['voucher_ean'] or False  if 'voucher_ean' in post else False


        _fields_includes_in_body = all([trx_no, 
                                        old_member, 
                                        new_member,
                                        voucher_ean])

        if not _fields_includes_in_body:
                data =  {
                    "err": True,
                    "message": "Missing fields",
                    "data": []
                }
                return valid_response(data)

        is_available = True
        arr_ean = voucher_ean.split('|')

        for voucher_ean in arr_ean:
            domain = [
                ('voucher_ean', '=', voucher_ean),
                ('member_id', '=', old_member)
            ]
            _logger.info(domain)
            voucher_order_line_id = http.request.env['weha.voucher.order.line'].sudo().search(domain, limit=1)
            if not voucher_order_line_id:
                is_available = False
                err_message = f'Voucher {voucher_ean} not found' 
                break
        

        if not is_available: 
            _logger.info("Search Voucher Order Line")
            response_data = {
                "err": True,
                "message": err_message,
                "data": []
            }
            return valid_response(response_data)

            
        voucher_change_member_obj = http.request.env['weha.voucher.change.member']
        values = {}
        values.update({'trx_no': trx_no})
        values.update({'old_member_id': old_member})
        values.update({'new_member_id': new_member})
        values.update({'voucher_ean': voucher_ean})
                
        #Create Voucher Change Member
        result = voucher_change_member_obj.sudo().create(values)   
        if result:
            #Return Successfull Response
            data = {
                "err": False,
                "message": message,
                "data": []
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

      