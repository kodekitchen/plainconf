import os
from unittest import mock

import pytest

from ..plainconf import Plainconf


@pytest.fixture
def conf():
    os.environ['PLAINCONF_VAULT_URL'] = 'http://test.url'
    with mock.patch('hvac.Client'):
        yield Plainconf()


def test_conf(conf):
    assert isinstance(conf, Plainconf)


def test_vault_token_not_shown(conf):
    assert not hasattr(conf, 'vault_token')
    

def test_environment(conf):
    assert conf.environment == 'default'


def test_vault_url(conf):
    assert conf.vault_url == 'http://test.url'


@mock.patch('hvac.Client')
def test_kwargs_environment(mock):
    conf = Plainconf(environment='testing')
    assert conf.environment == 'testing'


@mock.patch('hvac.Client')
def test_kwargs_vault_url(mock):
    conf = Plainconf(vault_url='https://test.url')
    assert conf.vault_url == 'https://test.url'


@mock.patch('hvac.Client')
def test_kwargs_vault_userpass_not_showing(mock):
    conf = Plainconf(vault_user='test', vault_pass='test')
    assert not hasattr(conf, 'vault_user')
    assert not hasattr(conf, 'vault_pass')


@mock.patch('hvac.Client')
def test_get_vault_client(mock):
    Plainconf(vault_url='https://test.url', vault_token='lala')
    assert mock.called


@mock.patch('hvac.Client')
def test_settings_file(mock):
    conf = Plainconf(environment='testing', settings_file='tests/test-settings.toml')
    assert conf.foo == 'testing test'


@mock.patch('hvac.Client')
def test_secrets_file(mock):
    conf = Plainconf(environment='testing', secrets_file='tests/.test-secrets.toml')
    assert conf.password == 'secret'
