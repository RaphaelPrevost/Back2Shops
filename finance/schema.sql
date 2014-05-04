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

CREATE TABLE trans_paypal (
    id serial PRIMARY KEY,
    id_internal_trans BIGINT not null,
    txn_id character varying(50) not null,
    tax float not null,
    payment_status character varying(20) not null,
    payer_id character varying(25) not null,
    receiver_id character varying(25) not null,
    mc_fee double precision not Null,
    mc_currency character varying(3) NOT NULL,
    mc_gross double precision not NULL,
    create_time timestamp without time zone DEFAULT now()  NOT NULL,
    update_time timestamp without time zone DEFAULT now()  NOT NULL,
    content text,

    FOREIGN KEY (id_internal_trans) REFERENCES transactions (id)
);
CREATE UNIQUE INDEX trans_paypal_by_txn_id ON trans_paypal USING btree (txn_id);
