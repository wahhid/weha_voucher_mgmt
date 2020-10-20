from odoo import models, fields, api,  _ 
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta, date
from dateutil.relativedelta import *
import logging
from random import randrange

_logger = logging.getLogger(__name__)


class VoucherAllocate(models.Model):
    _name = 'weha.voucher.allocate'
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
        stage_id = self.stage_id.next_stage_id
        res = super(VoucherAllocate, self).write({'stage_id': stage_id.id})
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
        stage_id = self.env['weha.voucher.allocate.stage'].search([('cancelled','=', True)], limit=1)
        if not stage_id:
            raise ValidationError('Stage Cancelled not found')
        super(VoucherAllocate, self).write({'stage_id': stage_id.id})

    def trans_close(self):
        if self.voucher_count != self.voucher_received_count:
            raise ValidationError("Receiving not completed")
        stage_id = self.stage_id.next_stage_id
        res = super(VoucherAllocate, self).write({'stage_id': stage_id.id})
        return res
        
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
    allocate_date = fields.Date('Allocate Date', required=False, default=lambda self: fields.date.today(), readonly=True)
    user_id = fields.Many2one('res.users', string='Requester', default=lambda self: self.env.user and self.env.user.id or False, readonly=True)  
    operating_unit_id = fields.Many2one('operating.unit','Store', related="user_id.default_operating_unit_id")
    source_operating_unit = fields.Many2one('operating.unit','Source Store', required=True)
    is_request = fields.Boolean('Is Request', default=False)

    voucher_type = fields.Selection(
        string='Voucher Type',
        selection=[('physical', 'Physical'), ('electronic', 'Electronic')],
        default='physical'
    )


    voucher_terms_id = fields.Many2one('weha.voucher.terms', 'Voucher Terms', required=False, readonly=True)
    voucher_code_id = fields.Many2one('weha.voucher.code', 'Voucher Code', required=False, readonly=True)
    year_id = fields.Many2one('weha.voucher.year','Year', required=False, readonly=True)
    voucher_promo_id = fields.Many2one('weha.voucher.promo', 'Promo', required=False, readonly=True)
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

    voucher_allocate_line_received_ids = fields.One2many(
        comodel_name='weha.voucher.allocate.line', 
        inverse_name='voucher_allocate_id', 
        string='Received Lines',
        domain="[('state','=','received')]"
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

    @api.model
    def create(self, vals):
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
