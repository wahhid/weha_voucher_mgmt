# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from datetime import datetime, timedelta, date
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class WehaWizardFindVoucherOrderLine(models.TransientModel):
    _name = 'weha.wizard.find.voucher.order.line'
    _description = 'Wizard form for find voucher'

    def find_voucher(self):
        voucher_order_line_id = self.env['weha.voucher.order.line'].sudo().search([('voucher_ean', '=', self.code_ean)], limit=1)
        _logger.info(voucher_order_line_id)
        return {
            'name': "Find Voucher",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'weha.voucher.order.line',
            'res_id': voucher_order_line_id.id,
            'view_id': self.env.ref('weha_voucher_mgmt.view_weha_voucher_order_line_form').id,
            'target': 'new',
            'flags':{ 'mode' :'readonly'},
            'context':{"bypass": True}
        }
        
   
    code_ean = fields.Char(string="Scan Code")

  