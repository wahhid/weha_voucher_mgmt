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
    voucher_order_id = fields.Many2one('weha.voucher.order', 'Voucher Order #')
    
    manual_entry = fields.Boolean(string="Manual entry")
    voucher_line_id = fields.Many2one(
        comodel_name="weha.voucher.order.line", string="Voucher Line", readonly=True
    )
    log_line_ids = fields.One2many(
        comodel_name="voucher.barcodes.read.log.line",
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

    _name = "voucher.barcodes.read.log.line"
    _description = "Stock barcodes read log lines"

    read_log_id = fields.Many2one(
        comodel_name="voucher.barcodes.read.log",
        string="Scanning log",
        ondelete="cascade",
        readonly=True,
    )
    
    voucher_line_id = fields.Many2one(
        comodel_name="weha.voucher.order.line", string="Voucher Line", readonly=True
    )
