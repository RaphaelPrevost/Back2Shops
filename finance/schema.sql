CREATE TABLE transactions (
    id serial PRIMARY KEY,
    id_user BIGINT NOT NULL,
    id_order BIGINT NOT NULL,
    id_invoices text NOT NULL,
    iv_numbers text NOT NULL,
    status SMALLINT NOT NULL,
    create_time timestamp without time zone NOT NULL,
    update_time timestamp without time zone NOT NULL,
    amount_due double precision NOT NULL,
    currency character varying(3) NOT NULL,
    invoices_data text not NULL,
    cookie character varying(300)
);

CREATE TABLE processor (
    id serial PRIMARY KEY,
    name character varying(100) NOT NULL,
    img  character varying(200)
);
