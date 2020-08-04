# -*- coding: utf-8 -*-
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo import models, fields, api


class SelectOrderLines(models.TransientModel):

    _name = 'weha.select.order.line.wizard'
    _description = 'Select Voucher Line'

    start_number = fields.Integer(string='Start Number')
    end_number = fields.Integer(string='End Number')
    line_ids = fields.Many2many('weha.voucher.order.line', string='Voucher Lines')
    flag_order = fields.Char('Flag Order')

    def select_order_line(self):
    
        voucher_request_id = self.env['weha.voucher.request'].browse(self._context.get('active_id', False))
        vals = {}
        vals.update({'voucher_request_id': voucher_request_id.id})
        self.line_ids.write(vals)

        # elif self.flag_order == 'po':
        #     order_id = self.env['purchase.order'].browse(self._context.get('active_id', False))
        #     for product in self.product_ids:
        #         self.env['purchase.order.line'].create({
        #             'product_id': product.id,
        #             'name': product.name,
        #             'date_planned': order_id.date_planned or datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
        #             'product_uom': product.uom_id.id,
        #             'price_unit': product.lst_price,
        #             'product_qty': 1.0,
        #             'display_type': False,
        #             'order_id': order_id.id
        #         })