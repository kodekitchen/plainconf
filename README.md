# Plainconf

Attempts to help build sensible configuration for python projects.

## DISCLAIMER

Unless you need some specific functionality in here, 
I recommend using [Dynaconf](https://www.dynaconf.com/) as it is more mature.


## Install 

```shell
pip install plainconf
```


## What does this do?

It will create a flat conf (no nesting or anything, just one level) 
taking entries from the same environment from
a settings file and either

 * a secrets file

 * hashicorp vault if vault_url, a mount_point and either token, 
   userpass or approle credentials are provided (optionally vault_path)
 
 * a secrets file with fernet encrypted values if the key is provided 
   (s. [encrypting toml file with fernet](#markdown-header-encrypting-toml-file-with-fernet)


settings.toml
``` toml
[development]
db_url = "localhost:4321"
```


.secrets.toml
``` toml
[development]
password = "secret"
``` 


``` python
    conf = Plainconf(
        environment="development",
        settings_file="settings.toml",
        secrets_file=".secrets.toml",
    )

    assert conf.db_url == "localhost:4321"
    assert conf.password == "secret"

``` 

## Assumptions

Plainconf assumes, that the setings and secrets are organised in envrironments.
Further it assumes, that the relevant configuration is the most specific one and
all levels above hold common information for the levels below.

``` toml
[development]
...                   <- this information is relevant to development.local

[development.local]   <- this is the environment you want to work with (including everything from development)
...


[development.staging]
...
``` 

## Encrypting toml file with fernet

In order to encrypt the values in the toml file you will need a fernet key

``` python
    from cyptography.fernet import Fernet

    key = Fernet.generate_key()
```

encrypt_toml(key: bytes, file: str) expects the key as bytes and the path to the secrets file to
be encrypted:

``` python
    from plainconf import encrypt_toml

    encrypt_toml(b'key', '.secrets.toml')
```
Which will output a file ending on \_enc.toml with the values encrypted

``` toml
[development]
password = "gAAAAABlDfsMIkZzIqKFQW8NBHVIqITKLCgQkzr6VKOYglHroZ--jFtkEsFr3feqSL1WCWy7gdlhvjHkBmx_JjQxKYKiqNge0A=="
```

In order to read the encrypted secrets, the key has to be given as 
keyword argument or environment variable (without the b at the beginning)

## Nested environments

Plainconf will read the environment given in the variable and the entries
above and flatten everything, as that is the use case I have.

``` toml
[development]
db_url = "localhost:4321"

[development.local]
db_username = "local"
```

``` python
conf = Plainconf(
    environment="development.local",
    settings_file="settings.toml",
)

assert conf.db_url == "localhost:4321"
assert conf.db_username == "local"
```


## Limitations

* Only supports userpass, approle and token authentication on Hashicorp Vault

* Only works with kv secret engine

* Only supports toml

(for now)


## Examples

With files

``` toml
    .mysecrets.toml:

    [development]
    password = 'secret'
```

``` python
    conf = Plainconf(
        secrets_file='.mysecrets.toml', 
        settings_file='mysettings.toml',
        environment='development'
    )
    
    ...

    conf.password ("secret")
```
 

With vault

    on the vault:
    
    somewhere/development:
    password = 'supersecret'


``` python
    conf = Plainconf(
        vault_url="http://localhost:8200",
        vault_token="hvs.abc123def456",
        vault_mount_point="somewhere",
        environment="development"
    )

    conf.password ("supersecret")
```


Enviroment from env

    .env file:

    PLAINCONF_ENVIRONMENT="development"
    PLAINCONF_VAULT_TOKEN="hvs.something123"
    PLAINCONF_VAULT_URL="http://development.vault:8200"

``` python
    conf = Plainconf()
    conf.password ("supersecret")
```
 
### Settings REQUIRED!

    Plainconf(settings_file='path_to_file')
    or environment variable PLAINCONF_SETTINGS_FILE="...""

Settings are read from the respective environment (default: default)

### Secrets 

    Plainconf(secrets_file='path_to_file')
    or environment variable PLAINCONF_SECRETS_FILE="...""

Secrets are read from the environment (default: default)

### Environments

    Plainconf(environment='name')
    or environment variable PLAINCONF_ENVIRONMENT="...""
    or default: default

### Vault

Hashicorp Vault can be accessed via token, approle or userpass.

Required configuration:

* Plainconf(vault_url='http...') 
  or environment variable PLAINCONF_VAULT_URL

* Plainconf(vault_mount_point='name')
  or environment variable PLAINCONF_VAULT_MOUNT_POINT

and either a token 

* Plainconf(vault_token="hvs...") 
  or PLAINCONF_VAULT_TOKEN

or user and pass

* Plainconf(vault_user='user', vault_pass='password') 
  or PLAINCONF_VAULT_USER and PLAINCONF_VAULT_PASS

or approle id and secret

* Plainconf(vault_approle_id='role_id', vault_approle_secret_id='secret_id')
  or PLAINCONF_APPROLE_ID and PLAINCONF_APPROLE_SECRET_ID

Optional:

* Plainconf(vault_path='secret/special...')
  or PLAINCONF_VAULT_PATH
  or default: environment (see above)

Plainconf tries to connect to the vault kv secrets engine v2 by default 
and v1 thereafter.


## Fernet Key

* Plainconf(fernet_key='key')
  or PLAINCONF_FERNET_KEY'