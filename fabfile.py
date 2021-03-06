import csv
import os
import tempfile

from asbool import asbool
from dotenvy import parse_string
from fabric import *
from fabric.api import cd, get, prefix, run, shell_env, task
from fabric.contrib.files import *
from six import StringIO

template_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'templates')

DEPLOY = {
    'master': [
        'auth',
    ],
}

repo = 'https://github.com/datashaman/wifidog-auth-flask.git'

def load_local_env(*path):
    full_path = os.path.join(template_dir, 'env', *path) + '.env'
    if os.path.exists(full_path):
        with open(full_path) as env_file:
            env.environment.update(read(env_file))

def load_env(*path):
    full_path = os.path.join('/etc', 'wifidog-auth-flask', 'env.d', *path) + '.env'
    if exists(full_path):
        env_file = StringIO()
        get(remote_path=full_path, local_path=env_file)
        env_string = env_file.getvalue()
        env_file.close()
        env.environment.update(parse_string(env_string))

def prepare(instance, commit, base_dir='/var/www', frontend=False, services=False, users_csv=None, testing=False):
    env.instance = instance
    env.environment = {}

    load_env(env.host)
    load_env(env.host, instance)

    venv = '/home/ubuntu/.virtualenvs/auth-%s' % instance

    with cd(base_dir):
        if not exists(instance):
            run('git clone -q %s %s' % (repo, instance))

        with cd(instance):
            run('git remote update -p')
            run('git fetch -q origin %s' % commit)
            run('git checkout -q FETCH_HEAD')
            run('git describe > app/static/version.txt')

            use_local = False

            if 'SQLALCHEMY_DATABASE_URI' not in env.environment:
                use_local = True
                env.environment['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///%s/%s/data/local.db' % (base_dir, instance)

            if not exists('.env'):
                upload_template('template.env', '.env', template_dir=template_dir, backup=False, context=env, use_jinja=True)

            if not exists(venv):
                run('virtualenv -p /usr/bin/python3 %s' % venv)

            with prefix('source %s/bin/activate' % venv):
                run('pip install -I -r requirements.txt')

                if use_local and not testing and not exists('data/local.db'):
                    run('python manage.py db_create_all')
                    run('python manage.py create_roles')
                    if users_csv:
                        with open(users_csv) as f:
                            for user in csv.reader(f):
                                run('python manage.py create_user %s %s %s' % user)
                    run('python manage.py create_country ZA "South Africa"')
                    run('python manage.py create_currency -p R ZA ZAR "South African Rand"')

            if frontend:
                run('yarn')
                run('gulp')

    if services:
        supervisor_conf = '/etc/supervisor/conf.d/%s.conf' % instance
        upload_template('supervisor.conf', supervisor_conf, template_dir=template_dir, context=env, use_jinja=True)

        run('supervisorctl reread')
        run('supervisorctl update')
        run('supervisorctl restart %s' % instance)

        nginx_conf = '/etc/nginx/sites-available/%s' % instance
        upload_template('nginx.conf', nginx_conf, template_dir=template_dir, context=env, use_jinja=True)

        nginx_link = '/etc/nginx/sites-enabled/%s' % instance
        if not exists(nginx_link):
            run('ln -s %s %s' % (nginx_conf, nginx_link))

        sudo('nginx -s reload')

    return venv, '%s/%s' % (base_dir, instance)

@task
def test(commit='develop'):
    run('rm -rf /tmp/test')
    venv, instance_dir = prepare('test', commit, '/tmp', testing=True)
    with shell_env(TESTING='true'), prefix('source %s/bin/activate' % venv), cd(instance_dir):
        run('python -m unittest discover -s tests')

@task
def deploy(commit='develop', users_csv=None):
    instances = DEPLOY.get(commit, [])
    for instance in instances:
        prepare(instance, commit, '/var/www', frontend=True, services=True, users_csv=users_csv)

@task
def downstream_db(source, destination, anonymise='true'):
    if asbool(anonymise):
        fd, filename = tempfile.mkstemp()
        os.close(fd)
        run('cp /var/www/%s/data/local.db %s' % (source, filename))
        put('anonymise.sql', '/tmp')
        run('sqlite3 %s < /tmp/anonymise.sql' % filename)
        run('mv %s /var/www/%s/data/local.db' % (filename, destination))
    else:
        run('cp /var/www/%s/data/local.db /var/www/%s/data/local.db' % (source, destination))

@task
def migrate(instance='auth'):
    pass

    # run('sqlite3 /var/www/%s/data/local.db "alter table users add column confirmed_at datetime"' % instance)
    # run('sqlite3 /var/www/%s/data/local.db "update users set confirmed_at = datetime(\'now\')"' % instance)
    # run('sqlite3 /var/www/%s/data/local.db "alter table gateways add column default_minutes integer"' % instance)
    # run('sqlite3 /var/www/%s/data/local.db "alter table gateways add column default_megabytes bigint"' % instance)
