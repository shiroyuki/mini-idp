-- Realms
DROP TABLE IF EXISTS realm CASCADE;
CREATE TABLE realm (
  id VARCHAR PRIMARY KEY,
  name VARCHAR NOT NULL
);
ALTER TABLE realm ADD CONSTRAINT uniq_realm_name UNIQUE (name);

-- Scopes
DROP TABLE IF EXISTS iam_scope CASCADE;
CREATE TABLE iam_scope (
  id VARCHAR PRIMARY KEY,
  realm_id VARCHAR,
  name VARCHAR NOT NULL,
  description VARCHAR,
  sensitive boolean,
  FOREIGN KEY (realm_id) REFERENCES realm (id) ON DELETE CASCADE
);
ALTER TABLE iam_scope ADD CONSTRAINT uniq_iam_scope_name UNIQUE (realm_id, name);

-- Roles
DROP TABLE IF EXISTS iam_role CASCADE;
CREATE TABLE iam_role (
  id VARCHAR PRIMARY KEY,
  realm_id VARCHAR NOT NULL,
  name VARCHAR NOT NULL,
  description VARCHAR,
  FOREIGN KEY (realm_id) REFERENCES realm (id) ON DELETE CASCADE
);
ALTER TABLE iam_role ADD CONSTRAINT uniq_iam_role_name UNIQUE (realm_id, name);

-- Users
DROP TABLE IF EXISTS iam_user CASCADE;
CREATE TABLE iam_user (
  id VARCHAR PRIMARY KEY,
  realm_id VARCHAR NOT NULL,
  name VARCHAR NOT NULL,
  hashed_password VARCHAR NOT NULL,
  password_salt VARCHAR NOT NULL,
  email VARCHAR NOT NULL,
  full_name VARCHAR,
  FOREIGN KEY (realm_id) REFERENCES realm (id) ON DELETE CASCADE
);
ALTER TABLE iam_user ADD CONSTRAINT uniq_iam_user_name UNIQUE (realm_id, name);
ALTER TABLE iam_user ADD CONSTRAINT uniq_iam_user_email UNIQUE (realm_id, email);

-- User-Role Links
DROP TABLE IF EXISTS iam_user_role;
CREATE TABLE iam_user_role (
  user_id VARCHAR NOT NULL,
  role_id VARCHAR NOT NULL,
  PRIMARY KEY (user_id, role_id),
  FOREIGN KEY (user_id) REFERENCES iam_user (id) ON DELETE CASCADE,
  FOREIGN KEY (role_id) REFERENCES iam_role (id) ON DELETE CASCADE
);

-- OAuth2 Client
DROP TABLE IF EXISTS client;
CREATE TABLE client (
  id VARCHAR PRIMARY KEY,
  realm_id VARCHAR NOT NULL,
  name VARCHAR NOT NULL,
  encrypted_secret VARCHAR,
  audience VARCHAR NOT NULL,
  grant_type VARCHAR NOT NULL,
  response_type VARCHAR,
  scopes VARCHAR[] NOT NULL,
  extras JSONB,
  description VARCHAR,
  FOREIGN KEY (realm_id) REFERENCES realm (id) ON DELETE CASCADE
);
ALTER TABLE client ADD CONSTRAINT uniq_client_name UNIQUE (realm_id, name);

-- Policies
DROP TABLE IF EXISTS iam_policy;
CREATE TABLE iam_policy (
  id VARCHAR PRIMARY KEY,
  realm_id VARCHAR NOT NULL,
  name VARCHAR NOT NULL,
  subjects JSONB NOT NULL,
  resource VARCHAR NOT NULL,
  scopes VARCHAR[] NOT NULL,
  FOREIGN KEY (realm_id) REFERENCES realm (id) ON DELETE CASCADE
);
ALTER TABLE iam_policy ADD CONSTRAINT uniq_iam_policy_name UNIQUE (realm_id, name);