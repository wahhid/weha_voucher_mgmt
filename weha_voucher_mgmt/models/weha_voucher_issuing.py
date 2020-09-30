from odoo import models, fields, api,  _ 
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta, date
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

    def action_issuing_voucher(self):
        
        for voucher_issuing_line_id in self.voucher_issuing_line_ids:
            vals = {}
            vals.update({'state': 'activated'})
            res = voucher_issuing_line_id.sudo().write(vals)

            vals = {}
            vals.update({'state': 'activated'})
            vals.update({'voucher_issuing_id': self.id})
            voucher_issuing_line_id.voucher_order_line_id.sudo().write(vals)

            vals = {}
            vals.update({'name': self.number})
            vals.update({'voucher_order_line_id': voucher_issuing_line_id.voucher_order_line_id.id})
            vals.update({'trans_date': datetime.now()})
            vals.update({'trans_type': 'AC'})
            self.env['weha.voucher.order.line.trans'].sudo().create(vals)

        stage_id = self.stage_id.next_stage_id
        res = super(VoucherIssuing, self).write({'stage_id': stage_id.id})
        return res

            
    def _get_default_stage_id(self):
        return self.env['weha.voucher.issuing.stage'].search([], limit=1).id
    
    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        stage_ids = self.env['weha.voucher.issuing.stage'].search([])
        return stage_ids
    
    @api.depends('voucher_issuing_line_ids')
    def _calculate_voucher_count(self):
        for row in self:
            self.voucher_count = len(self.voucher_issuing_line_ids)


    company_id = fields.Many2one('res.company', 'Company')
    number = fields.Char(string='Order number', default="/",readonly=True)
    ref = fields.Char(string='Source Document', required=True)
    issuing_date = fields.Date('Order Date', required=True, default=lambda self: fields.date.today())
    user_id = fields.Many2one('res.users', string='Requester', default=lambda self: self.env.user and self.env.user.id or False, readonly=True)  
    operating_unit_id = fields.Many2one('operating.unit','Store', related="user_id.default_operating_unit_id")
    voucher_code_id = fields.Many2one('weha.voucher.code', 'Voucher Code', required=False, readonly=True)
    year_id = fields.Many2one('weha.voucher.year','Year', required=False, readonly=True)
    voucher_promo_id = fields.Many2one('weha.voucher.promo', 'Promo', required=False, readonly=True)
    start_number = fields.Integer(string='Start Number', required=False, readonly=True)
    end_number = fields.Integer(string='End Number', required=False, readonly=True)


    #kanban
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
    
    #relation
    voucher_issuing_line_ids = fields.One2many(
        comodel_name='weha.voucher.issuing.line',
        inverse_name='voucher_issuing_id',
        string='Issuing Lines',
        domain="[('state','=','open')]"
    )
    
    #voucher
    voucher_count = fields.Integer('Voucher Count', compute="_calculate_voucher_count", store=False)
    
    @api.model
    def create(self, vals):
        if vals.get('number', '/') == '/':
            seq = self.env['ir.sequence']
            if 'company_id' in vals:
                seq = seq.with_context(force_company=vals['company_id'])
            vals['number'] = seq.next_by_code(
                'weha.voucher.issuing.sequence') or '/'
        res = super(VoucherIssuing, self).create(vals)
        return res    
    
    def write(self, vals):

        if self.stage_id.opened:
            raise ValidationError("Please Click Button Ready to Issuing")
        if self.stage_id.closed:
            raise ValidationError("Can not move, status Close")
        if self.stage_id.cancelled:
            raise ValidationError("Can not move, status Cancel")
           
        res = super(VoucherIssuing, self).write(vals)
        return res
