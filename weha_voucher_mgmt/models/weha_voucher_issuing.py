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
            if rec.stage_id.approval:
                rec.current_stage = 'approval'
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
    
    def send_notification(self, data):
        self.env['mail.activity'].create(data).action_feedback()

    def process_voucher_issuing(self):
        voucher_issuing_ids = self.env['weha.voucher.issuing'].search([('stage_id.opened','=',True),('is_employee','=',True)])
        for voucher_issuing_id in voucher_issuing_ids:
            _logger.info(voucher_issuing_id.number)
            _logger.info(voucher_issuing_id.current_stage)
            if voucher_issuing_id.is_employee:
                voucher_issuing_id.action_issuing_voucher()
            #voucher_issuing_id.trans_close()
            data =  {
                'activity_type_id': 4,
                'note': 'Voucher Issuing Background Job',
                'res_id': voucher_issuing_id.id,
                'res_model_id': self.env.ref('weha_voucher_mgmt.model_weha_voucher_issuing').id,
                'user_id': voucher_issuing_id.user_id.id,
                'date_deadline': datetime.now() + timedelta(days=2),
                'summary': 'Voucher Issuing Background Job'
            }
            self.send_notification(data)
        
    def action_issuing_voucher(self):
        #if self.voucher_count != self.estimate_voucher_count:
        #    raise ValidationError("Voucher count not match")
        if self.voucher_count == 0:
            raise ValidationError("Issuing Line empty")
        
        if not self.is_employee:
            for voucher_issuing_line_id in self.voucher_issuing_line_ids:
                if voucher_issuing_line_id.state == 'open':
                    vals = {}
                    vals.update({'state': 'issued'})
                    res = voucher_issuing_line_id.sudo().write(vals)

                    vals = {}
                    vals.update({'state': 'activated'})
                    voucher_issuing_line_id.voucher_order_line_id.sudo().write(vals)

                    vals = {}
                    vals.update({'name': self.number})
                    vals.update({'voucher_order_line_id': voucher_issuing_line_id.voucher_order_line_id.id})
                    vals.update({'trans_date': datetime.now()})
                    vals.update({'trans_type': 'AC'})
                    self.env['weha.voucher.order.line.trans'].sudo().create(vals)
            self.trans_close()
        else:
            for voucher_issuing_employee_line_id in self.voucher_issuing_employee_line_ids:
                if voucher_issuing_employee_line_id.state == 'open':
                    values = {}
                        
                    # #Save Voucher Purchase Transaction
                    voucher_trans_purchase_obj = self.env['weha.voucher.trans.purchase']
                    trans_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    values.update({'trans_date': trans_date})
                    values.update({'receipt_number': ''})
                    values.update({'t_id': ''})
                    values.update({'cashier_id': ''})
                    values.update({'store_id': ''})
                    values.update({'member_id': voucher_issuing_employee_line_id.member_id})
                    values.update({'sku': voucher_issuing_employee_line_id.sku + "|" + str(voucher_issuing_employee_line_id.quantity)})
                    values.update({'voucher_type': '4'})
                    
                    #Save Data
                    result = voucher_trans_purchase_obj.sudo().create(values)
                    voucher_issuing_employee_line_id.sudo().trans_close()
            self.sudo().trans_close()
        
    def process_voucher_issuing_line(self):
        _logger.info("Process Voucher Issuing Line")
        if not self.is_employee:
            for voucher_issuing_line_id in self.voucher_issuing_line_ids:
                voucher_order_line_id = voucher_issuing_line_id.voucher_order_line_id
                voucher_order_line_id.write({'state': 'activated'})
                voucher_order_line_id.create_order_line_trans(self.number, 'AC')
                voucher_issuing_line_id.write({'state': 'issued'})    
        else:  
            for voucher_issuing_employee_line_id in self.voucher_issuing_employee_line_ids:
                values = {}
                    
                # #Save Voucher Purchase Transaction
                voucher_trans_purchase_obj = http.request.env['weha.voucher.trans.purchase']
                trans_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                values.update({'trans_date': trans_date})
                values.update({'receipt_number': ''})
                values.update({'t_id': ''})
                values.update({'cashier_id': ''})
                values.update({'store_id': ''})
                values.update({'member_id': voucher_issuing_employee_line_id.member_id})
                values.update({'sku': voucher_issuing_employee_line_id.sku|voucher_issuing_employee_line_id.quantity})
                values.update({'voucher_type': '4'})
                
                #Save Data
                result = voucher_trans_purchase_obj.create(values)

    def trans_issuing_approval(self):
        stage_id = self.env['weha.voucher.issuing.stage'].search([('approval','=', True)], limit=1)
        if not stage_id:
            raise ValidationError('Stage not found')
        res = super(VoucherIssuing, self).write({'stage_id': stage_id.id})

    def trans_approve(self):
        _logger.info("Trans Approve")
        stage_id = self.stage_id.next_stage_id
        res = super(VoucherIssuing, self).write({'stage_id': stage_id.id})

    def trans_close(self):
        stage_id = self.env['weha.voucher.issuing.stage'].search([('closed','=',True)], limit=1)
        super(VoucherIssuing, self).write({'stage_id': stage_id.id})

    @api.depends('stage_id')
    def trans_confirm(self):
        if self.voucher_count == self.estimate_voucher_count:
            stage = self.stage_id.next_stage_id
            if stage:
                self.write({'stage_id': stage.id})
                self.process_voucher_issuing_line()
            else:
                raise ValidationError("Missing next stage configuration")
        else:
            raise ValidationError("Voucher count not match")

    #@api.depends('is_employee')
    def _calculate_voucher_count(self):
        for row in self:
            if not row.is_employee:
                row.voucher_count = len(self.voucher_issuing_line_ids)
            else:
                row.voucher_count = len(self.voucher_issuing_employee_line_ids)


    company_id = fields.Many2one('res.company', 'Company')
    number = fields.Char(string='Order number', default="/",readonly=True)
    ref = fields.Char(string='Source Document', required=True)
    issuing_date = fields.Date('Order Date', required=True, default=lambda self: fields.date.today())
    user_id = fields.Many2one('res.users', string='Requester', default=lambda self: self.env.user and self.env.user.id or False, readonly=True)  
    operating_unit_id = fields.Many2one('operating.unit','Store', related="user_id.default_operating_unit_id")
    is_employee = fields.Boolean('Is Employee', default=False)    

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
    
    estimate_voucher_count = fields.Integer('Voucher #', default=0)
    voucher_count = fields.Integer('Voucher Count', compute="_calculate_voucher_count", store=False)
    
    voucher_issuing_line_ids = fields.One2many(
        comodel_name='weha.voucher.issuing.line', 
        inverse_name='voucher_issuing_id', 
        string='Issued Lines',
    )

    voucher_issuing_employee_line_ids = fields.One2many(
        comodel_name='weha.voucher.issuing.employee.line', 
        inverse_name='voucher_issuing_id', 
        string='Employee Lines',
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
        return res    
    
    def write(self, vals):
        if 'stage_id' in vals:
            stage_obj = self.env['weha.voucher.issuing.stage'].browse([vals['stage_id']])
            if stage_obj.unattended:
                pass
            if self.stage_id.opened:
                raise ValidationError("Please Click Button Ready to Issuing")
            if self.stage_id.closed:
                raise ValidationError("Can not move, status Close")
            if self.stage_id.cancelled:
                raise ValidationError("Can not move, status Cancel")
           
        res = super(VoucherIssuing, self).write(vals)
        return res
