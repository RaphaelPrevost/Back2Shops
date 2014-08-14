CREATE TABLE users (
    id serial PRIMARY KEY,
    email character varying(128) NOT NULL,
    password character varying(128) NOT NULL,
    salt character varying(128) NOT NULL,
    hash_iteration_count integer NOT NULL,
    hash_algorithm integer NOT NULL
);
CREATE UNIQUE INDEX users_by_email ON users USING btree (email);

CREATE TABLE users_logins (
    id serial PRIMARY KEY,
    users_id integer NOT NULL,
    ip_address character varying(16) NOT NULL,
    headers character varying(64) NOT NULL,
    csrf_token character varying(32) NOT NULL,
    cookie_expiry timestamp without time zone NOT NULL,
    timestamp timestamp without time zone DEFAULT now() NOT NULL
);

CREATE TABLE country (
    iso character varying(2) PRIMARY KEY,
    name character varying(128) not null,
    printable_name character varying(128) not null,
    iso3 character varying(3),
    numcode smallint
);

CREATE TABLE country_calling_code (
    country_code character varying(2) PRIMARY KEY REFERENCES country(iso),
    calling_code character varying(8) NOT NULL
);

CREATE TABLE province (
    code character varying(8) NOT NULL,
    name character varying(128) NOT NULL,
    country_code character varying(2) NOT NULL REFERENCES country(iso),
    CONSTRAINT province_pkey PRIMARY KEY (code, country_code)
);

CREATE TABLE locale (
    name character varying(16) PRIMARY KEY
);

CREATE TABLE title (
    title character varying(16) NOT NULL,
    locale character varying(16) NOT NULL REFERENCES locale(name),
    CONSTRAINT title_key PRIMARY KEY (title, locale)
);

CREATE TABLE users_profile (
    id serial PRIMARY KEY,
    users_id integer NOT NULL,
    locale character varying(16) DEFAULT 'en-US',
    title character varying(16),
    first_name character varying(64),
    last_name character varying(64) NOT NULL,
    gender character varying(8),
    birthday timestamp without time zone,
    FOREIGN KEY (locale, title) REFERENCES title (locale, title)
);

CREATE TABLE users_phone_num (
    id serial PRIMARY KEY,
    users_id integer NOT NULL,
    country_num character varying(2) NOT NULL REFERENCES country_calling_code(country_code),
    phone_num character varying(25) NOT NULL,
    phone_num_desp character varying(128),
    valid boolean DEFAULT true NOT NULL
);

CREATE TABLE users_address (
    id serial PRIMARY KEY,
    users_id integer NOT NULL,
    addr_type smallint NOT NULL,
    address character varying(512) NOT NULL,
    address2 character varying(512) NOT NULL,
    city character varying(64) NOT NULL,
    postal_code character varying(25),
    country_code character varying(2) NOT NULL REFERENCES country(iso),
    province_code character varying(2),
    address_desp character varying(128),
    valid boolean DEFAULT true NOT NULL
);

CREATE TABLE orders (
    id serial PRIMARY KEY,
    id_user integer NOT NULL,
    confirmation_time timestamp without time zone DEFAULT now() NOT NULL,
    valid boolean DEFAULT true
);

CREATE TABLE order_items (
    id serial PRIMARY KEY,
    id_sale BIGINT NOT NULL,
    id_shop BIGINT,
    id_variant BIGINT,
    id_weight_type BIGINT,
    id_price_type BIGINT,
    price double precision NOT NULL,
    name character varying(150) NOT NULL,
    type_name character varying(50),
    picture character varying(200),
    description character varying(128),
    copy_time timestamp without time zone DEFAULT now() NOT NULL,
    barcode character varying(50)
);

CREATE TABLE order_details (
    id_order bigint REFERENCES orders(id),
    id_item bigint REFERENCES order_items(id),
    quantity integer NOT NULL
);

CREATE TABLE order_shipment_details (
    id_order bigint REFERENCES orders(id),
    id_shipaddr bigint REFERENCES users_address(id),
    id_billaddr bigint REFERENCES users_address(id),
    id_phone bigint REFERENCES users_phone_num(id)
);

CREATE TABLE shipments (
    id serial PRIMARY KEY,
    id_order bigint,
    id_shop bigint,
    id_brand bigint,
    mail_tracking_number character varying(50),
    tracking_name character varying(100),
    status SMALLINT,
    create_time timestamp without time zone NOT NULL,
    update_time timestamp without time zone NOT NULL default now(),
    calculation_method smallint,
    shipping_date date,
    shipping_carrier bigint,
    FOREIGN KEY (id_order) REFERENCES orders(id)
);

CREATE TABLE shipping_supported_services (
    id serial PRIMARY KEY,
    id_shipment bigint,
    id_postage bigint,
    supported_services text,
    FOREIGN KEY (id_shipment) REFERENCES shipments (id)
);

CREATE TABLE shipping_fee (
    id serial PRIMARY KEY,
    id_shipment bigint,
    handling_fee double precision,
    shipping_fee double precision,
    FOREIGN KEY (id_shipment) REFERENCES shipments (id)
);

CREATE TABLE shipping_list (
    id serial PRIMARY KEY,
    id_item BIGINT REFERENCES order_items(id),
    id_shipment BIGINT REFERENCES shipments(id),
    quantity INTEGER NOT NULL,
    packing_quantity INTEGER NOT NULL default 0,
    picture character varying(200),
    free_shipping boolean DEFAULT false NOT NULL
);
CREATE UNIQUE INDEX shipping_list_by_item_shipment ON shipping_list USING btree (id_item, id_shipment);

CREATE TABLE free_shipping_fee (
    id_shipment BIGINT UNIQUE,
    fee double precision,
    FOREIGN KEY (id_shipment) REFERENCES shipments (id)
);

CREATE TABLE currency (
    id serial PRIMARY KEY,
    code character varying(3) NOT NULL,
    description character varying(200) NOT NULL
);
CREATE UNIQUE INDEX currency_code ON currency USING btree (code);

CREATE TABLE invoices (
    id serial PRIMARY KEY,
    id_order BIGINT REFERENCES orders(id),
    id_shipment BIGINT REFERENCES shipments(id),
    creation_time timestamp without time zone DEFAULT now() NOT NULL,
    update_time timestamp without time zone DEFAULT now() NOT NULL,
    amount_due double precision NOT NULL,
    amount_paid double precision DEFAULT 0.0 NOT NULL,
    due_within BIGINT,
    shipping_within BIGINT,
    currency character varying(3) REFERENCES currency(code),
    invoice_file character varying(100),
    invoice_xml text,
    invoice_number BIGINT NOT NULL,
    status SMALLINT DEFAULT 1 NOT NULL
);

CREATE TABLE invoice_status(
    id_invoice BIGINT REFERENCES invoices(id),
    status SMALLINT DEFAULT 1 NOT NULL,
    amount_paid double precision,
    timestamp timestamp without time zone NOT NULL
);
---
-- invoice_status: status
-- 1 - INVOICE_OPEN,
-- 2 - INVOICE_PART,
-- 3 - INVOICE_VOID,
-- 4 - INVOICE_PAID,
-- 5 - INVOICE_LATE
---

CREATE TABLE shipment_status (
    id_shipment BIGINT REFERENCES shipments(id),
    status SMALLINT NOT NULL,
    timestamp timestamp without time zone DEFAULT now() NOT NULL
);

---
-- shipment_status: status
-- 1 - SHIPMENT_PACKING,
-- 2 - SHIPMENT_DELAYED,
-- 3 - SHIPMENT_DELIVER
---

CREATE TABLE returns (
    id serial PRIMARY KEY,
    id_order BIGINT REFERENCES orders(id),
    status SMALLINT NOT NULL,
    timestamp timestamp without time zone DEFAULT now() NOT NULL,
    amount double precision NOT NULL,
    currency character varying(3) -- TODO, REFERENCES currency(code)
 );

CREATE TABLE return_items (
    id_return BIGINT REFERENCES returns(id),
    id_item BIGINT REFERENCES order_items(id),
    quantity INTEGER NOT NULL,
    picture character varying(200),
    message character varying(300)
);

CREATE TABLE return_status (
    id_return BIGINT REFERENCES returns(id),
    status SMALLINT NOT NULL,
    timestamp timestamp without time zone NOT NULL,
    amount INTEGER NOT NULL
);

---
-- return_status: status
--  1    (1 << 0) - RETURN_ELIGIBLE,
--  2    (1 << 1) - RETURN_REJECTED,
--  4    (1 << 2) - RETURN_RECEIVED,
--  8    (1 << 3) - RETURN_EXAMINED,
--  16   (1 << 4) - RETURN_ACCEPTED,
--  32   (1 << 5) - RETURN_REJECTED,
--  64   (1 << 6) - RETURN_PROPOSAL,
--  128  (1 << 7) - RETURN_REFUNDED,
--  256  (1 << 8) - RETURN_REJECTED_FRAUD,
--  512  (1 << 9) - RETURN_REJECTED_INVAL,
--  1024 (1 << 10)  RETURN_PROPOSAL_ACCEPT,
--  2048 (1 << 11) - RETURN_PROPOSAL_REJECT
---
CREATE TABLE transactions (
    id serial PRIMARY KEY,
    id_order BIGINT NOT NULL,
    id_invoices text NOT NULL,
    status SMALLINT NOT NULL,
    create_time timestamp without time zone NOT NULL,
    update_time timestamp without time zone NOT NULL,
    amount_due double precision NOT NULL,
    cookie character varying(300),
    id_processor BIGINT,
    url_success character varying(100),
    url_failure character varying(100)
);
