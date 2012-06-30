
from fabric.api import run, local, cd, sudo
from fabric.state import env


if not env.hosts:
    env.hosts.append('athensdocket.org')
    env.user = 'docket'
env.use_ssh_config = True  # look at ~/.ssh/config


def update():
    "Update the git repo on the remote system and reload apache"
    with cd('/home/docket/apache2'):
        run('git fetch && git pull')
    with cd('/home/docket/athensdocket'):
        run('git fetch && git pull')
    sudo('/etc/init.d/apache2 restart', shell=False)
