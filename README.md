# plainconf

Attempts to help build sensible configuration for python projects.

* provide settings via toml file, keyword arguments or environment variables

* read secrets from toml file or vault or both

* can load environment variables from .env file

* supports environments

* allows to set path and mount point in vault 


Uses hvac and python-dotenv


## Limitations

* Only supports userpass and token authentication on Hashicorp Vault

* Only works with kv secret engine

* Only supports toml

(for now)


## Examples

With files

    .mysecrets.toml:

    [development]
    password = 'secret'


    conf = Plainconf(
        secrets_file='.mysecrets.toml', 
        settings_file='mysettings.toml',
        environment='development'
    )
    
    ...

    conf.password ("secret")
 

With vault

    on the vault:
    
    somewhere/development:
    password = 'supersecret'


    conf = Plainconf(
        vault_url="http://localhost:8200",
        vault_token="hvs.abc123def456",
        vault_mount_point="somewhere",
        environment="development"
    )

    conf.password ("supersecret")


Enviroment from env

    .env file:

    PLAINCONF_ENVIRONMENT="development"
    PLAINCONF_VAULT_TOKEN="hvs.something123"
    PLAINCONF_VAULT_URL="http://development.vault:8200"

    conf = Plainconf()
    conf.password ("supersecret")

 
### Settings

Plainconf(settings_file='path_to_file')
or environment variable SOBERCONF_SETTINGS_FILE="...""
or default: plainconf_settings.toml

Settings are read from the respective environment (default: default)

### Secrets 

Plainconf(secrets_file='path_to_file')
or environment variable SOBERCONF_SECRETS_FILE="...""
or default: .plainconf_secrets.toml

Secrets are read from the environment (default: default)

### Environments

Plainconf(environment='name')
or environment variable SOBERCONF_ENVIRONMENT="...""
or default: default

### Vault

Hashicorp Vault can be accessed via token or userpass.

Required configuration:

* Plainconf(vault_url='http...') 
  or environment variable SOBERCONF_VAULT_URL

* Plainconf(vault_mount_point='name')
  or environment variable SOBERCONF_VAULT_MOUNT_POINT

and either a token 

* Plainconf(vault_token="hvs...") 
  or SOBERCONF_VAULT_TOKEN

or user and pass

* Plainconf(vault_user='user', vault_pass='password') 
  or SOBERCONF_VAULT_USER and SOBERCONF_VAULT_PASS

Optional:

* Plainconf(vault_path='secret/special...')
  or SOBERCONF_VAULT_PATH
  or default: environment (see above)

Plainconf tries to connect to the vault kv secrets engine v2 by default 
and v1 thereafter.