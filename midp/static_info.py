import os

name = 'mini-idp'
version = '0.1a'
verification_ttl = 600
access_token_ttl = 3600
refresh_token_ttl = 3600 * 24 * 7
static_file_path = os.path.join(os.path.dirname(__file__), 'static')
web_ui_file_path = os.path.join(os.path.dirname(__file__), 'webui')
