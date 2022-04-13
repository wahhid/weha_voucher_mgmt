from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
from odoo.tools import formatLang
from odoo.addons.weha_voucher_mgmt.common import convert_utc_to_local
import logging

_logger = logging.getLogger(__name__)




    
class ReportVoucherPromoSummarylXlsx(models.AbstractModel):
    """Abstract Model for report template.

    for `_name` model, please use `report.` as prefix then add `module_name.report_name`.
    """

    _name = 'report.weha_voucher_mgmt.weha_voucher_promo_summary_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):
        """Abstract Model for report template.

        for `_name` model, please use `report.` as prefix then add `module_name.report_name`.
        """

        _name = 'report.weha_voucher_mgmt.print_stock_summary_view'


        @api.model
        def _get_report_values(self, docids, data=None):
            state = data['form']['state']
            date_start = data['form']['date_start']
            date_end = data['form']['date_end']
            operating_unit_ids = data['form']['operating_unit_ids']
            voucher_promo_ids = data['form']['voucher_promo_ids']
            date_start_obj = datetime.strptime(date_start, DATE_FORMAT)
            date_end_obj = datetime.strptime(date_end, DATE_FORMAT)

            date_start_obj = datetime.strptime(date_start, DATE_FORMAT)
            _logger.info(date_start_obj)
            date_end_obj = datetime.strptime(date_end, DATE_FORMAT)
            _logger.info(date_end_obj)

            docs = []
            
            for operating_unit in operating_unit_ids:
                operating_unit_id = self.env['operating.unit'].browse(operating_unit)
                if voucher_promo_ids:
                    voucher_promos = f'({voucher_promo_ids})' if isinstance(voucher_promo_ids, int) else tuple(voucher_promo_ids)
                else:
                    voucher_promos = False
            
                if voucher_promos:
                    strSQL = """
                        SELECT a.voucher_ean, a.voucher_sku, a.voucher_type, 
                            c.name as voucher_code_name, d.name as voucher_promo_name,
                            c.voucher_amount, a.state,
                            a.receipt_number, a.t_id, a.member_id
                        FROM weha_voucher_order_line a 
                        LEFT JOIN operating_unit b ON b.id = a.operating_unit_id
                        LEFT JOIN weha_voucher_code c ON c.id = a.voucher_code_id
                        LEFT JOIN weha_voucher_promo d ON d.id = a.voucher_promo_id
                        WHERE DATE(a.write_date) BETWEEN '{}' AND '{}'
                        AND a.state = '{}' AND a.operating_unit_id = {} AND a.voucher_promo_id in {} 
                        ORDER BY a.state, b.name, a.create_date
                    """.format(date_start, date_end, state, operating_unit_id.id, voucher_promos)

                else:
                    strSQL = """
                        SELECT a.voucher_ean, a.voucher_sku, a.voucher_type, 
                            c.name as voucher_code_name, d.name as voucher_promo_name,
                            c.voucher_amount, a.state,
                            a.receipt_number, a.t_id, a.member_id
                        FROM weha_voucher_order_line a 
                        LEFT JOIN operating_unit b ON b.id = a.operating_unit_id
                        LEFT JOIN weha_voucher_code c ON c.id = a.voucher_code_id
                        LEFT JOIN weha_voucher_promo d ON d.id = a.voucher_promo_id
                        WHERE DATE(a.write_date) BETWEEN '{}' AND '{}'
                        AND a.state = '{}' AND a.operating_unit_id = {}
                        ORDER BY a.state, b.name, a.create_date
                    """.format(date_start, date_end, state, operating_unit_id.id)

                _logger.info(strSQL)
        
                self.env.cr.execute(strSQL)
                rows = self.env.cr.fetchall()
                detail = []
                for row in rows:
                    user_tz = self.env.user.tz or "Asia/Jakarta"
                    _logger.info(str(row[0]))
                    #trans_date = convert_utc_to_local(user_tz, str(row[0]).split(".")[0])
                    #trans_date = datetime.strptime(str(row[0]).split(".")[0], DATETIME_FORMAT)
                    vals = {
                        'voucher_ean': row[0],
                        'voucher_sku': row[1],
                        'voucher_type': row[2],
                        'voucher_code_name': row[3],
                        'voucher_promo_name': row[4],
                        'voucher_amount': row[5],
                        'state': row[6],
                    }
                    detail.append(vals)
                docs.append({'operating_unit': operating_unit_id.name, 'detail': detail})

          

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
            sheet = workbook.add_worksheet('Voucher Promo Summary')
            sheet.merge_range('A1:L1', 'Voucher Promo Summary', header_format)
            sheet.merge_range('A2:L2', f'From {datetime.strptime(date_start,"%Y-%m-%d").strftime("%d-%m-%Y")} to {datetime.strptime(date_end,"%Y-%m-%d").strftime("%d-%m-%Y")}', sub_header_format)
            sheet.merge_range('A4:A5', f'Source Doc', sub_header_format)
            sheet.merge_range('B4:B5', f'Nama Promo', sub_header_format)
            sheet.merge_range('C4:C5', f'Requestor', sub_header_format)
            sheet.merge_range('D4:D5', f'Penerima', sub_header_format)
            sheet.merge_range('F4:G4', f'Alokasi', sub_header_format)
            sheet.write(4, 5, 'Dikirim Mktg ke Toko (Delivery)')
            sheet.write(4, 6, 'Diterima Toko dari Mktg ke (Received)')
            

            
            
            # keys = ['No', 'Operating Unit', 'Date', 'Time', 'SKU', 'Name SKU', 'Trx', 'Tid', 'Member ID', 'Promo', 'No Voucher', 'Trans Type', 'Amount']
            # col = 0
            # row = 2
            # no = 0
            # # for key in keys:
            # #     sheet.write(row, col, key)
            # #     col = col + 1

            # for detail in docs['detail']:
            #     row = row + 1
            #     no = no + 1
            #     sheet.write(row, 0, no)
            #     sheet.write(row, 1, detail['operating_unit_name'])
            #     sheet.write(row, 2, detail['trans_date'])
            #     sheet.write(row, 3, detail['trans_time'])
            #     sheet.write(row, 4, detail['voucher_sku'])
            #     sheet.write(row, 5, detail['voucher_name'])
            #     sheet.write(row, 6, detail['receipt_number'])
            #     sheet.write(row, 7, detail['t_id'])
            #     sheet.write(row, 8, detail['member_id'])
            #     sheet.write(row, 9, detail['promo_name'])
            #     sheet.write(row, 10, detail['voucher_ean'])
            #     sheet.write(row, 11, detail['trans_type'])
            #     sheet.write(row, 12, detail['voucher_amount'])
            
            # row = row + 3
            # no = 0
            # sheet.write(row, 0, "Summary Transaction")
            # for summary in docs['summary']:            
            #     row = row + 1
            #     no = no + 1
            #     sheet.write(row, 0, no)
            #     sheet.write(row, 1, summary['operating_unit_name'])
            #     sheet.write(row, 2, summary['trans_date'])
            #     sheet.write(row, 4, summary['voucher_sku'])
            #     sheet.write(row, 5, summary['voucher_name'])
            #     sheet.write(row, 10, summary['trans_count'])
            #     sheet.write(row, 11, summary['trans_type'])
            #     sheet.write(row, 12, summary['voucher_amount'])

