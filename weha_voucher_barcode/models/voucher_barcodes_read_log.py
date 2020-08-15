# Copyright 2019 Sergio Teruel <sergio.teruel@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class VoucherBarcodesReadLog(models.Model):
    _name = "voucher.barcodes.read.log"
    _description = "Log barcode scanner"
    _order = "id DESC"

    name = fields.Char(string="Barcode Scanned")
    res_model_id = fields.Many2one(comodel_name="ir.model", index=True)
    res_id = fields.Integer(index=True)
    voucher_order_id = fields.Many2one('voucher.order', 'Voucher Order #')
    voucher_allocated_id = fields.Many2one('voucher.allocated', 'Voucher Allocated #')
    voucher_request_id = fields.Many2one('voucher.request', 'Voucher Request #')
    voucher_transfer_id = fields.Many2one('voucher.transfer', 'Voucher Transfer #')
    voucher_return_id = fields.Many2one('voucher.return', 'Voucher Return #')
    voucher_scrap_id = fields.Many2one('voucher.scrap', 'Voucher Scrap #')
    manual_entry = fields.Boolean(string="Manual entry")
    log_line_ids = fields.One2many(
        comodel_name="stock.barcodes.read.log.line",
        inverse_name="read_log_id",
        string="Scanning log details",
    )


class VoucherBarcodesReadLogLine(models.Model):
    """
    The goal of this model is store detail about scanning log, for example,
    when user read in pickings the product quantity can be distributed in more
    than one stock move line.
    This help to know what records have been affected by a scanning read.
    """

    _name = "stock.barcodes.read.log.line"
    _description = "Stock barcodes read log lines"

    read_log_id = fields.Many2one(
        comodel_name="stock.barcodes.read.log",
        string="Scanning log",
        ondelete="cascade",
        readonly=True,
    )
    
    voucher_line_id = fields.Many2one(
        comodel_name="voucher_line_id", string="Voucher Line", readonly=True
    )
