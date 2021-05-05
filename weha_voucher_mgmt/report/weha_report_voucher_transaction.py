from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
from odoo.tools import formatLang
import logging

_logger = logging.getLogger(__name__)


class ReportVoucherTransactionDetail(models.AbstractModel):
    """Abstract Model for report template.

    for `_name` model, please use `report.` as prefix then add `module_name.report_name`.
    """

    _name = 'report.weha_voucher_mgmt.weha_voucher_transaction_detail_view'


    @api.model
    def _get_report_values(self, docids, data=None):
        state = data['form']['state']
        date_start = data['form']['date_start']
        date_end = data['form']['date_end']
        operating_unit_ids = data['form']['operating_unit_ids']
        date_start_obj = datetime.strptime(date_start, DATE_FORMAT)
        _logger.info(date_start_obj)
        date_end_obj = datetime.strptime(date_end, DATE_FORMAT)
        _logger.info(date_end_obj)

        docs = []
        if state == 'US':
            strSQL = """
                SELECT a.trans_date, d.name as operating_unit_name, b.voucher_sku, b.voucher_ean FROM weha_voucher_order_line_trans a
                LEFT JOIN weha_voucher_order_line b ON b.id = a.voucher_order_line_id
                LEFT JOIN weha_voucher_trans_status c ON c.name = a.name
                LEFT JOIN operating_unit d ON d.code = c.store_id
                WHERE trans_type='{}' AND DATE(a.trans_date) BETWEEN '{}' AND '{}'
                ORDER BY a.trans_date
            """.format(state, date_start, date_end)
        _logger.info(strSQL)
    
        self.env.cr.execute(strSQL)
        rows = self.env.cr.fetchall()
        for row in rows:
            trans_date = datetime.strptime(str(row[0]).split(".")[0], DATETIME_FORMAT)
            vals = {
                'trans_date': trans_date.strftime("%d-%m-%Y"),
                'store_id': row[1],
                'voucher_sku': row[2],
                'voucher_ean': row[3] 
            }
            docs.append(vals)
        _logger.info(docs)
    
        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'date_start': date_start_obj.strftime("%d-%m-%Y"),
            'date_end': date_end_obj.strftime("%d-%m-%Y"),
            'docs': docs,
        }
