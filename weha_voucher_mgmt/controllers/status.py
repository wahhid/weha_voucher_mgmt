import re
import ast
import functools
import logging
import json
import werkzeug.wrappers
import pytz
from odoo.exceptions import AccessError
from odoo.addons.weha_voucher_mgmt.common import invalid_response, valid_response
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime, timedelta, date as dt

from odoo import http

from odoo.addons.weha_voucher_mgmt.common import (
    extract_arguments,
    invalid_response,
    valid_response,
    convert_local_to_utc
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
    @http.route("/api/vms/v1.0/status", type="http", auth="none", methods=["POST"], csrf=False, cors="*")
    def vssales(self, **post):
        
        #Process Fields
        trans_date = post['date'] or False if 'date' in post else False
        trans_time = post['time'] or False if 'time' in post else False
        receipt_number = post['receipt_number'] or False if 'receipt_number' in post else False
        t_id = post['t_id'] or False if 't_id' in post else False
        cashier_id = post['cashier_id'] or False  if 'cashier_id' in post else False
        store_id = post['store_id'] or False  if 'store_id' in post else False
        member_id = post['member_id'] or False  if 'member_id' in post else False
        voucher_eans = post['voucher_ean'] or False if 'voucher_ean' in post else False
        process_type = post['process_type'] or False if 'process_type' in post else False
        void = post['void'] or False if 'void' in post else False

        
        #Check Field Process Type
        if not process_type:
            data =  {
                "err": True,
                "message": "Missing Process Type Fields",
                "data": []
            }
            return valid_response(data)
            
        #Check Field for Reserved
        if process_type == 'reserved':
            _logger.info("reserved")
            _fields_includes_in_body = all([trans_date, 
                                            trans_time, 
                                            t_id, 
                                            cashier_id, 
                                            store_id,
                                            voucher_eans,
                                            process_type
                                            ])
        #Check Field for Used
        if process_type == 'used':
            _logger.info("used")
            _fields_includes_in_body = all([trans_date, 
                                            trans_time, 
                                            receipt_number, #mandatory
                                            t_id, 
                                            cashier_id, 
                                            store_id,
                                            voucher_eans,
                                            process_type
                                            ])
        #Check Field for Activated
        if process_type == 'activated':
            _logger.info("activated")
            _fields_includes_in_body = all([trans_date, 
                                            trans_time, 
                                            receipt_number,  #Mandatory
                                            t_id, 
                                            cashier_id, 
                                            store_id,
                                            voucher_eans,
                                            process_type
                                            ])
        #Check Field for Re-Open
        if process_type == 'reopen':
            _logger.info("Re-Open")
            _fields_includes_in_body = all([trans_date, 
                                            trans_time,
                                            voucher_eans,
                                            process_type
                                            ])

        #Check Missing Fields
        _logger.info(process_type)
        if not _fields_includes_in_body:
            data =  {
                "err": True,
                "message": "Missing fields",
                "data": []
            }
            return valid_response(data)
        
  
        #Check Voucher Eans
        is_available = True
        err_message = ''
        voucher_order_line_ids = []
        arr_ean = voucher_eans.split('|')
        if process_type in 'reserved':
            for voucher_ean in arr_ean:
                domain = [
                    ('voucher_ean', '=', voucher_ean),
                    ('state', '=', 'activated','used','scrap')
                ]
                _logger.info(domain)
                voucher_order_line_id = http.request.env['weha.voucher.order.line'].sudo().search(domain, limit=1)
                
                if not voucher_order_line_id:
                    is_available = False
                    err_message = f'Voucher {voucher_ean} not found' 
                    break
                
                if voucher_order_line_id.voucher_type == 'electronic':
                    _logger.info('Electronic Voucher')
                    if not member_id:
                        is_available = False
                        err_message = f'Need Member Information' 
                        break
                    else:
                        if voucher_order_line_id.member_id != member_id:
                            is_available = False
                            err_message = f'Voucher {voucher_ean} member not found' 
                            break

                else:
                    _logger.info('Physical Voucher')

                #Check For Used
                if voucher_order_line_id.state != 'activated':
                    if voucher_order_line_id.state == 'used':
                        is_available = False
                        err_message = f'Voucher {voucher_ean} was used' 
                        break
                    elif voucher_order_line_id.state == 'scrap':
                        is_available = False
                        err_message = f'Voucher {voucher_ean} was expired' 
                        break
                    else:
                        is_available = False
                        err_message = f'Voucher {voucher_ean} not found' 
                        break
                #Check Voucher Expired Date
                if voucher_order_line_id.expired_date < dt.today():
                    is_available = False
                    err_message = f'Voucher {voucher_ean} expired' 
                    break
                
                #Add Voucher Order Line to List
                voucher_order_line_ids.append(voucher_order_line_id)    
        elif process_type == 'used':
            for voucher_ean in arr_ean:
                domain = [
                    ('voucher_ean', '=', voucher_ean),
                    ('state', '=', 'reserved')
                ]
                _logger.info(domain)
                voucher_order_line_id = http.request.env['weha.voucher.order.line'].sudo().search(domain, limit=1)
                if not voucher_order_line_id:
                    is_available = False
                    err_message = f'Voucher {voucher_ean} not found' 
                    break

                voucher_order_line_ids.append(voucher_order_line_id)  
        elif process_type == 'activated':
            for voucher_ean in arr_ean:
                domain = [
                    ('voucher_ean', '=', voucher_ean),
                    ('state', 'in', ['reserved','used'])
                ]

                _logger.info(domain)
                voucher_order_line_id = http.request.env['weha.voucher.order.line'].sudo().search(domain, limit=1)
                if not voucher_order_line_id:
                    is_available = False
                    err_message = f'Voucher {voucher_ean} not found' 
                    break

                voucher_order_line_ids.append(voucher_order_line_id)  
        elif process_type == 'reopen':
            for voucher_ean in arr_ean:
                domain = [
                    ('voucher_ean', '=', voucher_ean),
                    ('state', 'in', ['reserved','activated','used'])
                ]

                _logger.info(domain)
                voucher_order_line_id = http.request.env['weha.voucher.order.line'].sudo().search(domain, limit=1)
                if not voucher_order_line_id:
                    is_available = False
                    err_message = f'Voucher {voucher_ean} not found' 
                    break

                voucher_order_line_ids.append(voucher_order_line_id)  
        else:
            response_data = {
                "err": True,
                "message": "Process Type not valid",
                "data": [
                    {'code': 'N'}
                ]
            }
            return valid_response(response_data)

        if not is_available: 
            _logger.info("Search Voucher Order Line")
            response_data = {
                "err": True,
                "message": err_message,
                "data": []
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
        values.update({'voucher_ean': voucher_eans})
        values.update({'process_type': process_type})
        if process_type == 'activated':
            if void == '0':
                values.update({'void': False})
            else:
                values.update({'void': True})
                
        #Create Voucher Transaction Status
        result = voucher_trans_status_obj.sudo().create(values)    
        if result:
            if process_type == 'reserved':
                add_data = result.get_json()
                if not add_data['err']:
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
                                'min_card_payment': add_data['min_card_payment'],
                                'max_vchr_count': add_data['voucher_count_limit'],
                            }
                        ]
                    }
                else:
                    data = {
                        "err": True,
                        "message": add_data['message'],
                        "data": []
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
                add_data = result.get_json()
                if not add_data['err']:
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
                else:
                    data = {
                        "err": True,
                        "message": add_data['message'],
                        "data": []
                    }
            if process_type == 'reopen':
                data = {
                    "err": False,
                    "message": "Process Successfully",
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


    @validate_token
    @http.route("/api/vms/v2.0/status", type="http", auth="none", methods=["POST"], csrf=False, cors="*")
    def vssales2(self, **post):
        
        #Process Fields
        date = post['date'] or False if 'date' in post else False
        time = post['time'] or False if 'time' in post else False
        receipt_number = post['receipt_number'] or False if 'receipt_number' in post else False
        t_id = post['t_id'] or False if 't_id' in post else False
        cashier_id = post['cashier_id'] or False  if 'cashier_id' in post else False
        store_id = post['store_id'] or False  if 'store_id' in post else False
        member_id = post['member_id'] or False  if 'member_id' in post else False
        voucher_eans = post['voucher_ean'] or False if 'voucher_ean' in post else False
        process_type = post['process_type'] or False if 'process_type' in post else False
        void = post['void'] or False if 'void' in post else False
        batch_id = post['batch_id'] or False if 'batch_id' in post else False
        
        #Check Field Process Type
        if not process_type:
            data =  {
                "err": True,
                "message": "Missing Process Type Fields",
                "data": []
            }
            return valid_response(data)
            
        #Check Field for Reserved
        if process_type == 'reserved':
            _logger.info("reserved")
            _fields_includes_in_body = all([date, 
                                            time, 
                                            t_id, 
                                            cashier_id, 
                                            store_id,
                                            voucher_eans,
                                            process_type
                                            ])
        #Check Field for Used
        if process_type == 'used':
            _logger.info("used")
            _fields_includes_in_body = all([date, 
                                            time, 
                                            receipt_number, #mandatory
                                            t_id, 
                                            cashier_id, 
                                            store_id,
                                            voucher_eans,
                                            process_type
                                            ])
        #Check Field for Activated
        if process_type == 'activated':
            _logger.info("activated")
            if batch_id:
                _fields_includes_in_body = all([date, 
                                                time, 
                                                receipt_number,  #Mandatory
                                                t_id, 
                                                cashier_id, 
                                                store_id,
                                                batch_id,
                                                process_type
                                                ])
            else:
                _fields_includes_in_body = all([date, 
                                                time, 
                                                receipt_number,  #Mandatory
                                                t_id, 
                                                cashier_id, 
                                                store_id,
                                                voucher_eans,
                                                process_type
                                                ])
        #Check Field for Re-Open
        if process_type == 'reopen':
            _logger.info("Re-Open")
            _fields_includes_in_body = all([date, 
                                            time,
                                            voucher_eans,
                                            process_type
                                            ])

        #Check Missing Fields
        _logger.info(process_type)
        if not _fields_includes_in_body:
            data =  {
                "err": True,
                "message": "Missing fields",
                "data": []
            }
            return valid_response(data)
        
  
        #Check Voucher Eans
        is_available = True
        err_message = ''
        voucher_order_line_ids = []
        if not batch_id:
            arr_ean = voucher_eans.split('|')

        if process_type in 'reserved':
            #Non Batch
            #Reserver For Payment
            for voucher_ean in arr_ean:
                domain = [
                    ('voucher_ean', '=', voucher_ean),
                    ('state', 'in', ['activated','used','scrap'])
                ]
                _logger.info(domain)
                voucher_order_line_id = http.request.env['weha.voucher.order.line'].sudo().search(domain, limit=1)
                if not voucher_order_line_id:
                    is_available = False
                    err_message = f'Voucher {voucher_ean} not found 1' 
                    break
                
                #Check For Used
                if voucher_order_line_id.state != 'activated':
                    if voucher_order_line_id.state == 'used':
                        is_available = False
                        err_message = f'Voucher {voucher_ean} was used' 
                        break
                    elif voucher_order_line_id.state == 'scrap':
                        is_available = False
                        err_message = f'Voucher {voucher_ean} was expired' 
                        break
                    else:
                        is_available = False
                        err_message = f'Voucher {voucher_ean} not found' 
                        break
                else:
                    if voucher_order_line_id.voucher_type == 'electronic':
                        _logger.info('Electronic Voucher')
                        if not member_id:
                            is_available = False
                            err_message = f'Need Member Information' 
                            break
                        else:
                            if voucher_order_line_id.member_id != member_id:
                                is_available = False
                                err_message = f'Voucher {voucher_ean} member not found' 
                                break
                    else:
                        _logger.info('Physical Voucher')

                

                #Check Voucher Expired Date
                if not voucher_order_line_id.expired_date:
                    is_available = False
                    err_message = f'Voucher {voucher_ean} expired date not exist' 
                    break

                if voucher_order_line_id.expired_date < dt.today():
                    is_available = False
                    err_message = f'Voucher {voucher_ean} was expired' 
                    break
                #Add Voucher Order Line to List
                voucher_order_line_ids.append(voucher_order_line_id)    

        elif process_type == 'used':
            #Not Batch
            #User for Payment After Reserved
            for voucher_ean in arr_ean:
                domain = [
                    ('voucher_ean', '=', voucher_ean),
                    ('state', '=', 'reserved')
                ]
                _logger.info(domain)
                voucher_order_line_id = http.request.env['weha.voucher.order.line'].sudo().search(domain, limit=1)
                if not voucher_order_line_id:
                    is_available = False
                    err_message = f'Voucher {voucher_ean} not found' 
                    break
                    
                voucher_order_line_ids.append(voucher_order_line_id)  
        
        elif process_type == 'activated':
            #Batch
            #Activate After Sales
            if batch_id:
                #Check Voucher Status by Batch ID
                domain = [
                    ('batch_id', '=', batch_id)
                ]
                trans_status_id = http.request.env['weha.voucher.trans.status'].sudo().search(domain, limit=1)
                if trans_status_id:
                    is_available = False
                    err_message = f'Transaction Already Process' 

                #Check Voucher Trans Purchase
                domain = [
                    ('batch_id', '=', batch_id)
                ]
                trans_purchase_id = http.request.env['weha.voucher.trans.purchase'].sudo().search(domain, limit=1)
                if not trans_purchase_id:
                    is_available = False
                    err_message = f'Voucher {batch_id} not found' 
                
                voucher_eans = ""
                if len(trans_purchase_id.voucher_trans_purchase_line_ids) == 1:
                    voucher_eans = trans_purchase_id.voucher_trans_purchase_line_ids[0].voucher_order_line_id.voucher_ean
                else:
                    line_ids = [line_id.voucher_order_line_id.voucher_ean for line_id in trans_purchase_id.voucher_trans_purchase_line_ids]
                    _logger.info(line_ids)
                    delimiter = "|"
                    voucher_eans = delimiter.join(line_ids)
                    #for line_id in trans_purchase_id.voucher_trans_purchase_line_ids:
                    #    voucher_eans = line_id.voucher_order_line_id.voucher_ean + "|"

                arr_ean = voucher_eans.split('|')

                for voucher_ean in arr_ean:
                    domain = [
                        ('voucher_ean', '=', voucher_ean),
                        ('state', 'in', ['reserved','used'])
                    ]

                    _logger.info(domain)
                    voucher_order_line_id = http.request.env['weha.voucher.order.line'].sudo().search(domain, limit=1)
                    if not voucher_order_line_id:
                        is_available = False
                        err_message = f'Voucher {voucher_ean} not found' 
                        break

                    voucher_order_line_ids.append(voucher_order_line_id)
            else:
                #Non Batch
                #Activate for Cancel Payment
                for voucher_ean in arr_ean:
                    domain = [
                        ('voucher_ean', '=', voucher_ean),
                        ('state', 'in', ['reserved','used'])
                    ]

                    _logger.info(domain)
                    voucher_order_line_id = http.request.env['weha.voucher.order.line'].sudo().search(domain, limit=1)
                    if not voucher_order_line_id:
                        is_available = False
                        err_message = f'Voucher {voucher_ean} not found' 
                        break

                    voucher_order_line_ids.append(voucher_order_line_id)  
                    
        elif process_type == 'reopen':
            for voucher_ean in arr_ean:
                domain = [
                    ('voucher_ean', '=', voucher_ean),
                    ('state', 'in', ['reserved','activated','used'])
                ]

                _logger.info(domain)
                voucher_order_line_id = http.request.env['weha.voucher.order.line'].sudo().search(domain, limit=1)
                if not voucher_order_line_id:
                    is_available = False
                    err_message = f'Voucher {voucher_ean} not found' 
                    break

                voucher_order_line_ids.append(voucher_order_line_id)  
        else:
            response_data = {
                "err": True,
                "message": "Process Type not valid",
                "data": [
                    {'code': 'N'}
                ]
            }
            return valid_response(response_data)

        if not is_available: 
            _logger.info("Search Voucher Order Line")
            response_data = {
                "err": True,
                "message": err_message,
                "data": []
            }
            return valid_response(response_data)
        
        values = {}
            
        # Prepare Voucher Status Transaction
        user_tz = http.request.env.user.tz
        if not user_tz:
            data =  {
                        "err": True,
                        "message": "User didn't set timezone parameter",
                        "data": []
                    }
            return valid_response(data)
        _logger.info(user_tz)
        
        str_trans_date = date  +  " "  + time + ":00"
        trans_date = convert_local_to_utc(user_tz, str_trans_date)
        voucher_trans_status_obj = http.request.env['weha.voucher.trans.status']
        
        values.update({'batch_id': batch_id})
        values.update({'trans_date': trans_date})
        values.update({'receipt_number': receipt_number})
        values.update({'t_id': t_id})
        values.update({'cashier_id': cashier_id})
        values.update({'store_id': store_id})
        values.update({'member_id': member_id})
        values.update({'voucher_ean': voucher_eans})
        values.update({'process_type': process_type})
        if process_type == 'activated':
            if void == '0':
                values.update({'void': False})
            else:
                values.update({'void': True})
                
        #Create Voucher Transaction Status
        result = voucher_trans_status_obj.sudo().create(values)    
        if result:
            if process_type == 'reserved':
                add_data = result.get_json()
                if not add_data['err']:
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
                                'min_card_payment': add_data['min_card_payment'],
                                'max_vchr_count': add_data['voucher_count_limit'],
                            }
                        ]
                    }
                else:
                    data = {
                        "err": True,
                        "message": add_data['message'],
                        "data": []
                    }
            if process_type == 'used':
                #err, message = result.send_used_notification_to_trust()
                err, message = result.send_used_notification_to_trust_partial()
                if not err:
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
                else:
                     data = {
                        "err": True,
                        "message": message,
                        "data": []
                    }        

            if process_type == 'activated':
                if batch_id:
                    err, message = result.send_to_trust_by_batch_id()
                    if not err:
                        result.trans_close()
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
                    else:
                        data = {
                            "err": True,
                            "message": message,
                            "data": []
                        }
                else:
                    _logger.info("Not Batch - Activated")
                    add_data = result.get_json()
                    if not add_data['err']:
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
                    else:
                        data = {
                            "err": True,
                            "message": add_data['message'],
                            "data": []
                        }
            if process_type == 'reopen':
                data = {
                    "err": False,
                    "message": "Process Successfully",
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
