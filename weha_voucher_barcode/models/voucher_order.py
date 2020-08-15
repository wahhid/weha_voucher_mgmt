from odoo import models


class VoucherOrder(models.Model):
    _inherit = "voucher.order"

    def action_barcode_scan(self):
        action = self.env.ref("weha_voucher_code.action_stock_barcodes_read_voucher_order").read()[0]
        action["context"] = {
            "default_res_model_id": self.env.ref("weha_voucher_mgmt.weha.voucher.order").id,
            "default_res_id": self.id,
        }
        return action