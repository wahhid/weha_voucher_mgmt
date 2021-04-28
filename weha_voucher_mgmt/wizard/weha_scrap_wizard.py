# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from datetime import datetime, timedelta, date
from odoo.exceptions import ValidationError, UserError, Warning
import logging

_logger = logging.getLogger(__name__)

class WizardScanVoucherScrap(models.TransientModel):
    _name = "weha.wizard.scan.voucher.scrap"


    # @api.model
    # def default_get(self, fields):
    #     res = super(WizardScanVoucherAllocate, self).default_get(fields)
    #     active_id = self.env.context.get('active_id') or False
    #     if active_id:
    #         voucher_allocate_id = self.env['weha.voucher.allocate'].browse(active_id)
    #         if voucher_allocate_id.voucher_promo_id:
    #             domain = [
    #                 ('voucher_code_id','=', voucher_allocate_id.voucher_code_id.id),
    #                 ('year_id','=', voucher_allocate_id.year_id.id),
    #                 ('voucher_promo_id', '=', voucher_allocate_id.voucher_promo_id.id)
    #             ]
    #         else:
    #             domain = [
    #                 ('voucher_code_id','=', voucher_allocate_id.voucher_code_id.id),
    #                 ('year_id','=', voucher_allocate_id.year_id.id),
    #             ]
    #         voucher_order_line_ids = self.env['weha.voucher.order.line'].search(domain)

    #         res.update({'voucher_code_id':  voucher_allocate_id.voucher_code_id.id})
    #         res.update({'year_id':  voucher_allocate_id.year_id.id})
    #         res.update({'voucher_promo_id':  voucher_allocate_id.voucher_promo_id.id})
    #         res.update({'estimate_total': len(voucher_order_line_ids)})
    #     return res

    @api.onchange('start_number', 'end_number')
    def _onchange_voucher(self):     
        if self.start_number:     
            voucher_id  = self.env['weha.voucher.order.line'].search([('voucher_ean','=', self.start_number)],limit=1)
            if not voucher_id:
                self.start_number = False
                raise Warning('Voucher in start number not found')
            
            self.operating_unit_id = voucher_id.operating_unit_id.id
            self.voucher_code_id = voucher_id.voucher_code_id.id
            self.year_id = voucher_id.year_id.id
            self.voucher_promo_id =  voucher_id.voucher_promo_id.id
            
            if self.voucher_promo_id:
                domain = [
                    ('operating_unit_id','=', voucher_id.operating_unit_id.id),
                    ('voucher_code_id','=', voucher_id.voucher_code_id.id),
                    ('year_id','=', voucher_id.year_id.id),
                    ('voucher_promo_id', '=', voucher_id.voucher_promo_id.id)
                ]
            else:
                domain = [
                    ('operating_unit_id','=', voucher_id.operating_unit_id.id),
                    ('voucher_code_id','=', voucher_id.voucher_code_id.id),
                    ('year_id','=', voucher_id.year_id.id),
                ]
            
            voucher_order_line_ids = self.env['weha.voucher.order.line'].search(domain)
            self.estimate_total = len(voucher_order_line_ids)
            self.is_valid = True

        if self.end_number:     
            voucher_id = self.env['weha.voucher.order.line'].search([('voucher_ean','=', self.end_number)], limit=1)
            if not voucher_id:
                self.end_number = ''
                raise Warning('Voucher in end number not found')    
            
            if self.operating_unit_id.id != voucher_id.operating_unit_id.id and \
                self.voucher_code_id.id != voucher_id.voucher_code_id.id and \
                self.year_id.id != voucher_id.year_id.id and \
                self.voucher_promo_id.id != voucher_id.voucher_promo_id.id:
                self.end_number = False
                raise Validation('Voucher not match')
            

        #if self.start_number and self.end_number:
        #    voucher_range
        
        
    operating_unit_id = fields.Many2one('operating.unit', 'Operating Unit', required=False, readonly=True)
    voucher_code_id = fields.Many2one('weha.voucher.code', 'Voucher Code', required=False, readonly=True)
    year_id = fields.Many2one('weha.voucher.year','Year', required=False, readonly=True)
    voucher_promo_id = fields.Many2one('weha.voucher.promo', 'Promo', required=False, readonly=True)
    start_number = fields.Char("Start Number", size=13, required=True)
    end_number = fields.Char("End Number", size=13, required=True)
    is_valid = fields.Boolean("Valid", default=False)
    estimate_count = fields.Integer("Estimate Count", readonly=True)
    estimate_total = fields.Integer("Current Stock", readonly=True)

    def process(self):
        
        #Get Current Voucher Order Allocate
        active_id = self.env.context.get('active_id') or False
        voucher_scrap_id = self.env['weha.voucher.scrap'].browse(active_id)

        #Clear Voucher Allocate Line
        #for voucher_scrap_line_id in voucher_scrap_id.voucher_scrap_line_ids:
        #    voucher_scrap_line_id.unlink()
            
        #Get Voucher Check Number
        voucher_order_line_start_id  = self.env['weha.voucher.order.line'].search([('voucher_ean','=', self.start_number)], limit=1)
        start_check_number = voucher_order_line_start_id.check_number        
        
        #Get Voucher Check Number
        voucher_order_line_end_id  = self.env['weha.voucher.order.line'].search([('voucher_ean','=', self.end_number)], limit=1)
        end_check_number = voucher_order_line_end_id.check_number

        #Set Voucher Order Allocate Data
        voucher_scrap_id.voucher_code_id = voucher_order_line_start_id.voucher_code_id.id
        voucher_scrap_id.year_id = voucher_order_line_start_id.year_id.id 
        voucher_scrap_id.voucher_promo_id = voucher_order_line_start_id.voucher_promo_id.id 
        voucher_scrap_id.start_number = start_check_number
        voucher_scrap_id.end_number = end_check_number
        
        #Get Voucher Range
        voucher_ranges = range(start_check_number, end_check_number + 1)
        _logger.info(voucher_ranges)  

        #Get Vouchers
        if voucher_order_line_start_id.voucher_promo_id:
            domain = [
                ('operating_unit_id','=', voucher_order_line_start_id.operating_unit_id.id),
                ('voucher_code_id','=', voucher_order_line_start_id.voucher_code_id.id),
                ('year_id','=', voucher_order_line_start_id.year_id.id),
                ('voucher_promo_id', '=', voucher_order_line_start_id.voucher_promo_id.id),
                #('check_number', 'in', tuple(voucher_ranges))
                ('voucher_12_digit', '>=', voucher_order_line_start_id.voucher_12_digit),
                ('voucher_12_digit', '<=', voucher_order_line_end_id.voucher_12_digit),
            ]
        else:
            domain = [
                ('operating_unit_id','=', voucher_order_line_start_id.operating_unit_id.id),
                ('voucher_code_id','=', voucher_order_line_start_id.voucher_code_id.id),
                ('year_id','=', voucher_order_line_start_id.year_id.id),
                #('check_number', 'in', tuple(voucher_ranges))
                ('voucher_12_digit', '>=', voucher_order_line_start_id.voucher_12_digit),
                ('voucher_12_digit', '<=', voucher_order_line_end_id.voucher_12_digit),
            ]
        _logger.info(domain)

        voucher_order_line_ids = self.env['weha.voucher.order.line'].search(domain)
        _logger.info(voucher_order_line_ids)

        for voucher_order_line_id in voucher_order_line_ids:
            vals = {
                'voucher_scrap_id': active_id,
                'voucher_order_line_id': voucher_order_line_id.id
            }
            self.env['weha.voucher.scrap.line'].create(vals)