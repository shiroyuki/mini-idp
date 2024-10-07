class GrantType:
    # The authorization flow
    AUTHORIZATION = 'authorization'

    # The client-credentials flow
    CLIENT_CREDENTIALS = 'client_credentials'

    # The device-code flow
    DEVICE_CODE = 'urn:ietf:params:oauth:grant-type:device_code'

    # The on-behalf-of flow
    IMPERSONATION = 'urn:ietf:params:oauth:grant-type:jwt-bearer'
