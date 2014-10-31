CREATE TABLE vessel (
    id serial PRIMARY KEY,
    name character varying(64),
    imo character varying(64),
    mmsi character varying(64),
    cs character varying(64),
    type character varying(64),
    country_isocode character varying(2),
    photos text
);

CREATE TABLE vessel_navigation (
    id serial PRIMARY KEY,
    id_vessel bigint REFERENCES vessel(id),
    departure_portname character varying(64),
    departure_locode character varying(64),
    departure_time timestamp without time zone NOT NULL,
    arrival_portname character varying(64),
    arrival_locode character varying(64),
    arrival_time timestamp without time zone NOT NULL,
    created timestamp without time zone DEFAULT now() NOT NULL
);

CREATE TABLE vessel_position (
    id serial PRIMARY KEY,
    id_vessel bigint REFERENCES vessel(id),
    location character varying(32),
    longitude double precision,
    latitude double precision,
    heading double precision,
    speed double precision,
    status character varying(64),
    time timestamp without time zone DEFAULT now() NOT NULL
);

CREATE TABLE country (
    iso character varying(2) PRIMARY KEY,
    name character varying(128) not null,
    printable_name character varying(128) not null,
    iso3 character varying(3),
    numcode smallint
);

CREATE TABLE user_fleet (
    id serial PRIMARY KEY,
    id_user BIGINT NOT NULL,
    imo character varying(64),
    mmsi character varying(64)
);


CREATE TABLE container_x_vessel (
    id serial PRIMARY KEY,
    container character varying(64),
    bill_of_landing character varying(64),
    first_pol character varying(64),
    last_pod character varying(64),
    vessel_name character varying(64),
    voyage character varying(64)
);
