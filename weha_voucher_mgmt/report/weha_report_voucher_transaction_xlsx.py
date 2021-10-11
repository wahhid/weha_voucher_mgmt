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
        transaction_type_ids = data['form']['transaction_type_ids']

        date_start_obj = datetime.strptime(date_start, DATE_FORMAT)
        _logger.info(date_start_obj)
        date_end_obj = datetime.strptime(date_end, DATE_FORMAT)
        _logger.info(date_end_obj)

        docs = {}

        operating_units = f'({operating_unit_ids})' if isinstance(operating_unit_ids, int) else tuple(operating_unit_ids)
        
        if voucher_promo_ids:
            voucher_promos = f'({voucher_promo_ids})' if isinstance(voucher_promo_ids, int) else tuple(voucher_promo_ids)
        else:
            voucher_promos = False

        if transaction_type_ids:
            if isinstance(transaction_type_ids, int):
                ids = self.env['weha.voucher.transaction.type'].browse(transaction_type_ids)
                transaction_types = "('" + ids.code + "')"
            else:
                transaction_types = "("
                for transaction_type_id in transaction_type_ids:
                    ids = self.env['weha.voucher.transaction.type'].browse(transaction_type_id)
                    transaction_types = transaction_types + "'" + ids.code + "',"
                
                transaction_types = transaction_types[:-1]
                transaction_types = transaction_types + ")"
        else:
            transaction_types = False

        #DETAIL
        if voucher_promos:
            if not transaction_types:
                strSQL = """
                    SELECT a.trans_date, d.name as operating_unit_name, 
                        b.voucher_sku, e.name as voucher_name,
                        c.receipt_number, c.t_id, c.member_id, f.name as promo_name, b.voucher_ean,
                        a.trans_type, e.voucher_amount
                    FROM weha_voucher_order_line_trans a
                    LEFT JOIN weha_voucher_order_line b ON b.id = a.voucher_order_line_id
                    LEFT JOIN weha_voucher_trans_status c ON c.name = a.name
                    LEFT JOIN operating_unit d ON d.code = c.store_id
                    LEFT JOIN weha_voucher_code e ON e.id = b.voucher_code_id
                    LEFT JOIN weha_voucher_promo f ON f.id = b.voucher_promo_id
                    WHERE DATE(a.trans_date) BETWEEN '{}' AND '{}'
                    AND b.operating_unit_id in {} AND b.voucher_promo_id in {} 
                    ORDER BY d.name, a.trans_date
                """.format(date_start, date_end, operating_units, voucher_promos)
            else:
                strSQL = """
                    SELECT a.trans_date, d.name as operating_unit_name, 
                        b.voucher_sku, e.name as voucher_name,
                        c.receipt_number, c.t_id, c.member_id, f.name as promo_name, b.voucher_ean,
                        a.trans_type, e.voucher_amount
                    FROM weha_voucher_order_line_trans a
                    LEFT JOIN weha_voucher_order_line b ON b.id = a.voucher_order_line_id
                    LEFT JOIN weha_voucher_trans_status c ON c.name = a.name
                    LEFT JOIN operating_unit d ON d.code = c.store_id
                    LEFT JOIN weha_voucher_code e ON e.id = b.voucher_code_id
                    LEFT JOIN weha_voucher_promo f ON f.id = b.voucher_promo_id
                    WHERE a.trans_type in {} AND DATE(a.trans_date) BETWEEN '{}' AND '{}'
                    AND b.operating_unit_id in {} AND b.voucher_promo_id in {} 
                    ORDER BY d.name, a.trans_date
                """.format(transaction_types, date_start, date_end, operating_units, voucher_promos)
        else:
            if not transaction_types:
                strSQL = """
                    SELECT a.trans_date, d.name as operating_unit_name, 
                        b.voucher_sku, e.name as voucher_name,
                        c.receipt_number, c.t_id, c.member_id, f.name as promo_name, b.voucher_ean,
                        a.trans_type, e.voucher_amount
                    FROM weha_voucher_order_line_trans a
                    LEFT JOIN weha_voucher_order_line b ON b.id = a.voucher_order_line_id
                    LEFT JOIN weha_voucher_trans_status c ON c.name = a.name
                    LEFT JOIN operating_unit d ON d.code = c.store_id
                    LEFT JOIN weha_voucher_code e ON e.id = b.voucher_code_id
                    LEFT JOIN weha_voucher_promo f ON f.id = b.voucher_promo_id
                    WHERE DATE(a.trans_date) BETWEEN '{}' AND '{}'
                    AND b.operating_unit_id in {}
                    ORDER BY d.name, a.trans_date
                """.format(date_start, date_end, operating_units)
            else:
                strSQL = """
                    SELECT a.trans_date, d.name as operating_unit_name, 
                        b.voucher_sku, e.name as voucher_name,
                        c.receipt_number, c.t_id, c.member_id, f.name as promo_name, b.voucher_ean,
                        a.trans_type, e.voucher_amount
                    FROM weha_voucher_order_line_trans a
                    LEFT JOIN weha_voucher_order_line b ON b.id = a.voucher_order_line_id
                    LEFT JOIN weha_voucher_trans_status c ON c.name = a.name
                    LEFT JOIN operating_unit d ON d.code = c.store_id
                    LEFT JOIN weha_voucher_code e ON e.id = b.voucher_code_id
                    LEFT JOIN weha_voucher_promo f ON f.id = b.voucher_promo_id
                    WHERE a.trans_type in {} AND DATE(a.trans_date) BETWEEN '{}' AND '{}'
                    AND b.operating_unit_id in {}
                    ORDER BY d.name, a.trans_date
                """.format(transaction_types, date_start, date_end, operating_units)

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
                'trans_type': row[9],
                'voucher_amount': row[10] 
            }
            detail.append(vals)
        docs.update({'detail': detail})

                #SUMMARY

        if voucher_promo_ids:
            if not transaction_types:
                strSQL = """
                    SELECT DATE(a.trans_date), d.name as operating_unit_name, 
                        b.voucher_sku, e.name as voucher_name, count(*) as trans_count, a.trans_type, sum(e.voucher_amount)
                    FROM weha_voucher_order_line_trans a
                    LEFT JOIN weha_voucher_order_line b ON b.id = a.voucher_order_line_id
                    LEFT JOIN weha_voucher_trans_status c ON c.name = a.name
                    LEFT JOIN operating_unit d ON d.code = c.store_id
                    LEFT JOIN weha_voucher_code e ON e.id = b.voucher_code_id
                    WHERE DATE(a.trans_date) BETWEEN '{}' AND '{}'
                    AND b.operating_unit_id in {} AND b.voucher_promo_id in {}
                    GROUP BY d.name, DATE(a.trans_date), b.voucher_sku, e.name, a.trans_type
                    ORDER BY d.name, DATE(a.trans_date)
                """.format(date_start, date_end, f'({operating_unit_ids})' if isinstance(operating_unit_ids, int) else tuple(operating_unit_ids), f'({voucher_promo_ids})' if isinstance(voucher_promo_ids, int) else tuple(voucher_promo_ids))
            else:
                strSQL = """
                    SELECT DATE(a.trans_date), d.name as operating_unit_name, 
                        b.voucher_sku, e.name as voucher_name, count(*) as trans_count, a.trans_type, sum(e.voucher_amount)
                    FROM weha_voucher_order_line_trans a
                    LEFT JOIN weha_voucher_order_line b ON b.id = a.voucher_order_line_id
                    LEFT JOIN weha_voucher_trans_status c ON c.name = a.name
                    LEFT JOIN operating_unit d ON d.code = c.store_id
                    LEFT JOIN weha_voucher_code e ON e.id = b.voucher_code_id
                    WHERE a.trans_type in {} AND DATE(a.trans_date) BETWEEN '{}' AND '{}'
                    AND b.operating_unit_id in {} AND b.voucher_promo_id in {}
                    GROUP BY d.name, DATE(a.trans_date), b.voucher_sku, e.name, a.trans_type
                    ORDER BY d.name, DATE(a.trans_date)
                """.format(transaction_types, date_start, date_end, f'({operating_unit_ids})' if isinstance(operating_unit_ids, int) else tuple(operating_unit_ids), f'({voucher_promo_ids})' if isinstance(voucher_promo_ids, int) else tuple(voucher_promo_ids))
        else:
            if not transaction_types:
                strSQL = """
                    SELECT DATE(a.trans_date), d.name as operating_unit_name, 
                        b.voucher_sku, e.name as voucher_name, count(*) as trans_count, a.trans_type, sum(e.voucher_amount)
                    FROM weha_voucher_order_line_trans a
                    LEFT JOIN weha_voucher_order_line b ON b.id = a.voucher_order_line_id
                    LEFT JOIN weha_voucher_trans_status c ON c.name = a.name
                    LEFT JOIN operating_unit d ON d.code = c.store_id
                    LEFT JOIN weha_voucher_code e ON e.id = b.voucher_code_id
                    WHERE DATE(a.trans_date) BETWEEN '{}' AND '{}'
                    AND b.operating_unit_id in {}
                    GROUP BY d.name, DATE(a.trans_date), b.voucher_sku, e.name, a.trans_type
                    ORDER BY d.name, DATE(a.trans_date)
                """.format(date_start, date_end, tuple(operating_unit_ids.append(0)) if isinstance(operating_unit_ids, int) else tuple(operating_unit_ids))
            else:
                strSQL = """
                    SELECT DATE(a.trans_date), d.name as operating_unit_name, 
                        b.voucher_sku, e.name as voucher_name, count(*) as trans_count, a.trans_type, sum(e.voucher_amount)
                    FROM weha_voucher_order_line_trans a
                    LEFT JOIN weha_voucher_order_line b ON b.id = a.voucher_order_line_id
                    LEFT JOIN weha_voucher_trans_status c ON c.name = a.name
                    LEFT JOIN operating_unit d ON d.code = c.store_id
                    LEFT JOIN weha_voucher_code e ON e.id = b.voucher_code_id
                    WHERE trans_type in {} AND DATE(a.trans_date) BETWEEN '{}' AND '{}'
                    AND b.operating_unit_id in {}
                    GROUP BY d.name, DATE(a.trans_date), b.voucher_sku, e.name, a.trans_type
                    ORDER BY d.name, DATE(a.trans_date)
                """.format(transaction_types, date_start, date_end, tuple(operating_unit_ids.append(0)) if isinstance(operating_unit_ids, int) else tuple(operating_unit_ids))
    
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
                'trans_type': row[5],
                'voucher_amount': row[6] 
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
        keys = ['No', 'Operating Unit', 'Date', 'Time', 'SKU', 'Name SKU', 'Trx', 'Tid', 'Member ID', 'Promo', 'No Voucher', 'Trans Type', 'Amount']
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
            sheet.write(row, 11, detail['trans_type'])
            sheet.write(row, 12, detail['voucher_amount'])
        
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
            sheet.write(row, 11, summary['trans_type'])
            sheet.write(row, 12, summary['voucher_amount'])


    