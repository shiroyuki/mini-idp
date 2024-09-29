# mini-idp

The Mini Identity Provider for Local Development and Testing

## Features

* Provide the bare-bone compatibility with OAuth2 standards (authorization flow, device code flow, client credentials flow).

## Requirements

* Python 3.9 or newer
* PostgreSQL 16 or newer (compatible with 14+)

## Configuration

* The schema of the configuration file is `midp.config.MainConfig`.
* You can set the environment variable `MINI_IDP_CONFIG_PATHS` to specify the configuration file paths where `,` is the delimiter.
  * By default, the app will load the config file from `$(pwd)/config-default.yml`.

## Database Migation

Run the SQL scripts in `migrations/` in the alphanumeric order.

```shell
psql "postgres://shiroyuki:no-secret@localhost:5432/postgres" -v ON_ERROR_STOP=1 -c "CREATE DATABASE miniidp"
psql "postgres://shiroyuki:no-secret@localhost:5432/miniidp" -v ON_ERROR_STOP=1 -f migrations/001-init.sql
```

## References

### OAuth2 device-code flow
1. https://developer.okta.com/docs/guides/device-authorization-grant/main/

### OAuth2 on-behalf-of flow
1. https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-on-behalf-of-flow
2. https://developer.okta.com/docs/guides/set-up-token-exchange/main/