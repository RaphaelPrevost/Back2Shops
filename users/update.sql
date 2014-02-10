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
COMMIT;
