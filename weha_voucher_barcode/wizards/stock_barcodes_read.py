# Copyright 2019 Sergio Teruel <sergio.teruel@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)



class WizStockBarcodesRead(models.AbstractModel):
    _name = "wiz.stock.barcodes.read"
    _inherit = "barcodes.barcode_events_mixin"
    _description = "Wizard to read barcode"
    # To prevent remove the record wizard until 2 days old
    _transient_max_hours = 48

    barcode = fields.Char("Barcode")
    res_model_id = fields.Many2one(comodel_name="ir.model", index=True)
    res_id = fields.Integer(index=True)
    received_process = fields.Selection(
        [
            ('allocate', 'Allocate')
        ],
        'Process'
    )
    manual_entry = fields.Boolean(string="Manual entry data")
    # Computed field for display all scanning logs from res_model and res_id
    # when change product_id
    scan_log_ids = fields.Many2many(
        comodel_name="voucher.barcodes.read.log", compute="_compute_scan_log_ids"
    )
    
    message_type = fields.Selection(
        [
            ("info", "Barcode read with additional info"),
            ("not_found", "No barcode found"),
            ("more_match", "More than one matches found"),
            ("success", "Barcode read correctly"),
        ],
        readonly=True,
    )
    message = fields.Char(readonly=True)


    def _set_messagge_info(self, message_type, message):
        """
        Set message type and message description.
        For manual entry mode barcode is not set so is not displayed
        """
        self.message_type = message_type
        if self.barcode:
            self.message = _("Barcode: %s (%s)") % (self.barcode, message)
        else:
            self.message = "%s" % message

    def process_barcode(self, barcode):
        self._set_messagge_info("success", _("Barcode read correctly"))
        domain = self._barcode_domain(barcode)
        if self.received_process == 'allocate':
            active_id = self.env.context.get('active_id') or False
            if active_id:
                voucher_allocate_id = self.env['weha.voucher.allocate'].browse(active_id)
                domain = [
                    ('voucher_ean', '=', barcode),
                    #('state', '=', 'intransit')
                ]
                voucher_line_order_id = self.env['weha.voucher.order.line'].sudo().search(domain,limit=1)
                if voucher_line_order_id:
                    domain = [
                        ('voucher_order_line_id','=',voucher_line_order_id.id),
                        ('state', '=', 'open')
                    ]
                    voucher_allocate_line_id = self.env['weha.voucher.allocate.line'].sudo().search(domain, limit=1)
                    _logger.info(voucher_allocate_line_id)
                    
                    if not voucher_allocate_line_id:
                        raise ValidationError("No Voucher Allocation found or already received")

                    vals = {}
                    vals.update({'state': 'received'})
                    res = voucher_allocate_line_id.write(vals)

                    vals = {}
                    vals.update({'operating_unit_id': voucher_allocate_id.source_operating_unit.id})
                    vals.update({'state': 'open'})
                    voucher_allocate_line_id.voucher_order_line_id.write(vals)

                    vals = {}
                    vals.update({'name': voucher_allocate_id.number})
                    vals.update({'voucher_order_line_id': voucher_allocate_line_id.voucher_order_line_id.id})
                    vals.update({'trans_date': datetime.now()})
                    vals.update({'operating_unit_loc_fr_id': voucher_allocate_id.operating_unit_id.id})
                    vals.update({'operating_unit_loc_to_id': voucher_allocate_id.source_operating_unit.id})
                    vals.update({'trans_type': 'RV'})
                    self.env['weha.voucher.order.line.trans'].create(vals)
                    self._set_messagge_info("success", _("Voucher Received"))
                else:
                    self._set_messagge_info("not_found", _("Scan Voucher Process Error"))   
            else:
                self._set_messagge_info("not_found", _("Voucher not found"))
        else:
             self._set_messagge_info("not_found", _("Missing process information"))


        # voucher_line = self.env["weha.voucher.order.line"].search(domain)
        # if voucher_line:
        #     if len(voucher_line) > 1:
        #         self._set_messagge_info("more_match", _("More than one product found"))
        #         return
        #     else:
        #         # update state received
        #         vals = {}
        #         vals.update({'state': 'received'})
        #         res = voucher_line.write(vals)
		        
        #         _logger.info('Voucher Line Write : '+ str(res))
        #         # if not res:
		# 		# 	raise ValidationError("Can't write received Voucher!")
				
        #         # obj_order_line_trans = self.env['weha.voucher.order.line.trans']

        #         # vals = {}
        #         # vals.update({'name': obj_request.number})
        #         # vals.update({'voucher_order_line_id': voucher_line.id})
        #         # vals.update({'trans_date': datetime.now()})
        #         # vals.update({'trans_type': 'RV'})
        #         # row = obj_order_line_trans.create(vals)
				
		# 		# if not row:
		# 		# 	raise ValidationError("Can't create Voucher Line Trans!")
				
                
        #         #self.action_product_scaned_post(product)
        #         self.action_done()
        #         return
        # _logger.info('Voucher Line Not found')
        #self._set_messagge_info("not_found", _("Barcode not found"))

    def _barcode_domain(self, barcode):
        return [("voucher_ean", "=", barcode)]

    # Get Started
    def on_barcode_scanned(self, barcode):
        self.barcode = barcode
        self.process_barcode(barcode)

    def check_done_conditions(self):
        # if not self.product_qty:
        #     self._set_messagge_info("info", _("Waiting quantities"))
        #     return False
        if self.manual_entry:
            self._set_messagge_info("success", _("Manual entry OK"))
        return True

    def action_done(self):
        if not self.check_done_conditions():
            return False
        self._add_read_log()
        return True

    def action_cancel(self):
        return True

    # def action_product_scaned_post(self, product):
    #     self.packaging_id = False
    #     if self.product_id != product:
    #         self.lot_id = False
    #     self.product_id = product
    #     self.product_qty = 0.0 if self.manual_entry else 1.0

    # def action_packaging_scaned_post(self, packaging):
    #     self.packaging_id = packaging
    #     if self.product_id != packaging.product_id:
    #         self.lot_id = False
    #     self.product_id = packaging.product_id
    #     self.packaging_qty = 0.0 if self.manual_entry else 1.0
    #     self.product_qty = packaging.qty * self.packaging_qty

    # def action_lot_scaned_post(self, lot):
    #     self.lot_id = lot
    #     self.product_qty = 0.0 if self.manual_entry else 1.0

    # def action_clean_lot(self):
    #     self.lot_id = False

    def action_manual_entry(self):
        return True

    # def _prepare_scan_log_values(self, log_detail=False):
    #     return {
    #         "name": self.barcode,
    #         "location_id": self.location_id.id,
    #         "product_id": self.product_id.id,
    #         "packaging_id": self.packaging_id.id,
    #         "lot_id": self.lot_id.id,
    #         "packaging_qty": self.packaging_qty,
    #         "product_qty": self.product_qty,
    #         "manual_entry": self.manual_entry,
    #         "res_model_id": self.res_model_id.id,
    #         "res_id": self.res_id,
    #     }

    # def _add_read_log(self, log_detail=False):
    #     if self.product_qty:
    #         vals = self._prepare_scan_log_values(log_detail)
    #         self.env["stock.barcodes.read.log"].create(vals)

    #@api.depends("voucher_line_id")
    def _compute_scan_log_ids(self):
        logs = self.env["voucher.barcodes.read.log"].search(
            [
                ("res_model_id", "=", self.res_model_id.id),
                ("res_id", "=", self.res_id)
            ],
            limit=10,
        )
        self.scan_log_ids = logs

    # def reset_qty(self):
    #     self.product_qty = 0
    #     self.packaging_qty = 0

    def action_undo_last_scan(self):
        return True
