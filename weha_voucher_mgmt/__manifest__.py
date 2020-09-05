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
        'views/res_users.xml',
        'wizard/weha_select_order_line_wizard_view.xml',
        'wizard/weha_received_request_wizard_view.xml',
<<<<<<< HEAD
        'wizard/weha_received_allocate_wizard_view.xml',
=======
>>>>>>> wahyu
        'views/weha_voucher_menu.xml',
        'views/weha_voucher_stage_view.xml',
        'views/weha_voucher_order_view.xml',
        'views/weha_voucher_order_line_view.xml',
        'views/weha_voucher_request_view.xml',
        'views/weha_voucher_request_line_view.xml',
        'views/weha_voucher_number_ranges_view.xml',
        'views/weha_voucher_return_view.xml',
        'views/weha_voucher_return_line_view.xml',
        'views/weha_voucher_allocate_view.xml',
        'views/weha_voucher_allocate_line_view.xml',
        'views/weha_voucher_stock_transfer_view.xml',
        'views/weha_voucher_stock_transfer_line_view.xml',
        'views/weha_voucher_config_code_view.xml',
        'views/weha_voucher_config_mapping_pos_view.xml',
        'views/weha_voucher_config_mapping_sku_view.xml',
        'views/weha_voucher_config_location_view.xml',
        # 'views/weha_voucher_config_number_range_view.xml',
        'views/weha_voucher_config_terms_view.xml',
        'views/weha_voucher_config_type_view.xml',
        'views/weha_voucher_return_stage_view.xml',
        'views/weha_voucher_allocate_stage_view.xml',
<<<<<<< HEAD
        'views/weha_voucher_scrap_stage_view.xml',
        'views/weha_voucher_scrap_view.xml',
        'views/weha_voucher_scrap_line_view.xml',
        'views/weha_voucher_issuing_stage_view.xml',
        'views/weha_voucher_issuing_view.xml',
=======
>>>>>>> wahyu
        'views/weha_voucher_stock_transfer_stage_view.xml',
        'views/weha_voucher_code_minimum_stock_view.xml',
        'views/res_company_settings_view.xml',
        'views/weha_voucher_dashboard_view.xml',
         
    ],
    "depends": [
        'base',
        'mail',
        'operating_unit',
        'board'
    ],
    "installable": True,
}
