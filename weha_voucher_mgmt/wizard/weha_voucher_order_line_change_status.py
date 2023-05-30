# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from datetime import datetime, timedelta, date
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class WehaWizardVoucherOrderLineChangeStatus(models.TransientModel):
    _name = 'weha.wizard.voucher.order.line.change.status'
    _description = 'Wizard form voucher change status'

    def change_status(self):
        active_id = self.env.context.get('active_id') or False
        if not active_id:
            raise ValidationError('No Active Data')

        voucher_order_line_id = self.env['weha.voucher.order.line'].browse(active_id)
        if  voucher_order_line_id.voucher_type == 'electronic':
            raise ValidationError('Cannot Change Status Electronic Voucher')

        if not  voucher_order_line_id:
            raise ValidationError('Voucher not found')

        if self.state == 'used':
            voucher_order_line_id.state = self.state
            voucher_order_line_id.create_order_line_trans(voucher_order_line_id.name, 'US', self.reason)
            
        if self.state == 'activated':
            voucher_order_line_id.state = self.state
            voucher_order_line_id.create_order_line_trans(voucher_order_line_id.name, 'AC', self.reason)

        if self.state == 'open':
            voucher_order_line_id.state = self.state
            voucher_order_line_id.create_order_line_trans(voucher_order_line_id.name, 'OP', self.reason)


        if self.state == 'reserved':
            voucher_order_line_id.state = self.state
            voucher_order_line_id.create_order_line_trans(voucher_order_line_id.name, 'RS', self.reason)

        if self.state == 'intransit':
            voucher_order_line_id.state = self.state
            voucher_order_line_id.create_order_line_trans(voucher_order_line_id.name, 'DV', self.reason)

    state = fields.Selection(
        string='Voucher Status',
        selection=[('open','Open'),('activated', 'Activated'), ('used', 'Used'),('reserved','Reserved'),('intransit','In-Transit')],
        required=True
    )
    
    reason = fields.Char("Reason", size=250, required=True)

  