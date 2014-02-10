BEGIN ;
--
-- PostgreSQL database dump
--

--
-- Data for Name: accounts_brand; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY accounts_brand (id, name, logo, address, zipcode, city, country_id) FROM stdin;
1000001	corporate account 1	brand_logos/test.jpeg 	beijing qing nian hui	1000001	BEIJING	CN
1000002	corporate account 2	brand_logos/test.jpeg 	beijing qing nian gong she	1000001	BEIJING	CN
1000003	corporate account 3	brand_logos/test.jpeg	qing nian lu	100002	BEIJING	CN
1000004	corporate account 4	brand_logos/test.jpeg	tong zhou li yuan	100004	BEIJING	CN
\.


--
-- Data for Name: auth_user; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY auth_user (id, password, last_login, is_superuser, username, first_name, last_name, email, is_staff, is_active, date_joined) FROM stdin;
1000003	pbkdf2_sha256$10000$Ht0hiizn8erI$m1fikBu3Vg/weXzADR+AHmwrDUnddmDzBX+nizt53TU=	2013-12-31 05:49:20.210505+00	f	test_user2_1000000			user2@infinite-code.com	t	t	2013-12-30 08:59:24.348+00
1000002	pbkdf2_sha256$10000$ZBzadrTLzFlV$4RF8y2R96/njhvCk4GsJZHxsBks2Sc7zCOACQ5DIXJA=	2014-01-02 03:57:36.394391+00	f	test_user1_1000000			user1@infinite-code.com	t	t	2013-12-30 08:58:55.267+00
1000001	pbkdf2_sha256$10000$P5L1F8apMmEm$GRYb7vEvdj+5H5QfP+5fieH37NuI8s6/aq4s+9Ow4Y8=	2014-02-08 06:40:18.822346+00	t	test_admin_1000000			admin@infinite-code.com	t	t	2013-12-30 08:45:04.266+00
1000005	pbkdf2_sha256$10000$WE8o1XJiyPG9$ej57dR5dxROoDkafomKbktAAEwGKLzuNkTBx5mDck5w=	2014-02-08 06:42:30.454369+00	f	test_user4_1000000			user4@inifinite-code.com	t	t	2014-02-08 06:42:06.962951+00
1000004	pbkdf2_sha256$10000$FES6biRhcI0z$70PFBpJoZ2BAehTTTq08h1v9SsxHC2FwHooSJ+d5kTc=	2014-02-08 06:46:53.654438+00	f	test_user3_1000000			user3@infinite-code.com	t	t	2014-02-08 01:53:12.231276+00
\.


--
-- Data for Name: accounts_userprofile; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY accounts_userprofile (id, user_id, work_for_id, language) FROM stdin;
1000001	1000002	1000001	en
1000002	1000003	1000002	en
1000003	1000004	1000003	en
1000004	1000005	1000004	en
\.


--
-- Data for Name: shops_shop; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY shops_shop (id, mother_brand_id, gestion_name, address, zipcode, city, phone, name, catcher, description, opening_hours, latitude, longitude, upc, image, country_id) FROM stdin;
1000001	1000001	shop 1	beijing chaoyang	1000001	BEIJING		shop name 1				114	116	11111	shop_images/大学宿舍_1.jpeg	CN
1000002	1000001	shop 2	beijing haidian 	1000001	BEIJING		shop name 2				114	116	22222	shop_images/大学宿舍_2.jpeg	CN
1000003	1000002	shop 3	beijing tongzhou	1000001	BEIJING		shop name 3				114	116	33333	shop_images/大学宿舍_3.jpeg	CN
1000004	1000002	shop 4	beijing xuanwu	1000001	BEIJING		shop name 4				114	116	44444	shop_images/大学宿舍_4.jpeg	CN
1000005	1000003	shop 5	chaoyang da yue cheng	100005	BEIJING 	123123123123	shop name 5	Caption 5	The 5th shop	{}	39.911785100000003	116.422241400000075	55555	shop_images/earth2.jpg	CN
1000006	1000003	shop name 6	chao yang da yue cheng	100006	BEIJING	34534534534	shop name 6	caption 6	the 6th shop	{}	39.9117109000000028	116.409731700000066	66666		CN
\.


--
-- Data for Name: attributes_brandattribute; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY attributes_brandattribute (id, mother_brand_id, name, texture, premium_type, premium_amount) FROM stdin;
1000001	1000001	test brand attr 1		percentage	1
1000002	1000001	test brand attr 2		percentage	2
1000003	1000001	test brand attr 3		percentage	3
1000004	1000001	test brand attr 4		percentage	\N
1000005	1000001	test brand attr 5		percentage	5
1000006	1000001	test brand attr 6		percentage	\N
1000007	1000002	test brand attr 7		percentage	7
1000008	1000002	test brand attr 8		percentage	8
\.


--
-- Data for Name: sales_productbrand; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY sales_productbrand (id, seller_id, name, picture) FROM stdin;
1000001	1000001	product brand 1	product_brands/test.jpeg
1000002	1000002	product brand 2	product_brands/test.jpeg
1000003	1000003	product brand 3	product_brands/test.jpeg
1000004	1000004	product brand 4	product_brands/test.jpeg
\.


--
-- Data for Name: sales_productcategory; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY sales_productcategory (id, name) FROM stdin;
1000001	product category 1
1000002	product category 2
\.


--
-- Data for Name: sales_producttype; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY sales_producttype (id, name, category_id) FROM stdin;
1000001	product type 1	1000001
1000002	product type 2	1000001
1000003	product type 3	1000002
1000004	product type 4	1000002
1000005	item type 1	1000001
\.


--
-- Data for Name: sales_sale; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY sales_sale (id, direct_sale, mother_brand_id, type_stock, total_stock, total_rest_stock, gender, created) FROM stdin;
1000003	f	1000001	L	63	63	U	2013-12-30 09:29:53.147+00
1000004	f	1000002	L	83	83	U	2013-12-30 09:31:14.063+00
1000002	f	1000001	L	90	90	U	2013-12-30 09:28:28.969+00
1000001	f	1000001	L	50	50	U	2013-12-30 09:27:10.395+00
1000007	f	1000003	L	12	12	U	2014-02-08 02:49:40.569222+00
1000008	f	1000003	L	70	70	U	2014-02-08 02:51:20.587465+00
1000009	f	1000003	L	8	8	U	2014-02-08 02:52:38.45601+00
1000010	f	1000003	L	9	9	U	2014-02-08 02:53:43.696504+00
1000011	f	1000003	L	10	10	U	2014-02-08 02:55:04.389189+00
1000006	f	1000003	L	10	10	U	2014-02-08 02:48:27.804888+00
1000012	f	1000003	N	11	11	U	2014-02-08 06:37:11.884365+00
1000013	f	1000004	N	12	12	U	2014-02-08 06:45:17.020039+00
1000014	f	1000003	L	13	13	U	2014-02-08 07:50:01.246282+00
1000016	f	1000003	L	13	13	U	2014-02-08 07:53:20.303941+00
1000017	f	1000003	L	14	14	U	2014-02-08 07:54:40.041356+00
1000015	f	1000003	L	29	29	U	2014-02-08 07:51:57.688927+00
1000019	f	1000003	L	18	18	U	2014-02-08 08:25:57.266328+00
1000018	f	1000003	L	16	16	U	2014-02-08 08:24:17.698795+00
1000020	f	1000003	L	19	19	U	2014-02-08 08:27:22.706429+00
1000021	f	1000003	L	20	20	U	2014-02-08 08:28:30.135627+00
1000022	f	1000003	L	21	21	U	2014-02-08 09:52:26.671371+00
1000023	f	1000003	L	22	22	U	2014-02-08 09:54:29.639186+00
1000024	f	1000003	L	23	23	U	2014-02-08 09:56:12.824966+00
1000025	f	1000003	L	24	24	U	2014-02-08 09:57:08.857717+00
1000026	f	1000003	L	25	25	U	2014-02-08 09:58:06.500864+00
1000027	f	1000003	L	24	24	U	2014-02-08 10:12:48.363175+00
1000028	f	1000003	L	26	26	U	2014-02-08 10:13:48.534709+00
\.


--
-- Data for Name: sales_product; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY sales_product (id, sale_id, category_id, type_id, brand_id, name, description, normal_price, discount_type, discount, valid_from, valid_to, currency_id, weight_unit_id, standard_weight) FROM stdin;
1000003	1000003	1000002	1000003	1000001	product name 3	product 3	30	percentage	1	2013-12-30	\N	1	kg	30
1000004	1000004	1000001	1000001	1000002	product 4 name	product 4	40	percentage	1	2013-12-30	\N	1	kg	40
1000002	1000002	1000001	1000001	1000001	product name 2	product 2	10	percentage	1	2013-12-30	\N	1	kg	10
1000001	1000001	1000001	1000001	1000001	product name 1	product 1	10	percentage	1	2013-12-30	\N	1	kg	10
1000007	1000007	1000001	1000001	1000003	product name 6	product with carrier shipping	2	\N	\N	2014-02-08	\N	1	kg	2
1000008	1000008	1000001	1000001	1000003	product name 7	product with invoice shipping	3	\N	\N	2014-02-08	\N	1	kg	3
1000009	1000009	1000001	1000001	1000003	product name 8	product with flat rate	5	\N	\N	2014-02-08	\N	1	kg	5
1000010	1000010	1000001	1000001	1000003	product name 9	the product with free shipping 	9	\N	\N	2014-02-08	\N	1	kg	9
1000011	1000011	1000001	1000001	1000003	product name 10	the product with custom shipping	10	\N	\N	2014-02-08	\N	1	kg	10
1000023	1000023	1000002	1000003	1000003	item2 spm not allow group flat rate	product for test	2	\N	\N	2014-02-08	\N	1	kg	2
1000006	1000006	1000001	1000001	1000003	product name 5	the product with carrier shipping	1.02000000000000002	\N	\N	2014-02-08	\N	1	kg	1.05000000000000004
1000012	1000012	1000001	1000001	1000003	product name 11	the product for corporate account 3	2	\N	\N	2014-02-08	\N	1	kg	1
1000013	1000013	1000001	1000001	1000004	product name 12	the product for corporate account 4	4	\N	\N	2014-02-08	\N	1	kg	3
1000024	1000024	1000002	1000003	1000003	item3 spm not allow group carrier shipping	product for test	3	\N	\N	2014-02-08	\N	1	kg	3
1000014	1000014	1000001	1000001	1000003	spm group test with carrier EMS USPS item1	product for common carrier service	2	\N	\N	2014-02-08	\N	1	kg	1
1000025	1000025	1000001	1000001	1000003	item4 spm not allow group custom shipping	product for sale	3	\N	\N	2014-02-08	\N	1	kg	3
1000016	1000016	1000001	1000001	1000003	spm group test with carrier USPS item3	product for test	3	\N	\N	2014-02-08	\N	1	kg	3
1000017	1000017	1000002	1000003	1000003	spm group test with carrier EMS item4	product for sale	4	\N	\N	2014-02-08	\N	1	kg	4
1000026	1000026	1000001	1000001	1000003	item5 spm not allow group invoice shipping	product for sale	5	\N	\N	2014-02-08	\N	1	kg	5
1000015	1000015	1000001	1000001	1000003	spm group test with carrier EMS USPS item2	product for test	2	\N	\N	2014-02-08	\N	1	kg	2
1000019	1000019	1000001	1000001	1000003	spm group test with custom shipping 1, 2	product for test	4	\N	\N	2014-02-08	\N	1	kg	3
1000027	1000027	1000001	1000001	1000003	spm group test product in shop 5	product for test	1	\N	\N	2014-02-08	\N	1	kg	1
1000018	1000018	1000001	1000001	1000003	spm group test with custom shipping 1,2	product for test	2	\N	\N	2014-02-08	\N	1	kg	1
1000020	1000020	1000001	1000001	1000003	spm group test with custom shipping 1	product for test	6	\N	\N	2014-02-08	\N	1	kg	5
1000021	1000021	1000001	1000001	1000003	spm group test with custom shipping 2	product for test	8	\N	\N	2014-02-08	\N	1	kg	7
1000022	1000022	1000001	1000001	1000003	item1 spm not allow group free shipping	product for test	2	\N	\N	2014-02-08	\N	1	kg	1
1000028	1000028	1000001	1000001	1000003	spm group test product in shop 6	product for test	2	\N	\N	2014-02-08	\N	1	kg	2
\.


--
-- Data for Name: sales_productpicture; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY sales_productpicture (id, product_id, is_brand_attribute, picture) FROM stdin;
1000002	1000002	f	product_pictures/test.jpeg
1000003	1000003	f	product_pictures/test.jpeg
1000004	1000004	f	product_pictures/test.jpeg
1000001	1000001	f	product_pictures/test.jpeg
1000005	\N	f	product_pictures/test.jpeg
\.


--
-- Data for Name: attributes_brandattributepreview; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY attributes_brandattributepreview (id, product_id, brand_attribute_id, preview_id) FROM stdin;
1000005	1000003	1000005	\N
1000006	1000003	1000006	\N
1000007	1000004	1000007	\N
1000008	1000004	1000008	\N
1000009	1000002	1000001	\N
10000010	1000002	1000002	\N
1000003	1000002	1000003	\N
1000004	1000002	1000004	\N
1000001	1000001	1000001	\N
1000002	1000001	1000002	\N
10000011	1000001	1000003	\N
10000012	1000001	1000004	\N
\.


--
-- Data for Name: attributes_commonattribute; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY attributes_commonattribute (id, for_type_id, name) FROM stdin;
1000001	1000005	item gen prop 1
1000002	1000005	item gen prop 2
1000003	1000001	common attr1 for product type 1
1000004	1000002	common attr1 for product type 2
1000005	1000003	common attr1 for product type 3
1000006	1000004	common attr1 for product type 4
\.


--
-- Data for Name: barcodes_barcode; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY barcodes_barcode (id, upc, sale_id, brand_attribute_id, common_attribute_id) FROM stdin;
1000009	33331	1000003	1000005	1000005
10000010	33332	1000003	1000006	1000005
10000011	44441	1000004	1000007	1000003
10000012	44442	1000004	1000008	1000003
1000003	22221	1000002	1000001	1000003
1000004	22222	1000002	1000002	1000003
1000007	22223	1000002	1000003	1000003
1000008	22224	1000002	1000004	1000003
1000001	11111	1000001	1000001	1000003
1000002	11112	1000001	1000002	1000003
1000005	11113	1000001	1000003	1000003
1000006	11114	1000001	1000004	1000003
10000014	66660	1000007	\N	1000003
10000015	77770	1000008	\N	1000003
10000016	88880	1000009	\N	1000003
10000017	99990	1000010	\N	1000003
10000018	10100	1000011	\N	1000003
10000013	55550	1000006	\N	1000003
10000019	11000	1000012	\N	1000003
10000020	12000	1000013	\N	1000003
10000021	13000	1000014	\N	1000003
10000023	15000	1000016	\N	1000003
10000024	16000	1000017	\N	1000005
10000022	14000	1000015	\N	1000003
10000026	18000	1000019	\N	1000003
10000025	17000	1000018	\N	1000003
10000027	19000	1000020	\N	1000003
10000028	20000	1000021	\N	1000003
10000029	21000	1000022	\N	1000003
10000030	22000	1000023	\N	1000005
10000031	23000	1000024	\N	1000005
10000032	24000	1000025	\N	1000003
10000033	25000	1000026	\N	1000003
10000034	24000	1000027	\N	1000003
10000035	26000	1000028	\N	1000003
\.


--
-- Data for Name: django_session; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY django_session (session_key, session_data, expire_date) FROM stdin;
cu29i0sm2jzbav8ka4nnq9xqcpc52w6h	MWI4YmQwYWE1MDljZmVlNTYzM2ViMjI0NjMyMzllNDk3Yjg0OTFkODqAAn1xAShVFndpemFyZF9zYWxlX3dpemFyZF9uZXd9cQIoVQpzdGVwX2ZpbGVzfVUEc3RlcE5VCmV4dHJhX2RhdGF9VQlzdGVwX2RhdGF9dVUNX2F1dGhfdXNlcl9pZEpEQg8AVRJfYXV0aF91c2VyX2JhY2tlbmRVKWRqYW5nby5jb250cmliLmF1dGguYmFja2VuZHMuTW9kZWxCYWNrZW5kVQlwYWdlX3NpemVLZFUPZGphbmdvX2xhbmd1YWdlWAIAAABlbnUu	2014-02-22 10:21:32.818047+00
\.


--
-- Data for Name: shippings_shipping; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY shippings_shipping (id, handling_fee, allow_group_shipment, allow_pickup, pickup_voids_handling_fee, shipping_calculation) FROM stdin;
1000003	30	t	f	f	1
1000004	40	t	f	f	1
1000002	20	t	f	f	1
1000001	10	t	t	t	2
1000006	23	t	f	f	3
1000007	13	t	f	f	5
1000008	21	t	f	f	2
1000009	\N	t	f	f	1
1000010	23	t	f	f	4
1000005	12	t	f	f	3
1000011	10	t	f	f	3
1000012	10	t	f	f	3
1000013	11	t	f	f	3
1000015	13	t	f	f	3
1000016	14	t	f	f	3
1000014	12	t	f	f	3
1000018	18	t	f	f	4
1000017	17	t	f	f	4
1000019	19	t	f	f	4
1000020	20	t	f	f	4
1000021	\N	f	f	f	1
1000022	1	f	f	f	2
1000023	2	f	f	f	3
1000024	3	f	f	f	4
1000025	5	f	f	f	5
1000026	1	f	f	f	3
1000027	2	t	f	f	3
\.


--
-- Data for Name: sales_shippinginsale; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY sales_shippinginsale (id, sale_id, shipping_id) FROM stdin;
1000001	1000001	1000001
1000002	1000002	1000002
1000003	1000003	1000003
1000004	1000004	1000004
1000005	1000006	1000005
1000006	1000007	1000006
1000007	1000008	1000007
1000008	1000009	1000008
1000009	1000010	1000009
1000010	1000011	1000010
1000011	1000012	1000011
1000012	1000013	1000012
1000013	1000014	1000013
1000014	1000015	1000014
1000015	1000016	1000015
1000016	1000017	1000016
1000017	1000018	1000017
1000018	1000019	1000018
1000019	1000020	1000019
1000020	1000021	1000020
1000021	1000022	1000021
1000022	1000023	1000022
1000023	1000024	1000023
1000024	1000025	1000024
1000025	1000026	1000025
1000026	1000027	1000026
1000027	1000028	1000027
\.


--
-- Data for Name: sales_shopsinsale; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY sales_shopsinsale (id, sale_id, shop_id, is_freezed) FROM stdin;
1000003	1000003	1000002	f
1000004	1000004	1000003	f
1000002	1000002	1000001	f
1000001	1000001	1000001	f
1000007	1000007	1000006	f
1000008	1000008	1000006	f
1000009	1000009	1000006	f
1000010	1000010	1000006	f
1000011	1000011	1000006	f
1000006	1000006	1000006	f
1000012	1000014	1000006	f
1000013	1000016	1000006	f
1000014	1000017	1000006	f
1000015	1000015	1000006	f
1000017	1000019	1000006	f
1000016	1000018	1000006	f
1000018	1000020	1000006	f
1000019	1000021	1000006	f
1000020	1000022	1000006	f
1000021	1000023	1000006	f
1000022	1000024	1000006	f
1000023	1000025	1000006	f
1000024	1000026	1000006	f
1000025	1000027	1000005	f
1000026	1000028	1000006	f
\.


--
-- Data for Name: shippings_customshippingrate; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY shippings_customshippingrate (id, seller_id, shipment_type, total_order_type, total_order_upper, total_order_lower, shipping_rate) FROM stdin;
1000001	1000003	custom shipment 1	W	10	1	5
1000002	1000003	custom shipping 2	P	100	1	6
\.


--
-- Data for Name: shippings_customshippingrateinshipping; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY shippings_customshippingrateinshipping (id, shipping_id, custom_shipping_rate_id) FROM stdin;
1000001	1000010	1000001
1000002	1000017	1000001
1000003	1000017	1000002
1000004	1000018	1000001
1000005	1000018	1000002
1000006	1000019	1000001
1000007	1000020	1000002
1000008	1000024	1000001
1000009	1000024	1000002
\.


--
-- Data for Name: shippings_flatrateinshipping; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY shippings_flatrateinshipping (id, shipping_id, flat_rate) FROM stdin;
1000001	1000001	5
1000002	1000008	15
1000003	1000022	12
\.


--
-- Data for Name: shippings_serviceinshipping; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY shippings_serviceinshipping (id, shipping_id, service_id) FROM stdin;
1000001	1000005	1
1000002	1000006	1
1000003	1000011	1
1000004	1000012	1
1000005	1000013	1
1000006	1000013	2
1000007	1000014	1
1000008	1000014	2
1000009	1000015	2
1000010	1000016	1
1000011	1000023	1
1000012	1000023	2
1000013	1000026	1
1000014	1000027	1
\.


--
-- Data for Name: stocks_productstock; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY stocks_productstock (id, sale_id, brand_attribute_id, common_attribute_id, shop_id, stock, rest_stock) FROM stdin;
1000009	1000003	1000005	1000005	1000002	31	31
10000010	1000003	1000006	1000005	1000002	32	32
10000011	1000004	1000007	1000003	1000003	41	41
10000012	1000004	1000008	1000003	1000003	42	42
1000003	1000002	1000001	1000003	1000001	21	21
1000004	1000002	1000002	1000003	1000001	22	22
1000007	1000002	1000003	1000003	1000001	23	23
1000008	1000002	1000004	1000003	1000001	24	24
1000001	1000001	1000001	1000003	1000001	11	11
1000002	1000001	1000002	1000003	1000001	12	12
1000005	1000001	1000003	1000003	1000001	13	13
1000006	1000001	1000004	1000003	1000001	14	14
10000014	1000007	\N	1000003	1000006	12	12
10000015	1000008	\N	1000003	1000006	70	70
10000016	1000009	\N	1000003	1000006	8	8
10000017	1000010	\N	1000003	1000006	9	9
10000018	1000011	\N	1000003	1000006	10	10
10000013	1000006	\N	1000003	1000006	10	10
10000019	1000012	\N	1000003	\N	11	11
10000020	1000013	\N	1000003	\N	12	12
10000021	1000014	\N	1000003	1000006	13	13
10000022	1000015	\N	1000003	\N	14	14
10000023	1000016	\N	1000003	1000006	13	13
10000024	1000017	\N	1000005	1000006	14	14
10000025	1000015	\N	1000003	1000006	15	15
10000027	1000019	\N	1000003	1000006	18	18
10000026	1000018	\N	1000003	1000006	16	16
10000028	1000020	\N	1000003	1000006	19	19
10000029	1000021	\N	1000003	1000006	20	20
10000030	1000022	\N	1000003	1000006	21	21
10000031	1000023	\N	1000005	1000006	22	22
10000032	1000024	\N	1000005	1000006	23	23
10000033	1000025	\N	1000003	1000006	24	24
10000034	1000026	\N	1000003	1000006	25	25
10000035	1000027	\N	1000003	1000005	24	24
10000036	1000028	\N	1000003	1000006	26	26
\.


--
-- PostgreSQL database dump complete
--

COMMIT;

