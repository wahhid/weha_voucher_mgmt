# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from datetime import datetime, timedelta, date
from odoo.exceptions import ValidationError, UserError, Warning
import logging

_logger = logging.getLogger(__name__)

class WizardScanVoucherAllocate(models.TransientModel):
    _name = "weha.wizard.scan.voucher.allocate"
        

    @api.onchange('start_number')
    def _onchange_start_number(self):     
        #Get Current Voucher Order Allocate
        if self.start_number and len(self.start_number) == 13:    
            active_id = self.env.context.get('active_id') or False
            voucher_allocate_id = self.env['weha.voucher.allocate'].browse(active_id)
                
            domain = [
                ('voucher_type','=','physical'),
                ('voucher_ean','=', self.start_number),
                ('voucher_code_id','=', voucher_allocate_id.voucher_code_id.id),
                ('operating_unit_id', '=', voucher_allocate_id.operating_unit_id.id),
                ('year_id','=',voucher_allocate_id.year_id.id),
                ('state','=', 'open'),
            ]
            
            _logger.info(f'Domain : {domain}')

            voucher_id  = self.env['weha.voucher.order.line'].search(domain,limit=1)
            if not voucher_id:
                self.start_number = False
                raise Warning('Voucher in start number not found')
            
            self.operating_unit_id = voucher_id.operating_unit_id.id
            self.voucher_code_id = voucher_id.voucher_code_id.id
            self.year_id = voucher_id.year_id.id
            self.start_check_number = voucher_id.check_number

            #Set Valid Transaction
            self.is_valid = True

    api.onchange('end_number')
    def _onchange_end_number(self):
        #Get Current Voucher Order Allocate
        active_id = self.env.context.get('active_id') or False
        voucher_allocate_id = self.env['weha.voucher.allocate'].browse(active_id)
        if self.end_number and len(self.end_number) == 13:   
            domain = [
                ('voucher_type','=','physical'),
                ('voucher_ean','=', self.end_number),
                ('voucher_code_id','=', voucher_allocate_id.voucher_code_id.id),
                ('operating_unit_id', '=', voucher_allocate_id.operating_unit_id.id),
                ('year_id','=',voucher_allocate_id.year_id.id),
                ('state','=', 'open'),
            ]
            
            voucher_id  = self.env['weha.voucher.order.line'].search(domain,limit=1)
            if not voucher_id:
                self.start_number = False
                raise Warning('Voucher in end number not found')
            
            self.end_check_number = voucher_id.check_number
            if self.end_check_number < self.start_check_number:
                raise Warning('End Number not valid')

    voucher_allocate_id = fields.Many2one('weha.voucher.allocate','Voucher Allocate #')
    operating_unit_id = fields.Many2one('operating.unit', 'Operating Unit', required=False, readonly=True)
    voucher_code_id = fields.Many2one('weha.voucher.code', 'Voucher Code', required=False, readonly=True)
    year_id = fields.Many2one('weha.voucher.year','Year', required=False, readonly=True)
    voucher_promo_id = fields.Many2one('weha.voucher.promo', 'Promo', required=False, readonly=True)
    start_number = fields.Char("Start Number", size=13, required=True)
    start_check_number = fields.Integer("Start Check Number")
    end_check_number = fields.Integer("End Check Number")
    end_number = fields.Char("End Number", size=13, required=True)
    is_valid = fields.Boolean("Valid", default=False)
    is_checked = fields.Boolean("Checked", default=False)
    is_legacy = fields.Boolean("Legacy", default=False)
    estimate_count = fields.Integer("Estimate Count", readonly=True)
    estimate_total = fields.Integer("Current Stock", readonly=True)
    scan_voucher_allocate_line_ids = fields.One2many('weha.wizard.scan.voucher.allocate.line','scan_voucher_allocate_line_id','Lines')
    
    def confirm(self):
        voucher_allocate_id = self.voucher_allocate_id

        #Create Allocate Ranges
        vals = {
            'voucher_allocate_id': voucher_allocate_id.id,
            'start_number': self.start_number,
            'end_number': self.end_number,
            'start_check_number': self.start_check_number,
            'end_check_number': self.end_check_number,
        }
        
        line_range_id = self.env['weha.voucher.allocate.range'].create(vals)

        #Clear Voucher Allocate Line
        #for voucher_allocate_line_id in voucher_allocate_id.voucher_allocate_line_ids:
        #    voucher_allocate_line_id.unlink()

        for scan_voucher_allocate_line_id in self.scan_voucher_allocate_line_ids:
            if scan_voucher_allocate_line_id.state == 'available':
                vals = {
                    'voucher_allocate_id': voucher_allocate_id.id,
                    'voucher_order_line_id': scan_voucher_allocate_line_id.voucher_order_line_id.id,
                    'voucher_allocate_range_id':line_range_id.id,
                    'voucher_promo_id': self.voucher_promo_id.id if self.voucher_promo_id  else False,
                }
                self.env['weha.voucher.allocate.line'].create(vals)
        
        
    def process(self):
        
        #Get Current Voucher Order Allocate
        active_id = self.env.context.get('active_id') or False
        voucher_allocate_id = self.env['weha.voucher.allocate'].browse(active_id)
            
        #Get Voucher Check Number
        domain  = [
            ('voucher_type','=','physical'),
            ('voucher_code_id','=', voucher_allocate_id.voucher_code_id.id),
            ('operating_unit_id', '=', voucher_allocate_id.operating_unit_id.id),
            ('voucher_ean','=', self.start_number),
            ('year_id','=', voucher_allocate_id.year_id.id),
            ('state','=','open')
        ]
        voucher_order_line_start_id  = self.env['weha.voucher.order.line'].search(domain, limit=1)
        start_check_number = voucher_order_line_start_id.check_number        
        
        #Get Voucher Check Number
        domain  = [
            ('voucher_type','=','physical'),
            ('voucher_code_id','=', voucher_allocate_id.voucher_code_id.id),
            ('operating_unit_id', '=', voucher_allocate_id.operating_unit_id.id),
            ('voucher_ean','=', self.end_number),
            ('year_id','=', voucher_allocate_id.year_id.id),
            ('state','=','open')
        ]
        
        voucher_order_line_end_id  = self.env['weha.voucher.order.line'].search(domain, limit=1)
        end_check_number = voucher_order_line_end_id.check_number

        #Check Legacy
        if voucher_order_line_start_id.is_legacy == True or voucher_order_line_end_id.is_legacy == True:
            if voucher_order_line_start_id.is_legacy != voucher_order_line_end_id.is_legacy:
                raise ValidationError("Start and End of voucher not match")         
        
        domain = [
            ('voucher_type','=','physical'),
            ('operating_unit_id','=', voucher_order_line_start_id.operating_unit_id.id),
            ('voucher_code_id','=', voucher_order_line_start_id.voucher_code_id.id),
            ('year_id','=', voucher_order_line_start_id.year_id.id),
            ('state', '=', 'open'),
            ('voucher_12_digit', '>=', voucher_order_line_start_id.voucher_12_digit),
            ('voucher_12_digit', '<=', voucher_order_line_end_id.voucher_12_digit),
        ]

        
        _logger.info(domain)

        voucher_order_line_ids = self.env['weha.voucher.order.line'].search(domain)
        _logger.info(voucher_order_line_ids)
        
        line_ids = []
                
        estimate_count = 0
        for voucher_order_line_id in voucher_order_line_ids:
            #Check Voucher Order Line at other Voucher Allocate
            is_invalid = self.env['weha.voucher.allocate.line'].check_voucher_order_line(voucher_allocate_id.id, voucher_order_line_id.id)
            if not is_invalid:
                _logger.info('Is Invalid')
                estimate_count = estimate_count + 1
                vals = (0,0,{'voucher_order_line_id': voucher_order_line_id.id, 'state': 'available'})
                line_ids.append(vals)
            else:
                _logger.info('Voucher Order Line was allocate in other transaction')
                vals = (0,0,{'voucher_order_line_id': voucher_order_line_id.id, 'state': 'allocated'})
                line_ids.append(vals)

        _logger.info(line_ids)

        vals = {
            'voucher_allocate_id': voucher_allocate_id.id,
            'operating_unit_id':  voucher_order_line_start_id.operating_unit_id.id,
            'voucher_code_id': voucher_order_line_start_id.voucher_code_id.id,
            'year_id': voucher_order_line_start_id.year_id.id, 
            #'voucher_promo_id': voucher_order_line_start_id.voucher_promo_id.id,
            'start_number': self.start_number,
            'end_number': self.end_number,
            'is_valid': self.is_valid,
            'is_checked': True,
            'estimate_total': len(line_ids),
        }
        scan_voucher_allocate_id = self.env['weha.wizard.scan.voucher.allocate'].create(vals)
        scan_voucher_allocate_id.write({'estimate_count': estimate_count, 'scan_voucher_allocate_line_ids':line_ids})
        return {

            'name': 'Scan Voucher Allocate',
            'res_id': scan_voucher_allocate_id.id,
            'res_model': 'weha.wizard.scan.voucher.allocate',
            'target': 'new',
            'type': 'ir.actions.act_window',
            'view_id': self.env.ref('weha_voucher_mgmt.view_wizard_scan_voucher_allocate').id,
            'view_mode': 'form',
            'view_type': 'form',
        }
        
class WizardScanVoucherAllocateLine(models.TransientModel):
    _name = "weha.wizard.scan.voucher.allocate.line"

    scan_voucher_allocate_line_id = fields.Many2one("weha.wizard.scan.voucher.allocate", 'Scan Voucher Allocate #')
    voucher_order_line_id = fields.Many2one('weha.voucher.order.line', 'Voucher Order Line #')
    state = fields.Selection([('available','Available'),('allocated','Allocated')],'Status', readonly=True)
    
class WehaWizardReceivedAllocate(models.TransientModel):
    _name = 'weha.wizard.received.allocate'
    _description = 'Wizard form for received voucher'

    def confirm(self):
        voucher_allocate_id = self.voucher_allocate_id
        for allocate_line_wizard_id in self.allocate_line_wizard_ids:
            voucher_allocate_line_id = allocate_line_wizard_id.voucher_allocate_line_id
            _logger.info(voucher_allocate_line_id)
            
            vals = {}
            vals.update({'state': 'received'})
            res = voucher_allocate_line_id.write(vals)

            vals = {}
            vals.update({'operating_unit_id': voucher_allocate_id.source_operating_unit.id})
            if voucher_allocate_id.is_voucher_promo:
                vals.update({'is_voucher_promo': True})
                vals.update({'voucher_promo_id': voucher_allocate_id.voucher_promo_id.id})
                vals.update({'expired_date':voucher_allocate_id.promo_expired_date})
            else:
                vals.update({'expired_days':voucher_allocate_id.expired_days})
                
            vals.update({'state': 'open'})
            voucher_allocate_line_id.voucher_order_line_id.sudo().write(vals)

            vals = {}
            vals.update({'name': voucher_allocate_id.number})
            vals.update({'voucher_order_line_id': voucher_allocate_line_id.voucher_order_line_id.id})
            vals.update({'trans_date': datetime.now()})
            vals.update({'operating_unit_loc_fr_id': voucher_allocate_id.operating_unit_id.id})
            vals.update({'operating_unit_loc_to_id': voucher_allocate_id.source_operating_unit.id})
            vals.update({'trans_type': 'RV'})
            self.env['weha.voucher.order.line.trans'].create(vals)
        
        if voucher_allocate_id.voucher_count == voucher_allocate_id.voucher_received_count:
            voucher_allocate_id.sudo().trans_received()
            voucher_allocate_id.sudo().trans_close()
        else:
            voucher_allocate_id.sudo().trans_received()


    def trans_received(self):

        active_id = self.env.context.get('active_id') or False
        voucher_allocate_id = self.env['weha.voucher.allocate'].browse(active_id)

        if self.scan_method == 'start_end':
            _logger.info(self.start_ean)
            _logger.info(self.end_ean)

            domain = [
                ('voucher_type', '=', 'physical'),
                ('voucher_ean', '=', self.start_ean),
                ('state', '=', 'intransit')
            ]
            _logger.info(domain)
            start_voucher = self.env['weha.voucher.order.line'].sudo().search(domain, limit=1)
            _logger.info(start_voucher)
            
            domain =  [
                ('voucher_type', '=', 'physical'),
                ('voucher_ean', '=',  self.end_ean),
                ('state', '=', 'intransit')
            ]

            _logger.info(domain)
            end_voucher = self.env['weha.voucher.order.line'].sudo().search(domain, limit=1)
            _logger.info(end_voucher)

            if start_voucher.operating_unit_id.id == end_voucher.operating_unit_id.id and \
                start_voucher.voucher_code_id.id == end_voucher.voucher_code_id.id and \
                start_voucher.year_id.id == end_voucher.year_id.id and \
                start_voucher.voucher_promo_id.id == end_voucher.voucher_promo_id.id:
                
                voucher_range = tuple(range(start_voucher.check_number, end_voucher.check_number + 1))
                _logger.info(voucher_range)
                
                if start_voucher.voucher_promo_id:
                    domain = [
                        ('voucher_type', '=', 'physical'),
                        ('voucher_code_id', '=', start_voucher.voucher_code_id.id),
                        ('operating_unit_id', '=', start_voucher.operating_unit_id.id),
                        ('year_id', '=', start_voucher.year_id.id),
                        ('voucher_promo_id', '=', start_voucher.voucher_promo_id.id),
                        ('state', '=', 'intransit'),
                        ('voucher_12_digit', '>=', start_voucher.voucher_12_digit),
                        ('voucher_12_digit', '<=', end_voucher.voucher_12_digit),

                    ]
                else:
                    domain = [
                        ('voucher_type', '=', 'physical'),
                        ('voucher_code_id', '=', start_voucher.voucher_code_id.id),
                        ('operating_unit_id', '=', start_voucher.operating_unit_id.id),
                        ('year_id', '=', start_voucher.year_id.id),
                        ('state', '=', 'intransit'),
                        ('voucher_12_digit', '>=', start_voucher.voucher_12_digit),
                        ('voucher_12_digit', '<=', end_voucher.voucher_12_digit),
                    ]
                
                _logger.info(domain)
                voucher_order_line_ids = self.env['weha.voucher.order.line'].sudo().search(domain)
                _logger.info(voucher_order_line_ids)
                line_ids = []
                for voucher_order_line_id in voucher_order_line_ids:
                    domain = [
                        ('voucher_allocate_id','=', voucher_allocate_id.id),
                        ('voucher_order_line_id','=', voucher_order_line_id.id)
                    ]
                    voucher_allocate_line_id = self.env['weha.voucher.allocate.line'].search(domain, limit=1)
                    if voucher_allocate_line_id:
                        _logger.info('valid')
                        line_id = (0,0,{
                            'voucher_order_line_id': voucher_order_line_id.id,
                            'voucher_allocate_line_id' : voucher_allocate_line_id.id, 
                            'state': 'valid',
                        })
                        line_ids.append(line_id)
            else:
                raise ValidationError("Voucher not match")           
        else:
            _logger.info('Manual Input')
            domain = [
                ('voucher_type', '=', 'physical'),
                ('voucher_ean','=', self.code_ean),
                ('state','=','intransit')
            ]

            voucher_order_line_id = self.env['weha.voucher.order.line'].sudo().search(domain,limit=1)
            if not voucher_order_line_id:
                raise ValidationError("Voucher not found")
            
            domain = [
                ('voucher_allocate_id','=', voucher_allocate_id.id),
                ('voucher_order_line_id', '=', voucher_order_line_id.id),
                ('state', '=', 'open')
            ]

            line_ids = []
            voucher_allocate_line_id = self.env['weha.voucher.allocate.line'].search(domain, limit=1)
            if voucher_allocate_line_id:
                    _logger.info('valid')
                    line_id = (0,0,{
                        'voucher_order_line_id': voucher_order_line_id.id,
                        'voucher_allocate_line_id' : voucher_allocate_line_id.id, 
                        'state': 'valid',
                    })
                    line_ids.append(line_id)

        vals = {
            'voucher_allocate_id': voucher_allocate_id.id,
            'code_ean': self.code_ean,
            'start_ean': self.start_ean,
            'end_ean': self.end_ean,
            'scan_method': self.scan_method,
            'is_checked': True,
        }        
        _logger.info(line_ids)
        
        wizard_received_allocate_id = self.env['weha.wizard.received.allocate'].create(vals)
        wizard_received_allocate_id.write({'allocate_line_wizard_ids': line_ids})
        return {

            'name': 'Received Voucher Allocate',
            'res_id': wizard_received_allocate_id.id,
            'res_model': 'weha.wizard.received.allocate',
            'target': 'new',
            'type': 'ir.actions.act_window',
            'view_id': self.env.ref('weha_voucher_mgmt.view_wizard_received_allocate').id,
            'view_mode': 'form',
            'view_type': 'form',
        }
        

    #Fields
    voucher_allocate_id = fields.Many2one('weha.voucher.allocate','Voucher Allocate #')
    code_ean = fields.Char(string="Scan Code")
    start_ean = fields.Char(string="Start Ean")
    end_ean = fields.Char(string="End Ean")
    scan_method = fields.Selection(
        [
            ('start_end','Scan Start and End Voucher'),
            ('one','Scan Each Voucher'),
        ],
        "Scan Method",
        default='start_end'
    )
    is_checked = fields.Boolean("Checked", default=False)

    allocate_line_wizard_ids = fields.One2many(comodel_name='weha.wizard.received.allocate.line', inverse_name='wizard_received_allocate_id', string='Wizard Allocate Line')

class WehaWizardReceivedAllocateLine(models.TransientModel):
    _name = 'weha.wizard.received.allocate.line'

    name = fields.Char(string="Voucher")
    date = fields.Date('Date', default=lambda self: fields.date.today())
    wizard_received_allocate_id = fields.Many2one(comodel_name='weha.wizard.received.allocate', string='Wizard Allocate')
    voucher_order_line_id = fields.Many2one(comodel_name='weha.voucher.order.line', string='Voucher Order Line')
    voucher_allocate_line_id = fields.Many2one(comodel_name='weha.voucher.allocate.line', string='Voucher Allocate Line')
    state = fields.Selection([('valid','Valid'),('not_valid','Not Valid')],'Status', readonly=True)

class WehaWizardAllocatedReceived(models.TransientModel):
    _name = 'weha.wizard.allocate.received'

    voucher_allocated_id = fields.Many2one('weha.voucher.allocate','Voucher Allocate #', default=lambda self: self._default_voucher_allocate_id(),)
    
