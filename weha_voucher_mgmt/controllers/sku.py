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


class VMSSkuController(http.Controller):
    
    @validate_token
    @http.route("/api/vms/v1.0/getsku", type="http", auth="none", methods=["POST"], csrf=False)
    def getsku(self, **post):
        mapping_sku_ids = http.request.env['weha.voucher.mapping.sku'].search([])
        if not mapping_sku_ids:
            data =  {
                "err": True,
                "message": "SKU not found",
                "data": []
            }
            return valid_response(data)

        skus = []
        for mapping_sku_id in mapping_sku_ids:
            vals =  {
                    'code_sku': mapping_sku_id.code_sku,
                    'voucher_code': mapping_sku_id.voucher_code_id.name,
                    'voucher_type': mapping_sku_id.voucher_code_id.voucher_type,
                    'voucher_amount': mapping_sku_id.voucher_code_id.voucher_amount,
            }
            domain = [
                ('voucher_mapping_sku_id','=',mapping_sku_id.id)
            ]
            promos = []
            voucher_promo_line_id = http.request.env['weha.voucher.promo.line'].search(domain, limit=1)
            if not voucher_promo_line_id:
                vals.update({'promos': promos})
            else:
                voucher_promo_id = voucher_promo_line_id.voucher_promo_id
                promos.append(
                    {
                        'id': voucher_promo_id.id,
                        'name': voucher_promo_id.name, 
                        'start_date': voucher_promo_id.start_date,
                        'end_date': voucher_promo_id.end_date,
                        'term': voucher_promo_id.term if voucher_promo_id.term else "",
                        'image': "http://vms-dev.server007.weha-id.com/web/image?model=weha.voucher.promo&id=" + str(voucher_promo_id.id) + "&field=image"
                    }
                )
                vals.update({'promos': promos})
            skus.append(vals)

        data = {
            "err": False,
            "message": "",
            "data": skus
        }
        return valid_response(data)