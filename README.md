# mini-idp

The Mini Identity Provider for Local Development and Testing

## Features

* Provide the bare-bone compatibility with OAuth2 standards (authorization flow, device code flow, client credentials flow).

(Future)

* OTP Support

## Requirements

* Python 3.9 or newer
* PostgreSQL 16 or newer (compatible with 14+)

### Requirements for testing and development
* Python virtual environment, either one of these works.
  * `venv` - Python's built-in virtual environment
  * `poetry` - https://python-poetry.org/docs/

## Setup

### First-time setup

#### For any environment

1. Copy `.env.dist` to `.env` and modify as needed. 

#### Testing/Development Environment
* With `venv`...
  1. Initialize a new virtual environment with:
     ```shell
     python3 -m venv .venv
     ```
  2. Activate the virtual environment with:
     ```shell
     ./venv/bin/activate
     ```
  > This is the simplest option for quick work.
* With `poetry`...
  1. Install `poetry`.
     > WARNING: If you are using IntelliJ or PyCharm, please ensure that poetry is accessible via the default execute path
       (`$PATH`) as IntelliJ/PyCharm can detect where `poetry` is but cannot find it for some reason.
  3. Install the shell plugin with:
     ```shell
     poetry self add poetry-plugin-shell
     ```
  4. Activate the environment with:
     ```shell
     poetry shell
     ```

#### Production Environment
* Install dependencies

### Database Migration

Run the SQL scripts in `migrations/` in the alphanumeric order.

```shell
export MINI_IDP_DB_NAME=miniidp
psql "postgres://postgres:nosecret@localhost:5432/postgres" -c "CREATE DATABASE ${MINI_IDP_DB_NAME}"
psql "postgres://postgres:nosecret@localhost:5432/${MINI_IDP_DB_NAME}" -v ON_ERROR_STOP=1 -f migrations/001-init.sql
```

> You can name the database to whatever you want.

> In the development and testing, you can also define the environment variable `MINI_IDP_BOOTING_OPTIONS` with `bootstrap:data-reset` (operational data) or bootstrap:session-reset` (session data).

### Create signing keys

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
