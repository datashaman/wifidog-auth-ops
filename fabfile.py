import csv
import os
import tempfile

from dotenvy import read
from fabric import *
from fabric.api import cd, prefix, run, shell_env, task
from fabric.contrib.files import *

template_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'templates')

repo = 'https://github.com/datashaman/wifidog-auth-flask.git'

def load_env(*path):
    full_path = os.path.join(template_dir, 'env', *path) + '.env'
    if os.path.exists(full_path):
        with open(full_path) as env_file:
            env.environment.update(read(env_file))

def prepare(instance, commit, base_dir='/var/www', frontend=False, services=False, users_csv=None, testing=False):
    env.instance = instance
    env.environment = {}

    venv = '/home/ubuntu/.virtualenvs/auth-%s' % instance

    load_env(env.host)
    load_env(env.host, instance)

    with cd(base_dir):
        if not exists(instance):
            run('git clone %s %s' % (repo, instance))

        with cd(instance):
            run('git remote update -p')
            run('git checkout %s' % commit)
            run('git pull --ff-only')

            use_local = False

            if 'SQLALCHEMY_DATABASE_URI' not in env.environment:
                use_local = True
                env.environment['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///%s/%s/data/local.db' % (base_dir, instance)

            if not exists('.env'):
                upload_template('template.env', '.env', template_dir=template_dir, backup=False, context=env, use_jinja=True)

            if not exists(venv):
                run('virtualenv -p /usr/bin/python3 %s' % venv)

            with prefix('source %s/bin/activate' % venv):
                run('pip install -q -r requirements.txt')

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
def deploy(instance='auth', commit='develop', users_csv=None, test=True):
    if test:
        test(commit)
    prepare(instance, commit, '/var/www', frontend=True, services=True, users_csv=users_csv)

@task
def downstream_db(source, destination):
    fd, filename = tempfile.mkstemp()
    os.close(fd)
    run('cp /var/www/%s/data/local.db %s' % (source, filename))
    put('anonymise.sql', '/tmp')
    run('sqlite3 %s < /tmp/anonymise.sql' % filename)
    run('mv %s /var/www/%s/data/local.db' % (filename, destination))
