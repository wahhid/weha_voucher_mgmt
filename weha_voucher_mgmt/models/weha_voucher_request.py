from odoo import models, fields, api,  _ 
from odoo.exceptions import UserError, ValidationError
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
    
    @api.depends('line_ids')
    def _calculate_voucher_count(self):
        for row in self:
            self.voucher_count = len(self.line_ids)

    @api.depends('stage_id')
    def trans_approve1(self):
        
        stage = self.stage_id.next_stage_id.id
        _logger.info("Stage Here = " + str(self.stage_id.id))
        _logger.info("Next Stage = " + str(stage))
        self.write({'stage_id': stage})

        return True
    
    @api.depends('stage_id')
    def trans_approve2(self):
        
        stage = self.stage_id.next_stage_id.id
        _logger.info("Stage Here = " + str(self.stage_id.id))
        _logger.info("Next Stage = " + str(stage))
        self.write({'stage_id': stage})

        return True

    company_id = fields.Many2one('res.company', 'Company')
    number = fields.Char(string='Request number', default="/",readonly=True)
    date_request = fields.Date('Date Request')
    user_id = fields.Many2one('res.users', 'Requester', default=lambda self: self.env.user and self.env.user.id or False, readonly=True)
    operating_unit_id = fields.Many2one('operating.unit', 'Store', related="user_id.default_operating_unit_id")
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

    voucher_count = fields.Integer('Voucher Count', compute="_calculate_voucher_count", store=True)

    line_ids = fields.One2many(
        string='Vouchers',
        comodel_name='weha.voucher.order.line',
        inverse_name='voucher_request_id',
    )

    voucher_request_line_ids = fields.One2many(
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
        if 'stage_id' in vals:
            stage_obj = self.env['weha.voucher.request.stage'].browse([vals['stage_id']])
            if stage_obj.unattended:
                pass

            #Change To L1, Get User from Param
            # trans_approve = False
            # trans_approve = self.trans_approve()
            # if stage_obj.approval:
            #     if self.stage_id.id != stage_obj.from_stage_id.id:
            #         raise ValidationError('Cannot Process Approval')
            #     # self.send_l1_request_mail()

        if vals.get('stage_id.unattended'):
            _logger.info("stage unattended ID = " + str(vals.get('stage_id.unattended')))
            self.current_stage = 'unattended'
        if vals.get('stage_id.l1'):
            _logger.info("stage unattended ID = " + str(vals.get('stage_id.l1')))
            self.current_stage = 'approve_1'
        if vals.get('stage_id.l2'):
            _logger.info("stage unattended ID = " + str(vals.get('stage_id.l2')))
            self.current_stage = 'approve_2'
        if vals.get('stage_id.opened'):
            self.current_stage = 'open'
        if vals.get('stage_id.closed'):
            self.current_stage = 'closed'
           
        res = super(WeheVoucherRequest, self).write(vals)
        return res