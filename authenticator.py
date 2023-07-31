import json
import os

from dotenv import load_dotenv
from requests_oauthlib import OAuth2Session


class Authenticator:
    def __init__(self, token_file):
        load_dotenv()

        self.token_file = token_file

        # Enable non-HTTPS redirect URIs for local development
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

        self.client_id = os.getenv('client_id')
        self.client_secret = os.getenv('client_secret')
        self.redirect_uri = os.getenv('redirect_uri')
        self.authorization_base_url = 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize'
        self.token_url = 'https://login.microsoftonline.com/common/oauth2/v2.0/token'
        self.scope = [
            'https://graph.microsoft.com/Chat.Read',
            'https://graph.microsoft.com/Chat.ReadWrite',
            'https://graph.microsoft.com/User.Read',
            'https://graph.microsoft.com/User.ReadWrite',
            'https://graph.microsoft.com/Chat.Read',
            'openid',
            'profile',
            'email'
        ]
        self.token = {}

    def load_token(self):
        if os.path.exists(self.token_file):
            with open(self.token_file, 'r') as file:
                self.token = json.load(file)
        else:
            print('Token not found, starting new authentication flow')
            azure = OAuth2Session(self.client_id, redirect_uri=self.redirect_uri, scope=self.scope)
            authorization_url, state = azure.authorization_url(self.authorization_base_url)
            print(f'Please go here and authorize: {authorization_url}')
            redirect_response = input('Paste the full redirect URL here:')
            self.token = azure.fetch_token(self.token_url, client_secret=self.client_secret,
                                           authorization_response=redirect_response)
            self.save_token()

    def save_token(self):
        with open(self.token_file, 'w') as file:
            json.dump(self.token, file)

    def authenticate(self):
        self.load_token()

        extra = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
        }

        azure = OAuth2Session(self.client_id, token=self.token, auto_refresh_kwargs=extra,
                              auto_refresh_url=self.token_url, token_updater=self.save_token)

        return azure
