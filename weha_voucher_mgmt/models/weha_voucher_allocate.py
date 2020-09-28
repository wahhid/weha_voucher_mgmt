from odoo import models, fields, api,  _ 
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta, date
from dateutil.relativedelta import *
import logging
from random import randrange

_logger = logging.getLogger(__name__)


class VoucherAllocate(models.Model):
    _name = 'weha.voucher.allocate'
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
        return self.env['weha.voucher.allocate.stage'].search([], limit=1).id
    
    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        stage_ids = self.env['weha.voucher.allocate.stage'].search([])
        return stage_ids
    
    @api.depends('voucher_allocate_line_ids')
    def _calculate_voucher_count(self):
        self.voucher_count = len(self.voucher_allocate_line_ids)
    

    @api.depends('voucher_allocate_line_ids')
    def _calculate_voucher_received(self):
        count = 0
        for voucher_allocate_line_id in self.voucher_allocate_line_ids:
            if voucher_allocate_line_id.state == 'received':
                count += 1
        self.voucher_received_count = count

    # def send_l1_allocate_mail(self):
    #     for rec in self:
    #         template = self.env.ref('weha_voucher_mgmt.voucher_order_l1_approval_notification_template', raise_if_not_found=False)
    #         template.send_mail(rec.id)

        
    @api.onchange('voucher_type')
    def _voucher_code_onchange(self):
        res = {}
        res['domain']={'voucher_code_id':[('voucher_type', '=', self.voucher_type)]}
        return res


    # def trans_voucher_allocate_activate(self):
    #     line = len(self.voucher_allocate_line_ids)
    #     _logger.info("Allocate line = " + str(line))
    #
    #     for i in range(line):
    #         number_range = len(self.voucher_allocate_line_ids.number_ranges_ids)
    #         _logger.info("Number Range = " + str(number_range))
    #
    #         for rec in range(number_range):
    #
    #             startnum = self.voucher_allocate_line_ids.number_ranges_ids.start_num
    #             endnum = self.voucher_allocate_line_ids.number_ranges_ids.end_num
    #             vcode = self.voucher_allocate_line_ids.voucher_code_id.id
    #             store_voucher = self.operating_unit_id.id
    #             sourch_voucher = self.source_operating_unit.id
    #             terms = self.voucher_terms_id.code
    #
    #             _logger.info("start number = " + str(startnum))
    #             _logger.info("end number = " + str(endnum))
    #
    #             date_now = datetime.now()
    #             str_start_date = str(date_now.year) + "-" + str(date_now.month).zfill(2) + "-" + str(date_now.day).zfill(
    #                 2) + " 23:59:59"
    #             date_now = datetime.strptime(str_start_date, "%Y-%m-%d %H:%M:%S") + relativedelta(days=int(terms))
    #             exp_date = date_now - relativedelta(hours=7)
    #
    #             # obj_voucher_order_line = self.env['weha.voucher.order.line']
    #             # # search_v = obj_voucher_order_line.search(['&',('operating_unit_id','=', store_voucher),('voucher_code_id','=', vcode)])
    #             # search_se = obj_voucher_order_line.search([('check_number','>=',  startnum)])
    #             # _logger.info("Store Voucher ID = " + str(search_se))
    #             # _logger.info("Store Voucher ID = " + str(exp_date))
    #
    #             strSQL = """SELECT """ \
    #                  """id,check_number """ \
    #                  """FROM weha_voucher_order_line WHERE operating_unit_id='{}' AND voucher_code_id='{}' AND state='open' AND check_number BETWEEN '{}' AND '{}'""".format(store_voucher, vcode, startnum, endnum)
    #
    #             self.env.cr.execute(strSQL)
    #             voucher_order_line = self.env.cr.fetchall()
    #             _logger.info("fetch = " + str(voucher_order_line))
    #
    #             # for order_line in ot:
    #             #     check_number = order_line[0]
    #             #     order_id = order_line[1]
    #             #     _logger.info("check_number = " + str(check_number) + ", " + str(order_id))
    #
    #             for row in voucher_order_line:
    #                 vals = {}
    #                 vals.update({'voucher_terms_id': self.voucher_terms_id.id})
    #                 vals.update({'expired_date': exp_date})
    #                 vals.update({'operating_unit_id': sourch_voucher})
    #                 vals.update({'state': 'delivery'})
    #                 vals.update({'voucher_allocate_id': self.id})
    #                 obj_voucher_order_line_ids = voucher_order_line.write(vals)
    #
    #                 order_line_trans_obj = self.env['weha.voucher.order.line.trans']
    #
    #                 vals = {}
    #                 vals.update({'name': self.number})
    #                 vals.update({'trans_date': datetime.now()})
    #                 vals.update({'voucher_order_line_id': row[0]})
    #                 vals.update({'trans_type': 'DV'})
    #                 val_order_line_trans_obj = order_line_trans_obj.sudo().create(vals)
    #                 _logger.info("str_ean ID = " + str(val_order_line_trans_obj))

    def trans_delivery(self):
        stage_id = self.stage_id.next_stage_id
        res = super(VoucherAllocate, self).write({'stage_id': stage_id.id})
        for row in self.voucher_allocate_line_ids:
            row.voucher_order_line_id.write({'state':'intransit'})
        return res

    def trans_confirm_received(self):
        stage_id = self.stage_id.next_stage_id
        res = super(VoucherAllocate, self).write({'stage_id': stage_id.id})
        return res

    def trans_approve(self):
        stage_id = self.stage_id.next_stage_id
        res = super(VoucherAllocate, self).write({'stage_id': stage_id.id})
        return res
    
    def trans_reject(self):
        stage_id = self.stage_id.from_stage_id
        res = super(VoucherAllocate, self).write({'stage_id': stage_id.id})
        return res
    
    def trans_close(self):
        if self.voucher_count != self.voucher_received_count:
            raise ValidationError("Receiving not completed")
        stage_id = self.stage_id.next_stage_id
        res = super(VoucherAllocate, self).write({'stage_id': stage_id.id})
        return res
        
    def trans_allocate_approval(self):    
        if len(self.voucher_allocate_line_ids) == 0:
            raise ValidationError("No Voucher Allocated")
        stage_id = self.stage_id.next_stage_id
        res = super(VoucherAllocate, self).write({'stage_id': stage_id.id})
        return res

    company_id = fields.Many2one('res.company', 'Company')
    number = fields.Char(string='Allocate Number', default="/",readonly=True)
    ref = fields.Char(string='Source Document', required=True)
    allocate_date = fields.Date('Allocate Date', required=False, default=lambda self: fields.date.today(), readonly=True)
    user_id = fields.Many2one('res.users', string='Requester', default=lambda self: self.env.user and self.env.user.id or False, readonly=True)  
    operating_unit_id = fields.Many2one('operating.unit','Store', related="user_id.default_operating_unit_id")
    source_operating_unit = fields.Many2one('operating.unit','Source Store', required=True)
    voucher_type = fields.Selection(
        string='Voucher Type',
        selection=[('physical', 'Physical'), ('electronic', 'Electronic')],
        default='physical'
    )
    voucher_terms_id = fields.Many2one('weha.voucher.terms', 'Voucher Terms', required=True)
    voucher_code_id = fields.Many2one('weha.voucher.code', 'Voucher Code', required=False, readonly=True)
    year_id = fields.Many2one('weha.voucher.year','Year', required=False, readonly=True)
    voucher_promo_id = fields.Many2one('weha.voucher.promo', 'Promo', required=False, readonly=True)
    start_number = fields.Integer(string='Start Number', required=False, readonly=True)
    end_number = fields.Integer(string='End Number', required=False, readonly=True)
    
    stage_id = fields.Many2one(
        'weha.voucher.allocate.stage',
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

    voucher_allocate_line_ids = fields.One2many(
        comodel_name='weha.voucher.allocate.line', 
        inverse_name='voucher_allocate_id',
        string='Allocate Lines',
        domain="[('state','=','open')]"
    )

    voucher_allocate_line_received_ids = fields.One2many(
        comodel_name='weha.voucher.allocate.line', 
        inverse_name='voucher_allocate_id',
        string='Received Lines',
        domain="[('state','=','received')]"
    )

    voucher_request_id = fields.Many2one('weha.voucher.request', 'Voucher Request', required=False)
    voucher_qty = fields.Char(string='Quantity Ordered From Request', size=6, required=False)
    voucher_count = fields.Integer('Voucher Count', compute="_calculate_voucher_count", store=True)
    voucher_received_count = fields.Integer('Voucher Received', compute="_calculate_voucher_received", store=False)

    @api.model
    def create(self, vals):
        if vals.get('number', '/') == '/':
            seq = self.env['ir.sequence']
            if 'company_id' in vals:
                seq = seq.with_context(force_company=vals['company_id'])
            vals['number'] = seq.next_by_code(
                'weha.voucher.allocate.sequence') or '/'
        res = super(VoucherAllocate, self).create(vals)

        # Check if mail to the user has to be sent
        #if vals.get('user_id') and res:
        #    res.send_user_mail()
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


            #Change To L1, Get User from Param
            # trans_approve = False
            # trans_approve = self.trans_approve()
            # if stage_obj.approval:
            #     if self.stage_id.id != stage_obj.from_stage_id.id:
            #         raise ValidationError('Cannot Process Approval')
            #     # self.send_l1_allocate_mail()
           
        res = super(VoucherAllocate, self).write(vals)
        return res
