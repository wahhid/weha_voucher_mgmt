from odoo import models, fields, api,  _ 
from odoo.exceptions import UserError, ValidationError
import logging
from random import randrange

_logger = logging.getLogger(__name__)


class VoucherScrap(models.Model):
    _name = 'weha.voucher.scrap'
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
            if rec.stage_id.rejected:
                rec.current_stage = 'rejected'
            
    def _get_default_stage_id(self):
        return self.env['weha.voucher.scrap.stage'].search([], limit=1).id
    
    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        stage_ids = self.env['weha.voucher.scrap.stage'].search([])
        return stage_ids
    
    # @api.depends('line_ids')
    # def _calculate_voucher_count(self):
    #     for row in self:
    #         self.voucher_count = len(self.line_ids)
    
    # def send_l1_request_mail(self):
    #     for rec in self:
    #         template = self.env.ref('weha_voucher_mgmt.voucher_order_l1_approval_notification_template', raise_if_not_found=False)
    #         template.send_mail(rec.id)

    def trans_voucher_scrap(self):
        line = len(self.voucher_return_line_ids)
        _logger.info("Allocate line = " + str(line))

        for i in range(line):
            number_range = len(self.voucher_return_line_ids.number_ranges_ids)
            _logger.info("Number Range = " + str(number_range))

            for rec in range(number_range):

                startnum = self.voucher_return_line_ids.number_ranges_ids.start_num
                endnum = self.voucher_return_line_ids.number_ranges_ids.end_num
                vcode = self.voucher_return_line_ids.voucher_code_id.id
                store_voucher = self.operating_unit_id.id
                sourch_voucher = self.source_operating_unit_id.id
                terms = self.voucher_terms_id.code
                

                strSQL = """SELECT """ \
                     """id,check_number """ \
                     """FROM weha_voucher_order_line WHERE operating_unit_id='{}' AND voucher_code_id='{}' AND state='activated' AND check_number BETWEEN '{}' AND '{}'""".format(store_voucher, vcode, startnum, endnum)

                self.env.cr.execute(strSQL)
                voucher_order_line = self.env.cr.fetchall()
                _logger.info("fetch = " + str(voucher_order_line))


                for row in voucher_order_line:
                    vals = {}
                    # vals.update({'voucher_terms_id': self.voucher_terms_id.id})
                    # vals.update({'expired_date': exp_date})
                    vals.update({'operating_unit_id': sourch_voucher})
                    vals.update({'state': 'delivery'})
                    vals.update({'voucher_return_id': self.id}) 
                    obj_voucher_order_line_ids = search_se.write(vals)

                    order_line_trans_obj = self.env['weha.voucher.order.line.trans']

                    vals = {}
                    vals.update({'name': self.number})
                    vals.update({'trans_date': datetime.now()})
                    vals.update({'voucher_order_line_id': row[0]})
                    vals.update({'trans_type': 'DV'})
                    val_order_line_trans_obj = order_line_trans_obj.sudo().create(vals)
                    _logger.info("str_ean ID = " + str(val_order_line_trans_obj))
        
    @api.onchange('voucher_type')
    def _voucher_code_onchange(self):
        res = {}
        res['domain']={'voucher_code_id':[('voucher_type', '=', self.voucher_type)]}
        return res

    def trans_approve(self):
        stage_id = self.stage_id.next_stage_id
        res = super(VoucherScrap, self).write({'stage_id': stage_id.id})
        return res
    
    def trans_reject(self):
        stage_id = self.stage_id.from_stage_id
        res = super(VoucherScrap, self).write({'stage_id': stage_id.id})
        return res
    
    def trans_close(self):
        stage_id = self.stage_id.next_stage_id
        res = super(VoucherScrap, self).write({'stage_id': stage_id.id})
        return res
        
    def trans_cancelled(self):    
        stage_id = self.stage_id.next_stage_id
        res = super(VoucherScrap, self).write({'stage_id': stage_id.id})
        return res
        

    company_id = fields.Many2one('res.company', 'Company')
    number = fields.Char(string='Return number', default="/",readonly=True)
    ref = fields.Char(string='Source Document', required=False)
    scrap_date = fields.Date('Return Date', required=False, default=lambda self: fields.date.today())
    user_id = fields.Many2one('res.users', string='Requester', default=lambda self: self.env.user and self.env.user.id or False, readonly=True)  
    operating_unit_id = fields.Many2one('operating.unit','Store', related="user_id.default_operating_unit_id")
    source_operating_unit_id = fields.Many2one('operating.unit','Resource Store', related="user_id.default_operating_unit_id.company_id.res_company_return_operating_unit")
    stage_id = fields.Many2one(
        'weha.voucher.order.stage',
        string='Stage',
        group_expand='_read_group_stage_ids',
        default=_get_default_stage_id,
        track_visibility='onchange',
    )
    voucher_order_line_ids = fields.Many2many(comodel_name='weha.voucher.order.line', string='Voucher Lines')
    
    current_stage = fields.Char(string='Current Stage', size=50, compute="_compute_current_stage", readonly=True)
    voucher_scrap_line_ids = fields.One2many(comodel_name='weha.voucher.scrap.line', inverse_name='voucher_scrap_id', string='Scrap Line')
    
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
    
    @api.model
    def create(self, vals):
        if vals.get('number', '/') == '/':
            seq = self.env['ir.sequence']
            if 'company_id' in vals:
                seq = seq.with_context(force_company=vals['company_id'])
            vals['number'] = seq.next_by_code(
                'weha.voucher.scrap.sequence') or '/'
        res = super(VoucherScrap, self).create(vals)

        # Check if mail to the user has to be sent
        #if vals.get('user_id') and res:
        #    res.send_user_mail()
        return res    
    
    def write(self, vals):
        if 'stage_id' in vals:
            # stage_obj = self.env['weha.voucher.scrap.stage'].browse([vals['stage_id']])
            if self.stage_id.approval:
                raise ValidationError("Please using approve or reject button")
            if self.stage_id.opened:
                raise ValidationError("Please Return or Closed Button")
            if self.stage_id.closed:
                raise ValidationError("Can't Move, Because Status Closed")

            #Change To L1, Get User from Param
            # trans_approve = False
            # trans_approve = self.trans_approve()
            # if stage_obj.approval:
            #     if self.stage_id.id != stage_obj.from_stage_id.id:
            #         raise ValidationError('Cannot Process Approval')
            #     # self.send_l1_request_mail()
           
        res = super(VoucherScrap, self).write(vals)
        return res
