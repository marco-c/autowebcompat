import configparser
import logging
import os
import pathlib
import random
import string
import time

import hvac
import jinja2
import nomad
from nomad.api.exceptions import BadRequestNomadException

log = logging.getLogger(__name__)
root = pathlib.Path(__file__).parent.parent.resolve()

CONFIG_INI = os.getenv('CONFIG_INI', str(root / 'config.ini'))
SERVICE_JOBS = [
    'services.nomad',
    'browsers.nomad',
]
VAULT_MOUNT = 'autowebcompat'
GENERATED_VAULT_SECRETS = ['web/django_secret_key', 'web/postgres_password']
IMPORTED_VAULT_SECRETS = ['auth_gh_key', 'auth_gh_secret']

jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(str(root / 'jobs')),
    variable_start_string="%{",
    variable_end_string="}",
)


def load_config():
    assert os.path.isfile(CONFIG_INI)
    with open(CONFIG_INI) as f:
        config_content = f.read()

    config_file = configparser.ConfigParser()
    config_file.read(CONFIG_INI)

    return {
        'nomad_url': config_file.get('urls', 'nomad'),
        'consul_url': config_file.get('urls', 'consul'),
        'vault_url': config_file.get('urls', 'vault'),

        'domain': config_file.get('web', 'domain'),
        'run_backend_locally': config_file.getboolean('web', 'run_backend_locally', fallback=False),
        'debug': config_file.getboolean('web', 'debug', fallback=False),

        'auth_gh_key': config_file.get('auth', 'gh_key'),
        'auth_gh_secret': config_file.get('auth', 'gh_secret'),
        'vault_token': config_file.get('auth', 'vault_token'),

        'https_enabled': 'https' in config_file,
        'acme_email': config_file.get('https', 'acme_email', fallback=None),
        'acme_caServer': config_file.get('https', 'acme_caServer', fallback=None),

        'timestamp': int(time.time()),
        "config_ini_content": config_content,
    }


def get_client(app, config):
    if app == 'nomad':
        client = nomad.Nomad(address=config['nomad_url'])
        assert client.agent.get_agent()['config']['Vault']['Enabled']
        return client
    elif app == 'vault':
        client = hvac.Client(url=config['vault_url'], token=config['vault_token'])
        client.secrets.kv.default_kv_version = 1
        assert client.is_authenticated()
        assert not client.sys.is_sealed()
        return client
    else:
        raise ValueError("unknown app: " + app)


def ensure_secrets(config):
    vault = get_client('vault', config)

    mounts = vault.sys.list_mounted_secrets_engines()['data']
    if VAULT_MOUNT + '/' not in mounts:
        log.info('Creating new Vault secrets engine...')
        vault.sys.enable_secrets_engine("kv", VAULT_MOUNT)

    def get(path):
        try:
            return vault.secrets.kv.read_secret(path=path, mount_point=VAULT_MOUNT)
        except hvac.exceptions.InvalidPath:
            pass

    def set_secret(path, val):
        secret = {'val': val}
        log.info("Setting secret %s", path)
        vault.secrets.kv.create_or_update_secret(
            path=path,
            secret=secret,
            mount_point=VAULT_MOUNT,
        )
        assert get(path)['data']['val'] == val

    def random_key(length=32):
        alphabet = string.ascii_uppercase + string.ascii_lowercase + string.digits
        return ''.join(random.choice(alphabet) for _ in range(length))

    for path in GENERATED_VAULT_SECRETS:
        if not get(path):
            log.info("Generating new secret for %s...", path)
            set_secret(path, random_key())
        else:
            log.info("Secret %s already set.", path)

    for key in IMPORTED_VAULT_SECRETS:
        set_secret('web/' + key, config[key])


def get_job(template, config):
    log.debug('Parsing "%s"', template)
    hcl = jinja_env.get_template(template).render(config)
    nomad = get_client('nomad', config)
    try:
        return nomad.jobs.parse(hcl)
    except BadRequestNomadException as err:
        log.error('Failed to parse %s!', template)
        log.error(err.nomad_resp.reason)
        log.error(err.nomad_resp.text)
        raise


def run_services():
    config = load_config()
    ensure_secrets(config)
    nomad = get_client('nomad', config)

    for template in SERVICE_JOBS:
        job = get_job(template, config)

        log.info("Registering job %s", job['Name'])
        nomad.job.register_job(job['Name'], {'Job': job})


def dispatch_job(template, meta):
    config = load_config()
    job = get_job(template, config)

    nomad = get_client('nomad', config)
    log.info("Registering job %s", job['Name'])
    nomad.job.register_job(job['Name'], {'Job': job})
    log.info("Dispatching job %s: %s", job['Name'], str(meta))
    return nomad.job.dispatch_job(job['Name'], meta=meta)


def run_scrape(path):
    return dispatch_job('import.nomad', {'dataset_path': path})


def run_import(path, slug):
    return dispatch_job('import.nomad', {'dataset_path': path, 'dataset_slug': slug})
