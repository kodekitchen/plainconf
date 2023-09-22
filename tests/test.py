import os
from unittest import mock

import pytest

from ..plainconf import Plainconf, encrypt_toml


@pytest.fixture
def conf():
    os.environ['PLAINCONF_VAULT_URL'] = 'http://test.url'
    os.environ['PLAINCONF_VAULT_TOKE'] = 'supersecrettoken'
    with mock.patch('hvac.Client'):
        yield Plainconf(secrets_file='tests/.test-secrets.toml', settings_file='tests/test-settings.toml')


def test_conf(conf):
    assert isinstance(conf, Plainconf)


def test_vault_token_not_shown(conf):
    assert not hasattr(conf, 'vault_token')
    

def test_environment(conf):
    assert conf.environment == 'default'


def test_not_shown(conf):
    assert not hasattr(conf, 'vault_url')


@mock.patch('hvac.Client')
def test_kwargs_environment(mock):
    conf = Plainconf(environment='testing', settings_file='tests/test-settings.toml')
    assert conf.environment == 'testing'


@mock.patch('hvac.Client')
def test_get_vault_client(mock):
    Plainconf(vault_url='https://test.url', vault_token='lala', settings_file='tests/test-settings.toml')
    assert mock.called


@mock.patch('hvac.Client')
def test_settings_file(mock):
    conf = Plainconf(environment='testing', settings_file='tests/test-settings.toml')
    assert conf.foo == 'testing test'


@mock.patch('hvac.Client')
def test_secrets_file(mock):
    conf = Plainconf(environment='testing', settings_file='tests/test-settings.toml', secrets_file='tests/.test-secrets.toml')
    assert conf.password == 'secret'


@mock.patch('hvac.Client')
def test_secrets_file_2(mock):
    conf = Plainconf(settings_file='tests/test-settings.toml', secrets_file='tests/.test-secrets.toml')
    assert conf.password == 'secret2'


def test_encrypt_toml():
    encrypt_toml(b"Z4wPOsb3icNOXeVQ6d74RK_MmB2wdWGEu6vCtK6iKIE=", 'tests/.test-secrets.toml')
    assert os.path.exists('tests/.test-secrets_enc.toml')
    os.remove('tests/.test-secrets_enc.toml')
