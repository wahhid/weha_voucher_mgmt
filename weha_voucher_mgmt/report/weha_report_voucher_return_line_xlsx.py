from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
from odoo.tools import formatLang
from odoo.addons.weha_voucher_mgmt.common import convert_utc_to_local
import logging

_logger = logging.getLogger(__name__)


class ReportVoucherReturnLineXlsx(models.AbstractModel):
    """Abstract Model for report template.

    for `_name` model, please use `report.` as prefix then add `module_name.report_name`.
    """

    _name = 'report.weha_voucher_mgmt.weha_voucher_return_line_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):
        _logger.info(data)
        return_id = data['form']['return_id']

       
        
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
        sheet = workbook.add_worksheet('Voucher Return Line')
        sheet.merge_range('A1:H1', 'Voucher Return Line', header_format)
        keys = ['No', 'Voucher', 'Operating Unit', 'Voucher Code', 'Year', 'Voucher Promo', 'Voucher Status', 'Status']
        col = 0
        row = 2
        no = 0
        for key in keys:
            sheet.write(row, col, key)
            col = col + 1

        voucher_return_id = self.env['weha.voucher.return'].browse(return_id)
        details = []
        if voucher_return_id:
            for voucher_return_line_id in voucher_return_id.voucher_return_line_ids:
                row = row + 1
                no = no + 1
                sheet.write(row, 0, no)
                sheet.write(row, 1, voucher_return_line_id.voucher_order_line_id.name)
                sheet.write(row, 2, voucher_return_line_id.voucher_operating_unit_id.name)
                sheet.write(row, 3, voucher_return_line_id.voucher_code_id.name)
                sheet.write(row, 4, voucher_return_line_id.year_id.name)
                sheet.write(row, 5, voucher_return_line_id.voucher_promo_id.name or '')
                sheet.write(row, 6, voucher_return_line_id.voucher_state)
                sheet.write(row, 7, voucher_return_line_id.state)
        

