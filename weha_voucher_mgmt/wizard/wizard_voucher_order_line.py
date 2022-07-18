from odoo import _, api, fields, models, tools
from datetime import date

class WizardVoucherOrderLine(models.TransientModel):
    _name = 'wizard.voucher.order.line'

    def get_voucher_expired(self):
        is_expired = False
        for row in self:
            if row.expired_date:
                if row.expired_date < date.today():
                    is_expired = True
            row.is_expired = is_expired


    name = fields.Char('Name')
    batch_id = fields.Char('Batch #', size=10, readonly=True)
    
    #Customer Code
    customer_id = fields.Many2one('res.partner', 'Customer')
    member_id = fields.Char("Member #", size=20)

    #Transaction
    receipt_number = fields.Char("Receipt #", size=50, reaodnly=True)
    t_id = fields.Char("Terminal #", readonly=True)
    
    #Operating Unit
    operating_unit_id = fields.Many2one(
        string='Operating Unit',
        comodel_name='operating.unit'
    )
    #Voucher Type
    voucher_type = fields.Selection(
        string='Type',
        selection=[('physical', 'Physical'), ('electronic', 'Electronic')],
    )

    #Voucher Trans Type
    voucher_trans_type = fields.Selection(
        string='Trans Type',
        selection=[('1', 'Sales'),('2','Promo'),('3','Redeem'),('4','Employee'),('5','Payment')],
    )
    #Last Voucher Transaction Number
    #voucher_trans_number = fields.Char('Voucher Trans Number', size=200, readonly=True)

    #P-Voucher or E-Voucher
    voucher_code = fields.Char(string='Voucher Code')
    voucher_code_id = fields.Many2one(comodel_name='weha.voucher.code', string='Voucher Code ID', index=True)
    voucher_amount = fields.Float("Amount", related="voucher_code_id.voucher_amount", store=True)
    
    #Voucher Term (Expired Date)
    voucher_terms_id = fields.Many2one(comodel_name='weha.voucher.terms', string='Voucher Terms', index=True)
    
    #Voucher Promo
    voucher_promo_id = fields.Many2one('weha.voucher.promo','Promo')
    is_voucher_promo = fields.Boolean('Is Promo Voucher', default=False, readonly=True)
    tender_type_id = fields.Many2one('weha.voucher.tender.type', 'Tender Type')
    min_card_payment = fields.Float('Min Payment', default=0.0)
    voucher_count_limit = fields.Integer('Max Voucher Count', default=0)
    #tender_type_id = fields.Many2one('weha.voucher.tender.type', 'Tender Type', related='voucher_promo_id.tender_type_id', store=True)
    tender_type = fields.Char('Tender Type', size=20)
    bank_category_id = fields.Many2one('weha.voucher.bank.category', 'Bank Category')
    #bank_category_id = fields.Many2one('weha.voucher.bank.category', 'Bank Category', related='voucher_promo_id.bank_category_id', store=True)
    bank_category = fields.Char('Bank Category', size=20)

    #Check Number Voucher
    check_number = fields.Integer(string='Check Number', group_operator=False)
    #Voucher 12 Digit
    voucher_12_digit = fields.Char('Code 12', size=12)
    #Voucher EAN
    voucher_ean = fields.Char('Code', size=13)
    #Voucher SKU
    voucher_sku = fields.Char('SKU', size=20)
    #Loc Fr
    operating_unit_loc_fr_id = fields.Many2one(string='Loc.Fr', comodel_name='operating.unit')
    #Loc To
    operating_unit_loc_to_id = fields.Many2one(string='Loc.To', comodel_name='operating.unit')
    
    #Expired Date Voucher & Year
    expired_days =fields.Integer('Expired Days', default=0)
    expired_date = fields.Date(string='Expired Date')
    voucher_expired_date = fields.Date(string='Voucher Expired Date')
    booking_expired_date = fields.Datetime(string='Booking Expired Date')
    year_id = fields.Many2one('weha.voucher.year',string='Year')
    
    #Send CRM Status
    is_send_to_crm = fields.Boolean('Send to CRM', default=False)
    send_to_crm_retry_count = fields.Integer('Send to CRM Retry', default=0)
    send_to_crm_message = fields.Char("Send to CRM Message", size=255)


    is_expired = fields.Boolean('Is Expired', compute="get_voucher_expired")
    is_legacy = fields.Boolean('Is Legacy', default=False)
    
    #Operation Information
    source_doc = fields.Char('Source Document', size=100, readonly=True)
    cc_number = fields.Char('CC Number',size=100)
    total_transaction = fields.Float('Total Transaction', default=0.0)
    issued_on = fields.Datetime('Issued On', readonly=True)
    used_on = fields.Datetime('Used On', readonly=True)
    used_operating_unit_id = fields.Many2one('operating.unit', 'Used at')
    scrap_on = fields.Datetime('Scrap On', readonly=True)

    #State Voucher
    state = fields.Selection(
        string='Status',
        selection=[
            ('draft', 'New'), 
            ('inorder', 'In-Order'),
            ('open', 'Open'), 
            ('deactivated','Deactivated'),
            ('activated','Activated'), 
            ('damage', 'Damage'),
            ('transferred','Transferred'),
            ('intransit', 'In-Transit'),
            ('booking', 'Booking'),
            ('reserved', 'Reserved'),
            ('used', 'Used'),
            ('return', 'Return'),
            ('exception', 'Exception Request'),
            ('done','Close'),
            ('scrap','Scrap')
        ],
        default='inorder',
    )