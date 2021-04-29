import pytz
from odoo import models, fields, api
from datetime import timedelta, datetime, date
import logging

_logger = logging.getLogger(__name__)

class VoucherDashboard(models.Model):
    _inherit = 'weha.voucher.order.line'

    @api.model
    def get_voucher_summary(self):
        company_id = self.env.company.id
        operating_unit_id = self.env.user.default_operating_unit_id
        strSQL = """
            SELECT 
                count(a.*) as total_count, 
                sum(b.voucher_amount) as total_amount 
            FROM weha_voucher_order_line a
            LEFT JOIN weha_voucher_code b ON a.voucher_code_id = b.id 
            WHERE a.operating_unit_id={} 
        """.format(operating_unit_id.id)
        self._cr.execute(strSQL)
        docs = self._cr.dictfetchall()
        total_voucher_count = docs[0]['total_count']
        total_voucher_amount = docs[0]['total_amount']
        _logger.info(docs)

        strSQL = """
            SELECT count(a.*) as total_count FROM weha_voucher_order_line a
            WHERE a.state = 'open' and a.operating_unit_id={} 
        """.format(operating_unit_id.id)

        self._cr.execute(strSQL)
        docs = self._cr.dictfetchall()
        total_open_voucher = docs[0]['total_count']

        strSQL = """
            SELECT count(a.*) as total_count FROM weha_voucher_order_line a
            WHERE a.state = 'activated' and a.operating_unit_id={} 
        """.format(operating_unit_id.id)
        self._cr.execute(strSQL)
        docs = self._cr.dictfetchall()
        total_open_issuing = docs[0]['total_count']

        return {
            'total_voucher_count': total_voucher_count,
            'total_voucher_amount': total_voucher_amount,
            'total_open_voucher': total_open_voucher ,
            'total_issuing_voucher': total_open_issuing
        }
    

    @api.model
    def get_voucher_by_code(self):
        pass 
    