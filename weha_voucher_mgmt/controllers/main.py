"""Part of odoo. See LICENSE file for full copyright and licensing details."""
import re
import ast
import functools
import logging
import json
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


class VMSController(http.Controller):
    
    @validate_token
    @http.route("/api/vms/v1.0/vspurchase", type="http", auth="none", methods=["POST"], csrf=False)
    def vspurchase(self, **payload):

        #if payload['trans_type'] == 'redeem':
            
        values = {}
        
        #Save Voucher Purchase Transaction
        voucher_purchase_obj = http.request.env['voucher.purchase']
        values.update({'name': post['name']})
        values.update({'voucher_type': post['voucher_type']}) 
        values.update({'trans_date': post['trans_date']}) 
        values.update({'receipt_number': post['receipt_number']}) 
        values.update({'cashier_id': post['cashier_id']}) 
        values.update({'store_id': post['store_id']}) 
        values.update({'sku': post['sku']}) 
        values.update({'quantity': post['quantity']}) 
        values.update({'amount': post['amount']}) 
        values.update({'member_id': post['member_id']}) 
        values.update({'point': post['point']}) 
        values.update({'return_code': post['return_code']}) 
        values.update({'status_1': post['status_1']}) 
        values.update({'status_1_date': post['status_1_date']}) 
        values.update({'status_2': post['status_2']}) 
        values.update({'status_2_date': post['status_2_date']}) 
        #Save Data

        #validate Data

        #if validate set return_code = Y

        #if not validate set return_code = N

        #if return code not receive by VS send file to FTP
        #VMSyyyymmdd_Success 
        #VMSyyyymmdd_Fail 
    

        data = {
            'status': 'ok'
        }

        return json.dumps({'err': False, 'msg': 'VS Purchase Successfully', 'datas':json.dumps(data)})
    
    @validate_token
    @http.route("/api/vms/v1.0/bankpurchase", type="http", auth="none", methods=["POST"], csrf=False)
    def bankpurchase(self, **payload):
        if 'trans_type' not in payload:
            return {'err': True, 'msg': 'Bank Purchase Successfully', 'datas':[]}

        if payload['trans_type'] != 'promo':
            return {'err': True, 'msg': 'Bank Purchase Successfully', 'datas':[]}
        
        return {'err': False, 'msg': 'Bank Purchase Successfully', 'datas':[]}

    @validate_token
    @http.route("/api/vms/v1.0/custredeem", type="http", auth="none", methods=["POST"], csrf=False)
    def custredeem(self, **payload):
        if 'trans_type' not in payload:
            return {'err': True, 'msg': 'Bank Purchase Successfully', 'datas':[]}

        if payload['trans_type'] != 'redeem':
            return {'err': True, 'msg': 'Bank Purchase Successfully', 'datas':[]}

        return {'err': False, 'msg': 'Redeem Successfully', 'datas':[]}
    
    @validate_token
    @http.route("/api/vms/v1.0/vspayment", type="http", auth="none", methods=["POST"], csrf=False)
    def vspayment(self, **payload):
        if 'trans_type' not in payload:
            return {'err': True, 'msg': 'Bank Purchase Successfully', 'datas':[]}

        if payload['trans_type'] != 'payment':
            return {'err': True, 'msg': 'Bank Purchase Successfully', 'datas':[]}
        return {'err': False, 'msg': 'VS Payment Succesfully', 'datas':[]}
    
    @validate_token
    @http.route("/api/vms/v1.0/bankpayment", type="http", auth="none", methods=["POST"], csrf=False)
    def bankpayment(self, **payload):
        if 'trans_type' not in payload:
            return {'err': True, 'msg': 'Bank Purchase Successfully', 'datas':[]}

        if payload['trans_type'] != 'payment':
            return {'err': True, 'msg': 'Bank Purchase Successfully', 'datas':[]}
        return {'err': False, 'msg': 'Bank Payment Successfully', 'datas':[]}
    
    
    