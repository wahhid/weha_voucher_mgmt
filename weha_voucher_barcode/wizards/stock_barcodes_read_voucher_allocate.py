# Copyright 2019 Sergio Teruel <sergio.teruel@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import _, fields, models
from odoo.exceptions import ValidationError
from odoo.fields import first
import logging

_logger = logging.getLogger(__name__)

class WizStockBarcodesReadVoucherAllocate(models.TransientModel):
    _name = "wiz.stock.barcodes.read.voucher.allocate"
    _inherit = "wiz.stock.barcodes.read"
    _description = "Wizard to read barcode on voucher allocate"

    voucher_allocate_id = fields.Many2one(comodel_name="weha.voucher.allocate", readonly=True)
    voucher_order_id = fields.Many2one(comodel_name="weha.voucher.order.line", readonly=True)

    