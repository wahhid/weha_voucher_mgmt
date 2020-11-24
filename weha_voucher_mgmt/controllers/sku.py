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
                    'voucher_code': mapping_sku_id.voucher_code_id.name
                }
            skus.append(vals)

        data = {
            "err": False,
            "message": "",
            "data": skus
        }
        return valid_response(data)