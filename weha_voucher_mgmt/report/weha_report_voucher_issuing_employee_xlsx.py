from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
from odoo.tools import formatLang
from odoo.addons.weha_voucher_mgmt.common import convert_utc_to_local
import logging

_logger = logging.getLogger(__name__)


class ReportVoucherIssuingEmployeeXlsx(models.AbstractModel):
    """Abstract Model for report template.

    for `_name` model, please use `report.` as prefix then add `module_name.report_name`.
    """

    _name = 'report.weha_voucher_mgmt.print_voucher_issuing_employee_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):
        voucher_issuing_id = data['form']['voucher_issuing_id']

        strSQL = """SELECT employee_nik, employee_name FROM weha_voucher_issuing_employee_line 
                    WHERE voucher_issuing_id={}
                    GROUP BY employee_nik, employee_name
        """.format(voucher_issuing_id)
        
        _logger.info(strSQL)

        self.env.cr.execute(strSQL)
        rows = self.env.cr.fetchall()
        employees = []
        for row in rows:
            employees.append({'employee_nik': row[0], 'employee_name': row[1]})
        _logger.info(employees)

        strSQL = """SELECT a.mapping_sku_id, concat(b.code_sku, ' ', c.name) as mapping_sku_name, c.voucher_amount
                FROM weha_voucher_issuing_employee_line a
                LEFT JOIN weha_voucher_mapping_sku b ON a.mapping_sku_id = b.id
                LEFT JOIN weha_voucher_code c ON b.voucher_code_id = c.id
                WHERE voucher_issuing_id={}
                GROUP BY  a.mapping_sku_id, concat(b.code_sku, ' ', c.name), c.voucher_amount
        """.format(voucher_issuing_id)
        _logger.info(strSQL)
        self.env.cr.execute(strSQL)
        rows = self.env.cr.fetchall()
        skus = []
        for row in rows:
            skus.append({'mapping_sku_id': row[0], 'mapping_sku_name': row[1], 'voucher_amount': row[2]})
        _logger.info(skus)
        
        docs = []
        details = []
        for employee in employees:
            vals = {}
            vals.update({'employee_nik': employee.get('employee_nik')})
            vals.update({'employee_name': employee.get('employee_name')})
            vals.update({'nominal': 0})
            
            for sku in skus:
                vals.update({sku['mapping_sku_name']: 0})

            nominal = 0
            for sku in skus:
                _logger.info(sku)
                strSQL = """
                    SELECT sum(quantity) FROM  weha_voucher_issuing_employee_line
                    WHERE voucher_issuing_id={} AND employee_nik='{}' AND mapping_sku_id = {}
                """.format(voucher_issuing_id, employee.get('employee_nik'), sku['mapping_sku_id'])
                _logger.info(strSQL)
                self.env.cr.execute(strSQL)
                row = self.env.cr.fetchone()
                if row:
                    if row[0] is None:
                        vals.update({sku['mapping_sku_name']: 0})
                    else:
                        nominal = nominal + (sku['voucher_amount'] * int(row[0]))
                        vals.update({sku['mapping_sku_name']: row[0]})         
                else:
                    vals.update({sku['mapping_sku_name']: 0})

            _logger.info(vals)
            vals.update({'nominal': nominal})
            details.append(vals)

        docs.append({'details': details})
    

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
        sheet = workbook.add_worksheet('Report Voucher Issuing Employee')
        sheet.merge_range('A1:L1', 'Report Voucher Issuing Employee', header_format)
        keys = ['NIK', 'Employee Name', 'Nominal']
        for sku in skus:
            keys.append(sku['mapping_sku_name'])
        
        col = 0
        row = 2
        no = 0

        for key in keys:
            sheet.write(row, col, key)
            col = col + 1

        for detail in details:
            row = row + 1
            col = 0
            for key in detail:
                #_logger.info(key)
                #_logger.info(detail.get(key))
                sheet.write(row, col, detail.get(key))
                col = col + 1

