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
        voucher_order_id = self.voucher_order_id
        for order_line_wizard_id in self.order_line_wizard_ids:
            voucher_order_line_id = order_line_wizard_id.voucher_order_line_id
            vals = {}
            vals.update({'state': 'open'})
            voucher_order_line_id.write(vals)

            vals = {}
            vals.update({'name': voucher_order_id.number})
            vals.update({'voucher_order_line_id': voucher_order_line_id.id})
            vals.update({'trans_date': datetime.now()})
            vals.update({'trans_type': 'RV'})
            self.env['weha.voucher.order.line.trans'].create(vals)

        voucher_order_id.trans_received()


    def process(self):

        active_id = self.env.context.get('active_id') or False
        voucher_order_id = self.env['weha.voucher.order'].browse(active_id)

        if self.scan_method == 'start_end':
            _logger.info(self.start_ean)
            _logger.info(self.end_ean)

            domain = [
                ('voucher_type', '=', 'physical'),
                ('voucher_ean', '=', self.start_ean),
                #('state', '=', 'inorder')
            ]
            _logger.info(domain)
            start_voucher = self.env['weha.voucher.order.line'].sudo().search(domain, limit=1)
            _logger.info(start_voucher)
            
            domain =  [
                ('voucher_type', '=', 'physical'),
                ('voucher_ean', '=',  self.end_ean),
                #('state', '=', 'inorder')
            ]

            _logger.info(domain)
            end_voucher = self.env['weha.voucher.order.line'].sudo().search(domain, limit=1)
            _logger.info(end_voucher)

            if start_voucher.check_number > end_voucher.check_number:
                raise ValidationError("Please Check Start Number and End Number")

            if start_voucher.operating_unit_id.id == end_voucher.operating_unit_id.id and \
                start_voucher.voucher_code_id.id == end_voucher.voucher_code_id.id and \
                start_voucher.year_id.id == end_voucher.year_id.id:
                
                voucher_range = tuple(range(start_voucher.check_number, end_voucher.check_number + 1))
                _logger.info(voucher_range)
                  
                domain = [
                    ('voucher_type', '=', 'physical'),
                    ('voucher_code_id', '=', start_voucher.voucher_code_id.id),
                    ('operating_unit_id', '=', start_voucher.operating_unit_id.id),
                    ('year_id', '=', start_voucher.year_id.id),
                    ('check_number','in', voucher_range)
                ]
                
                _logger.info(domain)
                voucher_order_line_ids = self.env['weha.voucher.order.line'].sudo().search(domain)
                _logger.info(voucher_order_line_ids)
                line_ids = []
                for voucher_order_line_id in voucher_order_line_ids:
                    if voucher_order_line_id.state == 'inorder':
                        line_id = (0,0,{
                                'voucher_order_line_id': voucher_order_line_id.id,
                                'state': 'valid',
                            })
                        line_ids.append(line_id)
                    else:
                        line_id = (0,0,{
                                'voucher_order_line_id': voucher_order_line_id.id,
                                'state': 'not_valid',
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
            'voucher_order_id': voucher_order_id.id,
            'code_ean': self.code_ean,
            'start_ean': self.start_ean,
            'end_ean': self.end_ean,
            'scan_method': self.scan_method,
            'is_checked': True,
        }        
        _logger.info(line_ids)
        
        wizard_received_order_id = self.env['weha.wizard.received.order'].create(vals)
        wizard_received_order_id.write({'order_line_wizard_ids': line_ids})
        return {

            'name': 'Received Voucher Order',
            'res_id': wizard_received_order_id.id,
            'res_model': 'weha.wizard.received.order',
            'target': 'new',
            'type': 'ir.actions.act_window',
            'view_id': self.env.ref('weha_voucher_mgmt.view_wizard_received_order').id,
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
    wizard_received_order_id = fields.Many2one(comodel_name='weha.wizard.received.order', string='Wizard Order')
    voucher_order_line_id = fields.Many2one(comodel_name='weha.voucher.order.line', string='Voucher Order Line')
    state = fields.Selection([('valid','Valid'),('not_valid','Not Valid')],'Status', readonly=True)
