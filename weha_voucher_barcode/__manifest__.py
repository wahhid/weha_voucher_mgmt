{
    "name": "Voucher Barcode Scanner",
    "summary": "Ability to scan voucher barcode",
    "version": "13.0.1.0.1",
    "author": "WEHA",
    "website": "https://weha-id",
    "license": "AGPL-3",
    "category": "Extra Tools",
    "depends": ["barcodes", "weha_voucher_mgmt"],
    "data": [
        "security/ir.model.access.csv",
        "views/assets.xml",
        "views/voucher_allocation_view.xml",
        "views/voucher_return_view.xml",
        "views/voucher_scrap_view.xml",
        "views/voucher_issuing_view.xml",
        "wizards/stock_barcodes_read_views.xml",
        "wizards/stock_barcodes_read_voucher_allocate_views.xml",
        "wizards/stock_barcodes_read_voucher_issuing_views.xml",
        "wizards/stock_barcodes_read_voucher_return_views.xml",
        "wizards/stock_barcodes_read_voucher_scrap_views.xml",

    ],
    "installable": True,
}
