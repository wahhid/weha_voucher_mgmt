from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
from odoo.tools import formatLang
import logging

_logger = logging.getLogger(__name__)


class ReportVoucherStock(models.AbstractModel):
    """Abstract Model for report template.

    for `_name` model, please use `report.` as prefix then add `module_name.report_name`.
    """

    _name = 'report.weha_voucher_mgmt.print_stock_voucher_view'


    @api.model
    def _get_report_values(self, docids, data=None):
        state = data['form']['state']
        date_start = data['form']['date_start']
        date_end = data['form']['date_end']
        operating_unit_ids = data['form']['operating_unit_ids']
        date_start_obj = datetime.strptime(date_start, DATE_FORMAT)
        date_end_obj = datetime.strptime(date_end, DATE_FORMAT)

        docs = []

        for operating_unit in operating_unit_ids:

            domain = [
                ('create_date','>=',date_start_obj), ('create_date','<=',date_end_obj),
                ('operating_unit_id','=',operating_unit),
                ('state','=', state)
            ]
            line_obj = self.env['weha.voucher.order.line'].search(domain, order='create_date DESC', )

            _logger.info("OPERATING UNIT")
            _logger.info(operating_unit)

            # strSQL = """SELECT *
            #                 FROM weha_voucher_order_line
            #                 WHERE operating_unit_id = {}
            #             """.format(operating_unit)
            # _logger.info(strSQL)
            # self.env.cr.execute(strSQL)
            # records = self.env.cr.fetchall()

            _logger.info("OBJ ORDER LINE")
            _logger.info(line_obj)

            for line in line_obj:
                _logger.info("Line ID : ", str(line.id))
                line_trans = self.env['weha.voucher.order.line.trans'].search([('voucher_order_line_id', '=', line.id)],
                                                                        order='create_date DESC', limit=1)
                docs.append({
                    'name': line.name,
                    'operating_unit_id': line.operating_unit_id.name,
                    'voucher_type': line.voucher_type,
                    'voucher_code_id': line.voucher_code_id.name,
                    'voucher_promo_id': line.voucher_promo_id.name,
                    'state': line.state,
                    'voucher_trans_id': line_trans.name,
                    'loc_fr': line_trans.operating_unit_loc_fr_id.name,
                    'loc_to': line_trans.operating_unit_loc_to_id.name,
                    'trans_type': line_trans.trans_type
                })

        _logger.info(docs)

        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'date_start': date_start_obj.strftime("%d-%m-%Y"),
            'date_end': date_end_obj.strftime("%d-%m-%Y"),
            'docs': docs,
        }
