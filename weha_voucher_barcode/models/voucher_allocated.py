from odoo import models


class VoucherAllocate(models.Model):
    _inherit = "weha.voucher.allocate"

    def action_barcode_scan(self):
        action = self.env.ref("weha_voucher_barcode.action_stock_barcodes_read_voucher_order").read()[0]
        action["context"] = {
            "default_res_model_id": self.env.ref("weha_voucher_mgmt.model_weha_voucher_order").id,
            "default_res_id": self.id,
        }
        return action