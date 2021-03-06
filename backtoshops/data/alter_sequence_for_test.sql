BEGIN ;
SELECT pg_catalog.setval('accounts_brand_id_seq', 1000004, true);
SELECT pg_catalog.setval('accounts_userprofile_id_seq', 1000004, true);
SELECT pg_catalog.setval('attributes_brandattribute_id_seq', 1000014, true);
SELECT pg_catalog.setval('attributes_brandattributepreview_id_seq', 10000017, true);
SELECT pg_catalog.setval('attributes_commonattribute_id_seq', 1000007, false);
SELECT pg_catalog.setval('auth_user_id_seq', 1000005, true);
SELECT pg_catalog.setval('barcodes_barcode_id_seq', 10000039, true);
SELECT pg_catalog.setval('sales_product_id_seq', 1000032, true);
SELECT pg_catalog.setval('sales_productbrand_id_seq', 1000004, true);
SELECT pg_catalog.setval('sales_productcategory_id_seq', 1000003, false);
SELECT pg_catalog.setval('sales_productpicture_id_seq', 1000005, true);
SELECT pg_catalog.setval('sales_producttype_id_seq', 1000006, false);
SELECT pg_catalog.setval('sales_sale_id_seq', 1000033, true);
SELECT pg_catalog.setval('sales_shippinginsale_id_seq', 1000031, true);
SELECT pg_catalog.setval('sales_shopsinsale_id_seq', 1000033, true);
SELECT pg_catalog.setval('shippings_customshippingrate_id_seq', 1000002, true);
SELECT pg_catalog.setval('shippings_customshippingrateinshipping_id_seq', 1000009, true);
SELECT pg_catalog.setval('shippings_flatrateinshipping_id_seq', 1000003, true);
SELECT pg_catalog.setval('shippings_service_id_seq', 2, true);
SELECT pg_catalog.setval('shippings_serviceinshipping_id_seq', 1000018, true);
SELECT pg_catalog.setval('shippings_shipping_id_seq', 1000031, true);
SELECT pg_catalog.setval('shops_shop_id_seq', 1000006, true);
SELECT pg_catalog.setval('stocks_productstock_id_seq', 10000041, true);
SELECT pg_catalog.setval('sales_typeattributeprice_id_seq', 1000003, true);
SELECT pg_catalog.setval('sales_typeattributeweight_id_seq', 1000003, true);
COMMIT;
