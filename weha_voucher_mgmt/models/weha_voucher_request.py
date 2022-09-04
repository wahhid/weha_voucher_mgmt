from odoo import models, fields, api,  _ 
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta, date
from dateutil.relativedelta import *
import logging

_logger = logging.getLogger(__name__)

class WeheVoucherRequest(models.Model):
    _name = 'weha.voucher.request'
    _description = 'Voucher Request'
    _rec_name = 'number'
    _order = 'number desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        stage_ids = self.env['weha.voucher.request.stage'].search([])
        return stage_ids

    def _get_default_stage_id(self):
        return self.env['weha.voucher.request.stage'].search([], limit=1).id

    def get_is_mine(self):
        if self.operating_unit_id.id == self.env.user.default_operating_unit_id.id:
            self.is_mine = True
        else:
            self.is_mine = False
            
    @api.depends('stage_id')
    def _compute_current_stage(self):
        for rec in self:
            if rec.stage_id.unattended:
                rec.current_stage = 'unattended'
                rec.current_stage_approval_level = 0
            if rec.stage_id.approval:
                rec.current_stage = 'approval'
                rec.current_stage_approval_level = rec.stage_id.approval_level
            if rec.stage_id.opened:
                rec.current_stage = 'open'
                rec.current_stage_approval_level = 0
            if rec.stage_id.closed:
                rec.current_stage = 'closed'
                rec.current_stage_approval_level = 0
            if rec.stage_id.cancelled:
                rec.current_stage = 'cancelled'
                rec.current_stage_approval_level = 0
            if rec.stage_id.rejected:
                rec.current_stage = 'rejected'
                rec.current_stage_approval_level = 0
                
    def _calculate_voucher_count(self):
        voucher_count = 0
        for row in self:
            for line_id in self.line_ids:
                voucher_count += line_id.voucher_qty
        self.voucher_count = voucher_count
    
    def _calculate_voucher_total_amount(self):
        voucher_total_amount = 0
        for row in self:
            for line_id in row.line_ids:
                voucher_total_amount = voucher_total_amount +  line_id.total_amount
            row.voucher_total_amount = voucher_total_amount

    def send_notification(self, data):
        self.env['mail.activity'].create(data).action_feedback()

    def send_chief_request_aprroval_email(self):
        for rec in self:
            domain = [
                ('name','=','Request For Chief Approval')
            ]
            template = self.env['mail.template'].search(domain,limit=1)
            # template = self.env.ref('email_template_voucher_request_marketing_cheif_approval', raise_if_not_found=False)
            if not template:
                raise ValidationError(_("Email Template not found!"))
            template.send_mail(rec.id, force_send=True)

    def create_allocate_from_request(self, request_line):
        obj_allocate = self.env['weha.voucher.allocate']
        company_id = self.env.user.company_id
        operating_unit_id = self.operating_unit_id
        vals = {}
        vals.update({'user_id': company_id.res_company_request_allocate_user_id.id})
        vals.update({'source_operating_unit': self.operating_unit_id.id})
        vals.update({'ref': self.number})
        vals.update({'remark': self.remark})
        vals.update({'promo_expired_date': self.promo_expired_date})
        vals.update({'is_request': True})
        vals.update({'voucher_request_id': self.id})
        vals.update({'voucher_request_qty': request_line.voucher_qty})
        vals.update({'voucher_code_id': request_line.voucher_code_id.id})
        vals.update({'voucher_terms_id': request_line.voucher_code_id.voucher_terms_id.id})
        vals.update({'voucher_mapping_sku_id': request_line.voucher_mapping_sku_id.id})
        vals.update({'year_id': self.env['weha.voucher.year'].get_current_year().id})
        if self.voucher_promo_id:
            vals.update({'voucher_promo_id': self.voucher_promo_id.id})
            vals.update({'is_voucher_promo': True})
            vals.update({'promo_expired_date': self.promo_expired_date})
        else:
            vals.update({'expired_days': request_line.voucher_code_id.voucher_terms_id.number_of_days})
            vals.update({'voucher_promo_id': False})
        res = obj_allocate.sudo().create(vals)
        _logger.info("str_ean ID = " + str(res))
        
        #To Finance User
        for requester_user_id in company_id.res_company_request_operating_unit.requester_user_ids:
            data =  {
                'activity_type_id': 4,
                'note': 'Voucher Request from ' + operating_unit_id.name,
                'res_id': res.id,
                'res_model_id': self.env.ref('weha_voucher_mgmt.model_weha_voucher_allocate').id,
                'user_id': requester_user_id.id,
                'date_deadline': datetime.now() + timedelta(days=2),
                'summary': 'Voucher Request from ' + operating_unit_id.name
            }
            self.sudo().send_notification(data)
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
        
        #Create Voucher Allocated
        self.action_voucher_allocate_from_request()

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
        # company_id = self.env.user.company_id
        # for approval_user_id in company_id.res_company_request_operating_unit.approval_user_ids:
        #     data =  {
        #         'activity_type_id': 4,
        #         'note': 'Voucher Request from ' + operating_unit_id.name,
        #         'res_id': self.id,
        #         'res_model_id': self.env.ref('weha_voucher_mgmt.model_weha_voucher_request').id,
        #         'user_id': approval_user_id.id,
        #         'date_deadline': datetime.now() + timedelta(days=2),
        #         'summary': 'Voucher Request from ' + operating_unit_id.name
        #     }
        #     self.send_notification(data)
        #To Finance User
        # company_id = self.env.user.company_id
        # for requester_user_id in company_id.res_company_request_operating_unit.requester_user_ids:
        #     data =  {
        #         'activity_type_id': 4,
        #         'note': 'Voucher Request from ' + operating_unit_id.name,
        #         'res_id': self.id,
        #         'res_model_id': self.env.ref('weha_voucher_mgmt.model_weha_voucher_request').id,
        #         'user_id': requester_user_id.id,
        #         'date_deadline': datetime.now() + timedelta(days=2),
        #         'summary': 'Voucher Request from ' + operating_unit_id.name
        #     }
        #     self.send_notification(data)

    def trans_approve_marketing_manager(self):
        approval_level = self.stage_id.approval_level
        is_next_approval = self.stage_id.is_next_approval
        if is_next_approval:
            approval_level = approval_level + 1
            domain = [('approval','=', 1),('approval_level','=',2)]
            stage_id = self.env['weha.voucher.request.stage'].search(domain,limit=1)
            if not stage_id:
                raise UserError("Stage not found")
            res = super(WeheVoucherRequest, self).write({'stage_id': stage_id.id})
            operating_unit_id = self.operating_unit_id
            data = {}
            for approval_user_id in operating_unit_id.approval_level_2_user_ids:
                data.update({
                        'activity_type_id': 4,
                        'note': 'Voucher Request Approval',
                        'res_id': self.id,
                        'res_model_id': self.env.ref('weha_voucher_mgmt.model_weha_voucher_request').id,
                        'user_id': approval_user_id.id,
                        'date_deadline': datetime.now() + timedelta(days=2),
                        'summary': 'Voucher Request Chief Approval'
                })
            self.send_notification(data)
            self.send_chief_request_aprroval_email()
        else:
            stage_id = self.stage_id.next_stage_id
            res = super(WeheVoucherRequest, self).write({'stage_id': stage_id.id})
            #Create Voucher Allocated
            self.action_voucher_allocate_from_request()

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
            
    def trans_approve_marketing_chief(self):
        stage_id = self.stage_id.next_stage_id
        res = super(WeheVoucherRequest, self).write({'stage_id': stage_id.id})
        #Create Voucher Allocated
        self.action_voucher_allocate_from_request()

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

    def trans_reject_marketing_manager(self):
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
                'summary': 'Voucher Request was rejected by Marketing Manager'
            }).action_feedback()
            #self.send_l1_request_mail
    
    def trans_reject_marketing_chief(self):
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
                'summary': 'Voucher Request was rejected by Marketing Chief'
            }).action_feedback()

    def trans_request_approval(self):
        if len(self.voucher_request_line_ids) == 0:
            raise ValidationError('Request Line Empty!')
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
    ref = fields.Char(string='Source Document', required=False)
    date_request = fields.Date('Date Request', required=True, default=lambda self: fields.date.today())
    user_id = fields.Many2one('res.users', 'Requester', default=lambda self: self.env.user and self.env.user.id or False, readonly=True)
    operating_unit_id = fields.Many2one('operating.unit','Store', related="user_id.default_operating_unit_id")
    is_mine = fields.Boolean('Is Mine', compute="get_is_mine")
    source_operating_unit = fields.Many2one('operating.unit','Source Store', required=False)
    voucher_type = fields.Selection(
        string='Voucher Type',
        selection=[('physical', 'Physical'), ('electronic', 'Electronic')],
        default='physical'
    )
    voucher_promo_id = fields.Many2one('weha.voucher.promo','Promo')    
    promo_expired_date = fields.Date('Promo Expired Date')
    remark = fields.Char('Remark', size=200)
    voucher_total_amount = fields.Float("Total", compute="_calculate_voucher_total_amount", readonly=True)

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
    current_stage_approval_level = fields.Integer(string='Current Stage Approval Level', compute="_compute_current_stage", readonly=True)
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