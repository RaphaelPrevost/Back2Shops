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
    phone_num_desp character varying(128)
);

CREATE TABLE users_address (
    id serial PRIMARY KEY,
    users_id integer NOT NULL,
    addr_type smallint NOT NULL,
    address character varying(128) NOT NULL,
    city character varying(64) NOT NULL,
    postal_code character varying(25),
    country_code character varying(2) NOT NULL REFERENCES country(iso),
    province_code character varying(2),
    address_desp character varying(128)
);
