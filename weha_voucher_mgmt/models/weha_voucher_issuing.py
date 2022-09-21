from odoo import models, fields, api,  _ 
from odoo.exceptions import UserError, ValidationError
from odoo.addons.weha_voucher_mgmt.common import auth_trust
from datetime import datetime, timedelta, date
import logging
import requests
import json
from random import randrange

_logger = logging.getLogger(__name__)


class VoucherIssuing(models.Model):
    _name = 'weha.voucher.issuing'
    _description = 'Voucher Issuing'
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
        if self.voucher_count == 0:
            raise ValidationError("Issuing Line empty")

        if not self.is_employee:
            for voucher_issuing_line_id in self.voucher_issuing_line_ids:
                if voucher_issuing_line_id.state == 'open':
                    vals = {}
                    vals.update({'state': 'issued'})
                    res = voucher_issuing_line_id.sudo().write(vals)

                    vals = {}
                    vals.update({'state': 'activated', 'issued_on': datetime.today()})
                    vals.update({'source_doc': self.number})
                    vals.update({'member_id': self.member_id})
                    vals.update({'cc_number': self.cc_number})
                    vals.update({'total_transaction': self.total_transaction})
                    voucher_issuing_line_id.voucher_order_line_id.sudo().write(vals)
                    if not voucher_issuing_line_id.voucher_order_line_id.is_voucher_promo:
                        voucher_issuing_line_id.voucher_order_line_id.sudo().calculate_expired()

                    vals = {}
                    vals.update({'name': self.number})
                    vals.update({'voucher_order_line_id': voucher_issuing_line_id.voucher_order_line_id.id})
                    vals.update({'trans_date': datetime.now()})
                    vals.update({'trans_type': 'AC'})
                    self.env['weha.voucher.order.line.trans'].sudo().create(vals)
            
            self.trans_close()
        else:
            for voucher_issuing_employee_line_id in self.voucher_issuing_employee_line_ids.filtered(lambda r: r.state == "open" ):
                voucher_issuing_id = voucher_issuing_employee_line_id.voucher_issuing_id
                operating_unit_id = voucher_issuing_id.operating_unit_id
                mapping_sku_id = voucher_issuing_employee_line_id.mapping_sku_id
                voucher_code_id = mapping_sku_id.voucher_code_id
                member_id = voucher_issuing_employee_line_id.member_id
                for i in range(1,voucher_issuing_employee_line_id.quantity + 1):
                    vals = {}
                    vals.update({'voucher_type': 'electronic'})
                    vals.update({'voucher_code_id': voucher_code_id.id})
                    vals.update({'voucher_terms_id': voucher_code_id.voucher_terms_id.id})
                    vals.update({'member_id': member_id})
                    vals.update({'operating_unit_id': operating_unit_id.id})
                    current_year = self.env['weha.voucher.year'].get_current_year()
                    if not current_year:
                        pass
                    vals.update({'year_id': current_year.id})
                    voucher_number_range_id = self.env['weha.voucher.number.ranges'].sudo().search([('voucher_code_id','=',mapping_sku_id.voucher_code_id.id),('year_id','=',current_year.id)], limit=1)
                    check_number = voucher_number_range_id.sequence_id.next_by_id()
                    vals.update({'check_number': check_number})
                    vals.update({'voucher_trans_type': '4'})
                    vals.update({'voucher_sku': voucher_issuing_employee_line_id.sku})
                    if voucher_issuing_employee_line_id.expired_date:
                        vals.update({'expired_date': voucher_issuing_employee_line_id.expired_date})
                    voucher_order_line_id = self.env['weha.voucher.order.line'].sudo().create(vals)            
                    if not voucher_order_line_id:
                        raise ValidationError("Can't Generate voucher order line, contact administrator!")
                    voucher_order_line_id.write({'state': 'activated', 'issued_on': datetime.now()})
                    voucher_order_line_id.create_order_line_trans(voucher_issuing_id.number, 'AC')
                    #Create Employee Voucher Line
                    self.env['weha.voucher.issuing.employee.voucher.line'].create(
                        {
                            'employee_line_id': voucher_issuing_employee_line_id.id ,
                            'voucher_issuing_id': voucher_issuing_id.id ,
                            'voucher_order_line_id': voucher_order_line_id.id 
                        }
                    )
                    voucher_issuing_employee_line_id.trans_close()
                    #voucher_issuing_employee_line_id.state = 'issued'
            
            #Send Employee Data To Trust
            self.send_employee_data_to_trust()

            #self.state = 'issued'
            self.trans_close()

    def _auth_trust(self):
        _logger.info("_auth_trust")
        config_parameter_obj = self.env['ir.config_parameter'].sudo()
        crm_api_url = config_parameter_obj.get_param('crm_api_url')
        crm_api_username = config_parameter_obj.get_param('crm_api_username')
        crm_api_password = config_parameter_obj.get_param('crm_api_password')

        #url = "http://apiindev.trustranch.co.id/login"
        #payload='barcode=3000030930&password=weha.ID!!2020'

        payload=f'barcode={crm_api_username}&password={crm_api_password}'
        _logger.info(payload)
        
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        try:
            response = requests.request("POST", crm_api_url + "/login", headers=headers, data=payload)
            #json_data = json.loads(response.text)
            str_json_data  = response.text.replace("'"," ")
            json_data = json.loads(str_json_data)
            #_logger.info(response.text)
            _logger.info(json_data['data']['api_token'])
            return json_data['data']['api_token']
        except Exception as err:
            _logger.info("Error Auth Trust")
            _logger.info(err)  

    def send_employee_data_to_trust(self):
        _logger.info("Send Employee Data")
        api_token = self._auth_trust()
        headers = {'content-type': 'text/plain', 'charset':'utf-8'}
        config_parameter_obj = self.env['ir.config_parameter'].sudo()
        crm_api_url = config_parameter_obj.get_param('crm_api_url')
        base_url = 'http://apiindev.trustranch.co.id'
        try:
            for voucher_issuing_employee_line_id  in self.voucher_issuing_employee_line_ids :
                vouchers = []
                for voucher_issuing_employee_voucher_line_id  in  voucher_issuing_employee_line_id.voucher_issuing_employee_voucher_line_ids: 
                    voucher_order_line_id = voucher_issuing_employee_voucher_line_id.voucher_order_line_id
                    vouchers.append(voucher_order_line_id.voucher_ean + ';' + voucher_order_line_id.expired_date.strftime('%Y-%m-%d') + ";" + voucher_order_line_id.voucher_sku)
                data = {
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'time': datetime.now().strftime('%H:%M:%S'),
                    'receipt': self.number,
                    'transaction_id': self.number,
                    'cashier_id': self.number,
                    'store_id': 'H-100',
                    #'member_id': trans_purchase_id.member_id,
                    'member_id': voucher_issuing_employee_line_id.member_id,
                    'vouchers': '|'.join(vouchers)
                }
                _logger.info(data)
                headers = {'Authorization' : 'Bearer ' + api_token}
                req = requests.post('{}/vms/send-voucher'.format(crm_api_url), headers=headers ,data=data)
                _logger.info(req.text)
                if req.status_code != 200:
                    _logger.info(f'Error : {req.status_code}')
                    response_json = req.json()
                    _logger.info(f'Error Message: {response_json}')
                else:
                    response_json = req.json()
                    _logger.info(f'Success : {req.status_code}')
                    _logger.info(f'Data: {response_json}')
        except Exception as err:
            _logger.info("Error Exception")
            _logger.error(err)  

    #Ready for Issuing
    def action_issuing_voucher1(self):
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
                    vals.update({'state': 'activated', 'issued_on': datetime.today()})
                    voucher_issuing_line_id.voucher_order_line_id.sudo().write(vals)
                    voucher_issuing_line_id.voucher_order_line_id.sudo().calculate_expired()

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
                    
                    # voucher_trans_purchase_obj = self.env['weha.voucher.trans.purchase']
                    # trans_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    # values.update({'trans_date': trans_date})
                    # values.update({'receipt_number': ''})
                    # values.update({'t_id': ''})
                    # values.update({'cashier_id': ''})
                    # values.update({'store_id': ''})
                    # values.update({'member_id': voucher_issuing_employee_line_id.member_id})
                    # values.update({'sku': voucher_issuing_employee_line_id.sku + "|" + str(voucher_issuing_employee_line_id.quantity)})
                    # values.update({'voucher_type': '4'})
                    
                    #Create Trans Voucher
                    trans_purchase  = voucher_trans_purchase_obj.sudo().create(values)
                    
                    #Activate Voucher Order Line
                    for line_id in trans_purchase.voucher_trans_purchase_line_ids:
                        voucher_order_line_id  = line_id.voucher_order_line_id
                        voucher_order_line_id
                    voucher_issuing_employee_line_id.sudo().trans_close()                    
            self.sudo().trans_close()

    def issuing_voucher(self):
        seq = self.env['ir.sequence']
        for voucher_trans_purchase_sku_id in self.voucher_trans_purchase_sku_ids:
            for i in range(1,voucher_trans_purchase_sku_id.quantity + 1):
                vals = {}
                vals.update({'member_id': self.member_id})
                vals.update({'operating_unit_id': 3})
                vals.update({'voucher_type': 'electronic'})
                vals.update({'voucher_code_id': voucher_trans_purchase_sku_id.voucher_code_id.id})
                vals.update({'voucher_terms_id': voucher_trans_purchase_sku_id.voucher_code_id.voucher_terms_id.id})
                vals.update({'tender_type': self.tender_type})
                vals.update({'bank_category': self.bank_category})
                if voucher_trans_purchase_sku_id.voucher_promo_id:
                    vals.update({'voucher_promo_id': voucher_trans_purchase_sku_id.voucher_promo_id.id})
                
                vals.update({'year_id': voucher_trans_purchase_sku_id.year_id.id})
                check_number = voucher_trans_purchase_sku_id.voucher_number_range_id.sequence_id.next_by_id()
                vals.update({'check_number': check_number})
                voucher_order_line_id = self.env['weha.voucher.order.line'].sudo().create(vals)            
                if not voucher_order_line_id:
                    raise ValidationError("Can't Generate voucher order line, contact administrator!")
                voucher_order_line_id.write({'state': 'activated', 'issued_on': datetime.today()})
                voucher_order_line_id.create_order_line_trans(self.name, 'AC')

                vals = {
                    'voucher_trans_purchase_id': self.id,
                    'voucher_trans_purchase_sku_id': voucher_trans_purchase_sku_id.id,
                    'voucher_order_line_id': voucher_order_line_id.id
                }
                self.env['weha.voucher.trans.purchase.line'].create(vals)

    def process_voucher_issuing_line(self):
        _logger.info("Process Voucher Issuing Line")
        if not self.is_employee:
            for voucher_issuing_line_id in self.voucher_issuing_line_ids:
                voucher_order_line_id = voucher_issuing_line_id.voucher_order_line_id
                voucher_order_line_id.write({'state': 'activated'})
                #voucher_order_line_id.calculate_expired()
                voucher_order_line_id.create_order_line_trans(self.number, 'AC')
                voucher_issuing_line_id.write({'state': 'issued'})    
        else:  
            for voucher_issuing_employee_line_id in self.voucher_issuing_employee_line_ids:
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
                values.update({'sku': voucher_issuing_employee_line_id.sku|voucher_issuing_employee_line_id.quantity})
                values.update({'voucher_type': '4'})
                
                #Save Data
                result = voucher_trans_purchase_obj.create(values)
 
    def trans_issuing_approval(self):
        stage_id = self.env['weha.voucher.issuing.stage'].search([('approval','=', True)], limit=1)
        if not stage_id:
            raise ValidationError('Stage not found')
        res = super(VoucherIssuing, self).write({'stage_id': stage_id.id})
        #Create Schedule Activity
        operating_unit_id = self.operating_unit_id
        for approval_user_id in operating_unit_id.approval_user_ids:
            data = {
                'activity_type_id': 4,
                'note': 'Voucher Issuing for Approval',
                'res_id': self.id,
                'res_model_id': self.env.ref('weha_voucher_mgmt.model_weha_voucher_issuing').id,
                'user_id': approval_user_id.id,
                'date_deadline': datetime.now() + timedelta(days=2),
                'summary': 'Voucher Issuing for Approval'
            }
            self.send_notification(data)

    def trans_issuing_finance_approval(self):
        stage_id = self.env['weha.voucher.issuing.stage'].search([('approval','=', True)], limit=1)
        if not stage_id:
            raise ValidationError('Stage not found')
        res = super(VoucherIssuing, self).write({'stage_id': stage_id.id})

        #Create Schedule Activity
        operating_unit_id = self.operating_unit_id
        for approval_user_id in operating_unit_id.approval_user_ids:
            data = {
                'activity_type_id': 4,
                'note': 'Voucher Issuing for Finance Approval',
                'res_id': self.id,
                'res_model_id': self.env.ref('weha_voucher_mgmt.model_weha_voucher_issuing').id,
                'user_id': approval_user_id.id,
                'date_deadline': datetime.now() + timedelta(days=2),
                'summary': 'Voucher Issuing for Finance Approval'
            }
            self.send_notification(data) 

    def trans_approve(self):
        _logger.info("Trans Approve")
        stage_id = self.stage_id.next_stage_id
        res = super(VoucherIssuing, self).write({'stage_id': stage_id.id})
        #Create Schedule Activity
        operating_unit_id = self.operating_unit_id
        for requester_user_id in operating_unit_id.requester_user_ids:
            data = {
                'activity_type_id': 4,
                'note': 'Voucher Issuing was Approved',
                'res_id': self.id,
                'res_model_id': self.env.ref('weha_voucher_mgmt.model_weha_voucher_issuing').id,
                'user_id': requester_user_id.id,
                'date_deadline': datetime.now() + timedelta(days=2),
                'summary': 'Voucher Issuing was Approved'
            }
            self.send_notification(data)

    def trans_reject(self):
        stage_id = self.env['weha.voucher.issuing.stage'].search([('rejected','=', True)], limit=1)
        if not stage_id:
            raise ValidationError("Stage not found")
        res = super(VoucherIssuing, self).write({'stage_id': stage_id.id})
        #Create Schedule Activity
        operating_unit_id = self.operating_unit_id
        for requester_user_id in operating_unit_id.requester_user_ids:
            data = {
                'activity_type_id': 4,
                'note': 'Voucher Issuing was rejected',
                'res_id': self.id,
                'res_model_id': self.env.ref('weha_voucher_mgmt.model_weha_voucher_issuing').id,
                'user_id': requester_user_id.id,
                'date_deadline': datetime.now() + timedelta(days=2),
                'summary': 'Voucher Issuing was rejected'
            }
            self.send_notification(data)

    def trans_close(self):
        stage_id = self.env['weha.voucher.issuing.stage'].search([('closed','=',True)], limit=1)
        super(VoucherIssuing, self).write({'stage_id': stage_id.id})

    def trans_cancelled(self):
        stage_id = self.env['weha.voucher.issuing.stage'].search([('cancelled','=', True)], limit=1)
        if not stage_id:
            raise ValidationError('Stage not found')
        super(VoucherIssuing, self).write({'stage_id': stage_id.id})   
        for voucher_issuing_line_id in self.voucher_issuing_line_ids:
            if voucher_issuing_line_id.state == 'open':
                voucher_issuing_line_id.state = 'cancelled'

    def trans_force_cancel(self):
        for voucher_issuing_line_id in self.voucher_issuing_line_ids:
            if voucher_issuing_line_id.state == 'issued':

                vals = {'state': 'cancelled'}
                voucher_issuing_line_id.write(vals)

                vals = {
                    'state': 'open',
                    'issued_on': False,
                }
                
                voucher_issuing_line_id.voucher_order_line_id.sudo().write(vals)
                if not voucher_issuing_line_id.voucher_order_line_id.is_voucher_promo:
                    #voucher_issuing_line_id.voucher_order_line_id.sudo().calculate_expired()
                    voucher_issuing_line_id.voucher_order_line_id.sudo().write({'expired_date': False})

                vals = {}
                vals.update({'name': self.number})
                vals.update({'voucher_order_line_id': voucher_issuing_line_id.voucher_order_line_id.id})
                vals.update({'trans_date': datetime.now()})
                vals.update({'trans_type': 'FL'})
                self.env['weha.voucher.order.line.trans'].sudo().create(vals)

                vals = {}
                vals.update({'name': self.number})
                vals.update({'voucher_order_line_id': voucher_issuing_line_id.voucher_order_line_id.id})
                vals.update({'trans_date': datetime.now()})
                vals.update({'trans_type': 'OP'})
                self.env['weha.voucher.order.line.trans'].sudo().create(vals)
        
        stage_id = self.env['weha.voucher.issuing.stage'].search([('cancelled','=',True)], limit=1)
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

    def print_report_pdf(self): 
        data = {
            'ids': self.ids,
            'model':'weha.voucher.issuing',
            'form': {
                'voucher_issuing_id': self.id,
            },
        }
        return self.env.ref('weha_voucher_mgmt.print_voucher_issuing_employee').report_action(self, data=data)

    def print_report_excel(self): 
        data = {
            'ids': self.ids,
            'model':'weha.voucher.issuing',
            'form': {
                'voucher_issuing_id': self.id,
            },
        }
        return self.env.ref('weha_voucher_mgmt.print_voucher_issuing_employee_xlsx').report_action(self, data=data)

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
    is_employee = fields.Boolean('Is Employee', default=False, readonly=True)    

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
    
    cc_number = fields.Char('CC Number',size=100)
    member_id = fields.Char('Member ID / Nama Customer',size=100)
    total_transaction = fields.Float('Total Transaction', default=0.0)
    

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

    voucher_issuing_file_line_ids = fields.One2many(
        comodel_name='weha.voucher.issuing.file.line', 
        inverse_name='voucher_issuing_id', 
        string='File Lines',
    )

    # _sql_constraints = [
    #     ('ref_unique', 'unique(ref)', 'Source Document already exists!')
    # ]

    @api.model
    def create(self, vals):
        stage_id = self.env['weha.voucher.issuing.stage'].search([('closed','=','True')], limit=1)
        if not stage_id:
            raise ValidationError('Stage not found')
        voucher_issuing_id = self.env['weha.voucher.issuing'].search([('ref','=', vals['ref']),('stage_id','=',stage_id.id)], limit=1)
        if voucher_issuing_id:
            raise ValidationError('Source Document already exist')

        if 'cc_number' in vals.keys():
            if vals['cc_number']:
                if len(vals['cc_number']) != 8:
                    raise ValidationError("CC Number must be 8 digit!")
                    
        if vals.get('number', '/') == '/':
            seq = self.env['ir.sequence']
            if 'company_id' in vals:
                seq = seq.with_context(force_company=vals['company_id'])
            vals['number'] = seq.next_by_code(
                'weha.voucher.issuing.sequence') or '/'
        res = super(VoucherIssuing, self).create(vals)
        return res    
    
    def write(self, vals):
        if 'ref' in vals.keys():
            stage_id = self.env['weha.voucher.issuing.stage'].search([('closed','=','True')], limit=1)
            if not stage_id:
                raise ValidationError('Stage not found')
            voucher_issuing_id = self.env['weha.voucher.issuing'].search([('ref','=', vals['ref']),('stage_id','=',stage_id.id)], limit=1)
            if voucher_issuing_id:
                raise ValidationError('Source Document already exist')

        if 'cc_number' in vals.keys():
            if vals['cc_number']:
                if len(vals['cc_number']) != 8:
                    raise ValidationError("CC Number must be 8 digit!")
                    
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
