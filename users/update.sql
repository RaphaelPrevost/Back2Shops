BEGIN;
ALTER TABLE order_items ALTER COLUMN picture type character varying(200);
ALTER TABLE shipping_list ALTER COLUMN picture type character varying(200);
ALTER TABLE return_items ALTER COLUMN picture type character varying(200);
ALTER TABLE shipments ADD COLUMN supported_services text;
ALTER TABLE shipments ALTER COLUMN shipping_fee DROP DEFAULT;
ALTER TABLE shipments ALTER COLUMN shipping_fee DROP NOT NULL;

CREATE TABLE free_shipping_fee (
    id_shipment BIGINT UNIQUE,
    fee double precision,
    FOREIGN KEY (id_shipment) REFERENCES shipments (id)
);
ALTER TABLE shipments ADD COLUMN calculation_method smallint;
ALTER TABLE shipments DROP COLUMN shipping_fee;
ALTER TABLE shipments DROP COLUMN supported_services;
ALTER TABLE shipments DROP COLUMN id_postage;
ALTER TABLE order_items ADD COLUMN id_weight_type bigint;
ALTER TABLE order_items ADD COLUMN id_price_type bigint;

CREATE TABLE shipments_supported_services (
    id serial PRIMARY KEY,
    id_shipment bigint,
    id_postage bigint,
    supported_services text,
    FOREIGN KEY (id_shipment) REFERENCES shipments (id)
);

CREATE TABLE shipments_fee (
    id serial PRIMARY KEY,
    id_shipment bigint,
    handling_fee double precision,
    shipping_fee double precision,
    FOREIGN KEY (id_shipment) REFERENCES shipments (id)
);

ALTER TABLE shipping_list ADD COLUMN free_shipping boolean DEFAULT false NOT NULL;

/* alter tables name */
ALTER TABLE shipments_supported_services RENAME TO shipping_supported_services;
ALTER TABLE shipments_fee RENAME TO shipping_fee;

ALTER TABLE shipments DROP COLUMN id_address;
ALTER TABLE shipments DROP COLUMN id_phone;

CREATE TABLE order_shipment_details (
    id_order bigint REFERENCES orders(id) NOT null,
    id_shipaddr bigint REFERENCES users_address(id),
    id_billaddr bigint REFERENCES users_address(id),
    id_phone bigint REFERENCES users_phone_num(id)
);

ALTER TABLE shipments ADD COLUMN id_order bigint;
ALTER TABLE shipments ADD FOREIGN KEY(id_order) REFERENCES orders(id);
ALTER TABLE shipments ADD COLUMN id_shop bigint;
ALTER TABLE shipments ADD COLUMN id_brand bigint;


ALTER TABLE shipping_list ADD COLUMN id serial PRIMARY KEY;
ALTER TABLE shipping_list ADD COLUMN status smallint DEFAULT 1;
ALTER TABLE shipping_list ADD COLUMN id_orig_shipping_list bigint;
ALTER TABLE shipping_list ADD FOREIGN KEY(id_orig_shipping_list) REFERENCES shipping_list(id);
ALTER TABLE shipments ADD COLUMN shipping_date date;
ALTER TABLE shipments ADD COLUMN tacking_name character varying(100);
ALTER TABLE shipments ADD COLUMN shipping_carrier bigint;
ALTER TABLE shipments ADD COLUMN update_time timestamp without time zone NOT NULL DEFAULT now();
ALTER TABLE shipments RENAME COLUMN timestamp to create_time;

ALTER TABLE order_items ADD COLUMN type_name character varying(50);
ALTER TABLE invoices ADD COLUMN shipping_within BIGINT;

ALTER TABLE users_address ALTER COLUMN address type character varying(512);
ALTER TABLE users_address ADD COLUMN address2 character varying(512) DEFAULT '';

ALTER TABLE orders ADD COLUMN valid boolean DEFAULT true;

ALTER TABLE province ADD COLUMN geoip_name character varying(128);
ALTER TABLE users_address ADD COLUMN full_name character varying(128) DEFAULT '';

ALTER TABLE order_items ALTER COLUMN description type text;

ALTER TABLE invoices ADD COLUMN invoice_items text;

ALTER TABLE order_items ADD COLUMN id_type bigint;
ALTER TABLE order_items ADD COLUMN external_id character varying(50);


-- r516 --
CREATE TABLE incomes_log (
    order_id BIGINT PRIMARY KEY,
    users_id BIGINT NOT NULL,
    up_time timestamp without time zone DEFAULT now() NOT NULL
);

-- r522 --
ALTER TABLE order_items ADD COLUMN id_brand BIGINT NOT NULL;
CREATE TABLE orders_log (
    id serial PRIMARY KEY,
    users_id BIGINT NOT NULL,
    id_order BIGINT NOT NULL,
    id_brand BIGINT NOT NULL,
    id_shop BIGINT NOT NULL,
    pending_date date,
    waiting_payment_date date,
    waiting_shipping_date date,
    completed_date date
);

-- r530 --
CREATE TABLE bought_history (
    id serial PRIMARY KEY,
    id_sale BIGINT NOT NULL,
    users_id BIGINT NOT NULL
);

-- r547 --
ALTER TABLE order_items ADD COLUMN currency character varying(3);
ALTER TABLE order_items ADD COLUMN weight double precision;
ALTER TABLE order_items ADD COLUMN weight_unit character varying(2);
ALTER TABLE order_items ADD COLUMN weight_type_detail text;
ALTER TABLE order_items ADD COLUMN variant_detail text;
ALTER TABLE order_items ADD COLUMN item_detail text;

ALTER TABLE shipping_supported_services ADD COLUMN supported_services_details text;

---Note: Please run the comment out commands after execute: nohup python scripts/oneoff/populate_order_items_data.py --
-- ALTER TABLE order_items ALTER COLUMN currency set not NULL;
-- ALTER TABLE order_items ALTER COLUMN weight set not NULL;
-- ALTER TABLE order_items ALTER COLUMN weight_unit set not NULL;
-- ALTER TABLE order_items ALTER COLUMN item_detail set not NULL;

CREATE TABLE ticket (
    id serial PRIMARY KEY,
    thread_id BIGINT,
    parent_id BIGINT NOT NULL,
    subject character varying(128) NOT NULL,
    message text NOT NULL,
    priority smallint NOT NULL,
    feedback smallint,
    fo_author integer,
    bo_author integer,
    fo_recipient integer,
    bo_recipient integer,
    id_brand BIGINT NOT NULL,
    id_order BIGINT,
    id_shipment BIGINT,
    replied boolean DEFAULT false NOT NULL,
    created timestamp without time zone NOT NULL,
    locked boolean DEFAULT false NOT NULL,
    lock_time timestamp without time zone,
    escalation boolean DEFAULT false NOT NULL,
    escalation_time timestamp without time zone
);
CREATE INDEX ticket_by_thread_id ON ticket USING btree (thread_id);
CREATE INDEX ticket_by_created ON ticket USING btree (created);
CREATE INDEX ticket_by_priority ON ticket USING btree (priority);

CREATE TABLE ticket_attachment (
    id serial PRIMARY KEY,
    location character varying(128) NOT NULL,
    random_key character varying(128) NOT NULL,
    id_ticket BIGINT
);

ALTER TABLE users_profile ADD COLUMN is_business_account boolean DEFAULT false NOT NULL;
ALTER TABLE users_profile ADD COLUMN company_name text;
ALTER TABLE users_profile ADD COLUMN company_position text;
ALTER TABLE users_profile ADD COLUMN company_tax_id text;

CREATE TABLE coupons (
    id serial PRIMARY KEY,
    id_brand bigint NOT NULL,
    id_bo_user bigint NOT NULL,
    coupon_type smallint NOT NULL,
    creation_time timestamp without time zone DEFAULT now() NOT NULL,
    effective_time timestamp without time zone DEFAULT now() NOT NULL,
    expiration_time timestamp without time zone,
    stackable boolean NOT NULL,
    redeemable_always boolean NOT NULL,
    max_redeemable integer,
    first_order_only boolean NOT NULL,
    manufacturer boolean NOT NULL DEFAULT false,
    password character varying(256),
    description text,
    valid boolean NOT NULL DEFAULT true
);

CREATE TABLE coupon_accepted_at (
    id_coupon bigint NOT NULL REFERENCES coupons(id),
    id_shop bigint NOT NULL,
    CONSTRAINT coupon_accepted_at_key PRIMARY KEY (id_coupon, id_shop)
);

CREATE TABLE coupon_given_to (
    id_coupon bigint NOT NULL REFERENCES coupons(id),
    id_user integer NOT NULL REFERENCES users(id),
    CONSTRAINT coupon_given_to_key PRIMARY KEY (id_coupon, id_user)
);

CREATE TABLE coupon_condition (
    id serial PRIMARY KEY,
    id_coupon bigint NOT NULL REFERENCES coupons(id),
    id_value bigint,
    id_type smallint,
    operation integer NOT NULL,
    comparison integer,
    threshold double precision
);

CREATE TABLE coupon_discount (
    id_coupon bigint PRIMARY KEY NOT NULL REFERENCES coupons(id),
    discount_type integer NOT NULL,
    discount double precision NOT NULL
);

CREATE TABLE coupon_give_away (
    id_coupon bigint PRIMARY KEY NOT NULL REFERENCES coupons(id),
    max_selection integer,
);

CREATE TABLE coupon_gift (
    id_coupon bigint NOT NULL REFERENCES coupons(id),
    id_sale BIGINT NOT NULL,
    quantity integer NOT NULL,
    CONSTRAINT coupon_gift_key PRIMARY KEY (id_coupon, id_sale)
);

CREATE TABLE coupon_redeemed (
    id serial PRIMARY KEY,
    id_coupon bigint NOT NULL REFERENCES coupons(id),
    id_user integer NOT NULL,
    id_order BIGINT NOT NULL,
    id_invoice BIGINT,
    order_status smallint NOT NULL,
    redeemed_time timestamp without time zone DEFAULT now() NOT NULL,
    account_address text,
    account_phone character varying(32),
    user_agent text
);

CREATE TABLE store_credit (
    id_coupon bigint PRIMARY KEY NOT NULL REFERENCES coupons(id),
    currency character varying(3) REFERENCES currency(code),
    amount double precision NOT NULL,
    redeemed_in_full boolean DEFAULT false NOT NULL
);

CREATE TABLE store_credit_redeemed (
    id serial PRIMARY KEY,
    id_coupon bigint NOT NULL REFERENCES coupons(id),
    id_user integer NOT NULL,
    id_order BIGINT NOT NULL,
    id_invoice BIGINT,
    order_status smallint NOT NULL,
    currency character varying(3) REFERENCES currency(code),
    redeemed_amount double precision NOT NULL
);

ALTER TABLE order_items ADD COLUMN modified_by_coupon BIGINT;
ALTER TABLE coupons ADD COLUMN manufacturer boolean NOT NULL DEFAULT false;
ALTER TABLE shipping_fee ADD COLUMN details text;
ALTER TABLE coupons ADD COLUMN valid boolean NOT NULL DEFAULT true;
ALTER TABLE coupons ADD COLUMN effective_time timestamp without time zone DEFAULT now() NOT NULL;
COMMIT;
