# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from datetime import datetime, timedelta, date
from odoo.exceptions import ValidationError, UserError, Warning
import logging

_logger = logging.getLogger(__name__)

class WizardScanVoucherScrap(models.TransientModel):
    _name = "weha.wizard.scan.voucher.scrap"



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
        
        #Get Current Voucher Order scrap
        active_id = self.env.context.get('active_id') or False
        voucher_scrap_id = self.env['weha.voucher.scrap'].browse(active_id)

        #Clear Voucher scrap Line
        for voucher_scrap_line_id in voucher_scrap_id.voucher_scrap_line_ids:
            voucher_scrap_line_id.unlink()
            
        #Get Voucher Check Number
        voucher_order_line_start_id  = self.env['weha.voucher.order.line'].search([('voucher_ean','=', self.start_number)], limit=1)
        start_check_number = voucher_order_line_start_id.check_number        
        
        #Get Voucher Check Number
        voucher_order_line_end_id  = self.env['weha.voucher.order.line'].search([('voucher_ean','=', self.end_number)], limit=1)
        end_check_number = voucher_order_line_end_id.check_number

        #Set Voucher Order scrap Data
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
                ('check_number', 'in', tuple(voucher_ranges))
            ]
        else:
            domain = [
                ('operating_unit_id','=', voucher_order_line_start_id.operating_unit_id.id),
                ('voucher_code_id','=', voucher_order_line_start_id.voucher_code_id.id),
                ('year_id','=', voucher_order_line_start_id.year_id.id),
                ('check_number', 'in', tuple(voucher_ranges))
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
           
        
class WehaWizardReceivedScrap(models.TransientModel):
    _name = 'weha.wizard.received.scrap'
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
        obj_scrap = self.env['weha.voucher.scrap'].browse(self.env.context.get('active_id'))

        active_id = self.env.context.get('active_id') or False
        voucher_scrap_id = self.env['weha.voucher.scrap'].browse(active_id)

        stage_id = voucher_scrap_id.stage_id.next_stage_id
        voucher_scrap_id.sudo().write({'stage_id': stage_id.id})
        

        if self.scan_method == 'all':
            for voucher_scrap_line_id in voucher_scrap_id.voucher_scrap_line_ids:
                vals = {}
                vals.update({'state': 'received'})
                res = voucher_scrap_line_id.sudo().write(vals)

                vals = {}
                vals.update({'operating_unit_id': voucher_scrap_id.source_operating_unit.id})
                vals.update({'state': 'open'})
                voucher_scrap_line_id.voucher_order_line_id.sudo().write(vals)

                vals = {}
                vals.update({'name': voucher_scrap_id.number})
                vals.update({'voucher_order_line_id': voucher_scrap_line_id.voucher_order_line_id.id})
                vals.update({'trans_date': datetime.now()})
                vals.update({'operating_unit_loc_fr_id': voucher_scrap_id.operating_unit_id.id})
                vals.update({'operating_unit_loc_to_id': voucher_scrap_id.source_operating_unit.id})
                vals.update({'trans_type': 'RV'})
                self.env['weha.voucher.order.line.trans'].sudo().create(vals)
        elif self.scan_method == 'start_end':
            if self.start_ean and self.end_ean:
                start_voucher = self.env['weha.voucher.order.line'].search[('voucher_ean','=', self.start_ean)]
                end_voucher = self.env['weha.voucher.order.line'].search[('voucher_ean','=', self.end_ean)]
                
                if start_voucher.voucher_code_id.id == end_voucher.voucher_code_id.id and \
                    start_voucher.year_id.id == end_voucher.year_id.id and \
                    start_voucher.voucher_promo_id.id == end_voucher.voucher_promo_id.id:
                    
                    voucher_range = tuple(range(start_voucher.check_number, end_voucher.check_number + 1))
                    if start_voucher.voucher_promo_id:
                        domain = [
                            ('voucher_order_id', '=', start_voucher.voucher_code_id.id),
                            ('year_id', '=', start_voucher.year_id.id),
                            ('voucher_promo_id', '=', start_voucher.voucher_promo_id.id),
                            ('check_number','in', voucher_range)
                        ]
                    else:
                        domain = [
                            ('voucher_order_id', '=', start_voucher.voucher_code_id.id),
                            ('year_id', '=', start_voucher.year_id.id),
                            ('check_number','in', voucher_range)
                        ]
                    voucher_order_line_ids = self.env['weha.voucher.order.line'].search(domain)
                    
                    for voucher_order_line_id in voucher_order_line_ids:
                        
                        voucher_scrap_line_id = self.env['weha.voucher.scrap.line'].search(['voucher_order_line_id','=', voucher_order_line_id.id], limit=1)
                        
                        if voucher_scrap_line_id:
                            vals = {}
                            vals.update({'state': 'received'})
                            res = voucher_scrap_line_id.write(vals)

                            vals = {}
                            vals.update({'operating_unit_id': voucher_scrap_id.source_operating_unit.id})
                            vals.update({'state': 'open'})
                            voucher_scrap_line_id.voucher_order_line_id.write(vals)

                            vals = {}
                            vals.update({'name': voucher_scrap_id.number})
                            vals.update({'voucher_order_line_id': voucher_scrap_line_id.voucher_order_line_id.id})
                            vals.update({'trans_date': datetime.now()})
                            vals.update({'operating_unit_loc_fr_id': voucher_scrap_id.operating_unit_id.id})
                            vals.update({'operating_unit_loc_to_id': voucher_scrap_id.source_operating_unit.id})
                            vals.update({'trans_type': 'RV'})
                            self.env['weha.voucher.order.line.trans'].create(vals)
        else:
            pass
            

    def trans_received_all(self):

        obj_scrap = self.env['weha.voucher.scrap'].browse(self.env.context.get('active_id'))
        obj_order_line = self.env['weha.voucher.order.line'].search([('voucher_scrap_id','=', res.id)])
        
        for rec in obj_order_line:
            vals = {}
            vals.update({'state': 'received'})
            res = obj_order_line.write(vals)

            obj_order_line_trans = self.env['weha.voucher.order.line.trans']

            vals = {}
            vals.update({'name': obj_scrap.number})
            vals.update({'voucher_order_line_id': rec.id})
            vals.update({'trans_date': datetime.now()})
            vals.update({'trans_type': 'RV'})
            obj_order_line_trans.create(vals)
    
    @api.onchange('code_ean')
    def _onchange_barcode_scan(self):
        voucher_rec = self.env['weha.voucher.order.line']
        if self.code_ean:
            code_ean = self.code_ean
            self.code_ean = False
            voucher = voucher_rec.search([('voucher_ean','=', self.code_ean)])
            
            wizard_scrap_line_obj = self.env['weha.wizard.received.scrap.line']
            _logger.info("wizard = " + str(voucher))
            _logger.info("wizard = " + str(voucher.name))

            if voucher.id:
                vals = {}
                vals.update({'name': voucher.name})
                vals.update({'wizard_scrap_id': self.id})
                vals.update({'voucher_order_line_id': voucher.id})
                wizard_scrap_line_obj.write(vals)
            else:
                raise Warning('No voucher is available for this code')
            
    
    code_ean = fields.Char(string="Scan Code")
    start_ean = fields.Char(string="Start Ean")
    end_ean = fields.Char(string="End Ean")
    scan_method = fields.Selection(
        [
            ('all','Receive All'),
            ('start_end','Scan Start and End Voucher'),
            ('one','Scan Each Voucher'),
        ],
        "Scan Method",
        default='all'
    )

    scrap_line_wizard_ids = fields.One2many(comodel_name='weha.wizard.received.scrap.line', inverse_name='wizard_scrap_id', string='Wizard scrap Line')


class WehaWizardReceivedScrapLine(models.TransientModel):
    _name = 'weha.wizard.received.scrap.line'


    name = fields.Char(string="Voucher")
    date = fields.Date('Date', default=lambda self: fields.date.today())
    wizard_scrap_id = fields.Many2one(comodel_name='weha.wizard.received.scrap', string='Wizard scrap')
    voucher_order_line_id = fields.Many2one(comodel_name='weha.voucher.order.line', string='Voucher Order Line')

class WehaWizardScrapdReceived(models.TransientModel):
    _name = 'weha.wizard.scrap.received'
    _inherit = ['multi.step.wizard.mixin']

    voucher_scrap_id = fields.Many2one('weha.voucher.scrap','Voucher scrap #', default=lambda self: self._default_voucher_scrap_id(),)
    