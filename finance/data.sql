BEGIN;
--
-- Data for Name: processor; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY processor (id, name, img) FROM stdin;
1	Paypal	\N
2	VISA/Mastercard	\N
3	VISA/Mastercard with 3DSecure	\N
4	Paybox	\N
\.


--
-- Name: processor_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('processor_id_seq', 3, true);

COMMIT;
