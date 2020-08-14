"""Part of odoo. See LICENSE file for full copyright and licensing details."""
import re
import ast
import functools
import logging
import json
from odoo.exceptions import AccessError


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
    def vspurchase(self, **post):
        _logger.info(post)
        return json.dumps({'err': False, 'msg': 'VS Purchase Successfully', 'datas':[]})
    
    @validate_token
    @http.route("/api/vms/v1.0/bankpurchase", type="http", auth="none", methods=["POST"], csrf=False)
    def bankpurchase(self, **payload):
        return {'err': False, 'msg': 'Bank Purchase Successfully', 'datas':[]}
    
    @validate_token
    @http.route("/api/vms/v1.0/custredeem", type="http", auth="none", methods=["POST"], csrf=False)
    def custredeem(self, **payload):
        return {'err': False, 'msg': 'Redeem Successfully', 'datas':[]}
    
    @validate_token
    @http.route("/api/vms/v1.0/vspayment", type="http", auth="none", methods=["POST"], csrf=False)
    def vspayment(self, **payload):
        return {'err': False, 'msg': 'VS Payment Succesfully', 'datas':[]}
    
    @validate_token
    @http.route("/api/vms/v1.0/bankpayment", type="http", auth="none", methods=["POST"], csrf=False)
    def bankpayment(self, **payload):
        return {'err': False, 'msg': 'Bank Payment Successfully', 'datas':[]}
    
    
    