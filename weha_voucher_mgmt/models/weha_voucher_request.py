from odoo import models, fields, api,  _ 
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta, date
from dateutil.relativedelta import *
import logging

_logger = logging.getLogger(__name__)

class WeheVoucherRequest(models.Model):
    _name = 'weha.voucher.request'
    _rec_name = 'number'
    _order = 'number desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        stage_ids = self.env['weha.voucher.request.stage'].search([])
        return stage_ids

    def _get_default_stage_id(self):
        return self.env['weha.voucher.request.stage'].search([], limit=1).id

    @api.depends('stage_id')
    def _compute_current_stage(self):
        for rec in self:
            if rec.stage_id.unattended:
                rec.current_stage = 'unattended'
            if rec.stage_id.approval:
                rec.current_stage = 'approval'
            if rec.stage_id.opened:
                rec.current_stage = 'open'
            if rec.stage_id.closed:
                rec.current_stage = 'closed'
            if rec.stage_id.cancelled:
                rec.current_stage = 'cancelled'
            if rec.stage_id.rejected:
                rec.current_stage = 'rejected'
                
    def _calculate_voucher_count(self):
        voucher_count = 0
        for row in self:
            for line_id in self.line_ids:
                voucher_count += line_id.voucher_qty
        self.voucher_count = voucher_count
    
    def send_notification(self, data):
        self.env['mail.activity'].create(data).action_feedback()

    def send_l1_request_mail(self):
        for rec in self:
            template = self.env.ref('weha_voucher_mgmt.voucher_request_l1_approval_notification_template', raise_if_not_found=False)
            template.send_mail(rec.id)

    def create_allocate_from_request(self, request_line):
        obj_allocate = self.env['weha.voucher.allocate']
        vals = {}
        vals.update({'source_operating_unit': self.operating_unit_id.id})
        vals.update({'ref': self.number})
        vals.update({'is_request': True})
        vals.update({'voucher_request_id': self.id})
        vals.update({'voucher_request_qty': request_line.voucher_qty})
        vals.update({'voucher_code_id': request_line.voucher_code_id.id})
        vals.update({'voucher_terms_id': request_line.voucher_code_id.voucher_terms_id.id})
        #vals.update({'year_id': request_line.voucher_code_id.year_id.id})
        res = obj_allocate.sudo().create(vals)
        _logger.info("str_ean ID = " + str(res))

        return res
    
    def action_voucher_allocate_from_request(self):
        for request_line in self.voucher_request_line_ids:
            res = self.create_allocate_from_request(request_line)
            if not res:
                raise ValidationError("Can not create allocate from request")

    def trans_approve(self):
        approval_level = self.stage_id.approval_level
        stage_id = self.stage_id.next_stage_id
        res = super(WeheVoucherRequest, self).write({'stage_id': stage_id.id})
        #Create Schedule Activity
        #To Requester
        operating_unit_id = self.operating_unit_id
        for requester_user_id in operating_unit_id.requester_user_ids:
            _logger.info(requester_user_id.name)
            self.env['mail.activity'].create({
                'activity_type_id': 4,
                'note': 'Voucher Request was approved',
                'res_id': self.id,
                'res_model_id': self.env.ref('weha_voucher_mgmt.model_weha_voucher_request').id,
                'user_id': requester_user_id.id,
                'date_deadline': datetime.now() + timedelta(days=2),
                'summary': 'Voucher Request was approved'
            }).action_feedback()
            #To Finance Manager
        company_id = self.env.user.company_id
        for approval_user_id in company_id.res_company_request_operating_unit.approval_user_ids:
            data =  {
                'activity_type_id': 4,
                'note': 'Voucher Request from ' + operating_unit_id.name,
                'res_id': self.id,
                'res_model_id': self.env.ref('weha_voucher_mgmt.model_weha_voucher_request').id,
                'user_id': approval_user_id.id,
                'date_deadline': datetime.now() + timedelta(days=2),
                'summary': 'Voucher Request from ' + operating_unit_id.name
            }
            self.send_notification(data)
        #To Finance User
        company_id = self.env.user.company_id
        for requester_user_id in company_id.res_company_request_operating_unit.requester_user_ids:
            data =  {
                'activity_type_id': 4,
                'note': 'Voucher Request from ' + operating_unit_id.name,
                'res_id': self.id,
                'res_model_id': self.env.ref('weha_voucher_mgmt.model_weha_voucher_request').id,
                'user_id': requester_user_id.id,
                'date_deadline': datetime.now() + timedelta(days=2),
                'summary': 'Voucher Request from ' + operating_unit_id.name
            }
            self.send_notification(data)

    def trans_approve_finance(self):
        stage_id = self.stage_id.next_stage_id
        res = super(WeheVoucherRequest, self).write({'stage_id': stage_id.id})
        self.action_voucher_allocate_from_request()
        #To Finance User
        company_id = self.env.user.company_id
        for requester_user_id in company_id.res_company_request_operating_unit.requester_user_ids:
            data =  {
                'activity_type_id': 4,
                'note': 'Voucher Request was approved',
                'res_id': self.id,
                'res_model_id': self.env.ref('weha_voucher_mgmt.model_weha_voucher_request').id,
                'user_id': requester_user_id.id,
                'date_deadline': datetime.now() + timedelta(days=2),
                'summary': 'Voucher Request was approved'
            }
            self.send_notification(data)
    
    def trans_receiving(self):
        _logger.info('Change Stage to Receiving')
        stage_id = self.stage_id.next_stage_id
        res = super(WeheVoucherRequest, self).write({'stage_id': stage_id.id})
        return res
    
    def trans_reject(self):
        stage_id = self.env['weha.voucher.request.stage'].search([('rejected','=', True)])
        res = super(WeheVoucherRequest, self).write({'stage_id': stage_id.id})
        #To Requester
        operating_unit_id = self.operating_unit_id
        for requester_user_id in operating_unit_id.requester_user_ids:
            _logger.info(requester_user_id.name)
            self.env['mail.activity'].create({
                'activity_type_id': 4,
                'note': 'Voucher Request was rejected',
                'res_id': self.id,
                'res_model_id': self.env.ref('weha_voucher_mgmt.model_weha_voucher_request').id,
                'user_id': requester_user_id.id,
                'date_deadline': datetime.now() + timedelta(days=2),
                'summary': 'Voucher Request was rejected'
            }).action_feedback()

    def trans_request_approval(self):
        stage_id = self.stage_id.next_stage_id
        res = super(WeheVoucherRequest, self).write({'stage_id': stage_id.id})
        operating_unit_id = self.operating_unit_id
        for approval_user_id in operating_unit_id.approval_user_ids:
            data = {
                    'activity_type_id': 4,
                    'note': 'Voucher Request Approval',
                    'res_id': self.id,
                    'res_model_id': self.env.ref('weha_voucher_mgmt.model_weha_voucher_request').id,
                    'user_id': approval_user_id.id,
                    'date_deadline': datetime.now() + timedelta(days=2),
                    'summary': 'Voucher Request Approval'
            }
            self.send_notification(data)

    def trans_approve1(self):
        stage_id = self.stage_id.next_stage_id
        res = super(WeheVoucherRequest, self).write({'stage_id': stage_id.id})

    def trans_approve2(self):
        vals = { 'stage_id': self.stage_id.next_stage_id.id}
        self.write(vals)

        stage_id = self.stage_id.next_stage_id
        res = super(WeheVoucherRequest, self).write({'stage_id': stage_id.id})
        #To Finance User
        company_id = self.env.user.company_id
        for requester_user_id in company_id.res_company_request_operating_unit.requester_user_ids:
            data =  {
                'activity_type_id': 4,
                'note': 'Voucher Request was approved',
                'res_id': self.id,
                'res_model_id': self.env.ref('weha_voucher_mgmt.model_weha_voucher_request').id,
                'user_id': requester_user_id.id,
                'date_deadline': datetime.now() + timedelta(days=2),
                'summary': 'Voucher Request was approved'
            }
            self.send_notification(data)

    def trans_cancelled(self):
        stage_id = self.env['weha.voucher.request.stage'].search([('cancelled','=', True)], limit=1)
        if not stage_id:
            raise ValidationError('Stage Cancelled not found')
        super(WeheVoucherRequest, self).write({'stage_id': stage_id.id})

    company_id = fields.Many2one('res.company', 'Company')
    number = fields.Char(string='Request number', default="/",readonly=True)
    ref = fields.Char(string='Source Document', required=True)
    date_request = fields.Date('Date Request', required=True, default=lambda self: fields.date.today())
    user_id = fields.Many2one('res.users', 'Requester', default=lambda self: self.env.user and self.env.user.id or False, readonly=True)
    operating_unit_id = fields.Many2one('operating.unit','Store', related="user_id.default_operating_unit_id")
    source_operating_unit = fields.Many2one('operating.unit','Source Store', required=False)
    voucher_type = fields.Selection(
        string='Voucher Type',
        selection=[('physical', 'Physical'), ('electronic', 'Electronic')],
        default='physical'
    )    

    #Relation
    voucher_request_line_ids = fields.One2many(
        comodel_name='weha.voucher.request.line',
        inverse_name='voucher_request_id',
        string='Request Lines',
        domain="[('state','=','open')]"
    )

    voucher_request_allocate_line_ids = fields.One2many(
        comodel_name='weha.voucher.request.allocate.line', 
        inverse_name='voucher_request_id', 
        string='Request Allocate Lines',
        domain="[('state','=','open')]"
    )

    voucher_request_line_received_ids = fields.One2many(
        comodel_name='weha.voucher.request.line',
        inverse_name='voucher_request_id',
        string='Received Lines',
        domain="[('state','=','received')]"
    )

    #Qty Voucher
    # voucher_allocate_count = fields.Integer('Voucher Allocate Count', compute="_calculate_voucher_allocate_count", store=False)
    # voucher_count = fields.Integer('Voucher Count', compute="_calculate_voucher_count", store=False)
    # voucher_received_count = fields.Integer('Voucher Received', compute="_calculate_voucher_received", store=False)

    #For Kanban
    stage_id = fields.Many2one(
        'weha.voucher.request.stage',
        string='Stage',
        group_expand='_read_group_stage_ids',
        default=_get_default_stage_id,
        rack_visibility='onchange',
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

    voucher_count = fields.Integer('Voucher Count', compute="_calculate_voucher_count", store=False)

    line_ids = fields.One2many(
        string='Vouchers Lines',
        comodel_name='weha.voucher.request.line',
        inverse_name='voucher_request_id',
    )
        
    @api.model
    def create(self, vals):
        if vals.get('number', '/') == '/':
            seq = self.env['ir.sequence']
            if 'company_id' in vals:
                seq = seq.with_context(force_company=vals['company_id'])
            vals['number'] = seq.next_by_code(
                'weha.voucher.request.sequence') or '/'
        res = super(WeheVoucherRequest, self).create(vals)
        return res

    def write(self, vals):
        #if self.stage_id.opened:
        #    raise ValidationError("Please Click Button Allocate Form")
        if self.stage_id.closed:
            raise ValidationError("Can not move, status Closed")
        if self.stage_id.cancelled:
            raise ValidationError("Can not move, status Cancel")
        if self.stage_id.rejected:
            raise ValidationError("Can not Move, status reject")

        res = super(WeheVoucherRequest, self).write(vals)
        return res