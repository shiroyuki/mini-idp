-- Scopes
DROP TABLE IF EXISTS iam_scope CASCADE;
CREATE TABLE iam_scope (
  id VARCHAR PRIMARY KEY,
  name VARCHAR NOT NULL,
  description VARCHAR,
  sensitive boolean DEFAULT false NOT NULL,
  fixed BOOLEAN DEFAULT false NOT NULL
);
ALTER TABLE iam_scope ADD CONSTRAINT uniq_iam_scope_name UNIQUE (name);

-- Roles
DROP TABLE IF EXISTS iam_role CASCADE;
CREATE TABLE iam_role (
  id VARCHAR PRIMARY KEY,
  name VARCHAR NOT NULL,
  description VARCHAR,
  sensitive boolean DEFAULT false NOT NULL,
  fixed BOOLEAN DEFAULT false NOT NULL
);
ALTER TABLE iam_role ADD CONSTRAINT uniq_iam_role_name UNIQUE (name);

-- Users
DROP TABLE IF EXISTS iam_user CASCADE;
CREATE TABLE iam_user (
  id VARCHAR PRIMARY KEY,
  name VARCHAR NOT NULL,
  encrypted_password VARCHAR NOT NULL,
  email VARCHAR NOT NULL,
  full_name VARCHAR,
  roles JSONB
);
ALTER TABLE iam_user ADD CONSTRAINT uniq_iam_user_name UNIQUE (name);
ALTER TABLE iam_user ADD CONSTRAINT uniq_iam_user_email UNIQUE (email);

-- OAuth2 Client
DROP TABLE IF EXISTS iam_client;
CREATE TABLE iam_client (
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
ALTER TABLE iam_client ADD CONSTRAINT uniq_client_name UNIQUE (name);

-- Policies
DROP TABLE IF EXISTS iam_policy;
CREATE TABLE iam_policy (
  id VARCHAR PRIMARY KEY,
  name VARCHAR NOT NULL,
  subjects JSONB NOT NULL,
  resource VARCHAR NOT NULL,
  scopes JSONB NOT NULL,
  fixed BOOLEAN DEFAULT false NOT NULL
);
ALTER TABLE iam_policy ADD CONSTRAINT uniq_iam_policy_name UNIQUE (name);

-- Per-Realm Key-value Store
DROP TABLE IF EXISTS kv;
CREATE TABLE kv (
    k VARCHAR NOT NULL,
    v JSONB NOT NULL,
    expiry_timestamp INTEGER,
    PRIMARY KEY (k)
);
CREATE INDEX idx_realm_kv_expiry_timestamp ON kv (k, expiry_timestamp);
