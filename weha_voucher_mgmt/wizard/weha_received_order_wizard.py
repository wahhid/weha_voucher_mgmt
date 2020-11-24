# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from datetime import datetime, timedelta, date
from odoo.exceptions import ValidationError, UserError, Warning
import logging

_logger = logging.getLogger(__name__)

class WehaWizardReceivedOrder(models.TransientModel):
    _name = 'weha.wizard.received.order'
    _description = 'Wizard form for received voucher'

    @api.onchange('start_ean')
    def onchange_start_ean(self):
        pass
            

    @api.onchange('end_ean')
    def onchange_end_ean(self):
        pass 

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
            vals.update({'state': 'open'})
            voucher_allocate_line_id.voucher_order_line_id.write(vals)

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


    def process(self):

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
                        ('check_number','in', voucher_range)
                    ]
                else:
                    domain = [
                        ('voucher_type', '=', 'physical'),
                        ('voucher_code_id', '=', start_voucher.voucher_code_id.id),
                        ('operating_unit_id', '=', start_voucher.operating_unit_id.id),
                        ('year_id', '=', start_voucher.year_id.id),
                        ('state', '=', 'intransit'),
                        ('check_number','in', voucher_range)
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
    voucher_order_id = fields.Many2one('weha.voucher.order','Voucher order #')
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
    wizard_step = fields.Selection([
        ('receiving','Receiving'),
        ('processed','Processed'),
        ('confirm','Confirm')
    ])
    is_checked = fields.Boolean("Checked", default=False)
    order_line_wizard_ids = fields.One2many(comodel_name='weha.wizard.received.order.line', inverse_name='wizard_received_order_id', string='Wizard Allocate Line')

class WehaWizardReceivedOrderLine(models.TransientModel):
    _name = 'weha.wizard.received.order.line'

    name = fields.Char(string="Voucher")
    date = fields.Date('Date', default=lambda self: fields.date.today())
    wizard_received_order_id = fields.Many2one(comodel_name='weha.wizard.received.allocate', string='Wizard Order')
    voucher_order_line_id = fields.Many2one(comodel_name='weha.voucher.order.line', string='Voucher Order Line')
    state = fields.Selection([('valid','Valid'),('not_valid','Not Valid')],'Status', readonly=True)
