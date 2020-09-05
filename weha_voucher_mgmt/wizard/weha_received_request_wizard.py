# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
<<<<<<< HEAD
from datetime import datetime, timedelta, date
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)
=======
from odoo.exceptions import UserError

>>>>>>> wahyu

class WehaWizardReceivedRequest(models.TransientModel):
    _name = 'weha.wizard.received.request'
    _description = 'Wizard form for received voucher'

<<<<<<< HEAD
    def trans_received(self):

        obj_order_line = self.env['weha.voucher.order.line'].search([('voucher_ean','=', self.code_ean)])
        obj_request = self.env['weha.voucher.request'].browse(self.env.context.get('active_id'))
        _logger.info("obj_request ID = " + str(obj_request))
        _logger.info("obj_request IDs = " + str(obj_request.id))
        _logger.info("obj_request IDs = " + str(obj_request.number))
        
        for rec in obj_order_line:
            vals = {}
            vals.update({'state': 'activated'})
            res = obj_order_line.write(vals)

            obj_order_line_trans = self.env['weha.voucher.order.line.trans']

            vals = {}
            vals.update({'name': obj_request.number})
            vals.update({'voucher_order_line_id': rec.id})
            vals.update({'operating_unit_id': obj_request.operating_unit_id.id})
            vals.update({'trans_date': datetime.now()})
            vals.update({'trans_type': 'AC'})
            obj_order_line_trans.create(vals)

    def trans_received_all(self):

        obj_request = self.env['weha.voucher.request'].browse(self.env.context.get('active_id'))
        obj_order_line = self.env['weha.voucher.order.line'].search([('voucher_request_id','=', res.id)])
        
        for rec in obj_order_line:
            vals = {}
            vals.update({'state': 'activated'})
            res = obj_order_line.write(vals)

            obj_order_line_trans = self.env['weha.voucher.order.line.trans']

            vals = {}
            vals.update({'name': obj_request.number})
            vals.update({'voucher_order_line_id': rec.id})
            vals.update({'operating_unit_id': obj_request.operating_unit_id.id})
            vals.update({'trans_date': datetime.now()})
            vals.update({'trans_type': 'AC'})
            obj_order_line_trans.create(vals)

    code_ean = fields.Char(string="Scan Code")
=======
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
>>>>>>> wahyu
