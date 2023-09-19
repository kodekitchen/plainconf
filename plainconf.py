import os

from dotenv import load_dotenv

import hvac

import tomllib


def _get_vault_client(vault_url, vault_token):
    return hvac.Client(url=vault_url, token=vault_token)


def _get_vault_client_userpass(vault_url, vault_user, vault_pass):
    vault_client = hvac.Client(url=vault_url)
    token_request = vault_client.auth.userpass.login(
        username=vault_user, password=vault_pass
    )
    return token_request.get("auth").get("client_token")


def _load_file(file, env):
    try:
        with open(file, mode="rb") as f:
            toml = tomllib.load(f)
            if toml.get(env):
                return toml.get(env)
    except FileNotFoundError:
        print(f'{file} could not be found.')


def _get_vault_secrets(vault_client, vault_mount_point, vault_path):
    try:
        _secrets = vault_client.secrets.kv.v2.read_secret_version(
            mount_point=vault_mount_point, path=vault_path
        )
        return _secrets.get("data").get("data")
    except hvac.exceptions.InvalidPath:
        _secrets = vault_client.secrets.kv.v1.read_secret(
            mount_point=vault_mount_point, 
            path=vault_path
        )
        return _secrets.get("data")


class Plainconf:
    
    def __init__(self, *args, **kwargs):

        # load dotenv file

        load_dotenv()

        self.settings_file = (
            kwargs.get("settings_file")
            or os.getenv("PLAINCONF_SETTINGS_FILE")
            or "plainconf_settings.toml"
        )
        self.secrets_file = (
            kwargs.get("secrets_file")
            or os.getenv("PLAINCONF_SECRETS_FILE")
            or '.plainconf_secrets.toml'
        )
        self.environment = (
            kwargs.get("environment") 
            or os.getenv("PLAINCONF_ENVIRONMENT") 
            or "default"
        )

        # vault options

        self.vault_url = (
            kwargs.get("vault_url") 
            or os.getenv("PLAINCONF_VAULT_URL")
        )
        vault_token = (
            kwargs.get("vault_token") 
            or os.getenv("PLAINCONF_VAULT_TOKEN")
        )
        vault_user = (
            kwargs.get("vault_user") 
            or os.getenv("PLAINCONF_VAULT_USER") 
            or None
        )
        vault_pass = (
            kwargs.get("vault_pass") 
            or os.getenv("PLAINCONF_VAULT_PASS") 
            or None
        )
        self.vault_mount_point = (
            kwargs.get("vault_mount_point") 
            or os.getenv("PLAINCONF_VAULT_MOUNT_POINT")
        )
        self.vault_path = (
            kwargs.get("vault_path")
            or os.getenv("PLAINCONF_VAULT_PATH")
            or self.environment
        )

        # get settings

        settings = _load_file(self.settings_file, self.environment)
        if settings:
            for k, v in settings.items():
                setattr(self, k, v)

        # handling vault

        if self.vault_url:
            if vault_user and vault_pass:
                
                self.vault_token = _get_vault_client_userpass(
                    self.vault_url, 
                    vault_user, 
                    vault_pass
                )
            
            vault_client = _get_vault_client(
                self.vault_url, 
                vault_token
            )
        
            if vault_client:
                vault_secrets = _get_vault_secrets(
                    vault_client,
                    self.vault_mount_point,
                    self.vault_path,
                )
            if vault_secrets:
                for k, v in vault_secrets.items():
                    setattr(self, k, v)

        # overwrite or append secrets with local file 

        if self.secrets_file:
            secrets = _load_file(self.secrets_file, self.environment)
            if secrets:
                for k, v in secrets.items():
                    setattr(self, k, v)
