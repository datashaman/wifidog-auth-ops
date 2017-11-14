import csv
import os

from dotenvy import read_file
from fabric import *
from fabric.api import cd, prefix, run, task
from fabric.contrib.files import *

template_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'templates')

repo = 'https://github.com/datashaman/wifidog-auth-flask.git'

def load_env(*path):
    full_path = os.path.join(template_dir, 'env', *path) + '.env'
    if os.path.exists(full_path):
        env.environment.update(read_file(full_path))

@task
def test():
    run('ssh -T git@github.com')

@task
def deploy(instance='auth', commit='develop', users_csv=None):
    env.instance = instance
    env.environment = {}

    load_env(env.host)
    load_env(env.host, instance)

    with cd('/var/www'):
        if not exists(instance):
            run('git clone %s %s' % (repo, instance))

        with cd(instance):
            run('git remote update -p')
            run('git checkout %s' % commit)
            run('git pull --ff-only')

            use_local = False

            if 'SQLALCHEMY_DATABASE_URI' not in env.environment:
                use_local = True
                env.environment['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////var/www/%s/data/local.db' % instance

            upload_template('template.env', '.env', template_dir=template_dir, backup=False, context=env, use_jinja=True)

            venv = '/home/ubuntu/.virtualenvs/%s' % instance

            if not exists(venv):
                run('virtualenv -p /usr/bin/python3 %s' % venv)

            with prefix('source %s/bin/activate' % venv):
                run('pip install -q -r requirements.txt')

                if use_local and not exists('data/local.db'):
                    run('python manage.py db_create_all')
                    run('python manage.py create_roles')
                    if users_csv:
                        with open(users_csv) as f:
                            for user in csv.reader(f):
                                run('python manage.py create_user %s %s %s' % user)
                    run('python manage.py create_country ZA South Africa')
                    run('python manage.py create_currency ZA ZAR "South African" Rand R')

            run('yarn')
            run('gulp')

    supervisor_conf = '/etc/supervisor/conf.d/%s.conf' % instance
    upload_template('supervisor.conf', supervisor_conf, template_dir=template_dir, context=env, use_jinja=True)

    run('supervisorctl reread')
    run('supervisorctl update')

    nginx_conf = '/etc/nginx/sites-available/%s' % instance
    upload_template('nginx.conf', nginx_conf, template_dir=template_dir, context=env, use_jinja=True)

    nginx_link = '/etc/nginx/sites-enabled/%s' % instance
    if not exists(nginx_link):
        run('ln -s %s %s' % (nginx_conf, nginx_link))

    sudo('nginx -s reload')
