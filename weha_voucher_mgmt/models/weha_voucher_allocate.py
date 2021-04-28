from odoo import models, fields, api,  _ 
from odoo.exceptions import UserError, ValidationError, Warning
from datetime import datetime, timedelta, date
from dateutil.relativedelta import *
import logging
from random import randrange

_logger = logging.getLogger(__name__)


class VoucherAllocate(models.Model):
    _name = 'weha.voucher.allocate'
    _description = 'Voucher Allocate'
    _rec_name = 'number'
    _order = 'number desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.depends('stage_id')
    def _compute_current_stage(self):
        for rec in self:
            if rec.stage_id.unattended:
                rec.current_stage = 'unattended'
            if rec.stage_id.approval:
                rec.current_stage = 'approval'
            if rec.stage_id.opened:
                rec.current_stage = 'open'
            if rec.stage_id.progress:
                rec.current_stage = 'progress'
            if rec.stage_id.receiving:
                rec.current_stage = 'receiving'
            if rec.stage_id.closed:
                rec.current_stage = 'closed'
            if rec.stage_id.cancelled:
                rec.current_stage = 'cancelled'
            if rec.stage_id.rejected:
                rec.current_stage = 'rejected'
     
    def _get_default_stage_id(self):
        return self.env['weha.voucher.allocate.stage'].search([], limit=1).id
    
    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        stage_ids = self.env['weha.voucher.allocate.stage'].search([])
        return stage_ids
    
    @api.depends('voucher_allocate_line_ids')
    def _calculate_voucher_count(self):
        self.voucher_count = len(self.voucher_allocate_line_ids)
    
    @api.depends('voucher_allocate_line_ids')
    def _calculate_voucher_received(self):
        count = 0
        for voucher_allocate_line_id in self.voucher_allocate_line_ids:
            if voucher_allocate_line_id.state == 'received':
                count += 1
        self.voucher_received_count = count

    def send_notification(self, data):
        self.env['mail.activity'].create(data).action_feedback()
        
    @api.onchange('voucher_type')
    def _voucher_code_onchange(self):
        res = {}
        res['domain']={'voucher_code_id':[('voucher_type', '=', self.voucher_type)]}
        return res

    @api.onchange('voucher_code_id')
    def _voucher_code_id_onchange(self):
        _logger.info('Voucher Code Onchange')
        self.expired_days = self.voucher_code_id.voucher_terms_id.number_of_days
        _logger.info(self.expired_days)
    
    @api.onchange('voucher_promo_id')
    def _voucher_promo_id_onchange(self):
        if self.voucher_promo_id:
            self.is_voucher_promo = True
            self.promo_expired_date = self.voucher_promo_id.end_date
        else:
            self.is_voucher_promo = False
            self.promo_expired_date = False

    def trans_delivery(self):
        stage_id = self.stage_id.next_stage_id
        res = super(VoucherAllocate, self).write({'stage_id': stage_id.id})
        for row in self.voucher_allocate_line_ids:
            row.voucher_order_line_id.write({'state':'intransit'})
            row.voucher_order_line_id.create_order_line_trans(self.number, 'DV')

        for requester_user_id in self.source_operating_unit.requester_user_ids:
            data =  {
                'activity_type_id': 4,
                'note': 'Voucher Allocate was delivered',
                'res_id': self.id,
                'res_model_id': self.env.ref('weha_voucher_mgmt.model_weha_voucher_allocate').id,
                'user_id': requester_user_id.id,
                'date_deadline': datetime.now() + timedelta(days=2),
                'summary': 'Voucher Allocate was delivered'
            }
            self.send_notification(data)

    def trans_confirm_received(self):
        stage_id = self.stage_id.next_stage_id
        res = super(VoucherAllocate, self).write({'stage_id': stage_id.id})
        
    def trans_received(self):
        if not self.stage_id.receiving:
            stage_id = self.stage_id.next_stage_id
            res = super(VoucherAllocate, self).write({'stage_id': stage_id.id})
            data =  {
                'activity_type_id': 4,
                'note': 'Voucher Allocate was received',
                'res_id': self.id,
                'res_model_id': self.env.ref('weha_voucher_mgmt.model_weha_voucher_allocate').id,
                'user_id': self.user_id.id,
                'date_deadline': datetime.now() + timedelta(days=2),
                'summary': 'Voucher Allocate was received'
            }
            self.send_notification(data)
        

    def trans_approve(self):
        stage_id = self.stage_id.next_stage_id
        res = super(VoucherAllocate, self).write({'stage_id': stage_id.id})
        for requester_user_id in self.operating_unit_id.requester_user_ids:
            data =  {
                'activity_type_id': 4,
                'note': 'Voucher Allocate was approved',
                'res_id': self.id,
                'res_model_id': self.env.ref('weha_voucher_mgmt.model_weha_voucher_allocate').id,
                'user_id': requester_user_id.id,
                'date_deadline': datetime.now() + timedelta(days=2),
                'summary': 'Voucher Allocate was approved'
            }
            self.send_notification(data)
        for approval_user_id in self.source_operating_unit.approval_user_ids:
            data =  {
                'activity_type_id': 4,
                'note': 'Voucher Allocate was approved',
                'res_id': self.id,
                'res_model_id': self.env.ref('weha_voucher_mgmt.model_weha_voucher_allocate').id,
                'user_id': approval_user_id.id,
                'date_deadline': datetime.now() + timedelta(days=2),
                'summary': 'Voucher Allocate was approved'
            }
            self.send_notification(data)
    
    def trans_reject(self):
        stage_id = self.env['weha.voucher.allocate.stage'].search([('rejected','=', True)], limit=1)
        if not stage_id:
            raise ValidationError('Stage Rejected not found')
        super(VoucherAllocate, self).write({'stage_id': stage_id.id})
        data =  {
            'activity_type_id': 4,
            'note': 'Voucher Allocate was rejected',
            'res_id': self.id,
            'res_model_id': self.env.ref('weha_voucher_mgmt.model_weha_voucher_allocate').id,
            'user_id': self.user_id.id,
            'date_deadline': datetime.now() + timedelta(days=2),
            'summary': 'Voucher Allocate was rejected'
        }
        self.send_notification(data)
    
    def trans_cancelled(self):
        received = False        
        for voucher_allocate_line_id in self.voucher_allocate_line_ids:
            if voucher_allocate_line_id.state == 'open':
                vals = {}
                vals.update({'state': 'cancelled'})
                res = voucher_allocate_line_id.write(vals)

                vals = {}
                vals.update({'operating_unit_id': self.operating_unit_id.id})
                vals.update({'state': 'open'})
                voucher_allocate_line_id.voucher_order_line_id.write(vals)

                vals = {}
                vals.update({'name': self.number})
                vals.update({'voucher_order_line_id': voucher_allocate_line_id.voucher_order_line_id.id})
                vals.update({'trans_date': datetime.now()})
                vals.update({'operating_unit_loc_fr_id': self.source_operating_unit.id})
                vals.update({'operating_unit_loc_to_id': self.operating_unit_id.id})
                vals.update({'trans_type': 'CL'})
                self.env['weha.voucher.order.line.trans'].create(vals)
            
            if voucher_allocate_line_id.state == 'received':
                received = True

        stage_id = self.env['weha.voucher.allocate.stage'].search([('cancelled','=', True)], limit=1)
        
        if not stage_id:
            raise ValidationError('Stage Cancelled not found')
        
        if not received:
            super(VoucherAllocate, self).write({'stage_id': stage_id.id})
            self.message_post(body="Cancel voucher allocated")
        else:
            stage_id = self.env['weha.voucher.allocate.stage'].search([('closed','=', True)], limit=1)
            super(VoucherAllocate, self).write({'stage_id': stage_id.id, 'is_force_cancelled': True})
            #self.is_force_cancelled = True
            self.message_post(body="Cannot cancel all voucher, There are voucher was received, Please close voucher return and cancel voucher return by managers")
            #raise Warning("Cannot cancel all voucher, There are voucher was received ,  Please close voucher return and cancel voucher return by managers")
            return {
		        'warning': {'title': "Warning", 'message': "Cannot cancel all voucher, There are voucher was received, Please close voucher return and cancel voucher return by managers"},
		    }

    def trans_force_cancelled_approval(self):
        self.is_force_cancelled = True
        
    def trans_force_cancelled(self):
        if self.current_stage == 'closed':
            for voucher_allocate_line_id in self.voucher_allocate_line_ids:
                if voucher_allocate_line_id.voucher_order_line_id.state in ['open','activated']:
                    vals = {}
                    vals.update({'state': 'cancelled'})
                    res = voucher_allocate_line_id.write(vals)

                    vals = {}
                    vals.update({'operating_unit_id': self.operating_unit_id.id})
                    vals.update({'state': 'open'})
                    voucher_allocate_line_id.voucher_order_line_id.write(vals)

                    vals = {}
                    vals.update({'name': self.number})
                    vals.update({'voucher_order_line_id': voucher_allocate_line_id.voucher_order_line_id.id})
                    vals.update({'trans_date': datetime.now()})
                    vals.update({'operating_unit_loc_fr_id': self.source_operating_unit.id})
                    vals.update({'operating_unit_loc_to_id': self.operating_unit_id.id})
                    vals.update({'trans_type': 'CL'})
                    self.env['weha.voucher.order.line.trans'].create(vals)

            stage_id = self.env['weha.voucher.allocate.stage'].search([('cancelled','=', True)], limit=1)
            if not stage_id:
                raise ValidationError('Stage Cancelled not found')
            super(VoucherAllocate, self).write({'stage_id': stage_id.id})

    def trans_force_cancelled_reject(self):
        self.is_force_cancelled = False
    
    def trans_close(self):
        if self.voucher_count != self.voucher_received_count:
            raise ValidationError("Receiving not completed")
        stage_id = self.stage_id.next_stage_id
        if not self.env.user.has_group('weha_voucher_mgmt.group_voucher_finance_user'):
            res = super(VoucherAllocate, self).sudo().write({'stage_id': stage_id.id})
        else:
            res = super(VoucherAllocate, self).write({'stage_id': stage_id.id})

        
    def trans_allocate_approval(self):    
        if len(self.voucher_allocate_line_ids) == 0:
            raise ValidationError("No Voucher Allocated")
        #if self.is_request:
        #    if self.voucher_count !=  self.voucher_request_qty:
        #        raise ValidationError("Number of vouchers not match")

        stage_id = self.stage_id.next_stage_id
        res = super(VoucherAllocate, self).write({'stage_id': stage_id.id})
        for approval_user_id in  self.operating_unit_id.approval_user_ids:
            _logger.info(approval_user_id.name)
            data =  {
                'activity_type_id': 4,
                'note': 'Request Voucher Allocate for Approval',
                'res_id': self.id,
                'res_model_id': self.env.ref('weha_voucher_mgmt.model_weha_voucher_allocate').id,
                'user_id': approval_user_id.id,
                'date_deadline': datetime.now() + timedelta(days=2),
                'summary': 'Request Voucher Allocate for Approval'
            }
            self.send_notification(data)

    
    company_id = fields.Many2one('res.company', 'Company')
    number = fields.Char(string='Allocate Number', default="/",readonly=True)
    ref = fields.Char(string='Source Document', required=True)
    allocate_date = fields.Date('Allocate Date', required=True, default=lambda self: fields.date.today(), readonly=True)
    user_id = fields.Many2one('res.users', string='Requester', default=lambda self: self.env.user and self.env.user.id or False, readonly=True)  
    operating_unit_id = fields.Many2one('operating.unit','Store', related="user_id.default_operating_unit_id")
    source_operating_unit = fields.Many2one('operating.unit','Request Store', required=True)
    is_request = fields.Boolean('Is Request', default=False)

    voucher_type = fields.Selection(
        string='Voucher Type',
        selection=[('physical', 'Physical'), ('electronic', 'Electronic')],
        default='physical'
    )

    voucher_code_id = fields.Many2one('weha.voucher.code', 'Voucher Code', required=True, readonly=False)
    voucher_terms_id = fields.Many2one('weha.voucher.terms', 'Voucher Terms', related="voucher_code_id.voucher_terms_id")
    year_id = fields.Many2one('weha.voucher.year','Year', required=True, readonly=False)
    
    voucher_promo_id = fields.Many2one('weha.voucher.promo', 'Promo', readonly=False)
    is_voucher_promo = fields.Boolean('Is Voucher Promo', default=False)
    promo_expired_date = fields.Date('Promo Expired Date')
    expired_days =fields.Integer('Expired Days', default=0, required=True)

    start_number = fields.Integer(string='Start Number', required=False, readonly=True)
    end_number = fields.Integer(string='End Number', required=False, readonly=True)
    
    stage_id = fields.Many2one(
        'weha.voucher.allocate.stage',
        string='Stage',
        group_expand='_read_group_stage_ids',
        default=_get_default_stage_id,
        track_visibility='onchange',
    )

    current_stage = fields.Char(string='Current Stage', size=50, compute="_compute_current_stage", readonly=True)
    priority = fields.Selection(selection=[
        ('0', _('Low')),
        ('1', _('Medium')),
        ('2', _('High')),
        ('3', _('Very High')),
    ], string='Priority', default='1')

    color = fields.Integer(string='Color Index')
    kanban_state = fields.Selection([
        ('normal', 'Default'),
        ('done', 'Ready for next stage'),
        ('blocked', 'Blocked')], string='Kanban State')

    voucher_allocate_line_ids = fields.One2many(
        comodel_name='weha.voucher.allocate.line', 
        inverse_name='voucher_allocate_id', 
        string='Allocate Lines',
        domain="[('state','=','open')]"
    )
    
    voucher_allocate_range_ids = fields.One2many(
        comodel_name='weha.voucher.allocate.range', 
        inverse_name='voucher_allocate_id', 
        string='Allocate Ranges',
        domain="[('state','=','open')]"
    )

    voucher_allocate_line_received_ids = fields.One2many(
        comodel_name='weha.voucher.allocate.line', 
        inverse_name='voucher_allocate_id', 
        string='Received Lines',
        domain="[('state','=','received')]"
    )

    voucher_request_id = fields.Many2one('weha.voucher.request', 'Voucher Request', required=False)
    voucher_request_qty = fields.Integer(string='Quantity Ordered From Request', readonly=True)
    voucher_count = fields.Integer('Voucher Count', compute="_calculate_voucher_count", store=False)
    voucher_received_count = fields.Integer('Voucher Received', compute="_calculate_voucher_received", store=False)

    is_force_cancelled = fields.Boolean('Force Cancelled', default=False)

    @api.model
    def create(self, vals):
        if 'voucher_promo_id' in vals.keys() and vals.get('voucher_promo_id'):
            pass 
        else:
            if vals.get('expired_days') == 0:
                raise ValidationError('Expired Days must be greater than zero!')

        if vals.get('number', '/') == '/':
            seq = self.env['ir.sequence']
            if 'company_id' in vals:
                seq = seq.with_context(force_company=vals['company_id'])
            vals['number'] = seq.next_by_code(
                'weha.voucher.allocate.sequence') or '/'
        res = super(VoucherAllocate, self).create(vals)

        # Check if mail to the user has to be sent
        #if vals.get('user_id') and res:
        #    res.send_user_mail()
        return res    
    
    def write(self, vals):
        if 'expired_days' in vals.keys() and vals.get('expired_days') == 0:
            raise ValidationError('Expired Days must be greater than zero!')
        
        if 'stage_id' in vals:
            # stage_obj = self.env['weha.voucher.allocate.stage'].browse([vals['stage_id']])        
            if self.stage_id.approval:
                raise ValidationError("Please using approve or reject button")
            if self.stage_id.opened:
                raise ValidationError("Please Click Delivery Button")
            if self.stage_id.progress:
                raise ValidationError("Please Click Receive Button")
            if self.stage_id.closed:
                raise ValidationError("Can not move, status Closed")
            if self.stage_id.cancelled:
                raise ValidationError("Can not move, status Cancel")
            if self.stage_id.rejected:
                raise ValidationError("Can not Move, status reject")
           
        res = super(VoucherAllocate, self).write(vals)
        return res
