# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class WehaWizardReceivedRequest(models.TransientModel):
    _name = 'weha.wizard.received.request'
    _description = 'Wizard form for received voucher'

    # def trans_received(self):
    #
    #     obj_request = self.env['weha.voucher.request'].browse(self.env.context.get('active_id'))
    #
    #     obj_request.voucher_request_line_ids.
    #
    #         obj_order_line = self.env['weha.voucher.order.line'].search([('','=',)])
    #
    #         for rec in obj_order_line:
    #             vals = {}
    #             vals.update({'state': 'received'})
    #             obj_order_line.write(vals)
    #
    #             obj_order_line_trans = self.env['weha.voucher.order.line.trans']
    #
    #             vals = {}
    #             vals.update({'order_line_id': rec.id})
    #             vals.update({'trans_type': 'RC'})
    #             obj_order_line_trans.create(vals)

    code_ean = fields.Integer(string="Scan Code")