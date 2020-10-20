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
            ('allocate', 'Allocate'),
            ('issuing', 'Issuing'),
            ('return', 'Return'),
            ('scrap', 'Scrap'),
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
        _logger.info("Process Barcode")
        self._set_messagge_info("success", _("Barcode read correctly"))
        domain = self._barcode_domain(barcode)
        _logger.info(self.received_process)
        if self.received_process == 'allocate':
            _logger.info("Process Voucher Allocate")
            active_id = self.env.context.get('active_id') or False
            if active_id:
                voucher_allocate_id = self.env['weha.voucher.allocate'].browse(active_id)
                if voucher_allocate_id.current_stage == 'unattended':
                    _logger.info('Allocate Unattended')
                    domain = [
                        ('voucher_ean', '=', barcode),
                        ('operating_unit_id', '=', voucher_return_id.operating_unit_id.id)
                        ('state', '=', 'open')
                    ]
                elif voucher_allocate_id.current_stage == 'progress' or voucher_allocate_id.current_stage == 'receiving':
                    _logger.info('Allocate Intrasit or Received')
                    domain = [
                        ('voucher_ean', '=', barcode),
                        ('operating_unit_id', '=', voucher_return_id.operating_unit_id.id)
                        ('state', '=', 'intransit')
                    ]
                else:
                    _logger.info("Stage Pass")
                    pass

                voucher_order_line_id = self.env['weha.voucher.order.line'].sudo().search(domain,limit=1)
                if voucher_order_line_id:
                    self._set_messagge_info("info", _("Barcode found"))
                    domain = [
                        ('voucher_allocate_id', '=', active_id),
                        ('voucher_order_line_id', '=', voucher_order_line_id.id),
                        ('state', '=', 'open') 
                    ]
                    voucher_allocate_line_id = self.env['weha.voucher.allocate.line'].search(domain,limit=1)
                    if voucher_allocate_line_id:
                        if voucher_allocate_line_id.state == 'open':
                            if voucher_allocate_id.current_stage == 'unattended':
                                self._set_messagge_info("info", _("Allocate Line already exist"))
                            elif voucher_allocate_id.current_stage == 'progress' or voucher_allocate_id.current_stage == 'receiving':
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

                                if voucher_allocate_id.voucher_count == voucher_allocate_id.voucher_received_count:
                                    voucher_allocate_id.sudo().trans_received()    
                            else:
                                pass
                    else:
                        if voucher_allocate_line_id.state == 'open':
                            vals = {
                                'voucher_allocate_id': active_id,
                                'voucher_order_line_id': voucher_order_line_id.id
                            }
                            self.env['weha.voucher.allocate.line'].create(vals)
                            self._set_messagge_info("success", _("Allocate Line Create Successfully"))
                            
                            vals = {
                                'name': self.barcode,
                                'res_model_id': self.res_model_id.id,
                                'res_id': self.res_id,
                                'voucher_allocate_id': self.res_id,
                                'voucher_order_line_id' : voucher_order_line_id.id 
                            }
                            self._add_read_log(vals)
                        else:
                            self._set_messagge_info("not_found", _("Barcode not found"))
                else:
                    self._set_messagge_info("not_found", _("Barcode not found"))

        if self.received_process == 'issuing':
            _logger.info("Process Voucher Issuing")
            active_id = self.env.context.get('active_id') or False
            if active_id:
                voucher_issuing_id = self.env['weha.voucher.issuing'].browse(active_id)
                if voucher_issuing_id.current_stage == 'unattended':
                    _logger.info('Issuing Unattended')
                    domain = [
                        ('voucher_ean', '=', barcode),
                        ('operating_unit_id', '=', voucher_issuing_id.operating_unit_id.id),
                        ('state', '=', 'open')
                    ]
                else:
                    _logger.info("Stage Pass")
                    pass

                voucher_order_line_id = self.env['weha.voucher.order.line'].sudo().search(domain,limit=1)
                if voucher_order_line_id:
                    self._set_messagge_info("info", _("Barcode found"))
                    domain = [
                        ('voucher_issuing_id', '=', voucher_issuing_id.id),
                        ('voucher_order_line_id', '=', voucher_order_line_id.id),
                        ('state', '=', 'open') 
                    ]
                    voucher_issuing_line_id = self.env['weha.voucher.issuing.line'].search(domain,limit=1)
                    if voucher_issuing_line_id:
                        self._set_messagge_info("info", _("Issuing Line already exist"))                               
                    else:
                        vals = {
                            'voucher_issuing_id': active_id,
                            'voucher_order_line_id': voucher_order_line_id.id
                        }
                        self.env['weha.voucher.issuing.line'].create(vals)
                        self._set_messagge_info("success", _("Issuing Line Create Successfully"))
                        
                        vals = {
                            'name': self.barcode,
                            'res_model_id': self.res_model_id.id,
                            'res_id': self.res_id,
                            'voucher_issuing_id': self.res_id,
                            'voucher_order_line_id' : voucher_order_line_id.id 
                        }
                        self._add_read_log(vals)
                else:
                    self._set_messagge_info("not_found", _("Barcode not found"))

        if self.received_process == 'return':
            _logger.info("Process Voucher Return")
            active_id = self.env.context.get('active_id') or False
            if active_id:
                voucher_return_id = self.env['weha.voucher.return'].browse(active_id)
                if voucher_return_id.current_stage == 'unattended':
                    _logger.info('Return Unattended')
                    domain = [
                        ('voucher_ean', '=', barcode),
                        ('operating_unit_id', '=', voucher_return_id.operating_unit_id.id),
                        ('state', '=', 'open')
                    ]
                    voucher_order_line_id = self.env['weha.voucher.order.line'].sudo().search(domain,limit=1)
                    if voucher_order_line_id:
                        self._set_messagge_info("info", _("Barcode found"))
                        domain = [
                            ('voucher_return_id', '=', voucher_return_id.id),
                            ('voucher_order_line_id', '=', voucher_order_line_id.id),
                            ('state', '=', 'open') 
                        ]
                        voucher_return_line_id = self.env['weha.voucher.return.line'].search(domain,limit=1)
                        if voucher_return_line_id:
                            self._set_messagge_info("info", _("Issuing Line already exist"))                               
                        else:
                            vals = {
                                'voucher_return_id': active_id,
                                'voucher_order_line_id': voucher_order_line_id.id
                            }
                            self.env['weha.voucher.return.line'].create(vals)
                            self._set_messagge_info("success", _("Return Line Create Successfully"))
                            
                            vals = {
                                'name': self.barcode,
                                'res_model_id': self.res_model_id.id,
                                'res_id': self.res_id,
                                'voucher_return_id': self.res_id,
                                'voucher_order_line_id' : voucher_order_line_id.id 
                            }
                            self._add_read_log(vals)
                    else:
                        _logger.info("Stage Pass")
                elif voucher_return_id.current_stage == 'progress' or voucher_return_id.current_stage == 'receiving':
                    domain = [
                        ('voucher_ean', '=', barcode),
                        ('operating_unit_id', '=', voucher_return_id.operating_unit_id.id),
                        ('state', '=', 'intransit')
                    ]
                    voucher_order_line_id = self.env['weha.voucher.order.line'].sudo().search(domain,limit=1)
                    if voucher_order_line_id:
                        self._set_messagge_info("info", _("Barcode found"))
                        domain = [
                            ('voucher_return_id', '=', voucher_return_id.id),
                            ('voucher_order_line_id', '=', voucher_order_line_id.id),
                            ('state', '=', 'open') 
                        ]
                        voucher_return_line_id = self.env['weha.voucher.return.line'].search(domain,limit=1)
                        if voucher_return_line_id:
                            vals = {}
                            vals.update({'state': 'received'})
                            res = voucher_return_line_id.write(vals)

                            company_id = self.env.user.company_id
                            vals = {}
                            vals.update({'operating_unit_id': company_id.res_company_return_operating_unit.id})
                            vals.update({'state': 'open'})
                            voucher_return_line_id.voucher_order_line_id.sudo().write(vals)
                            
                            vals = {}
                            vals.update({'name': voucher_return_id.number})
                            vals.update({'voucher_order_line_id': voucher_return_line_id.voucher_order_line_id.id})
                            vals.update({'trans_date': datetime.now()})
                            vals.update({'operating_unit_loc_fr_id': voucher_return_id.operating_unit_id.id})
                            vals.update({'operating_unit_loc_to_id': company_id.res_company_return_operating_unit.id})
                            vals.update({'trans_type': 'RV'})
                            self.env['weha.voucher.order.line.trans'].create(vals)
                            voucher_return_id.sudo().trans_received() 
                        else:
                            self._set_messagge_info("not_found", _("Voucher already received"))  
                    else:
                        self._set_messagge_info("not_found", _("Barcode not found or already received"))  
                else:
                    self._set_messagge_info("not_found", _("Barcode not found"))

        if self.received_process == 'scrap':
            _logger.info("Process Voucher Scrap")
            active_id = self.env.context.get('active_id') or False
            if active_id:
                voucher_scrap_id = self.env['weha.voucher.scrap'].browse(active_id)
                if voucher_scrap_id:
                    domain = [
                        ('voucher_ean', '=', barcode),
                        ('operating_unit_id', '=', voucher_scrap_id.operating_unit_id.id),
                        ('state', '=', 'open')
                    ]
                    voucher_order_line_id = self.env['weha.voucher.order.line'].sudo().search(domain,limit=1)
                    if voucher_order_line_id:
                        self._set_messagge_info("info", _("Barcode found"))
                        domain = [
                            ('voucher_scrap_id', '=', voucher_scrap_id.id),
                            ('voucher_order_line_id', '=', voucher_order_line_id.id),
                            ('state', '=', 'open') 
                        ]
                        voucher_scrap_line_id = self.env['weha.voucher.scrap.line'].search(domain,limit=1)
                        if voucher_scrap_line_id:
                            self._set_messagge_info("info", _("Scrap Line already exist"))                               
                        else:
                            vals = {
                                'voucher_scrap_id': active_id,
                                'voucher_order_line_id': voucher_order_line_id.id
                            }
                            self.env['weha.voucher.scrap.line'].create(vals)
                            self._set_messagge_info("success", _("Scrap Line Create Successfully"))
                            
                            vals = {
                                'name': self.barcode,
                                'res_model_id': self.res_model_id.id,
                                'res_id': self.res_id,
                                'voucher_scrap_id': self.res_id,
                                'voucher_order_line_id' : voucher_order_line_id.id 
                            }
                            self._add_read_log(vals)
                    else:
                        self._set_messagge_info("not_found", _("Barcode not found"))
                else:
                    self._set_messagge_info("not_found", _("Voucher Scrap not found"))
            else:
                self._set_messagge_info("not_found", _("Barcode not found"))

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
        #self._add_read_log()
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

    def _add_read_log(self, vals):
        self.env["voucher.barcodes.read.log"].create(vals)

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
