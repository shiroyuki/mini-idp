-- Root Users
DROP TABLE IF EXISTS root_user CASCADE;
CREATE TABLE root_user (
  id VARCHAR PRIMARY KEY,
  name VARCHAR NOT NULL,
  hashed_password VARCHAR NOT NULL,
  email VARCHAR NOT NULL,
  full_name VARCHAR
);
ALTER TABLE root_user ADD CONSTRAINT uniq_root_user_name UNIQUE (name);
ALTER TABLE root_user ADD CONSTRAINT uniq_root_user_email UNIQUE (email);

-- Root User-Role Links
DROP TABLE IF EXISTS root_user_scope;
CREATE TABLE root_user_scope (
  user_id VARCHAR NOT NULL,
  scope VARCHAR NOT NULL,
  PRIMARY KEY (user_id, scope),
  FOREIGN KEY (user_id) REFERENCES root_user (id) ON DELETE CASCADE
);

-- OAuth2 Client
DROP TABLE IF EXISTS root_client;
CREATE TABLE root_client (
  id VARCHAR PRIMARY KEY,
  name VARCHAR NOT NULL,
  encrypted_secret VARCHAR,
  audience VARCHAR NOT NULL,
  grant_types JSONB NOT NULL,
  response_types JSONB,
  scopes JSONB NOT NULL,
  extras JSONB,
  description VARCHAR
);
ALTER TABLE client ADD CONSTRAINT uniq_root_client_name UNIQUE (name);