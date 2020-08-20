# Copyright 2019 Sergio Teruel <sergio.teruel@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import _, fields, models
from odoo.exceptions import ValidationError
from odoo.fields import first


class WizStockBarcodesReadVoucherOrder(models.TransientModel):
    _name = "wiz.stock.barcodes.read.voucher.order"
    _inherit = "wiz.stock.barcodes.read"
    _description = "Wizard to read barcode on voucher order"

    name = fields.Char()
    # voucher_order_id = fields.Many2one(comodel_name="weha.voucher.order", readonly=True)
    voucher_order_id = fields.Many2one(comodel_name="weha.voucher.order.line", readonly=True)

    # def name_get(self):
    #     return [
    #         (
    #             rec.id,
    #             "{} - {} - {}".format(
    #                 _("Barcode reader"), rec.voucher_order_id.name, self.env.user.name
    #             ),
    #         )
    #         for rec in self
    #     ]
