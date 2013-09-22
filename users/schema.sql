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
