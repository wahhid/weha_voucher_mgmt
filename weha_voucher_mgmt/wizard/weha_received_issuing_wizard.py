# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from datetime import datetime, timedelta, date
from odoo.exceptions import ValidationError, UserError, Warning
import logging

_logger = logging.getLogger(__name__)

class WizardScanVoucherIssuing(models.TransientModel):
    _name = "weha.wizard.scan.voucher.issuing"


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

                 
    operating_unit_id = fields.Many2one('operating.unit', 'Operating Unit', required=False, readonly=True)
    voucher_code_id = fields.Many2one('weha.voucher.code', 'Voucher Code', required=False, readonly=True)
    year_id = fields.Many2one('weha.voucher.year','Year', required=False, readonly=True)
    voucher_promo_id = fields.Many2one('weha.voucher.promo', 'Promo', required=False, readonly=True)
    start_number = fields.Char("Start Number", size=13, required=True)
    end_number = fields.Char("End Number", size=13, required=True)
    is_valid = fields.Boolean("Valid", default=False)
    is_checked = fields.Boolean("Is Checked", default=False)
    estimate_count = fields.Integer("Estimate Count", readonly=True)
    estimate_total = fields.Integer("Current Stock", readonly=True)
    voucher_issuing_id = fields.Many2one('weha.voucher.issuing', 'Voucher Issuing #')
    scan_voucher_issuing_line_ids = fields.One2many('weha.wizard.scan.voucher.issuing.line','scan_voucher_issuing_line_id','Lines')



    def confirm(self):        
        voucher_issuing_id = self.voucher_issuing_id

        #Clear Voucher Issuing Line
        for voucher_issuing_line_id in voucher_issuing_id.voucher_issuing_line_ids:
            voucher_issuing_line_id.unlink()

        for scan_voucher_issuing_line_id in self.scan_voucher_issuing_line_ids:
            if scan_voucher_issuing_line_id.state == 'available':
                vals = {
                    'voucher_issuing_id': voucher_issuing_id.id,
                    'voucher_order_line_id': scan_voucher_issuing_line_id.voucher_order_line_id.id
                }
                self.env['weha.voucher.issuing.line'].create(vals)

    def process(self):
        
        #Get Current Voucher Order issuing
        active_id = self.env.context.get('active_id') or False
        voucher_issuing_id = self.env['weha.voucher.issuing'].browse(active_id)

        #Clear Voucher issuing Line
        #for voucher_issuing_line_id in voucher_issuing_id.voucher_issuing_line_ids:
        #    voucher_issuing_line_id.unlink()
            
        #Get Voucher Check Number
        voucher_order_line_start_id  = self.env['weha.voucher.order.line'].search([('voucher_ean','=', self.start_number)], limit=1)
        start_check_number = voucher_order_line_start_id.check_number        
        
        #Get Voucher Check Number
        voucher_order_line_end_id  = self.env['weha.voucher.order.line'].search([('voucher_ean','=', self.end_number)], limit=1)
        end_check_number = voucher_order_line_end_id.check_number

        #Set Voucher Order issuing Data
        voucher_issuing_id.voucher_code_id = voucher_order_line_start_id.voucher_code_id.id
        voucher_issuing_id.year_id = voucher_order_line_start_id.year_id.id 
        voucher_issuing_id.voucher_promo_id = voucher_order_line_start_id.voucher_promo_id.id 
        voucher_issuing_id.start_number = start_check_number
        voucher_issuing_id.end_number = end_check_number
        
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
                #('check_number', 'in', tuple(voucher_ranges)),
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
            is_invalid = self.env['weha.voucher.issuing.line'].check_voucher_order_line(voucher_issuing_id.id, voucher_order_line_id.id)
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
            'voucher_issuing_id': voucher_issuing_id.id,
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
        scan_voucher_issuing_id = self.env['weha.wizard.scan.voucher.issuing'].create(vals)
        scan_voucher_issuing_id.write({'estimate_count': estimate_count, 'scan_voucher_issuing_line_ids':line_ids})
        return {

            'name': 'Scan Voucher Issuing',
            'res_id': scan_voucher_issuing_id.id,
            'res_model': 'weha.wizard.scan.voucher.issuing',
            'target': 'new',
            'type': 'ir.actions.act_window',
            'view_id': self.env.ref('weha_voucher_mgmt.view_wizard_scan_voucer_issuing').id,
            'view_mode': 'form',
            'view_type': 'form',
        }

class WizardScanVoucherIssuingLine(models.TransientModel):
    _name = "weha.wizard.scan.voucher.issuing.line"

    scan_voucher_issuing_line_id = fields.Many2one("weha.wizard.scan.issuing.scrap", 'Scan Voucher Issuing #')
    voucher_issuing_line_id = fields.Many2one('weha.voucher.issuing.line', 'Voucher Issuing Line #')
    voucher_order_line_id = fields.Many2one('weha.voucher.order.line', 'Voucher Order Line #')
    state = fields.Selection([('available','Available'),('allocated','Allocated')],'Status', readonly=True)
    



class WehaWizardReceivedIssuing(models.TransientModel):
    _name = 'weha.wizard.received.issuing'
    _description = 'Wizard form for received voucher'

    def trans_received(self):

     
        obj_order_line = self.env['weha.voucher.order.line'].search([('voucher_ean','=', self.code_ean)])
        obj_issuing = self.env['weha.voucher.issuing'].browse(self.env.context.get('active_id'))

        active_id = self.env.context.get('active_id') or False
        voucher_issuing_id = self.env['weha.voucher.issuing'].browse(active_id)

        stage_id = voucher_issuing_id.stage_id.next_stage_id
        voucher_issuing_id.sudo().write({'stage_id': stage_id.id})
        
        if self.scan_method == 'start_end':
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
                        
                        voucher_issuing_line_id = self.env['weha.voucher.issuing.line'].search(['voucher_order_line_id','=', voucher_order_line_id.id], limit=1)
                        
                        if voucher_issuing_line_id:
                            vals = {}
                            vals.update({'state': 'received'})
                            res = voucher_issuing_line_id.write(vals)

                            vals = {}
                            vals.update({'operating_unit_id': voucher_issuing_id.source_operating_unit.id})
                            vals.update({'state': 'open'})
                            voucher_issuing_line_id.voucher_order_line_id.write(vals)

                            vals = {}
                            vals.update({'name': voucher_issuing_id.number})
                            vals.update({'voucher_order_line_id': voucher_issuing_line_id.voucher_order_line_id.id})
                            vals.update({'trans_date': datetime.now()})
                            vals.update({'operating_unit_loc_fr_id': voucher_issuing_id.operating_unit_id.id})
                            vals.update({'operating_unit_loc_to_id': voucher_issuing_id.source_operating_unit.id})
                            vals.update({'trans_type': 'RV'})
                            self.env['weha.voucher.order.line.trans'].create(vals)
        else:
            pass
            

    def trans_received_all(self):

        obj_issuing = self.env['weha.voucher.issuing'].browse(self.env.context.get('active_id'))
        obj_order_line = self.env['weha.voucher.order.line'].search([('voucher_issuing_id','=', res.id)])
        
        for rec in obj_order_line:
            vals = {}
            vals.update({'state': 'received'})
            res = obj_order_line.write(vals)

            obj_order_line_trans = self.env['weha.voucher.order.line.trans']

            vals = {}
            vals.update({'name': obj_issuing.number})
            vals.update({'voucher_order_line_id': rec.id})
            vals.update({'trans_date': datetime.now()})
            vals.update({'trans_type': 'RV'})
            obj_order_line_trans.create(vals)
    
    #@api.onchange('code_ean')
    def _onchange_barcode_scan(self):
        voucher_rec = self.env['weha.voucher.order.line']
        if self.code_ean:
            code_ean = self.code_ean
            self.code_ean = False
            voucher = voucher_rec.search([('voucher_ean','=', self.code_ean)])
            
            wizard_issuing_line_obj = self.env['weha.wizard.received.issuing.line']
            _logger.info("wizard = " + str(voucher))
            _logger.info("wizard = " + str(voucher.name))

            if voucher.id:
                vals = {}
                vals.update({'name': voucher.name})
                vals.update({'wizard_issuing_id': self.id})
                vals.update({'voucher_order_line_id': voucher.id})
                wizard_issuing_line_obj.write(vals)
            else:
                raise Warning('No voucher is available for this code')
            
    voucher_issuing_id = fields.Many2one('weha.voucher.issuing', 'Voucher Issuing #')
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
    issuing_line_wizard_ids = fields.One2many(comodel_name='weha.wizard.received.issuing.line', inverse_name='wizard_issuing_id', string='Wizard issuing Line')


class WehaWizardReceivedIssuingLine(models.TransientModel):
    _name = 'weha.wizard.received.issuing.line'


    name = fields.Char(string="Voucher")
    
    date = fields.Date('Date', default=lambda self: fields.date.today())
    wizard_received_issuing_id = fields.Many2one(comodel_name='weha.wizard.received.issuing', string='Wizard Issuing')
    wizard_issuing_id = fields.Many2one(comodel_name='weha.wizard.received.issuing', string='Wizard issuing')
    voucher_order_line_id = fields.Many2one(comodel_name='weha.voucher.order.line', string='Voucher Order Line')
    state = fields.Selection([('valid','Valid'),('not_valid','Not Valid')],'Status', readonly=True)


class WehaWizardIssuingdReceived(models.TransientModel):
    _name = 'weha.wizard.issuing.received'

    voucher_issuing_id = fields.Many2one('weha.voucher.issuing','Voucher issuing #', default=lambda self: self._default_voucher_issuing_id(),)
