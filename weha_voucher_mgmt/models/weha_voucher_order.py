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
            if rec.stage_id.approval:
                rec.current_stage = 'approval'
            if rec.stage_id.opened:
                rec.current_stage = 'open'
            if rec.stage_id.closed:
                rec.current_stage = 'closed'
                   
    def _get_default_stage_id(self):
        return self.env['weha.voucher.order.stage'].search([], limit=1).id
    
    def _check_voucher_order_number(self):
        pass

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

    # Generate Voucher
    def trans_generate_voucher(self):
        _logger.info("Generate Voucher ID = " + str('OK'))
        obj_voucher_order_line = self.env['weha.voucher.order.line']        
        
        start_number = self.start_number
        end_number = self.end_number
        voucher_year = self.year
        number = start_number

        for i in range(self.start_number,self.end_number + 1): 
            vals = {}
            vals.update({'operating_unit_id': self.operating_unit_id.id})
            #vals.update({'operating_unit_loc_fr_id': self.operating_unit_id.id})
            vals.update({'voucher_type': self.voucher_type})
            vals.update({'voucher_order_id': self.id})
            #vals.update({'voucher_code': self.voucher_code_id.code})
            vals.update({'voucher_code_id': self.voucher_code_id.id})
            if self.voucher_promo_id:
                vals.update({'voucher_promo_id': self.voucher_promo_id.id})
            vals.update({'year_id': self.year.id})
            vals.update({'check_number': number})
            
            val_order_line_obj = obj_voucher_order_line.sudo().create(vals)            
            if not val_order_line_obj:
                raise ValidationError("Can't Generate voucher order line, contact administrator!")
            number=number+1
         
        self.is_voucher_generated = True
        next_stage_id =  self.stage_id.next_stage_id
        vals = { 'stage_id': next_stage_id.id}
        #self.write(vals)
        super(VoucherOrder,self).write(vals)
        
    @api.onchange('voucher_type')
    def _voucher_code_onchange(self):
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

    @api.onchange('start_number','end_number')
    def check_voucher_order_line(self):
        if self.start_number and self.end_number:
            if self.start_number == 0 or self.end_number == 0:
                raise UserError('Start number or end number cannot be zero value')
            if self.start_number >= self.end_number:
                raise UserError('End number must be greater than start number')
        
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

    def check_order_overlap(self, voucher_type, voucher_code_id, year, voucher_promo_id, start_number, end_number):
        if voucher_promo_id:
            domain = [
                ('voucher_type','=', voucher_type),
                ('voucher_code_id','=', voucher_code_id),
                ('year','=', year),
                ('voucher_promo_id','=', voucher_promo_id)
            ]
        else:
            domain = [
                ('voucher_type','=', voucher_type),
                ('voucher_code_id','=',voucher_code_id),
                ('year','=', year)
            ]

        _logger.info(domain)
        voucher_order_ids = self.env['weha.voucher.order'].search(domain)
        _logger.info(voucher_order_ids)
        is_overlap = False
        for voucher_order_id in voucher_order_ids:
            _logger.info(voucher_order_ids)
            result = self.overlap(start_number,end_number,voucher_order_id.start_number, voucher_order_id.end_number)
            _logger.info(result)
            if result:
                is_overlap = True
                break 

        if is_overlap:
            raise ValidationError('Overlap Voucher Number')

    def trans_approve(self):
        stage_id = self.stage_id.next_stage_id

        super(VoucherOrder, self).write({'stage_id': stage_id.id})
        
        #Send Notification

        #template_id = self.env.ref('weha_voucher_mgmt.voucher_order_l1_approval_notification_template').id 
        #template = self.env['mail.template'].browse(template_id)
        #template.email_to = self.user_id.partner_id.email
        #template.send_mail(self.id, force_send=True)
    
    def trans_reject(self):
        stage_id = self.stage_id.from_stage_id
        super(VoucherOrder, self).write({'stage_id': stage_id.id})
        #Send Notification
        template_id = self.env.ref('weha_voucher_mgmt.voucher_order_l1_approval_notification_template').id 
        template = self.env['mail.template'].browse(template_id)
        template.email_to = self.user_id.partner_id.email
        template.send_mail(self.id, force_send=True)
        #stage = self.stage_id.next_stage_id.id
        #_logger.info("Stage Here = " + str(self.stage_id.id))
        #_logger.info("Next Stage = " + str(stage))
        #self.write({'stage_id': stage})

    def trans_close(self):
        stage_id = self.stage_id.next_stage_id
        res = super(VoucherOrder, self).write({'stage_id': stage_id.id})
        return res
        
    def trans_request_approval(self):    
    
        next_stage_id =  self.stage_id.next_stage_id
        vals = { 'stage_id': next_stage_id.id}
        #self.write(vals)
        super(VoucherOrder,self).write(vals)

        #Create Schedule Activity
        activity = self.env['mail.activity'].create({
            'activity_type_id': 4,
            'note': 'Voucher Order Approval',
            'res_id': self.id,
            'res_model_id': self.env.ref('model_weha_voucher_order').id,
            'user_id': next_stage_id.approval_user_id.id
        })

        #template_id = self.env.ref('weha_voucher_mgmt.voucher_order_l1_approval_notification_template').id 
        #template = self.env['mail.template'].browse(template_id)
        #_logger.info(next_stage_id.approval_user_id)
        #template.email_to = next_stage_id.approval_user_id.partner_id.email
        #template.send_mail(self.id, force_send=True)
        
    def trans_order_approval(self):    
        stage_id = self.stage_id.next_stage_id
        res = super(VoucherOrder, self).write({'stage_id': stage_id.id})
        return res

    def trans_create_activity(self):
        activity = self.env['mail.activity'].create({
            'activity_type_id': 4,
            'note': 'Voucher Order Approval',
            'res_id': self.id,
            'res_model_id': self.env.ref('weha_voucher_mgmt.model_weha_voucher_order').id,
            'user_id': self.stage_id.approval_user_id.id
        })


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
    
    voucher_promo_id = fields.Many2one('weha.voucher.promo','Promo')
    start_number = fields.Integer(string='Start Number', required=True)
    end_number = fields.Integer(string='End Number', required=True)
    #estimate_voucher_count = fields.Integer('Estimate Voucher Count', compute="_calculate_voucher_count", store=True)
    year = fields.Many2one('weha.voucher.year', 'Year', required=True)
    
    
    kanban_state = fields.Selection([
        ('normal', 'Default'),
        ('done', 'Ready for next stage'),
        ('blocked', 'Blocked')], string='Kanban State')
    
    is_voucher_generated = fields.Boolean('Is Voucher Generated', default=False)
    
    voucher_count = fields.Integer('Voucher Count', compute="_calculate_voucher_count", store=True)
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
        self.check_order_overlap(vals.get('voucher_type'), vals.get('voucher_code_id'), vals.get('year') , vals.get('voucher_promo_id'), vals.get('start_number'),vals.get('end_number'))

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
