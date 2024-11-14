# mini-idp

The Mini Identity Provider for Local Development and Testing

## Features

* Provide the bare-bone compatibility with OAuth2 standards (authorization flow, device code flow, client credentials flow).

(Future)

* OTP Support

## Requirements

* Python 3.9 or newer
* PostgreSQL 16 or newer (compatible with 14+)

## Setup

### Configuration

* The schema of the configuration file is `midp.config.MainConfig`.
* You can set the environment variable `MINI_IDP_CONFIG_PATHS` to specify the configuration file paths where `,` is the delimiter.
  * By default, the app will load the config file from `$(pwd)/config-default.yml`.

### Database Migration

Run the SQL scripts in `migrations/` in the alphanumeric order.

```shell
psql "postgres://shiroyuki:no-secret@localhost:5432/postgres" -c "CREATE DATABASE miniidp"
psql "postgres://shiroyuki:no-secret@localhost:5432/miniidp" -v ON_ERROR_STOP=1 -f migrations/001-init.sql
```

#### How to reset the system

```sql
DELETE FROM iam_scope WHERE id IS NOT NULL;
DELETE FROM iam_role WHERE id IS NOT NULL;
DELETE FROM iam_user WHERE id IS NOT NULL;
DELETE FROM iam_client WHERE id IS NOT NULL;
DELETE FROM iam_policy WHERE id IS NOT NULL;
DELETE FROM kv WHERE k IS NOT NULL;
```

### Signing Keys

```shell
openssl genrsa -out private.pem 2048
openssl rsa -in private.pem -outform PEM -pubout -out public.pem
```

## Known Issues

* All network operations (DB, HTTP) may still be blocking or running in a different thread. This will be improved over time.

## References

### OAuth2 device-code flow
1. https://datatracker.ietf.org/doc/html/rfc8628
2. https://developer.okta.com/docs/guides/device-authorization-grant/main/

### OAuth2 on-behalf-of flow
1. https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-on-behalf-of-flow
2. https://developer.okta.com/docs/guides/set-up-token-exchange/main/

## Copyright and License Acknowledgements

* FastAPI - © Sebastián Ramírez. Used under MIT license
* Imagination - © Juti Noppornpitak. Used under MIT license
* Material Symbols - © Google Inc. Used under Apache 2 license
* (TBD)