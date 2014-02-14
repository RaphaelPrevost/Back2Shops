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
COMMIT;
