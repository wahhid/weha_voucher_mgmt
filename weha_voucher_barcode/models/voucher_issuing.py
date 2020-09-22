from odoo import models


class VoucherIssuing(models.Model):
    _inherit = "weha.voucher.issuing"

    def action_barcode_scan(self):
        action = self.env.ref("weha_voucher_barcode.action_stock_barcodes_read_voucher_issuing").read()[0]
        action["context"] = {
            "default_res_model_id": self.env.ref("weha_voucher_mgmt.model_weha_voucher_issuing").id,
            "default_res_id": self.id,
            "default_received_process": 'issuing',
        }
        return action