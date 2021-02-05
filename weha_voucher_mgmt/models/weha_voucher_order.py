from odoo import models, fields, api,  _ 
from odoo.exceptions import UserError, ValidationError
import logging
from random import randrange
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


class VoucherOrder(models.Model):
    _name = 'weha.voucher.order'
    _description = 'Voucher Order'
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
            if rec.stage_id.rejected:
                rec.current_stage = 'rejected'
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
                   
    def _get_default_stage_id(self):
        return self.env['weha.voucher.order.stage'].search([], limit=1).id
    
    def _check_voucher_order_number(self):
        pass

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        stage_ids = self.env['weha.voucher.order.stage'].search([])
        return stage_ids
    
    def _calculate_voucher_count(self):
        for row in self:
            row.voucher_count = len(row.line_ids)

    def _calculate_voucher_request(self):
        for row in self:
            row.voucher_request = len(range(row.start_number,row.end_number+1))

    def _calculate_voucher_received(self):
        for row in self:
            row.voucher_received = len(row.line_ids.filtered(lambda r: r.state == 'open'))

    def _calculate_voucher_total_amount(self):
        for row in self:
            row.voucher_total_amount = len(range(row.start_number,row.end_number+1)) * row.voucher_code_id.voucher_amount 

    def delete_lines(self):
        self.env.cr.execute('DELETE FROM weha_voucher_order_line WHERE voucher_order_id=' + str(self.id))

    def send_notification(self, data):
        self.env['mail.activity'].create(data).action_feedback()

    @api.onchange('voucher_type')
    def _voucher_type_onchange(self):
        if self.voucher_type:
            self.voucher_code_id = False
            res = {}
            res['domain']={'voucher_code_id':[('voucher_type', '=', self.voucher_type)]}
    
    @api.onchange('year')
    def _onchange_year(self):
        if self.year:
            domain = [
                ('voucher_type','=', self.voucher_type),
                ('voucher_code_id','=', self.voucher_code_id.id),
                ('year_id','=', self.year.id),
            ]
            voucher_order_line_id = self.env['weha.voucher.order.line'].search(domain, order="check_number desc", limit=1)
            _logger.info(voucher_order_line_id)
            if not voucher_order_line_id:
                self.start_number = 1
            else:
                self.start_number = voucher_order_line_id.check_number + 1

    @api.constrains('start_number', 'end_number')
    def _check_length(self):
        for record in self:
            if len(str(record.start_number)) > 6:
                raise ValidationError("Start Number 6 digit maximum")
            if len(str(record.end_number)) > 6:
                raise ValidationError("End Number 6 digit maximum")

    def overlap(self, start1, end1, start2, end2):
        """Does the range (start1, end1) overlap with (start2, end2)?"""
        return (
            start1 <= start2 <= end1 or
            start1 <= end2 <= end1 or
            start2 <= start1 <= end2 or
            start2 <= end1 <= end2
        )

    def check_order_overlap(self, voucher_type, voucher_code_id, year, start_number, end_number):
        
        domain = [
            ('voucher_type','=', voucher_type),
            ('voucher_code_id','=',voucher_code_id),
            ('year','=', year),
            ('current_stage','in', ['unattended','approval','open','closed']),
        ]

        _logger.info(domain)

        voucher_order_ids = self.env['weha.voucher.order'].search(domain, order="create_date desc")
        _logger.info(voucher_order_ids)
        is_overlap = False
        for voucher_order_id in voucher_order_ids:
            _logger.info(voucher_order_id.start_number)
            _logger.info(voucher_order_id.end_number)
            result = self.overlap(start_number,end_number,voucher_order_id.start_number, voucher_order_id.end_number)
            _logger.info(result)
            if result:
                is_overlap = True
                break 
        return is_overlap

    # Generate Voucher
    def trans_generate_voucher(self):
        _logger.info("Generate Voucher ID = " + str('OK'))
        obj_voucher_order_line = self.env['weha.voucher.order.line']        
        
        start_number = self.start_number
        end_number = self.end_number
        voucher_year = self.year
        number = start_number

        voucher_order_lines = []

        for i in range(self.start_number,self.end_number + 1): 
            vals = {}
            vals.update({'operating_unit_id': self.operating_unit_id.id})
            vals.update({'voucher_type': self.voucher_type})
            vals.update({'voucher_order_id': self.id})
            vals.update({'voucher_code_id': self.voucher_code_id.id})
            vals.update({'voucher_amount': self.voucher_code_id.voucher_amount})
            vals.update({'voucher_terms_id': self.voucher_code_id.voucher_terms_id.id})
            vals.update({'year_id': self.year.id})
            vals.update({'check_number': i})
            vals.update({'state': 'inorder'})
            _logger.info(vals)
            _logger.info("postgresql_create")
            self.env['weha.voucher.order.line'].postgresql_create(vals)


        #val_order_line_obj = obj_voucher_order_line.sudo().create(voucher_order_lines)   
        #if not val_order_line_obj:
        #    raise ValidationError("Can't Generate voucher order line, contact administrator!")
    
        self.is_voucher_generated = True
        next_stage_id =  self.stage_id.next_stage_id
        vals = {'stage_id': next_stage_id.id }
        #self.write(vals)
        super(VoucherOrder,self).write(vals)
        
    def trans_received(self):
        stage_id = self.env['weha.voucher.order.stage'].search([('receiving','=', True)], limit=1)
        if not stage_id:
            raise ValidationError('Stage receiving not found')
        super(VoucherOrder, self).write({'stage_id': stage_id.id})

    def trans_approve(self):
        #Approve Voucher Order
        stage_id = self.stage_id.next_stage_id
        super(VoucherOrder, self).write({'stage_id': stage_id.id})
        
        #Create Schedule Activity
        operating_unit_id = self.operating_unit_id
        for requester_user_id in operating_unit_id.requester_user_ids:
            _logger.info(requester_user_id.name)
            self.env['mail.activity'].create({
                'activity_type_id': 4,
                'note': 'Voucher Order was approved',
                'res_id': self.id,
                'res_model_id': self.env.ref('weha_voucher_mgmt.model_weha_voucher_order').id,
                'user_id': requester_user_id.id,
                'date_deadline': datetime.now() + timedelta(days=2),
                'summary': 'Voucher Order was approved'
            }).action_feedback()

        #Send Notification
        #template_id = self.env.ref('weha_voucher_mgmt.voucher_order_l1_approval_notification_template').id 
        #template = self.env['mail.template'].browse(template_id)
        #template.email_to = self.user_id.partner_id.email
        #template.send_mail(self.id, force_send=True)
    
    def trans_reject(self):
        stage_id = self.env['weha.voucher.order.stage'].search([('rejected','=', True)], limit=1)
        if not stage_id:
            raise ValidationError('Stage Rejected not found')
        super(VoucherOrder, self).write({'stage_id': stage_id.id})

        #Create Schedule Activity
        self.env['mail.activity'].create({
            'activity_type_id': 4,
            'note': 'Voucher Order was rejected',
            'res_id': self.id,
            'res_model_id': self.env.ref('weha_voucher_mgmt.model_weha_voucher_order').id,
            'user_id': self.user_id.id,
            'date_deadline': datetime.now() + timedelta(days=2),
            'summary': 'Voucher Order was rejected'
        }).action_feedback()

        #Send Notification
        #template_id = self.env.ref('weha_voucher_mgmt.voucher_order_l1_approval_notification_template').id 
        #template = self.env['mail.template'].browse(template_id)
        #template.email_to = self.user_id.partner_id.email
        #template.send_mail(self.id, force_send=True)
        #stage = self.stage_id.next_stage_id.id
        #_logger.info("Stage Here = " + str(self.stage_id.id))
        #_logger.info("Next Stage = " + str(stage))
        #self.write({'stage_id': stage})

    def trans_close(self):
        stage_id = self.env['weha.voucher.order.stage'].search([('closed','=', True)], limit=1)
        if not stage_id:
            raise ValidationError('Stage closed not found')
        super(VoucherOrder, self).write({'stage_id': stage_id.id})
        
    def trans_request_approval(self):    
        _logger.info('Trans Request Approval Process')
        stage_id =  self.stage_id.next_stage_id
        vals = { 'stage_id': stage_id.id}
        #self.write(vals)
        super(VoucherOrder,self).write(vals)

        #Create Schedule Activity
        data = {
            'activity_type_id': 4,
            'note': 'Voucher Order Approval',
            'res_id': self.id,
            'res_model_id': self.env.ref('model_weha_voucher_order').id,
            'user_id': stage_id.approval_user_id.id,
            'date_deadline': datetime.now() + timedelta(days=2),
            'summary': 'Voucher Order Approval'
        }
        self.send_notification(data)
        
        #template_id = self.env.ref('weha_voucher_mgmt.voucher_order_l1_approval_notification_template').id 
        #template = self.env['mail.template'].browse(template_id)
        #_logger.info(next_stage_id.approval_user_id)
        #template.email_to = next_stage_id.approval_user_id.partner_id.email
        #template.send_mail(self.id, force_send=True)
        
    def trans_order_approval(self):    
        stage_id = self.stage_id.next_stage_id
        super(VoucherOrder, self).write({'stage_id': stage_id.id})
        operating_unit_id = self.operating_unit_id
        for approval_user_id in operating_unit_id.approval_user_ids:
            data = {
                    'activity_type_id': 4,
                    'note': 'Voucher Order Approval',
                    'res_id': self.id,
                    'res_model_id': self.env.ref('weha_voucher_mgmt.model_weha_voucher_order').id,
                    'user_id': approval_user_id.id,
                    'date_deadline': datetime.now() + timedelta(days=2),
                    'summary': 'Voucher Order Approval'
            }
            self.send_notification(data)
               
    def trans_cancelled(self):
        stage_id = self.env['weha.voucher.order.stage'].search([('cancelled','=', True)], limit=1)
        if not stage_id:
            raise ValidationError('Stage Cancelled not found')
        super(VoucherOrder, self).write({'stage_id': stage_id.id})
        self.delete_lines()


    company_id = fields.Many2one('res.company', 'Company')
    number = fields.Char(string='Order number', default="/", readonly=True)
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
    
    current_stage = fields.Char(string='Current Stage', size=50, compute="_compute_current_stage", readonly=True, store=True)

    priority = fields.Selection(selection=[
        ('0', _('Low')),
        ('1', _('Medium')),
        ('2', _('High')),
        ('3', _('Very High')),
    ], string='Priority', default='1')
   
    color = fields.Integer(string='Color Index')
    
    #voucher_promo_id = fields.Many2one('weha.voucher.promo','Promo')
    start_number = fields.Integer(string='Start Number', required=True)
    end_number = fields.Integer(string='End Number', required=True)
    year = fields.Many2one('weha.voucher.year', 'Year', required=True)
    
    
    kanban_state = fields.Selection([
        ('normal', 'Default'),
        ('done', 'Ready for next stage'),
        ('blocked', 'Blocked')], string='Kanban State')
    
    is_voucher_generated = fields.Boolean('Is Voucher Generated', default=False)
    
    voucher_request = fields.Integer('Voucher Request', compute="_calculate_voucher_request", store=False)
    voucher_count = fields.Integer('Voucher Count', compute="_calculate_voucher_count", store=False)
    voucher_received = fields.Integer('Voucher Received', compute="_calculate_voucher_received", store=False)
    voucher_total_amount =  fields.Float('Voucher Total Amount', compute="_calculate_voucher_total_amount", store=False, readonly=True)
    
    line_ids = fields.One2many(
        string='Vouchers',
        comodel_name='weha.voucher.order.line',
        inverse_name='voucher_order_id',
    )

    
    @api.model
    def create(self, vals):
        #Check Start Number and End Number
        if vals.get('start_number') > vals.get('end_number'):
            raise ValidationError('Start Number greater than End Number')

        #Check Overlap Range Number
        is_overlap = self.check_order_overlap(vals.get('voucher_type'), vals.get('voucher_code_id'), vals.get('year') , vals.get('start_number'),vals.get('end_number'))
        if is_overlap:
            raise ValidationError('Overlap Voucher Number')
        
        #Create Trans #
        if vals.get('number', '/') == '/':
            seq = self.env['ir.sequence']
            if 'company_id' in vals:
                seq = seq.with_context(force_company=vals['company_id'])
            vals['number'] = seq.next_by_code(
                'weha.voucher.order.sequence') or '/'

        #Create Trans
        res = super(VoucherOrder, self).create(vals)
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
