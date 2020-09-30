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
            if rec.stage_id.l1:
                rec.current_stage = 'approve_1'
            if rec.stage_id.l2:
                rec.current_stage = 'approve_2'
            if rec.stage_id.opened:
                rec.current_stage = 'open'
            if rec.stage_id.closed:
                rec.current_stage = 'closed'
            if rec.stage_id.cancelled:
                rec.current_stage = 'cancelled'
            if rec.stage_id.rejected:
                rec.current_stage = 'rejected'
                
    # @api.depends('line_ids')
    # def _calculate_voucher_count(self):
    #     voucher_count = 0
    #     for row in self:
    #         for line_id in self.line_ids:
    #             voucher_count += line_id.amount
    #     self.voucher_count = voucher_count
    
    # @api.depends('line_ids')
    # def _calculate_voucher_count(self):
    #     for row in self:
    #         self.voucher_count = len(self.line_ids)

    def send_l1_request_mail(self):
        for rec in self:
            template = self.env.ref('weha_voucher_mgmt.voucher_request_l1_approval_notification_template', raise_if_not_found=False)
            template.send_mail(rec.id)


    def create_allocate_from_request(self, request_line):

        obj_allocate = self.env['weha.voucher.allocate']
        vals = {}
        vals.update({'source_operating_unit': self.operating_unit_id.id})
        vals.update({'voucher_terms_id': request_line.voucher_terms_id.id})
        vals.update({'ref': self.ref})
        vals.update({'voucher_request_id': self.id})
        vals.update({'voucher_qty': request_line.voucher_qty})
        vals.update({'voucher_code_id': request_line.voucher_code_id.id})
        res = obj_allocate.sudo().create(vals)
        
        _logger.info("str_ean ID = " + str(res))

        return res
    
    def action_voucher_allocate_from_request(self):

        for request_line in self.voucher_request_line_ids:
            res = self.create_allocate_from_request(request_line)
            if not res:
                raise ValidationError("Can not create allocate from request")


    def trans_approve1(self):
        stage_id = self.stage_id.next_stage_id
        # self.send_l1_request_mail()
        res = super(WeheVoucherRequest, self).write({'stage_id': stage_id.id})
        return res
    
    def trans_progress(self):
        stage_id = self.stage_id.from_stage_id
        res = super(WeheVoucherRequest, self).write({'stage_id': stage_id.id})
        return res
    
    def trans_receiving(self):
        stage_id = self.stage_id.next_stage_id
        res = super(WeheVoucherRequest, self).write({'stage_id': stage_id.id})
        return res
    
    def trans_reject(self):
        stage_id = self.stage_id.from_stage_id
        res = super(WeheVoucherRequest, self).write({'stage_id': stage_id.id})
        return res

    # @api.depends('voucher_count')
    # def _calculate_voucher_count(self):
    #     res = self.env['weha.voucher.order.line'].search_count([('voucher_request_id', '=', self.id)])
    #     return res

    # @api.depends('voucher_allocate_count')
    def _calculate_voucher_allocate_count(self):
        # request_from_allocate_count = 0
        request_from_allocate_count = self.env['weha.voucher.allocate'].sudo().search_count([('voucher_request_id','=',self.id)])
        self.voucher_allocate_count = request_from_allocate_count

    def trans_request_approval(self):
        stage_id = self.stage_id.next_stage_id
        res = super(WeheVoucherRequest, self).write({'stage_id': stage_id.id})
        return res

    def trans_approve1(self):
        stage_id = self.stage_id.next_stage_id
        res = super(WeheVoucherRequest, self).write({'stage_id': stage_id.id})
        return res
    
    def trans_approve2(self):
        stage_id = self.stage_id.next_stage_id
        res = super(WeheVoucherRequest, self).write({'stage_id': stage_id.id})
        return res

    def trans_cancel(self):    
        stage_id = self.stage_id.from_stage_id
        res = super(WeheVoucherRequest, self).write({'stage_id': stage_id.id})
        return res

    def trans_reject(self):    
        stage_id = self.stage_id.from_stage_id
        res = super(WeheVoucherRequest, self).write({'stage_id': stage_id.id})
        return res

    company_id = fields.Many2one('res.company', 'Company')
    number = fields.Char(string='Request number', default="/",readonly=True)
    ref = fields.Char(string='Source Document', required=True)
    date_request = fields.Date('Date Request', default=lambda self: fields.date.today())
    user_id = fields.Many2one('res.users', 'Requester', default=lambda self: self.env.user and self.env.user.id or False, readonly=True)
    operating_unit_id = fields.Many2one('operating.unit','Store', related="user_id.default_operating_unit_id")
    source_operating_unit = fields.Many2one('operating.unit','Source Store', required=False)
    voucher_type = fields.Selection(
        string='Voucher Type',
        selection=[('physical', 'Physical'), ('electronic', 'Electronic')],
        default='physical'
    )
    voucher_terms_id = fields.Many2one('weha.voucher.terms', 'Voucher Terms', required=False)
    voucher_code_id = fields.Many2one('weha.voucher.code', 'Voucher Code', required=False, readonly=False)
    year_id = fields.Many2one('weha.voucher.year','Year', required=False, readonly=False)
    voucher_promo_id = fields.Many2one('weha.voucher.promo', 'Promo', required=False, readonly=False)
    start_number = fields.Integer(string='Start Number', required=False, readonly=True)
    end_number = fields.Integer(string='End Number', required=False, readonly=True)
    voucher_qty = fields.Char(string='Quantity Ordered', size=6, required=False)
    

    #Relation
    voucher_request_line_ids = fields.One2many(
        comodel_name='weha.voucher.request.line',
        inverse_name='voucher_request_id',
        string='Request Lines',
        domain="[('state','=','open')]"
    )
    voucher_request_line_received_ids = fields.One2many(
        comodel_name='weha.voucher.request.line',
        inverse_name='voucher_request_id',
        string='Received Lines',
        domain="[('state','=','received')]"
    )

    #Qty Voucher
    voucher_allocate_count = fields.Integer('Voucher Allocate Count', compute="_calculate_voucher_allocate_count", store=False)
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
      
        if self.stage_id.l1:
            raise ValidationError("Please using approve or reject button")
        if self.stage_id.l2:
            raise ValidationError("Please using approve or reject button")
        if self.stage_id.opened:
            raise ValidationError("Please Click Button Allocate Form")
        # if self.stage_id.closed:
        #     raise ValidationError("Can not move, status Closed")
        if self.stage_id.cancelled:
            raise ValidationError("Can not move, status Cancel")
        if self.stage_id.rejected:
            raise ValidationError("Can not Move, status reject")

        res = super(WeheVoucherRequest, self).write(vals)
        return res