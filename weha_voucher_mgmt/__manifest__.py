{
    "name": "Voucher Management System",
    "summary": "Voucher Management System",
    "version": "13.0.1.0.0",
    "author": "Wahyu Hidayat, "
              "WEHA",
    "category": "Voucher",
    "website": "https://www.weha-id.com",
    "license": "AGPL-3",
    'data': [
        'data/weha_voucher_data.xml',
        'data/ir_config_param.xml',
        'security/weha_voucher_security.xml',
        'security/ir.model.access.csv',
<<<<<<< HEAD
        'views/res_users.xml',
=======
        'wizard/weha_select_order_line_wizard_view.xml',
>>>>>>> origin/yogi
        'views/weha_voucher_menu.xml',
        'views/weha_voucher_stage_view.xml',
        'views/weha_voucher_code_view.xml',
        'views/weha_voucher_order_view.xml',
        'views/weha_voucher_order_line_view.xml',
        'views/weha_voucher_request_view.xml',
        'views/weha_voucher_request_line_view.xml',
        'views/weha_voucher_request_line_range_view.xml',
        'views/weha_voucher_return_view.xml',
        # 'views/weha_voucher_issuing_view.xml',
        # 'views/weha_voucher_stock_transfer_view.xml',
        'views/weha_voucher_config_location_view.xml',
        'views/weha_voucher_config_number_range_view.xml',
        'views/weha_voucher_config_terms_view.xml',
        'views/weha_voucher_config_type_view.xml',
        'views/weha_voucher_return_stage_view.xml',
        # 'views/weha_voucher_issuing_stage_view.xml',
        # 'views/weha_voucher_stock_transfer_stage_view.xml',
        'views/weha_voucher_dashboard_view.xml',
         
    ],
    "depends": [
        'base',
        'mail',
        'operating_unit'
    ],
    "installable": True,
}
