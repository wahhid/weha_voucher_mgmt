from odoo import models, fields, api,  _ 
from odoo.exceptions import UserError, ValidationError
import logging
from random import randrange

_logger = logging.getLogger(__name__)


class VoucherStockTransfer(models.Model):
    _name = 'weha.voucher.stock.transfer'
    _rec_name = 'number'
    _order = 'number desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.depends('stage_id')
    def _compute_current_stage(self):
        for rec in self:
            if rec.stage_id.unattended:
                rec.current_stage = 'unattended'
            if rec.stage_id.approval1:
                rec.current_stage = 'approval1'
            if rec.stage_id.approval2:
                rec.current_stage = 'approval2'
            if rec.stage_id.closed:
                rec.current_stage = 'closed'
            if rec.stage_id.progress:
                rec.current_stage = 'progress'
            if rec.stage_id.receiving:
                rec.current_stage = 'receiving'
            if rec.stage_id.cancelled:
                rec.current_stage = 'cancelled'
            if rec.stage_id.rejected:
                rec.current_stage = 'rejected'
            
    def _get_default_stage_id(self):
        return self.env['weha.voucher.stock.transfer.stage'].search([], limit=1).id
    
    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        stage_ids = self.env['weha.voucher.stock.transfer.stage'].search([])
        return stage_ids
    
    # @api.depends('line_ids')
    # def _calculate_voucher_count(self):
    #     for row in self:
    #         self.voucher_count = len(self.line_ids)
    
    # def send_l1_request_mail(self):
    #     for rec in self:
    #         template = self.env.ref('weha_voucher_mgmt.voucher_order_l1_approval_notification_template', raise_if_not_found=False)
    #         template.send_mail(rec.id)

    def trans_voucher_stock_transfer_activate(self):
        line = len(self.voucher_transfer_line_ids)
        _logger.info("Allocate line = " + str(line))

        for i in range(line):
            number_range = len(self.voucher_transfer_line_ids.number_ranges_ids)
            _logger.info("Number Range = " + str(number_range))

            for rec in range(number_range):

                startnum = self.voucher_transfer_line_ids.number_ranges_ids.start_num
                endnum = self.voucher_transfer_line_ids.number_ranges_ids.end_num
                vcode = self.voucher_transfer_line_ids.voucher_code_id.id
                store_voucher = self.operating_unit_id.id
                sourch_voucher = self.source_operating_unit.id
                terms = self.voucher_terms_id.code
                
                # date_now = datetime.now()
                # str_start_date = str(date_now.year) + "-" + str(date_now.month).zfill(2) + "-" + str(date_now.day).zfill(
                #     2) + " 23:59:59"
                # date_now = datetime.strptime(str_start_date, "%Y-%m-%d %H:%M:%S") + relativedelta(days=int(terms))
                # exp_date = date_now - relativedelta(hours=7)

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
                    vals.update({'voucher_stock_transfer_id': self.id}) 
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
<<<<<<< HEAD
        res = super(VoucherStockTransfer, self).write({'stage_id': stage_id.id})
        return res
    
    def trans_reject(self):
        stage_id = self.stage_id.from_stage_id
        res = super(VoucherStockTransfer, self).write({'stage_id': stage_id.id})
        return res
    
    def trans_close(self):
        stage_id = self.stage_id.next_stage_id
        res = super(VoucherStockTransfer, self).write({'stage_id': stage_id.id})
        return res
        
    def trans_stock_transfer_approval(self):    
        stage_id = self.stage_id.next_stage_id
        res = super(VoucherStockTransfer, self).write({'stage_id': stage_id.id})
        return res
=======
        self.write({'stage_id': stage_id.id})
    
    def trans_reject(self):
        stage_id = self.stage_id.from_stage_id
        self.write({'stage_id': stage_id.id})
    
    def trans_close(self):
        stage_id = self.stage_id.next_stage_id
        self.write({'stage_id': stage_id.id})
        
    def trans_request_approval(self):    
        vals = { 'stage_id': self.stage_id.next_stage_id.id}
        self.write(vals)
>>>>>>> wahyu

    # def pass_context_operating_unit(self):
    #     res = self.env['operating.unit'].search([])
    #     return res


    company_id = fields.Many2one('res.company', 'Company')
    number = fields.Char(string='Transfer Number', default="/",readonly=True)
    ref = fields.Char(string='Source Document', required=False)
    transfer_date = fields.Date('Transfer Date', required=False, default=lambda self: fields.date.today())
    user_id = fields.Many2one('res.users', string='Requester', default=lambda self: self.env.user and self.env.user.id or False, readonly=True)  
    operating_unit_id = fields.Many2one('operating.unit','Store', related="user_id.default_operating_unit_id")
    source_operating_unit = fields.Many2one('operating.unit','Source Store', )
    stage_id = fields.Many2one(
        'weha.voucher.stock.transfer.stage',
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
        
    voucher_count = fields.Integer('Voucher Count', compute="_calculate_voucher_count", store=True)
    voucher_transfer_line_ids = fields.One2many(
        string='Vouchers Transfer Lines',
        comodel_name='weha.voucher.stock.transfer.line',
        inverse_name='voucher_transfer_id',
    )
    
    @api.model
    def create(self, vals):
        if vals.get('number', '/') == '/':
            seq = self.env['ir.sequence']
            if 'company_id' in vals:
                seq = seq.with_context(force_company=vals['company_id'])
            vals['number'] = seq.next_by_code(
                'weha.voucher.stock.transfer.sequence') or '/'
        res = super(VoucherStockTransfer, self).create(vals)

        # Check if mail to the user has to be sent
        #if vals.get('user_id') and res:
        #    res.send_user_mail()
        return res    
    
    def write(self, vals):
        if 'stage_id' in vals:
            # stage_obj = self.env['weha.voucher.stock.transfer.stage'].browse([vals['stage_id']])
            if self.stage_id.approval:
                raise ValidationError("Please using approve or reject button")
            if self.stage_id.opened:
                raise ValidationError("Please Stock Transfer or Closed Button")
            if self.stage_id.closed:
                raise ValidationError("Can't Move, Because Status Closed")

            #Change To L1, Get User from Param
            # trans_approve = False
            # trans_approve = self.trans_approve()
            # if stage_obj.approval:
            #     if self.stage_id.id != stage_obj.from_stage_id.id:
            #         raise ValidationError('Cannot Process Approval')
            #     # self.send_l1_request_mail()

        res = super(VoucherStockTransfer, self).write(vals)
        return res
