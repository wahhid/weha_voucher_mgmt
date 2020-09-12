# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from datetime import datetime, timedelta, date
from odoo.exceptions import ValidationError, UserError, Warning
import logging

_logger = logging.getLogger(__name__)

class WizardScanVoucherAllocate(models.TransientModel):
    _name = "weha.wizard.scan.voucher.allocate"


    @api.onchange('start_number', 'end_number')
    def _onchange_voucher(self):     
        if self.start_number:     
            voucher_ids  = self.env['weha.voucher.order.line'].search([('voucher_ean','=', self.start_number)])
            if not voucher_ids:
                self.start_number = ''
                raise Warning('Voucher in start number not found')

        if self.end_number:     
            voucher_ids  = self.env['weha.voucher.order.line'].search([('voucher_ean','=', self.end_number)])
            if not voucher_ids:
                self.end_number = ''
                raise Warning('Voucher in end number not found')    

        if self.start_number and self.end_number:
            self.estimate_count = 10
        
        

    start_number = fields.Char("Start Number", size=13, required=True)
    end_number = fields.Char("End Number", size=13, required=True)
    estimate_count = fields.Integer("Estimate Count", readonly=True)

    def process(self):
        voucher_id  = self.env['weha.voucher.order.line'].search([('voucher_ean','=', self.start_number)], limit=1)
        start_check_number = voucher_id.check_number        
        voucher_id  = self.env['weha.voucher.order.line'].search([('voucher_ean','=', self.end_number)], limit=1)
        end_check_number = voucher_id.check_number
        voucher_ranges = range(start_check_number, end_check_number)
        _logger.info(voucher_ranges)  



class WehaWizardReceivedAllocate(models.TransientModel):
    _name = 'weha.wizard.received.allocate'
    _description = 'Wizard form for received voucher'

    # @api.onchange('code_ean')
    # def code_ean_scanning(self):
    #     match = False
    #     voucher_order_line_obj = self.env['weha.voucher.order.line']
    #     voucher_order_line_id = voucher_order_line_obj.search([('voucher_ean','=', self.code_ean)])
    #     if self.code_ean and not voucher_order_line_id:
    #         raise Warning('No voucher is available for this code')
        
        # if self.code_ean and not match:
        #     if voucher_order_line_id:
        #         raise Warning('This product is not available in the order.'
        #                       'You can add this product by clicking the "Add an item" and scan')

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
    
    @api.onchange('code_ean')
    def _onchange_barcode_scan(self):
        voucher_rec = self.env['weha.voucher.order.line']
        if self.code_ean:
            voucher = voucher_rec.search([('voucher_ean','=', self.code_ean)])
            wizard_allocate_line_obj = self.env['weha.wizard.received.allocate.line']
            _logger.info("wizard = " + str(voucher))
            _logger.info("wizard = " + str(voucher.name))

            if voucher.id:
                vals = {}
                vals.update({'name': voucher.name})
                vals.update({'wizard_allocate_id': self.id})
                vals.update({'voucher_order_line_id': voucher.id})
                wizard_allocate_line_obj.write(vals)
            else:
                raise Warning('No voucher is available for this code')
            
    code_ean = fields.Char(string="Scan Code")
    allocate_line_wizard_ids = fields.One2many(comodel_name='weha.wizard.received.allocate.line', inverse_name='wizard_allocate_id', string='Wizard Allocate Line')


class WehaWizardReceivedAllocateLine(models.TransientModel):
    _name = 'weha.wizard.received.allocate.line'


    name = fields.Char(string="Voucher")
    date = fields.Date('Date', default=lambda self: fields.date.today())
    wizard_allocate_id = fields.Many2one(comodel_name='weha.wizard.received.allocate', string='Wizard Allocate')
    voucher_order_line_id = fields.Many2one(comodel_name='weha.voucher.order.line', string='Voucher Order Line')