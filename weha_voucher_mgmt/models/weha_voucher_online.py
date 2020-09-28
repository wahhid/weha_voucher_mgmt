from odoo import models, fields, api,  _ 
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
import logging
from random import randrange


_logger = logging.getLogger(__name__)


TRANSACTION_TYPE_SELECTIONS = [
    ('sales', 'Sales'),
    ('redeem', 'Redeem'),
    ('promo', 'Promo'),
    ('sales', 'Sales'),
]

class VoucherPurchase(models.Model):
    _name = "voucher.purchase"

    name = fields.Char("Trans #", size=100, required=True)
    voucher_type = fields.Selection("Voucher Type", size=100)
    #transaction_type = fields.
    trans_date = fields.Datetime("Date", default=datetime.now())
    receipt_number = fields.Char("Receipt #", size=100)
    cashier_id= fields.Char("Cashier", size=100)
    store_id = fields.Char("Store", size=100)
    sku = fields.Char("SKU #", size=100)
    quantity = fields.Integer("Quantity")
    amount = fields.Float("Amount", default=0.0)
    member_id = fields.Char("Member ID", size=100)
    point = fields.Integer("Point")
    return_code = fields.Char("Return Code", size=10)
    status_1 = fields.Char("Status 1",size=10)
    status_1_date = fields.Datetime("Status 1 Date")
    status_2 = fields.Char("Status 2",size=10)
    status_2_date = fields.Datetime("Status 2 Date")


class VoucherPayment(models.Model):
    _name = "voucher.payment"

    name = fields.Char("Trans #", size=100, required=True)
    trans_date = fields.Datetime("Date", default=datetime.now())
    receipt_number = fields.Char("Receipt #", size=100)
    cashier_id= fields.Char("Cashier", size=100)
    store_id = fields.Char("Store", size=100)
    sku = fields.Char("SKU #", size=100)
    quantity = fields.Integer("Quantity")
    amount = fields.Float("Amount", default=0.0)
    voucher_type = fields.Char("Voucher Type", size=100)
    member_id = fields.Char("Member ID", size=100)
    point = fields.Integer("Point")
    return_code = fields.Char("Return Code", size=10)
    status_1 = fields.Char("Status 1",size=10)
    status_1_date = fields.Datetime("Status 1 Date")
    status_2 = fields.Char("Status 2",size=10)
    status_2_date = fields.Datetime("Status 2 Date")



