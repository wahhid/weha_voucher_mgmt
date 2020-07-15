from odoo import models, fields, api,  _ 
from odoo.exceptions import UserError, ValidationError
import logging
from random import randrange

_logger = logging.getLogger(__name__)


class VoucherOrder(models.Model):
    _name = 'weha.voucher.order'
    _rec_name = 'number'
    _order = 'number desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    @api.depends('line_ids')
    def _calculate_voucher_count(self):
        for row in self:
            self.voucher_count = len(self.line_ids)
    
    def _get_default_stage_id(self):
        return self.env['weha.voucher.order.stage'].search([], limit=1).id
    
    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        stage_ids = self.env['weha.voucher.order.stage'].search([])
        return stage_ids
    
    company_id = fields.Many2one('res.company', 'Company')
    number = fields.Char(string='Order number', default="/",readonly=True)
    ref = fields.Char(string='Source Document', required=True)
    request_date = fields.Date('Order Date', required=True, default=lambda self: fields.date.today())
    user_id = fields.Many2one('res.users', string='Requester',)    
    voucher_type = fields.Selection(
        string='Voucher Type',
        selection=[('physical', 'Physical'), ('electronic', 'Electronic')],
        default='physical'
    )
    voucher_code_id = fields.Many2one('weha.voucher.code', 'Voucher Code', required=True)
    
    stage_id = fields.Many2one(
        'weha.voucher.order.stage',
        string='Stage',
        group_expand='_read_group_stage_ids',
        default=_get_default_stage_id,
        track_visibility='onchange',
    )
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
        inverse_name='voucher_order_id',
    )
    
    @api.model
    def create(self, vals):
        if vals.get('number', '/') == '/':
            seq = self.env['ir.sequence']
            if 'company_id' in vals:
                seq = seq.with_context(force_company=vals['company_id'])
            vals['number'] = seq.next_by_code(
                'weha.voucher.order.sequence') or '/'
        res = super().create(vals)

        # Check if mail to the user has to be sent
        #if vals.get('user_id') and res:
        #    res.send_user_mail()
        return res    