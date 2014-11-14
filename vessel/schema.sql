CREATE TABLE vessel (
    id serial PRIMARY KEY,
    name character varying(64),
    imo character varying(64),
    mmsi character varying(64),
    cs character varying(64),
    type character varying(64),
    country_isocode character varying(2),
    photos text,
    next_update_time timestamp without time zone DEFAULT now() NOT NULL
);
CREATE INDEX vessel_by_name ON vessel USING btree (name);
CREATE INDEX vessel_by_imo ON vessel USING btree (imo);
CREATE INDEX vessel_by_mmsi ON vessel USING btree (mmsi);
CREATE INDEX vessel_by_next_update_time ON vessel USING btree (next_update_time);


CREATE TABLE vessel_navigation (
    id serial PRIMARY KEY,
    id_vessel bigint REFERENCES vessel(id),
    departure_locode character varying(64),
    departure_time timestamp without time zone NOT NULL,
    arrival_locode character varying(64),
    arrival_time timestamp without time zone NOT NULL,
    created timestamp without time zone DEFAULT now() NOT NULL
);
CREATE INDEX vessel_navigation_by_created ON vessel_navigation USING btree (created desc);
CREATE INDEX vessel_navigation_by_arrival_time ON vessel_navigation USING btree (arrival_time desc);


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
CREATE INDEX vessel_position_by_time ON vessel_position USING btree (time desc);


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
CREATE INDEX user_fleet_by_id_user ON user_fleet USING btree (id_user);


CREATE TABLE vessel_arrival_notif (
    id serial PRIMARY KEY,
    id_user BIGINT NOT NULL,
    email character varying(128) NOT NULL,
    imo character varying(64),
    mmsi character varying(64),
    done boolean DEFAULT false
);
CREATE INDEX vessel_arrival_notif_by_id_user_not_done ON vessel_arrival_notif USING btree (id_user) WHERE not done;
CREATE INDEX vessel_arrival_notif_by_mmsi_not_done ON vessel_arrival_notif USING btree (mmsi) WHERE not done;


CREATE TABLE container_arrival_notif (
    id serial PRIMARY KEY,
    id_user BIGINT NOT NULL,
    email character varying(128) NOT NULL,
    container character varying(64),
    done boolean DEFAULT false
);
CREATE INDEX container_arrival_notif_by_id_user_not_done ON container_arrival_notif USING btree (id_user) WHERE not done;
CREATE INDEX container_arrival_notif_by_container_not_done ON container_arrival_notif USING btree (container) WHERE not done;


CREATE TABLE port (
    locode character varying(64) PRIMARY KEY,
    name character varying(128) not null,
    longitude double precision,
    latitude double precision
);

