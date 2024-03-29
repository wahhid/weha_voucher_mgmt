# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from datetime import datetime, timedelta, date
from odoo.exceptions import ValidationError, UserError, Warning
import logging

_logger = logging.getLogger(__name__)

class WehaWizardScanVoucherReturn(models.TransientModel):
    _name = "weha.wizard.scan.voucher.return"

    @api.onchange('start_number')
    def _onchange_voucher_start_number(self):     
        if self.start_number and len(self.start_number) == 13:    
            domain = [
                ('voucher_ean','=', self.start_number),
                ('state','=','open')
            ]
            voucher_id  = self.env['weha.voucher.order.line'].search(domain,limit=1)
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
                    ('voucher_promo_id', '=', voucher_id.voucher_promo_id.id),
                    ('state','=','open')
                ]
            else:
                domain = [
                    ('operating_unit_id','=', voucher_id.operating_unit_id.id),
                    ('voucher_code_id','=', voucher_id.voucher_code_id.id),
                    ('year_id','=', voucher_id.year_id.id),
                    ('state','=','open')
                ]
            
            voucher_order_line_ids = self.env['weha.voucher.order.line'].search(domain)
            self.estimate_total = len(voucher_order_line_ids)
            self.is_valid = True
        
    @api.onchange('end_number')
    def _onchange_voucher_end_number(self):
        if self.end_number and len(self.start_number) == 13:    
            domain = [
                ('voucher_ean','=', self.end_number),
                ('state','=','open')
            ]
            voucher_id = self.env['weha.voucher.order.line'].search(domain, limit=1)
            if not voucher_id:
                self.end_number = ''
                raise Warning('Voucher in end number not found')    
            
            if self.operating_unit_id.id != voucher_id.operating_unit_id.id and \
                self.voucher_code_id.id != voucher_id.voucher_code_id.id and \
                self.year_id.id != voucher_id.year_id.id and \
                self.voucher_promo_id.id != voucher_id.voucher_promo_id.id:
                self.end_number = False
                raise Validation('Voucher not match')
        
        #Generate Wizard Voucher Return Line
            
    
    voucher_return_id = fields.Many2one('weha.voucher.return', 'Voucher Return #')
    operating_unit_id = fields.Many2one('operating.unit', 'Operating Unit', required=False, readonly=True)
    voucher_code_id = fields.Many2one('weha.voucher.code', 'Voucher Code', required=False, readonly=True)
    year_id = fields.Many2one('weha.voucher.year','Year', required=False, readonly=True)
    voucher_promo_id = fields.Many2one('weha.voucher.promo', 'Promo', required=False, readonly=True)
    start_number = fields.Char("Start Number", size=13, required=True)
    end_number = fields.Char("End Number", size=13, required=True)
    is_valid = fields.Boolean("Valid", default=False)
    is_checked = fields.Boolean("Checked", default=False)
    estimate_count = fields.Integer("Estimate Count", readonly=True)
    estimate_total = fields.Integer("Current Stock", readonly=True)
    scan_voucher_return_line_ids = fields.One2many('weha.wizard.scan.voucher.return.line','wizard_scan_voucher_return_id')

    def confirm(self):
        voucher_return_id = self.voucher_return_id

         #Clear Voucher Allocate Line
        for voucher_return_line_id in voucher_return_id.voucher_return_line_ids:
            voucher_return_line_id.unlink()

        for scan_voucher_return_line_id in self.scan_voucher_return_line_ids:
            if scan_voucher_return_line_id.state == 'available':
                vals = {
                    'voucher_return_id': voucher_return_id.id,
                    'voucher_order_line_id': scan_voucher_return_line_id.voucher_order_line_id.id
                }
                self.env['weha.voucher.return.line'].create(vals)

    def process(self):
        
        #Get Current Voucher Order return
        active_id = self.env.context.get('active_id') or False
        voucher_return_id = self.env['weha.voucher.return'].browse(active_id)

        #Clear Voucher return Line
        for voucher_return_line_id in voucher_return_id.voucher_return_line_ids:
            voucher_return_line_id.unlink()
            
        #Get Voucher Check Number
        domain = [
            ('voucher_ean','=', self.start_number),
        ]
        voucher_order_line_start_id  = self.env['weha.voucher.order.line'].search(domain, limit=1)
        start_check_number = voucher_order_line_start_id.check_number        
        
        #Get Voucher Check Number
        domain = [
            ('voucher_ean','=', self.end_number),
        ]
        voucher_order_line_end_id  = self.env['weha.voucher.order.line'].search(domain, limit=1)
        end_check_number = voucher_order_line_end_id.check_number

        #Set Voucher Order return Data
        voucher_return_id.voucher_code_id = voucher_order_line_start_id.voucher_code_id.id
        voucher_return_id.year_id = voucher_order_line_start_id.year_id.id 
        voucher_return_id.voucher_promo_id = voucher_order_line_start_id.voucher_promo_id.id 
        voucher_return_id.start_number = start_check_number
        voucher_return_id.end_number = end_check_number
        
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
                ('state','=','open'),
                #('check_number', 'in', tuple(voucher_ranges))
                ('voucher_12_digit', '>=', voucher_order_line_start_id.voucher_12_digit),
                ('voucher_12_digit', '<=', voucher_order_line_end_id.voucher_12_digit),
            ]
        else:
            domain = [
                ('operating_unit_id','=', voucher_order_line_start_id.operating_unit_id.id),
                ('voucher_code_id','=', voucher_order_line_start_id.voucher_code_id.id),
                ('year_id','=', voucher_order_line_start_id.year_id.id),
                ('state','=','open'),
                #('check_number', 'in', tuple(voucher_ranges))
                ('voucher_12_digit', '>=', voucher_order_line_start_id.voucher_12_digit),
                ('voucher_12_digit', '<=', voucher_order_line_end_id.voucher_12_digit),
            ]
        _logger.info(domain)

        voucher_order_line_ids = self.env['weha.voucher.order.line'].search(domain)
        _logger.info(voucher_order_line_ids)
        line_ids = []
        estimate_count = 0
        for voucher_order_line_id in voucher_order_line_ids:
            is_invalid = self.env['weha.voucher.return.line'].check_voucher_order_line(voucher_return_id.id, voucher_order_line_id.id)
            if not is_invalid:
                estimate_count = estimate_count + 1
                vals = (0,0, {
                    'voucher_order_line_id': voucher_order_line_id.id,
                    'state': 'available',
                })
                line_ids.append(vals)
                #self.env['weha.wizard.scan.voucher.return.line'].create(vals)
            else:
                vals = (0,0,{
                    'voucher_order_line_id': voucher_order_line_id.id,
                    'state': 'not_available',
                })
                line_ids.append(vals)
                #self.env['weha.wizard.scan.voucher.return.line'].create(vals)
        
        
        vals = {
            'voucher_return_id': voucher_return_id.id,
            'operating_unit_id':  voucher_order_line_start_id.operating_unit_id.id,
            'voucher_code_id': voucher_order_line_start_id.voucher_code_id.id,
            'year_id': voucher_order_line_start_id.year_id.id, 
            'voucher_promo_id': voucher_order_line_start_id.voucher_promo_id.id,
            'start_number': self.start_number,
            'end_number': self.end_number,
            'is_valid': self.is_valid,
            'is_checked': True,
            'estimate_total': len(voucher_ranges),
        }
        scan_voucher_return_id = self.env['weha.wizard.scan.voucher.return'].create(vals)
        scan_voucher_return_id.write({'estimate_count': estimate_count, 'scan_voucher_return_line_ids':line_ids})
        
        return {
            'name': 'Scan Voucher Return',
            'res_id': scan_voucher_return_id.id,
            'res_model': 'weha.wizard.scan.voucher.return',
            'target': 'new',
            'type': 'ir.actions.act_window',
            'view_id': self.env.ref('weha_voucher_mgmt.view_wizard_scan_voucer_return').id,
            'view_mode': 'form',
            'view_type': 'form',
        }
                       
class WehaWizardScanVoucherReturnLine(models.TransientModel):
    _name = 'weha.wizard.scan.voucher.return.line'
    _rec_name = "voucher_order_line_id"

    #name = fields.Char(string="Voucher")
    #date = fields.Date('Date', default=lambda self: fields.date.today())
    wizard_scan_voucher_return_id = fields.Many2one(comodel_name='weha.wizard.scan.voucher.return', string='Wizard Return')
    voucher_order_line_id = fields.Many2one(comodel_name='weha.voucher.order.line', string='Voucher Order Line')
    state = fields.Selection([('available','Available'),('not_available','Not Available')],'Status', readonly=True)

class WehaWizardReceivedReturn(models.TransientModel):
    _name = 'weha.wizard.received.return'
    _description = 'Wizard form for received voucher'

    def confirm(self):
        voucher_return_id = self.voucher_return_id

        for return_line_wizard_id in self.return_line_wizard_ids:
            voucher_return_line_id = return_line_wizard_id.voucher_return_line_id

            vals = {}
            vals.update({'state': 'received'})
            res = voucher_return_line_id.write(vals)

            company_id = self.env.user.company_id

            vals = {}   
            vals.update({'operating_unit_id': company_id.res_company_return_operating_unit.id})
            vals.update({'state': 'open'})
            voucher_return_line_id.voucher_order_line_id.write(vals)

            vals = {}
            vals.update({'name': voucher_return_id.number})
            vals.update({'voucher_order_line_id': voucher_return_line_id.voucher_order_line_id.id})
            vals.update({'trans_date': datetime.now()})
            vals.update({'operating_unit_loc_fr_id': voucher_return_id.operating_unit_id.id})
            vals.update({'operating_unit_loc_to_id': company_id.res_company_return_operating_unit.id})
            vals.update({'trans_type': 'RV'})
            self.env['weha.voucher.order.line.trans'].create(vals)

        if voucher_return_id.voucher_count == voucher_return_id.voucher_received_count:
            voucher_return_id.sudo().trans_received()
            voucher_return_id.sudo().trans_close()
        else:
            voucher_return_id.sudo().trans_received()

        # if voucher_return_line_id.voucher_return_id.voucher_count == voucher_return_line_id.voucher_return_id.voucher_received_count:
        #         voucher_return_line_id.voucher_return_id.sudo().trans_received()


    def process(self):
     
        #obj_order_line = self.env['weha.voucher.order.line'].search([('voucher_ean','=', self.code_ean)])
        #obj_return = self.env['weha.voucher.return'].browse(self.env.context.get('active_id'))

        active_id = self.env.context.get('active_id') or False
        voucher_return_id = self.env['weha.voucher.return'].browse(active_id)

        # stage_id = voucher_return_id.stage_id.next_stage_id
        # voucher_return_id.sudo().trans_confirm_received()

        # return_unit_to = voucher_return_id.user_id.default_operating_unit_id.company_id.res_company_request_operating_unit.id
        
        if self.scan_method == 'start_end':
            if self.start_ean and self.end_ean:
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
                if start_voucher.voucher_promo_id:
                    domain = [
                        ('voucher_type', '=', 'physical'),
                        ('voucher_code_id', '=', start_voucher.voucher_code_id.id),
                        ('operating_unit_id', '=', start_voucher.operating_unit_id.id),
                        ('year_id', '=', start_voucher.year_id.id),
                        ('voucher_promo_id', '=', start_voucher.voucher_promo_id.id),
                        ('state', '=', 'intransit'),
                        #('check_number','in', voucher_range)
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
                        #('check_number','in', voucher_range)
                        ('voucher_12_digit', '>=', start_voucher.voucher_12_digit),
                        ('voucher_12_digit', '<=', end_voucher.voucher_12_digit),
                    ]
                voucher_order_line_ids = self.env['weha.voucher.order.line'].search(domain)
                _logger.info("voucher_order_line_ids")
                _logger.info(voucher_order_line_ids)

                line_ids = []
                for voucher_order_line_id in voucher_order_line_ids:
                    domain = [
                        ('voucher_order_line_id','=', voucher_order_line_id.id)
                    ]
                    voucher_return_line_id = self.env['weha.voucher.return.line'].search(domain, limit=1)
                    if voucher_return_line_id:
                        _logger.info('valid')
                        line_id = (0,0,{
                            'voucher_order_line_id': voucher_order_line_id.id,
                            'voucher_return_line_id' : voucher_return_line_id.id, 
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
            
            line_ids = []
            
            domain = [
                ('voucher_return_id','=', voucher_return_id.id),
                ('voucher_order_line_id', '=', voucher_order_line_id.id),
                ('state', '=', 'open')
            ]
            voucher_return_line_id = self.env['weha.voucher.return.line'].search(domain, limit=1)
            if voucher_return_line_id:
                _logger.info('valid')
                line_id = (0,0,{
                    'voucher_order_line_id': voucher_order_line_id.id,
                    'voucher_return_line_id' : voucher_return_line_id.id, 
                    'state': 'valid',
                })
                line_ids.append(line_id)

        vals = {
            'voucher_return_id': voucher_return_id.id,
            'code_ean': self.code_ean,
            'start_ean': self.start_ean,
            'end_ean': self.end_ean,
            'scan_method': self.scan_method,
            'is_checked': True,
        }        
        _logger.info(line_ids)
        
        wizard_received_return_id = self.env['weha.wizard.received.return'].create(vals)
        wizard_received_return_id.write({'return_line_wizard_ids': line_ids})
        return {

            'name': 'Received Voucher Return',
            'res_id': wizard_received_return_id.id,
            'res_model': 'weha.wizard.received.return',
            'target': 'new',
            'type': 'ir.actions.act_window',
            'view_id': self.env.ref('weha_voucher_mgmt.view_wizard_received_return').id,
            'view_mode': 'form',
            'view_type': 'form',
        }
            

    #@api.onchange('code_ean')
    def _onchange_barcode_scan(self):
        voucher_rec = self.env['weha.voucher.order.line']
        if self.code_ean:
            code_ean = self.code_ean
            self.code_ean = False
            voucher = voucher_rec.search([('voucher_ean','=', self.code_ean)])
            
            wizard_return_line_obj = self.env['weha.wizard.received.return.line']
            _logger.info("wizard = " + str(voucher))
            _logger.info("wizard = " + str(voucher.name))

            if voucher.id:
                vals = {}
                vals.update({'name': voucher.name})
                vals.update({'wizard_return_id': self.id})
                vals.update({'voucher_order_line_id': voucher.id})
                wizard_return_line_obj.write(vals)
            else:
                raise Warning('No voucher is available for this code')
            
    voucher_return_id = fields.Many2one('weha.voucher.return','Voucher Return #')
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
    return_line_wizard_ids = fields.One2many(comodel_name='weha.wizard.received.return.line', inverse_name='wizard_received_return_id', string='Wizard Return Line')

class WehaWizardReceivedReturnLine(models.TransientModel):
    _name = 'weha.wizard.received.return.line'

    name = fields.Char(string="Voucher")
    date = fields.Date('Date', default=lambda self: fields.date.today())
    wizard_received_return_id = fields.Many2one(comodel_name='weha.wizard.received.return', string='Wizard Return')
    voucher_order_line_id = fields.Many2one(comodel_name='weha.voucher.order.line', string='Voucher Order Line')
    voucher_return_line_id = fields.Many2one(comodel_name='weha.voucher.return.line', string='Voucher Return Line')
    state = fields.Selection([('valid','Valid'),('not_valid','Not Valid')],'Status', readonly=True)

class WehaWizardReturndReceived(models.TransientModel):
    _name = 'weha.wizard.return.received'

    voucher_return_id = fields.Many2one('weha.voucher.return','Voucher Return #', default=lambda self: self._default_voucher_return_id(),)
    
class WehaWizardReturnCancelReceived(models.TransientModel):
    _name = 'weha.wizard.return.cancel.received'
    _description = 'Wizard Return Cancel Recevied'

    reason = fields.Html('Reason')

    def submit(self):
        active_id = self.env.context.get('active_id') or False
        voucher_return_id = self.env['weha.voucher.return'].browse(active_id)
        _logger.info(self.reason)
        voucher_return_id.message_post(body=self.reason)
        voucher_return_id.change_stage_to_intransit()