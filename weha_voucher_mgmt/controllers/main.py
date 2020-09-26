"""Part of odoo. See LICENSE file for full copyright and licensing details."""
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


class VMSController(http.Controller):
    

    @validate_token
    @http.route("/api/vms/v1.0/sales", type="http", auth="none", methods=["POST"], csrf=False)
    def vssales(self, **post):
        data =  {
                    "err": False,
                    "message": "",
                    "data": []
                }
        return valid_response(data)

    @validate_token
    @http.route("/api/vms/v1.0/promo", type="http", auth="none", methods=["POST"], csrf=False)
    def vspromo(self, **post):
        data =  {
                    "err": False,
                    "message": "Fields are missing",
                    "data": []
                }
        return valid_response(data)

    @validate_token
    @http.route("/api/vms/v1.0/redeem", type="http", auth="none", methods=["POST"], csrf=False)
    def csredeem(self, **post):
        data =  {
                    "err": False,
                    "message": "Fields are missing",
                    "data": []
                }
        return valid_response(data)


    #API 1, API3
    @validate_token
    @http.route("/api/vms/v1.0/purchase", type="http", auth="none", methods=["POST"], csrf=False)
    def vspurchase(self, **post):
        if 'voucher_type' not in post:
            return werkzeug.wrappers.Response(
            status=200,
            content_type="application/json; charset=utf-8",
            headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
            response=json.dumps(
                {
                    "err": True,
                    "message": "Fields are missing",
                    "data": []
                }
            ),
        )

        #Check Bank Promo and Voucher Availability
        if post['voucher_type'] == '1':
            domain = [
                ('code_sku','=', post['sku']),
            ]
            mapping_sku_id = http.request.env['weha.voucher.mapping.sku'].sudo().search(domain, limit=1)
            if not mapping_sku_id:
                return werkzeug.wrappers.Response(
                    status=200,
                    content_type="application/json; charset=utf-8",
                    headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
                    response=json.dumps(
                        {
                            "err": True,
                            "message": "SKU not found",
                            "data": [
                                {'code': 'N'}
                            ]
                        }
                    ),
                )

            domain = [
                ('voucher_code_id','=',mapping_sku_id.voucher_code_id.id),
                ('state', '=', 'open')
            ]

            voucher_count = http.request.env['weha.voucher.order.line'].sudo().search_count(domain)
            if voucher_count < int(post['quantity']):
                return werkzeug.wrappers.Response(
                    status=200,
                    content_type="application/json; charset=utf-8",
                    headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
                    response=json.dumps(
                        {
                            "err": True,
                            "message": "Voucher not available",
                            "data": [
                                {'code': 'N'}
                            ]
                        }
                    ),
                )
                            
            values = {}
            
            # #Save Voucher Purchase Transaction
            voucher_trans_purchase_obj = http.request.env['weha.voucher.trans.purchase']
            trans_date = post['date']  +  " "  + post['time'] + ":00"
            values.update({'trans_date': trans_date})
            values.update({'receipt_number': post['receipt_number']})
            values.update({'t_id': post['t_id']})
            values.update({'cashier_id': post['cashier_id']})
            values.update({'store_id': post['store_id']})
            values.update({'member_id': post['member_id']})
            values.update({'sku': post['sku']})
            values.update({'quantity': post['quantity']})
            values.update({'amount': post['amount']})
            values.update({'voucher_type': post['voucher_type']})

            #Save Data
            result = voucher_trans_purchase_obj.create(values)
            #validate Data

            #if validate set return_code = Y

            #if not validate set return_code = N

            #if return code not receive by VS send file to FTP
            #VMSyyyymmdd_Success 
            #VMSyyyymmdd_Fail 
        
            return werkzeug.wrappers.Response(
                status=200,
                content_type="application/json; charset=utf-8",
                headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
                response=json.dumps(
                    {
                        "err": False,
                        "message": "Create Successfully",
                        "data": [
                            {
                                'code': 'Y',
                                'vouchers': []
                            }
                        ]
                    }
                ),
            )
        
        elif post['voucher_type'] == '2':
            
            tender_type_id = http.request.env['weha.voucher.tender.type'].search([('code', '=', post['tender_type'])], limit=1)
            if not tender_type_id:
                return werkzeug.wrappers.Response(
                    status=200,
                    content_type="application/json; charset=utf-8",
                    headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
                    response=json.dumps(
                        {
                            "err": True,
                            "message": "Voucher not available",
                            "data": [
                                {'code': 'N'}
                            ]
                        }
                    ),
                )

            bank_category_id = http.request.env['weha.voucher.bank.category'].search([('bin_number', '=', post['bin_number'])], limit=1)
            if not tender_type_id:
                return werkzeug.wrappers.Response(
                    status=200,
                    content_type="application/json; charset=utf-8",
                    headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
                    response=json.dumps(
                        {
                            "err": True,
                            "message": "Voucher not available",
                            "data": [
                                {'code': 'N'}
                            ]
                        }
                    ),
                )

            domain = [
                ('tender_type_id','=', tender_type_id.id),
                ('bank_category_id', '=', bank_category_id.id),
                ('state', '=', 'open')
            ]

            voucher_count = http.request.env['weha.voucher.order.line'].sudo().search_count(domain)
            if voucher_count < int(post['quantity']):
                return werkzeug.wrappers.Response(
                    status=200,
                    content_type="application/json; charset=utf-8",
                    headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
                    response=json.dumps(
                        {
                            "err": True,
                            "message": "Voucher not available",
                            "data": [
                                {'code': 'N'}
                            ]
                        }
                    ),
                )
                          

            values = {}
            
            # #Save Voucher Purchase Transaction
            voucher_trans_purchase_obj = http.request.env['weha.voucher.trans.purchase']
            trans_date = post['date']  +  " "  + post['time'] + ":00"
            values.update({'trans_date': trans_date})
            values.update({'t_id': post['t_id']})
            values.update({'cashier_id': post['cashier_id']})
            values.update({'store_id': post['store_id']})
            values.update({'bin_number': post['bin_number']})
            values.update({'tender_type': post['tender_type']})
            values.update({'bank_category': post['bank_category']})
            values.update({'quantity': post['quantity']})
            values.update({'amount': post['amount']})
            values.update({'voucher_type': post['voucher_type']})

            #Save Data
            result = voucher_trans_purchase_obj.create(values)
            #validate Data

            #if validate set return_code = Y

            #if not validate set return_code = N

            #if return code not receive by VS send file to FTP
            #VMSyyyymmdd_Success 
            #VMSyyyymmdd_Fail 
        
            return werkzeug.wrappers.Response(
                status=200,
                content_type="application/json; charset=utf-8",
                headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
                response=json.dumps(
                    {
                        "err": False,
                        "message": "Create Successfully",
                        "data": [
                            {
                                'code': 'Y'
                            }
                        ]
                    }
                ),
            )

        elif post['voucher_type'] == '3':
            #Redeem
            domain = [
                ('code_sku','=', post['sku']),
            ]
            mapping_sku_id = http.request.env['weha.voucher.mapping.sku'].sudo().search(domain, limit=1)
            if not mapping_sku_id:
                return werkzeug.wrappers.Response(
                    status=200,
                    content_type="application/json; charset=utf-8",
                    headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
                    response=json.dumps(
                        {
                            "err": True,
                            "message": "SKU not found",
                            "data": [
                                {'code': 'N'}
                            ]
                        }
                    ),
                )

            domain = [
                ('voucher_code_id','=',mapping_sku_id.voucher_code_id.id),
                ('state', '=', 'open')
            ]

            voucher_count = http.request.env['weha.voucher.order.line'].sudo().search_count(domain)
            if voucher_count < int(post['quantity']):
                return werkzeug.wrappers.Response(
                    status=200,
                    content_type="application/json; charset=utf-8",
                    headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
                    response=json.dumps(
                        {
                            "err": True,
                            "message": "Voucher not available",
                            "data": [
                                {'code': 'N'}
                            ]
                        }
                    ),
                )
                            
            values = {}
            
            # #Save Voucher Purchase Transaction
            voucher_trans_purchase_obj = http.request.env['weha.voucher.trans.purchase']
            trans_date = post['date']  +  " "  + post['time'] + ":00"
            values.update({'trans_date': trans_date})
            values.update({'receipt_number': post['receipt_number']})
            values.update({'t_id': post['t_id']})
            values.update({'cashier_id': post['cashier_id']})
            values.update({'store_id': post['store_id']})
            values.update({'member_id': post['member_id']})
            values.update({'sku': post['sku']})
            values.update({'quantity': post['quantity']})
            values.update({'amount': post['amount']})
            values.update({'voucher_type': post['voucher_type']})

            #Save Data
            result = voucher_trans_purchase_obj.create(values)
            #validate Data

            #if validate set return_code = Y

            #if not validate set return_code = N

            #if return code not receive by VS send file to FTP
            #VMSyyyymmdd_Success 
            #VMSyyyymmdd_Fail 
        
            return werkzeug.wrappers.Response(
                status=200,
                content_type="application/json; charset=utf-8",
                headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
                response=json.dumps(
                    {
                        "err": False,
                        "message": "Create Successfully",
                        "data": [
                            {
                                'code': 'Y',
                                'vouchers': []
                            }
                        ]
                    }
                ),
            )
        

        else:
            return werkzeug.wrappers.Response(
                    status=200,
                    content_type="application/json; charset=utf-8",
                    headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
                    response=json.dumps(
                        {
                            "err": True,
                            "message": "Unknown Transaction",
                            "data": []
                        }
                    ),
                )

      
    #API4
    @validate_token
    @http.route("/api/vms/v1.0/voucherstatus", type="http", auth="none", methods=["POST"], csrf=False)
    def updatevoucherstatus(self, **post):
        if 'voucher_type' not in post:
            return werkzeug.wrappers.Response(
            status=200,
            content_type="application/json; charset=utf-8",
            headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
            response=json.dumps(
                {
                    "err": True,
                    "message": "Fields are missing",
                    "data": []
                }
            ),
        )

        #Tender Type, Bank Category ,BIN
        #Check Bank Promo and Voucher Availability
        if post['voucher_type'] == '2':
            tender_type_id = http.request.env['weha.voucher.tender.type'].search([('code', '=', post['tender_type'])], limit=1)
            if not tender_type_id:
                return werkzeug.wrappers.Response(
                    status=200,
                    content_type="application/json; charset=utf-8",
                    headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
                    response=json.dumps(
                        {
                            "err": True,
                            "message": "Voucher not available",
                            "data": [
                                {'code': 'N'}
                            ]
                        }
                    ),
                )

            bank_category_id = http.request.env['weha.voucher.bank.category'].search([('bin_number', '=', post['bin_number'])], limit=1)
            if not tender_type_id:
                return werkzeug.wrappers.Response(
                    status=200,
                    content_type="application/json; charset=utf-8",
                    headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
                    response=json.dumps(
                        {
                            "err": True,
                            "message": "Voucher not available",
                            "data": [
                                {'code': 'N'}
                            ]
                        }
                    ),
                )

            domain = [
                ('tender_type_id','=', tender_type_id.id),
                ('bank_category_id', '=', bank_category_id.id),
                ('state', '=', 'activated')
            ]

            voucher_order_line_ids = http.request.env['weha.voucher.order.line'].sudo().search(domain,limit=int(post['quantity']))
            for voucher_order_line_id in voucher_order_line_ids:
                voucher_order_line_id.write({'member_id': post['member_id'], 'state':'activated'})

            return werkzeug.wrappers.Response(
                status=200,
                content_type="application/json; charset=utf-8",
                headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
                response=json.dumps(
                    {
                        "err": True,
                        "message": "Voucher not available",
                        "data": [
                            {'code': 'N'}
                        ]
                    }
                ),
            )
                          
        else:
            return werkzeug.wrappers.Response(
                status=200,
                content_type="application/json; charset=utf-8",
                headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
                response=json.dumps(
                    {
                        "err": True,
                        "message": "Voucher Available",
                        "data": []
                    }
                ),
            )


    #
    @validate_token
    @http.route("/api/vms/v1.0/payment", type="http", auth="none", methods=["POST"], csrf=False)
    def vspayment(self, **payload):
        if 'trans_type' not in payload:
            return {'err': True, 'msg': 'Bank Purchase Successfully', 'datas':[]}

        if payload['trans_type'] != 'payment':
            return {'err': True, 'msg': 'Bank Purchase Successfully', 'datas':[]}
        return {'err': False, 'msg': 'VS Payment Succesfully', 'datas':[]}
    

   