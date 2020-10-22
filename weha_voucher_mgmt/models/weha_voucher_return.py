from odoo import models, fields, api,  _ 
from odoo.exceptions import UserError, ValidationError
import logging
from random import randrange
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


class VoucherReturn(models.Model):
    _name = 'weha.voucher.return'
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
        return self.env['weha.voucher.return.stage'].search([], limit=1).id
    
    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        stage_ids = self.env['weha.voucher.return.stage'].search([])
        return stage_ids

    def send_notification(self, data):
        self.env['mail.activity'].create(data).action_feedback()

    def _calculate_voucher_count(self):
        count = self.env['weha.voucher.return.line'].search_count([('voucher_return_id','=', self.id)])
        self.voucher_count = count

    def _calculate_voucher_received(self):
        count = 0
        for voucher_return_line_id in self.voucher_return_line_ids:
            if voucher_return_line_id.state == 'received':
                count += 1
        self.voucher_received_count = count

    @api.onchange('voucher_type')
    def _voucher_code_onchange(self):
        res = {}
        res['domain']={'voucher_code_id':[('voucher_type', '=', self.voucher_type)]}
        return res

    def trans_delivery(self):
        company_id = self.env.user.company_id
        stage_id = self.stage_id.next_stage_id
        res = super(VoucherReturn, self).write({'stage_id': stage_id.id})
        for row in self.voucher_return_line_ids:
            row.voucher_order_line_id.write({'state':'intransit'})
        # data = {
        #         'activity_type_id': 4,
        #         'note': 'Voucher Return on delivery',
        #         'res_id': self.id,
        #         'res_model_id': self.env.ref('model_weha_voucher_return').id,
        #         'user_id': user_id.id,
        #         'date_deadline': datetime.now() + timedelta(days=2),
        #         'summary': 'Voucher Return on delivery'
        #     }
        # self.send_notification(data)

    def trans_confirm_received(self):
        stage_id = self.stage_id.next_stage_id
        res = super(VoucherReturn, self).write({'stage_id': stage_id.id})
        
    def trans_approve(self):
        stage_id = self.stage_id.next_stage_id
        # self.send_l1_return_mail()
        res = super(VoucherReturn, self).write({'stage_id': stage_id.id})
        data = {
                'activity_type_id': 4,
                'note': 'Voucher Return was approved',
                'res_id': self.id,
                'res_model_id': self.env.ref('weha_voucher_mgmt.model_weha_voucher_return').id,
                'user_id': self.user_id.id,
                'date_deadline': datetime.now() + timedelta(days=2),
                'summary': 'Voucher Return was approved'
            }
        self.send_notification(data)
    
    def trans_received(self):
        stage_id = self.stage_id.next_stage_id
        res = super(VoucherReturn, self).write({'stage_id': stage_id.id})
        data =  {
            'activity_type_id': 4,
            'note': 'Voucher Return was received',
            'res_id': self.id,
            'res_model_id': self.env.ref('weha_voucher_mgmt.model_weha_voucher_return').id,
            'user_id': self.user_id.id,
            'date_deadline': datetime.now() + timedelta(days=2),
            'summary': 'Voucher Return was received'
        }
        self.send_notification(data)

    def trans_reject(self):
        stage_id = self.stage_id.from_stage_id
        res = super(VoucherReturn, self).write({'stage_id': stage_id.id})
        data = {
                'activity_type_id': 4,
                'note': 'Voucher Return was rejected',
                'res_id': self.id,
                'res_model_id': self.env.ref('model_weha_voucher_return').id,
                'user_id': user_id.id,
                'date_deadline': datetime.now() + timedelta(days=2),
                'summary': 'Voucher Return was rejected'
            }
        self.send_notification(data)
  
    def trans_close(self):
        stage_id = self.stage_id.next_stage_id
        res = super(VoucherReturn, self).write({'stage_id': stage_id.id})

    def trans_return_approval(self):    
        if self.voucher_count == 0:
            raise ValidationError("Return Lines Empty")
        stage_id = self.stage_id.next_stage_id
        res = super(VoucherReturn, self).write({'stage_id': stage_id.id})
        if not stage_id.approval_user_id:
            manager_id = self.operating_unit_id.manager_id
            data = {
                'activity_type_id': 4,
                'note': 'Voucher Return Approval',
                'res_id': self.id,
                'res_model_id': self.env.ref('model_weha_voucher_return').id,
                'user_id': manager_id.id,
                'date_deadline': datetime.now() + timedelta(days=2),
                'summary': 'Voucher Return Approval'
            }
            self.send_notification(data)

            
        

        

    company_id = fields.Many2one('res.company', 'Company')
    number = fields.Char(string='Return number', default="/",readonly=True)
    ref = fields.Char(string='Source Document', required=True)
    return_date = fields.Date('Return Date', required=True, default=lambda self: fields.date.today())
    user_id = fields.Many2one('res.users', string='Requester', default=lambda self: self.env.user and self.env.user.id or False, readonly=True)  
    operating_unit_id = fields.Many2one('operating.unit','Store', related="user_id.default_operating_unit_id")

    voucher_code_id = fields.Many2one('weha.voucher.code', 'Voucher Code', required=False, readonly=True)
    year_id = fields.Many2one('weha.voucher.year','Year', required=False, readonly=True)
    voucher_promo_id = fields.Many2one('weha.voucher.promo', 'Promo', required=False, readonly=True)
    start_number = fields.Integer(string='Start Number', required=False, readonly=True)
    end_number = fields.Integer(string='End Number', required=False, readonly=True)


    #for kanban
    stage_id = fields.Many2one(
        'weha.voucher.return.stage',
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
    voucher_return_line_ids = fields.One2many(
        comodel_name='weha.voucher.return.line',
        inverse_name='voucher_return_id',
        string='Return Lines',
        domain="[('state','=','open')]"
    )
    voucher_return_line_received_ids = fields.One2many(
        comodel_name='weha.voucher.return.line',
        inverse_name='voucher_return_id',
        string='Received Lines',
        domain="[('state','=','received')]"
    )
    
    #qty voucher
    voucher_count = fields.Integer('Voucher Count', compute="_calculate_voucher_count", store=False)
    voucher_received_count = fields.Integer('Voucher Received', compute="_calculate_voucher_received", store=False)

    @api.model
    def create(self, vals):
        if vals.get('number', '/') == '/':
            seq = self.env['ir.sequence']
            if 'company_id' in vals:
                seq = seq.with_context(force_company=vals['company_id'])
            vals['number'] = seq.next_by_code(
                'weha.voucher.return.sequence') or '/'
        res = super(VoucherReturn, self).create(vals)
        return res    
    
    def write(self, vals):
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
           
        res = super(VoucherReturn, self).write(vals)
        return res
