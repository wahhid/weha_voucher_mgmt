from odoo import models, fields, api,  _ 
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta, date
<<<<<<< HEAD
from dateutil.relativedelta import *
=======
>>>>>>> wahyu
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
            if rec.stage_id.approval:
                rec.current_stage = 'approval'
            if rec.stage_id.opened:
                rec.current_stage = 'open'
            if rec.stage_id.progress:
                rec.current_stage = 'progress'
            if rec.stage_id.receiving:
                rec.current_stage = 'receiving'
            if rec.stage_id.cancelled:
                rec.current_stage = 'cancelled'
            if rec.stage_id.rejected:
                rec.current_stage = 'rejected'
    
<<<<<<< HEAD
    # @api.depends('line_ids')
    # def _calculate_voucher_count(self):
    #     for row in self:
    #         self.voucher_count = len(self.line_ids)

    def send_l1_request_mail(self):
        for rec in self:
            template = self.env.ref('weha_voucher_mgmt.voucher_request_l1_approval_notification_template', raise_if_not_found=False)
            template.send_mail(rec.id)

    def trans_voucher_request_activate(self):
        for i in range(len(self.voucher_request_line_ids)):
            for rec in range(len(self.voucher_request_line_ids.number_ranges_ids)):
                startnum = self.voucher_request_line_ids.number_ranges_ids.start_num
                endnum = self.voucher_request_line_ids.number_ranges_ids.end_num
                vcode = self.voucher_request_line_ids.voucher_code_id.id
                sourch_voucher = self.user_id.default_operating_unit_id.company_id.res_company_request_operating_unit.id
                
                exp_date = datetime.now() + relativedelta(days=terms)

                # obj_voucher_order_line = self.env['weha.voucher.order.line']
                # search_v = obj_voucher_order_line.search(['&',('operating_unit_id','=', sourch_voucher),('voucher_code_id','=', vcode)])
                # search_se = search_v.search(['&',('check_number','>=',  startnum),('check_number','<=', endnum)])

                strSQL = """SELECT """ \
                     """id,check_number """ \
                     """FROM weha_voucher_order_line WHERE operating_unit_id='{}' AND voucher_code_id='{}' AND state='open' AND check_number BETWEEN '{}' AND '{}'""".format(sourch_voucher, vcode, startnum, endnum)

                self.env.cr.execute(strSQL)
                voucher_order_line = self.env.cr.fetchall()
                _logger.info("fetch = " + str(voucher_order_line))

                for row in voucher_order_line:
                    vals = {}
                    vals.update({'voucher_terms_id': self.voucher_terms_id.id})
                    vals.update({'expired_date': exp_date})
                    vals.update({'operating_unit_loc_to_id': self.operating_unit_id})
                    vals.update({'voucher_request_id': self.id}) 
                    obj_voucher_order_line_ids = voucher_order_line.write(vals)

                    # order_line_trans_obj = self.env['weha.voucher.order.line.trans']

                    # vals = {}
                    # vals.update({'name': self.number})
                    # vals.update({'trans_date': datetime.now()})
                    # vals.update({'voucher_order_line_id': row[0]})
                    # vals.update({'trans_type': 'DV'})
                    # val_order_line_trans_obj = order_line_trans_obj.sudo().create(vals)
                    # _logger.info("str_ean ID = " + str(val_order_line_trans_obj))
        

    def trans_approve(self):
        stage_id = self.stage_id.next_stage_id
        # self.send_l1_request_mail()
        res = super(WeheVoucherRequest, self).write({'stage_id': stage_id.id})
        return res
    
    def trans_progress(self):
        stage_id = self.stage_id.from_stage_id
        res = super(WeheVoucherRequest, self).write({'stage_id': stage_id.id})
        return res
    
    def trans_receiving(self):
        stage_id = self.stage_id.next_stage_id
        res = super(WeheVoucherRequest, self).write({'stage_id': stage_id.id})
        return res
    
    def trans_reject(self):
        stage_id = self.stage_id.from_stage_id
        res = super(WeheVoucherRequest, self).write({'stage_id': stage_id.id})
        return res
=======
    @api.depends('line_ids')
    def _calculate_voucher_count(self):
        for row in self:
            self.voucher_count = len(self.line_ids)

    def trans_voucher_request_activate(self):
        for i in range(len(self.voucher_request_line_ids)):
            for rec in range(len(self.voucher_request_line_ids.request_line_range_ids)):
                startnum = self.voucher_request_line_ids.request_line_range_ids.start_num
                endnum = self.voucher_request_line_ids.request_line_range_ids.end_num
                vcode = self.voucher_request_line_ids.voucher_code_id.id
                sourch_voucher = self.user_id.default_operating_unit_id.company_id.res_company_request_operating_unit.id
                
                obj_voucher_order_line = self.env['weha.voucher.order.line']
                search_v = obj_voucher_order_line.search(['&',('operating_unit_id','=', sourch_voucher),('voucher_code_id','=', vcode)])
                search_se = search_v.search(['&',('check_number','>=',  startnum),('check_number','<=', endnum)])

                for row in search_se:
                    vals = {}
                    vals.update({'operating_unit_id': self.operating_unit_id.id})
                    vals.update({'state': 'activated'})
                    vals.update({'voucher_request_id': self.id}) 
                    obj_voucher_order_line_ids = search_se.write(vals)

                    order_line_trans_obj = self.env['weha.voucher.order.line.trans']

                    vals = {}
                    vals.update({'name': self.number})
                    vals.update({'trans_date': datetime.now()})
                    vals.update({'voucher_order_line_id': row.id})
                    vals.update({'trans_type': 'AC'})
                    val_order_line_trans_obj = order_line_trans_obj.sudo().create(vals)
                    _logger.info("str_ean ID = " + str(val_order_line_trans_obj))
        

    def trans_approve1(self):
        vals = { 'stage_id': self.stage_id.next_stage_id.id}
        self.write(vals)
    
    def trans_approve2(self):
        vals = { 'stage_id': self.stage_id.next_stage_id.id}
        self.write(vals)
>>>>>>> wahyu

    def trans_request_approval(self):    
        vals = { 'stage_id': self.stage_id.next_stage_id.id}
        self.write(vals)

    company_id = fields.Many2one('res.company', 'Company')
    number = fields.Char(string='Request number', default="/",readonly=True)
    date_request = fields.Date('Date Request', default=lambda self: fields.date.today())
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
    voucher_terms_id = fields.Many2one('weha.voucher.terms', 'Voucher Terms', required=False)
    color = fields.Integer(string='Color Index')
    
    kanban_state = fields.Selection([
        ('normal', 'Default'),
        ('done', 'Ready for next stage'),
        ('blocked', 'Blocked')], string='Kanban State')

    voucher_count = fields.Integer('Voucher Count', compute="_calculate_voucher_count", store=True)

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
            # stage_obj = self.env['weha.voucher.request.stage'].browse([vals['stage_id']])
            if self.stage_id.l1:
                raise ValidationError("Please using approve or reject button")
            if self.stage_id.l2:
                raise ValidationError("Please using approve or reject button")
            if self.stage_id.opened:
                raise ValidationError("Please Close Request")

            #Change To L1, Get User from Param
            # trans_approve = False
            # trans_approve = self.trans_approve()
            # if stage_obj.approval:
            #     if self.stage_id.id != stage_obj.from_stage_id.id:
            #         raise ValidationError('Cannot Process Approval')
            #     # self.send_l1_request_mail()

        res = super(WeheVoucherRequest, self).write(vals)
        return res