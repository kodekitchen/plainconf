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
    *left, right = file.rsplit('.')
    middle = left.pop(-1) + '_enc'
    outfile = '.'.join(left + [middle] + [right])
    with open(f'{os.getcwd()}/{outfile}', "w") as f:
        f.write(tomli_w.dumps(enc))


def _get_vault_client(vault_url: str, vault_token: str) -> hvac.Client:
    return hvac.Client(url=vault_url, token=vault_token)


def _get_vault_token_userpass(vault_url: str, vault_user: str, vault_pass: str) -> str:
    vault_client = hvac.Client(url=vault_url)
    token_request = vault_client.auth.userpass.login(
        username=vault_user, password=vault_pass
    )
    return token_request.get("auth").get("client_token")


def _get_vault_token_approle(vault_url: str, vault_approle_id: str, vault_approle_secret_id: str):
    client = hvac.Client("http://localhost:8200")
    token_request = client.auth.approle.login(
        role_id=vault_approle_id,
        secret_id=vault_approle_secret_id
    )
    return token_request.get("auth").get("client_token")


def _load_file(file_path: str) -> dict | None:
    with open(f'{os.getcwd()}/{file_path}', mode="rb") as f:
        toml = tomllib.load(f)
        return toml

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


def _find_leaves(d, leaves=[]):
    assert d, 'Environment not configured.'
    for k, v in d.items():
        if isinstance(v, dict):
            _find_leaves(v, leaves)
        else:
            leaves.append((k, v))
    return leaves


def _find_env(elements, d, leaves=[]):
    for i in elements:
        d = d.get(i)
        elements.pop(0)
        if elements:
            for k, v in d.items():
                if not isinstance(v, dict):
                    leaves.append((k, v))
            return _find_env(elements, d, leaves)
        else:
            leaves = _find_leaves(d, leaves)
            return leaves
       

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
        )
        secrets_file: str = (
            kwargs.get("secrets_file")
            or os.getenv("PLAINCONF_SECRETS_FILE")
        )

        # vault configuration for hvac

        vault_url: str = (
            kwargs.get("vault_url") 
            or os.getenv("PLAINCONF_VAULT_URL")
        )
        vault_mount_point: str = (
            kwargs.get("vault_mount_point") 
            or os.getenv("PLAINCONF_VAULT_MOUNT_POINT")
            or '/kv'
        )
        vault_path: str = (
            kwargs.get("vault_path")
            or os.getenv("PLAINCONF_VAULT_PATH")
            or self.environment
        )

        # vault authentication

        vault_token: str = (
            kwargs.get("vault_token") 
            or os.getenv("PLAINCONF_VAULT_TOKEN")
        )
        vault_user: str = (
            kwargs.get("vault_user") 
            or os.getenv("PLAINCONF_VAULT_USER") 
        )
        vault_pass: str = (
            kwargs.get("vault_pass") 
            or os.getenv("PLAINCONF_VAULT_PASS") 
        )
        vault_approle_id: str = (
            kwargs.get('vault_approle_id')
            or os.getenv('PLAINCONF_APPROLE_ID')
        )
        vault_approle_secret_id: str = (
            kwargs.get('vault_approle_secret_id')
            or os.getenv('PLAINCONF_APPROLE_SECRET_ID')
        )

        # fernet key

        fernet_key: str = (
            kwargs.get('fernet_key')
            or os.getenv('PLAINCONF_FERNET_KEY')
        )
        if fernet_key:
            fernet = Fernet(bytes(fernet_key, 'utf-8'))
        else:
            fernet = None

        # handling vault

        if vault_url:
            
            if vault_user and vault_pass:
                vault_token = _get_vault_token_userpass(
                    vault_url, 
                    vault_user, 
                    vault_pass
                )

            if vault_approle_id and vault_approle_secret_id:
                vault_token = _get_vault_token_approle(
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
                for k, v in secrets:
                    if fernet:
                        setattr(self, k, fernet.decrypt(v).decode())
                    else:
                        setattr(self, k, v)

        # get settings

        settings_f = _load_file(settings_file)
        settings = _find_env(self.environment.split('.'), settings_f)
        if settings:
            for k, v in settings:
                setattr(self, k, v)
