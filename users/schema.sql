CREATE TABLE users (
    id serial PRIMARY KEY,
    email character varying(128) NOT NULL,
    password character varying(128) NOT NULL,
    salt character varying(128) NOT NULL,
    hash_iteration_count integer NOT NULL,
    hash_algorithm integer NOT NULL
);

CREATE UNIQUE INDEX users_by_email ON users USING btree (email); 
