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

    @api.depends('stage_id')
    def _compute_current_stage(self):
        for rec in self:
            if rec.stage_id.unattended:
                rec.current_stage = 'unattended'
            # if rec.stage_id.waiting:
            #     rec.current_stage = 'waiting'
            if rec.stage_id.approval:
                rec.current_stage = 'approval'
            if rec.stage_id.opened:
                rec.current_stage = 'open'
            if rec.stage_id.closed:
                rec.current_stage = 'closed'
            
            
    def _get_default_stage_id(self):
        return self.env['weha.voucher.order.stage'].search([], limit=1).id
    
    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        stage_ids = self.env['weha.voucher.order.stage'].search([])
        return stage_ids
    
    @api.depends('line_ids')
    def _calculate_voucher_count(self):
        for row in self:
            self.voucher_count = len(self.line_ids)
    
    def send_l1_request_mail(self):
        for rec in self:
            template = self.env.ref('weha_voucher_mgmt.voucher_order_l1_approval_notification_template', raise_if_not_found=False)
            template.send_mail(rec.id)

    def generate_voucher(self):
        _logger.info("Generate Voucher ID = " + str('OKK'))

        start_number = self.start_number
        end_number = self.end_number
        obj_voucher_order_line = self.env['weha.voucher.order.line']
        _logger.info("Voucher LINE ID = " + str(obj_voucher_order_line))
        
        number = start_number
        _logger.info("Start Number = " + str(start_number))
        _logger.info("End Number = " + str(end_number))

        for i in range(start_number,end_number): 
            vals = {}
            vals.update({'operating_unit_id': self.operating_unit_id.id})
            vals.update({'voucher_order_id': self.id})
            vals.update({'voucher_code': self.voucher_code_id.code})
            vals.update({'voucher_code_id': self.voucher_code_id.id})
            vals.update({'check_number': number})
            vals.update({'start_number': start_number})
            vals.update({'end_number': end_number})
            vals.update({'voucher_type': self.voucher_type})
            vals.update({'state': 'open'})
            val_order_line_obj = obj_voucher_order_line.sudo().create(vals)

            _logger.info("Generate Voucher ID = " + str(val_order_line_obj))
            
            if not val_order_line_obj:
                raise ValidationError("Can't Generate voucher order line, contact administrator!")
            number = number+1
        
    @api.onchange('voucher_type')
    def _voucher_code_onchange(self):
        self.voucher_code_id = False
        res = {}
        res['domain']={'voucher_code_id':[('voucher_type', '=', self.voucher_type)]}
        return res

    def trans_approve(self):
        stage_id = self.stage_id.next_stage_id
        res = super(VoucherOrder, self).write({'stage_id': stage_id.id})
        return res
    
    def trans_reject(self):
        stage_id = self.stage_id.from_stage_id
        res = super(VoucherOrder, self).write({'stage_id': stage_id.id})
        return res
    
    def trans_close(self):
        stage_id = self.stage_id.next_stage_id
        res = super(VoucherOrder, self).write({'stage_id': stage_id.id})
        return res
        
    def trans_order_approval(self):    
        stage_id = self.stage_id.next_stage_id
        res = super(VoucherOrder, self).write({'stage_id': stage_id.id})
        return res

    
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
        'weha.voucher.order.stage',
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
    start_number = fields.Integer(string='Start Number')
    end_number = fields.Integer(string='End Number')
    
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
        res = super(VoucherOrder, self).create(vals)

        # Check if mail to the user has to be sent
        #if vals.get('user_id') and res:
        #    res.send_user_mail()
        return res    
    
    def write(self, vals):
        if 'stage_id' in vals:
            stage_id = self.env['weha.voucher.order.stage'].browse([vals['stage_id']])
            if self.stage_id.approval:
                raise ValidationError("Please using approve or reject button")
            if self.stage_id.opened:
                raise ValidationError("Please using Generate Voucher or Close Order")
            if self.stage_id.closed:
                raise ValidationError("Voucher Close")
        res = super(VoucherOrder, self).write(vals)
        return res
