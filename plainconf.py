import os

from cryptography.fernet import Fernet

from dotenv import load_dotenv

import hvac

import tomli_w

import tomllib


def _traverse_dict(d, fernet):
    for k, v in d.items():
        if isinstance(v, dict):
            _traverse_dict(v, fernet)
        else:
            d[k] = fernet.encrypt(v.encode()).decode()
    return d


def encrypt_toml(key, file):
    fernet = Fernet(key)
    with open(f'{os.getcwd()}/{file}', "rb") as f:
        secrets = tomllib.load(f)
    enc = _traverse_dict(secrets, fernet)
    with open(f'{os.getcwd()}/{file}', "w") as f:
        f.write(tomli_w.dumps(enc))


def _get_vault_client(vault_url: str, vault_token: str) -> hvac.Client:
    return hvac.Client(url=vault_url, token=vault_token)


def _get_vault_client_userpass(vault_url: str, vault_user: str, vault_pass: str) -> str:
    vault_client = hvac.Client(url=vault_url)
    token_request = vault_client.auth.userpass.login(
        username=vault_user, password=vault_pass
    )
    return token_request.get("auth").get("client_token")


def _load_file(file: str) -> dict | None:
    try:
        with open(f'{os.getcwd()}/{file}', mode="rb") as f:
            toml = tomllib.load(f)
            return toml
    except FileNotFoundError:
        print(f'{file} could not be found.')


def _get_vault_secrets(vault_client: hvac.Client, vault_mount_point: str, vault_path: str) -> dict:
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


def _find_env(elements, d):
    for i in elements:
        d = d.get(i)
        elements.pop(0)
        if elements:
            return _find_env(elements, d)
        else:
            return d
       

class Plainconf:
    
    def __init__(self, *args, **kwargs):

        # load dotenv file

        load_dotenv(f'{os.getcwd()}/.env')

        # environment can be an attribute as it might be handy

        self.environment: str = (
            kwargs.get("environment") 
            or os.getenv("PLAINCONF_ENVIRONMENT") 
            or "default"
        )

        # settings and secrets files

        settings_file: str = (
            kwargs.get("settings_file")
            or os.getenv("PLAINCONF_SETTINGS_FILE")
            or "plainconf_settings.toml"
        )
        secrets_file: str = (
            kwargs.get("secrets_file")
            or os.getenv("PLAINCONF_SECRETS_FILE")
            or '.plainconf_secrets.toml'
        )

        # vault options

        vault_url: str = (
            kwargs.get("vault_url") 
            or os.getenv("PLAINCONF_VAULT_URL")
        )
        vault_token: str = (
            kwargs.get("vault_token") 
            or os.getenv("PLAINCONF_VAULT_TOKEN")
        )
        vault_user: str = (
            kwargs.get("vault_user") 
            or os.getenv("PLAINCONF_VAULT_USER") 
            or None
        )
        vault_pass: str = (
            kwargs.get("vault_pass") 
            or os.getenv("PLAINCONF_VAULT_PASS") 
            or None
        )
        vault_mount_point: str = (
            kwargs.get("vault_mount_point") 
            or os.getenv("PLAINCONF_VAULT_MOUNT_POINT")
        )
        vault_path: str = (
            kwargs.get("vault_path")
            or os.getenv("PLAINCONF_VAULT_PATH")
            or self.environment
        )

        # fernet key

        fernet_key: str = (
            kwargs.get('fernet_key')
            or os.getenv('PLAINCONF_FERNET_KEY')
        )
        if fernet_key:
            fernet = Fernet(bytes(fernet_key, 'utf-8'))

        # handling vault

        if vault_url:
            
            if vault_user and vault_pass:
                vault_token = _get_vault_client_userpass(
                    vault_url, 
                    vault_user, 
                    vault_pass
                )
            
            vault_client = _get_vault_client(
                vault_url, 
                vault_token
            )
        
            if vault_client:
                vault_secrets = _get_vault_secrets(
                    vault_client,
                    vault_mount_point,
                    vault_path,
                )

            if vault_secrets:
                for k, v in vault_secrets.items():
                    setattr(self, k, v)

        # overwrite or append secrets with local file 

        if secrets_file:
            secrets_f = _load_file(secrets_file)
            secrets = _find_env(self.environment.split('.'), secrets_f)
            if secrets:
                for k, v in secrets.items():
                    if fernet:
                        setattr(self, k, fernet.decrypt(v).decode())
                    else:
                        setattr(self, k, v)

        # get settings

        settings_f = _load_file(settings_file)
        settings = _find_env(self.environment.split('.'), settings_f)
        if settings:
            for k, v in settings.items():
                setattr(self, k, v)
