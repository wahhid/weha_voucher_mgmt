from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
from odoo.tools import formatLang
import logging

_logger = logging.getLogger(__name__)


class ReportVoucherTransactionDetailXlsx(models.AbstractModel):
    """Abstract Model for report template.

    for `_name` model, please use `report.` as prefix then add `module_name.report_name`.
    """

    _name = 'report.weha_voucher_mgmt.weha_voucher_transaction_detail_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):
        _logger.info(data)
        state = data['form']['state']
        date_start = data['form']['date_start']
        date_end = data['form']['date_end']
        operating_unit_ids = data['form']['operating_unit_ids']
        voucher_promo_ids = data['form']['voucher_promo_ids']
        date_start_obj = datetime.strptime(date_start, DATE_FORMAT)
        _logger.info(date_start_obj)
        date_end_obj = datetime.strptime(date_end, DATE_FORMAT)
        _logger.info(date_end_obj)

        docs = {}
        if state == 'US':
            if voucher_promo_ids:
                strSQL = """
                    SELECT a.trans_date, d.name as operating_unit_name, 
                        b.voucher_sku, e.name as voucher_name,
                        c.receipt_number, c.t_id, c.member_id, f.name as promo_name, b.voucher_ean,
                        e.voucher_amount
                    FROM weha_voucher_order_line_trans a
                    LEFT JOIN weha_voucher_order_line b ON b.id = a.voucher_order_line_id
                    LEFT JOIN weha_voucher_trans_status c ON c.name = a.name
                    LEFT JOIN operating_unit d ON d.code = c.store_id
                    LEFT JOIN weha_voucher_code e ON e.id = b.voucher_code_id
                    LEFT JOIN weha_voucher_promo f ON f.id = b.voucher_promo_id
                    WHERE trans_type='{}' AND DATE(a.trans_date) BETWEEN '{}' AND '{}'
                    AND b.operating_unit_id in {} AND b.voucher_promo_id in {}
                    ORDER BY d.name, a.trans_date
                """.format(state, date_start, date_end, tuple(operating_unit_ids), tuple(voucher_promo_ids))
            else:
                 strSQL = """
                    SELECT a.trans_date, d.name as operating_unit_name, 
                        b.voucher_sku, e.name as voucher_name,
                        c.receipt_number, c.t_id, c.member_id, f.name as promo_name, b.voucher_ean,
                        e.voucher_amount
                    FROM weha_voucher_order_line_trans a
                    LEFT JOIN weha_voucher_order_line b ON b.id = a.voucher_order_line_id
                    LEFT JOIN weha_voucher_trans_status c ON c.name = a.name
                    LEFT JOIN operating_unit d ON d.code = c.store_id
                    LEFT JOIN weha_voucher_code e ON e.id = b.voucher_code_id
                    LEFT JOIN weha_voucher_promo f ON f.id = b.voucher_promo_id
                    WHERE trans_type='{}' AND DATE(a.trans_date) BETWEEN '{}' AND '{}'
                    AND b.operating_unit_id in {}
                    ORDER BY d.name, a.trans_date
                """.format(state, date_start, date_end, tuple(operating_unit_ids))

        _logger.info(strSQL)
    
        self.env.cr.execute(strSQL)
        rows = self.env.cr.fetchall()
        detail = []
        for row in rows:
            trans_date = datetime.strptime(str(row[0]).split(".")[0], DATETIME_FORMAT)
            vals = {
                'trans_date': trans_date.strftime("%d-%m-%Y"),
                'trans_time': trans_date.strftime("%H:%M:%S"),
                'operating_unit_name': row[1],
                'voucher_sku': row[2],
                'voucher_name': row[3],
                'receipt_number': row[4],
                't_id': row[5],
                'member_id': row[6],
                'promo_name': row[7],
                'voucher_ean': row[8],
                'voucher_amount': row[9] 
            }
            detail.append(vals)
        docs.update({'detail': detail})

        if state == 'US':
            if voucher_promo_ids:
                strSQL = """
                    SELECT DATE(a.trans_date), d.name as operating_unit_name, 
                        b.voucher_sku, e.name as voucher_name, count(*) as trans_count, sum(e.voucher_amount)
                    FROM weha_voucher_order_line_trans a
                    LEFT JOIN weha_voucher_order_line b ON b.id = a.voucher_order_line_id
                    LEFT JOIN weha_voucher_trans_status c ON c.name = a.name
                    LEFT JOIN operating_unit d ON d.code = c.store_id
                    LEFT JOIN weha_voucher_code e ON e.id = b.voucher_code_id
                    WHERE trans_type='{}' AND DATE(a.trans_date) BETWEEN '{}' AND '{}'
                    AND b.operating_unit_id in {} AND b.voucher_promo_id in {}
                    GROUP BY d.name, DATE(a.trans_date), b.voucher_sku, e.name
                    ORDER BY d.name, DATE(a.trans_date)
                """.format(state, date_start, date_end, tuple(operating_unit_ids), tuple(voucher_promo_ids))
            else:
                strSQL = """
                    SELECT DATE(a.trans_date), d.name as operating_unit_name, 
                        b.voucher_sku, e.name as voucher_name, count(*) as trans_count, sum(e.voucher_amount)
                    FROM weha_voucher_order_line_trans a
                    LEFT JOIN weha_voucher_order_line b ON b.id = a.voucher_order_line_id
                    LEFT JOIN weha_voucher_trans_status c ON c.name = a.name
                    LEFT JOIN operating_unit d ON d.code = c.store_id
                    LEFT JOIN weha_voucher_code e ON e.id = b.voucher_code_id
                    WHERE trans_type='{}' AND DATE(a.trans_date) BETWEEN '{}' AND '{}'
                    AND b.operating_unit_id in {}
                    GROUP BY d.name, DATE(a.trans_date), b.voucher_sku, e.name
                    ORDER BY d.name, DATE(a.trans_date)
                """.format(state, date_start, date_end, tuple(operating_unit_ids))
        _logger.info(strSQL)
        
        self.env.cr.execute(strSQL)
        rows = self.env.cr.fetchall()
        summary = []
        for row in rows:
            trans_date = datetime.strptime(str(row[0]), DATE_FORMAT)
            vals = {
                'trans_date': trans_date.strftime("%d-%m-%Y"),
                'operating_unit_name': row[1],
                'voucher_sku': row[2],
                'voucher_name': row[3],
                'trans_count': row[4],
                'voucher_amount': row[5] 
            }
            summary.append(vals)
        docs.update({'summary': summary})
        _logger.info(docs)

        header_format = workbook.add_format(
            {
                'bold': 1,
                'font_size': 18,
                'align': 'center',
                'valign': 'vcenter'
            }
        )
        sub_header_format = workbook.add_format(
            {
                'bold': 1,
                'align': 'center',
                'valign': 'vcenter'
            }
        )
        sheet = workbook.add_worksheet('Voucher Transaction Detail')
        sheet.merge_range('A1:L1', 'Voucher Transaction Detail', header_format)
        sheet.merge_range('A2:L2', f'From {date_start} to {date_end}', sub_header_format)
        keys = ['No', 'Operating Unit', 'Date', 'Time', 'SKU', 'Name SKU', 'Trx', 'Tid', 'Member ID', 'Promo', 'No Voucher', 'Amount']
        col = 0
        row = 2
        for key in keys:
            sheet.write(row, col, key)
            col = col + 1

        for detail in docs['detail']:
            row = row + 1
            sheet.write(row, 0, row)
            sheet.write(row, 1, detail['trans_date'])
            sheet.write(row, 2, detail['trans_time'])
            sheet.write(row, 3, detail['operating_unit_name'])
            sheet.write(row, 4, detail['voucher_sku'])
            sheet.write(row, 5, detail['voucher_name'])
            sheet.write(row, 6, detail['receipt_number'])
            sheet.write(row, 7, detail['t_id'])
            sheet.write(row, 8, detail['member_id'])
            sheet.write(row, 9, detail['promo_name'])
            sheet.write(row, 10, detail['voucher_ean'])
            sheet.write(row, 11, detail['voucher_amount'])
        
        row = row + 3
        sheet.write(row, 0, "Summary Transaction")
        for summary in docs['summary']:            
            row = row + 1
            sheet.write(row, 0, row)
            sheet.write(row, 1, summary['operating_unit_name'])
            sheet.write(row, 2, summary['trans_date'])
            sheet.write(row, 4, summary['voucher_sku'])
            sheet.write(row, 5, summary['voucher_name'])
            sheet.write(row, 10, summary['trans_count'])
            sheet.write(row, 11, summary['voucher_amount'])


    