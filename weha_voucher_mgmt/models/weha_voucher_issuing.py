from odoo import models, fields, api,  _ 
from odoo.exceptions import UserError, ValidationError
import logging
from random import randrange

_logger = logging.getLogger(__name__)


class VoucherIssuing(models.Model):
    _name = 'weha.voucher.issuing'
    _rec_name = 'number'
    _order = 'number desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.depends('stage_id')
    def _compute_current_stage(self):
        for rec in self:
            if rec.stage_id.unattended:
                rec.current_stage = 'unattended'
            if rec.stage_id.opened:
                rec.current_stage = 'open'
            if rec.stage_id.closed:
                rec.current_stage = 'closed'
            if rec.stage_id.cancelled:
                rec.current_stage = 'cancelled'
            
    def _get_default_stage_id(self):
        return self.env['weha.voucher.issuing.stage'].search([], limit=1).id
    
    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        stage_ids = self.env['weha.voucher.issuing.stage'].search([])
        return stage_ids
    
    # @api.depends('line_ids')
    # def _calculate_voucher_count(self):
    #     for row in self:
    #         self.voucher_count = len(self.line_ids)
    
    # def send_l1_request_mail(self):
    #     for rec in self:
    #         template = self.env.ref('weha_voucher_mgmt.voucher_order_l1_approval_notification_template', raise_if_not_found=False)
    #         template.send_mail(rec.id)


    @api.depends('stage_id')
    def trans_confirm(self):
        stage = self.stage_id.next_stage_id.id
        self.write({'stage_id': stage.id})


    company_id = fields.Many2one('res.company', 'Company')
    number = fields.Char(string='Order number', default="/",readonly=True)
    ref = fields.Char(string='Source Document', required=True)
    request_date = fields.Date('Order Date', required=True, default=lambda self: fields.date.today())
    user_id = fields.Many2one('res.users', string='Requester', default=lambda self: self.env.user and self.env.user.id or False, readonly=True)  
    operating_unit_id = fields.Many2one('operating.unit','Store', related="user_id.default_operating_unit_id")
    voucher_type = fields.Selection(
        string='Voucher Type',
        selection=[('physical', 'Physical'), ('electronic', 'Electronic')],
        default='physical'
    )
    voucher_code_id = fields.Many2one('weha.voucher.code', 'Voucher Code', required=True)
    stage_id = fields.Many2one(
        'weha.voucher.issuing.stage',
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
    
    estimate_voucher_count = fields.Integer('Voucher #', default=0)
    voucher_count = fields.Integer('Voucher Count', compute="_calculate_voucher_count", store=True)
    
    voucher_issuing_line_ids = fields.One2many(
        comodel_name='weha.voucher.issuing.line', 
        inverse_name='voucher_issuing_id', 
        string='Issued Lines',
        domain="[('state','=','open')]"
    )

    @api.model
    def create(self, vals):
        if vals.get('number', '/') == '/':
            seq = self.env['ir.sequence']
            if 'company_id' in vals:
                seq = seq.with_context(force_company=vals['company_id'])
            vals['number'] = seq.next_by_code(
                'weha.voucher.issuing.sequence') or '/'
        res = super(VoucherIssuing, self).create(vals)

        # Check if mail to the user has to be sent
        #if vals.get('user_id') and res:
        #    res.send_user_mail()
        return res    
    
    def write(self, vals):
        if 'stage_id' in vals:
            stage_obj = self.env['weha.voucher.issuing.stage'].browse([vals['stage_id']])
            if stage_obj.unattended:
                pass
        res = super(VoucherIssuing, self).write(vals)
        return res
