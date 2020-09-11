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
        _logger.info("Generate Voucher ID = " + str('OKK'))

        start_number = self.start_number
        end_number = self.end_number
        voucher_year = self.year
        obj_voucher_order_line = self.env['weha.voucher.order.line']
        _logger.info("Voucher LINE ID = " + str(obj_voucher_order_line))
        
        number = start_number
        _logger.info("Start Number = " + str(start_number))
        _logger.info("End Number = " + str(end_number))

        # initialize tuple 
        strSQL = """SELECT """ \
                     """check_number """ \
                     """FROM weha_voucher_order_line WHERE year={} AND check_number BETWEEN '{}' AND '{}'""".format(voucher_year, start_number, end_number)

        self.env.cr.execute(strSQL)
        test_tup = self.env.cr.fetchall()

        # printing original tuple 
        _logger.info("The original tuple : " + str(test_tup)) 

        # Check if tuple has any None value 
        # using any() + map() + lambda 
        res_start = any(map(lambda ele: ele is start_number, test_tup))
        res_end = any(map(lambda ele: ele is end_number, test_tup))

        # printing result 
        _logger.info("Does tuple contain value ? : " + str(res_start))
        _logger.info("Does tuple contain value ? : " + str(res_end)) 

        if res_start == False or res_end == False:
            for i in range(start_number,end_number): 
                vals = {}
                vals.update({'operating_unit_id': self.operating_unit_id.id})
                vals.update({'operating_unit_loc_fr_id': self.operating_unit_id.id})
                vals.update({'voucher_order_id': self.id})
                vals.update({'voucher_code': self.voucher_code_id.code})
                vals.update({'voucher_code_id': self.voucher_code_id.id})
                vals.update({'year': voucher_year})
                vals.update({'check_number': number})
                vals.update({'voucher_type': self.voucher_type})
                vals.update({'state': 'open'})
                val_order_line_obj = obj_voucher_order_line.sudo().create(vals)

                _logger.info("Generate Voucher ID = " + str(val_order_line_obj))
                
                if not val_order_line_obj:
                    raise ValidationError("Can't Generate voucher order line, contact administrator!")
                number = number+1
        else:
            raise ValidationError("Can't generate voucher because this number "+ str(start_number) +" <--> "+ str(end_number) +" already exists")
        
        self.is_voucher_generated = True
        
    @api.onchange('voucher_type')
    def _voucher_code_onchange(self):
        self.voucher_code_id = False
        res = {}
        res['domain']={'voucher_code_id':[('voucher_type', '=', self.voucher_type)]}
        return res

    @api.onchange('start_number','end_number')
    def check_voucher_order_line(self):
        if self.start_number and self.end_number:
            if self.start_number == 0 or self.end_number == 0:
                raise UserError('Start number or end number cannot be zero value')
            if self.start_number >= self.end_number:
                raise UserError('End number must be greater than start number')
        
    def trans_approve(self):
        stage_id = self.stage_id.next_stage_id

        super(VoucherOrder, self).write({'stage_id': stage_id.id})
        #Send Notification
        template_id = self.env.ref('weha_voucher_mgmt.voucher_order_l1_approval_notification_template').id 
        template = self.env['mail.template'].browse(template_id)
        template.email_to = self.user_id.partner_id.email
        template.send_mail(self.id, force_send=True)
    
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

    def trans_reject(self):
        stage_id = self.stage_id.from_stage_id
        self.write({'stage_id': stage_id.id})
        template_id = self.env.ref('weha_voucher_mgmt.voucher_order_l1_approval_notification_template').id 
        template = self.env['mail.template'].browse(template_id)
        #_logger.info(next_stage_id.approval_user_id)
        #template.email_to = next_stage_id.approval_user_id.partner_id.email
        #template.send_mail(self.id, force_send=True)
        # self.send_l1_request_mail()

        res = super(VoucherOrder, self).write({'stage_id': stage_id.id})
        return res
    
    def trans_reject(self):
        stage_id = self.stage_id.from_stage_id
        res = super(VoucherOrder, self).write({'stage_id': stage_id.id})
        template_id = self.env.ref('weha_voucher_mgmt.voucher_order_l1_approval_notification_template').id 
        template = self.env['mail.template'].browse(template_id)
        #_logger.info(next_stage_id.approval_user_id)
        #template.email_to = next_stage_id.approval_user_id.partner_id.email
        #template.send_mail(self.id, force_send=True)
        return res
    
    def trans_close(self):
        stage_id = self.stage_id.next_stage_id
        res = super(VoucherOrder, self).write({'stage_id': stage_id.id})
        return res
        
    def trans_request_approval(self):    
        next_stage_id =  self.stage_id.next_stage_id
        vals = { 'stage_id': next_stage_id.id}
        self.write(vals)
        template_id = self.env.ref('weha_voucher_mgmt.voucher_order_l1_approval_notification_template').id 
        template = self.env['mail.template'].browse(template_id)
        _logger.info(next_stage_id.approval_user_id)
        template.email_to = next_stage_id.approval_user_id.partner_id.email
        template.send_mail(self.id, force_send=True)
        
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
    
    start_number = fields.Integer(string='Start Number', required=True)
    end_number = fields.Integer(string='End Number', required=True)
    #estimate_voucher_count = fields.Integer('Estimate Voucher Count', compute="_calculate_voucher_count", store=True)
    year = fields.Integer(string='Year Made')
    
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
        if vals.get('number', '/') == '/':
            seq = self.env['ir.sequence']
            if 'company_id' in vals:
                seq = seq.with_context(force_company=vals['company_id'])
            vals['number'] = seq.next_by_code(
                'weha.voucher.order.sequence') or '/'
            
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
