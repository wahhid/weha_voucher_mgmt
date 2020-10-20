# Copyright 2019 Sergio Teruel <sergio.teruel@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import _, fields, models
from odoo.exceptions import ValidationError
from odoo.fields import first
import logging

_logger = logging.getLogger(__name__)

class WizStockBarcodesReadVoucherScrap(models.TransientModel):
    _name = "wiz.stock.barcodes.read.voucher.scrap"
    _inherit = "wiz.stock.barcodes.read"
    _description = "Wizard to read barcode on voucher scrap"

    voucher_scrap_id = fields.Many2one(comodel_name="weha.voucher.scrap", readonly=True)

    