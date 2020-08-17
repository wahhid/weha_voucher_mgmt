# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from datetime import datetime, timedelta, date
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class WehaWizardReceivedAllocate(models.TransientModel):
    _name = 'weha.wizard.received.allocate'
    _description = 'Wizard form for received voucher'

    def trans_received(self):

        obj_order_line = self.env['weha.voucher.order.line'].search([('voucher_ean','=', self.code_ean)])
        obj_allocate = self.env['weha.voucher.allocate'].browse(self.env.context.get('active_id'))
        _logger.info("obj_allocate ID = " + str(obj_allocate))
        _logger.info("obj_allocate IDs = " + str(obj_allocate.id))
        _logger.info("obj_allocate IDs = " + str(obj_allocate.number))
        
        for rec in obj_order_line:
            vals = {}
            vals.update({'state': 'received'})
            res = obj_order_line.write(vals)

            obj_order_line_trans = self.env['weha.voucher.order.line.trans']

            vals = {}
            vals.update({'name': obj_allocate.number})
            vals.update({'voucher_order_line_id': rec.id})
            vals.update({'trans_date': datetime.now()})
            vals.update({'trans_type': 'RV'})
            obj_order_line_trans.create(vals)

    def trans_received_all(self):

        obj_allocate = self.env['weha.voucher.allocate'].browse(self.env.context.get('active_id'))
        obj_order_line = self.env['weha.voucher.order.line'].search([('voucher_allocate_id','=', res.id)])
        
        for rec in obj_order_line:
            vals = {}
            vals.update({'state': 'received'})
            res = obj_order_line.write(vals)

            obj_order_line_trans = self.env['weha.voucher.order.line.trans']

            vals = {}
            vals.update({'name': obj_allocate.number})
            vals.update({'voucher_order_line_id': rec.id})
            vals.update({'trans_date': datetime.now()})
            vals.update({'trans_type': 'RV'})
            obj_order_line_trans.create(vals)

    code_ean = fields.Char(string="Scan Code")