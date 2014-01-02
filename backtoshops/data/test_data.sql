BEGIN;
--
-- PostgreSQL database dump
--

--
-- Data for Name: accounts_brand; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY accounts_brand (id, name, logo) FROM stdin;
1000001	brand 1	brand_logos/test.jpeg
1000002	brand 2	brand_logos/test.jpeg
\.


--
-- Data for Name: auth_user; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY auth_user (id, password, last_login, is_superuser, username, first_name, last_name, email, is_staff, is_active, date_joined) FROM stdin;
1000003	pbkdf2_sha256$10000$Ht0hiizn8erI$m1fikBu3Vg/weXzADR+AHmwrDUnddmDzBX+nizt53TU=	2013-12-31 05:49:20.210505+00	f	test_user2_1000000			user2@infinite-code.com	t	t	2013-12-30 08:59:24.348+00
1000001	pbkdf2_sha256$10000$P5L1F8apMmEm$GRYb7vEvdj+5H5QfP+5fieH37NuI8s6/aq4s+9Ow4Y8=	2014-01-02 03:56:46.496675+00	t	test_admin_1000000			admin@infinite-code.com	t	t	2013-12-30 08:45:04.266+00
1000002	pbkdf2_sha256$10000$ZBzadrTLzFlV$4RF8y2R96/njhvCk4GsJZHxsBks2Sc7zCOACQ5DIXJA=	2014-01-02 03:57:36.394391+00	f	test_user1_1000000			user1@infinite-code.com	t	t	2013-12-30 08:58:55.267+00
\.


--
-- Data for Name: accounts_userprofile; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY accounts_userprofile (id, user_id, work_for_id, language) FROM stdin;
1000001	1000002	1000001	en
1000002	1000003	1000002	en
\.


--
-- Data for Name: shops_shop; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY shops_shop (id, mother_brand_id, gestion_name, address, zipcode, city, phone, name, catcher, description, opening_hours, latitude, longitude, upc, image, country_id) FROM stdin;
1000001	1000001	shop 1	beijing chaoyang	1000001	BEIJING		shop name 1				114	116	11111	shop_images/大学宿舍_1.jpeg	CN
1000002	1000001	shop 2	beijing haidian 	1000001	BEIJING		shop name 2				114	116	22222	shop_images/大学宿舍_2.jpeg	CN
1000003	1000002	shop 3	beijing tongzhou	1000001	BEIJING		shop name 3				114	116	33333	shop_images/大学宿舍_3.jpeg	CN
1000004	1000002	shop 4	beijing xuanwu	1000001	BEIJING		shop name 4				114	116	44444	shop_images/大学宿舍_4.jpeg	CN
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
\.


--
-- Data for Name: sales_product; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY sales_product (id, sale_id, category_id, type_id, brand_id, name, description, normal_price, discount_type, discount, valid_from, valid_to, currency_id, weight_unit_id, weight) FROM stdin;
1000003	1000003	1000002	1000003	1000001	product name 3	product 3	30	percentage	1	2013-12-30	\N	1	kg	30
1000004	1000004	1000001	1000001	1000002	product 4 name	product 4	40	percentage	1	2013-12-30	\N	1	kg	40
1000002	1000002	1000001	1000001	1000001	product name 2	product 2	10	percentage	1	2013-12-30	\N	1	kg	10
1000001	1000001	1000001	1000001	1000001	product name 1	product 1	10	percentage	1	2013-12-30	\N	1	kg	10
\.


--
-- Data for Name: sales_productpicture; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY sales_productpicture (id, product_id, is_brand_attribute, picture) FROM stdin;
1000002	1000002	f	product_pictures/test.jpeg
1000003	1000003	f	product_pictures/test.jpeg
1000004	1000004	f	product_pictures/test.jpeg
1000001	1000001	f	product_pictures/test.jpeg
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
\.


--
-- Data for Name: django_session; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY django_session (session_key, session_data, expire_date) FROM stdin;
\.


--
-- Data for Name: shippings_shipping; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY shippings_shipping (id, handling_fee, allow_group_shipment, allow_pickup, pickup_voids_handling_fee, shipping_calculation) FROM stdin;
1000003	30	t	f	f	1
1000004	40	t	f	f	1
1000002	20	t	f	f	1
1000001	10	t	t	t	2
\.


--
-- Data for Name: sales_shippinginsale; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY sales_shippinginsale (id, sale_id, shipping_id) FROM stdin;
1000001	1000001	1000001
1000002	1000002	1000002
1000003	1000003	1000003
1000004	1000004	1000004
\.


--
-- Data for Name: sales_shopsinsale; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY sales_shopsinsale (id, sale_id, shop_id, is_freezed) FROM stdin;
1000003	1000003	1000002	f
1000004	1000004	1000003	f
1000002	1000002	1000001	f
1000001	1000001	1000001	f
\.


--
-- Data for Name: shippings_flatrateinshipping; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY shippings_flatrateinshipping (id, shipping_id, flat_rate) FROM stdin;
1000001	1000001	5
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
\.


--
-- PostgreSQL database dump complete
--

COMMIT;
