from fabric.api import env, run
from fabric.context_managers import cd, prefix
from fabric.operations import require, sudo
from fabric.state import output

output.everything = True
env.user = "ubuntu"
env.key_filename = "/Users/guillaume/Projects/VPN/amazon-key.pem"
env.hosts = ['moonstrap.com']
www_dir = "/var/www/"
project_name = "backtoshops"
venv_name = "backtoshops-env"
venv_path = www_dir + project_name + "/" + venv_name
env.path = www_dir + project_name
src_dir = env.path + "/" + project_name
git_rep = "/home/git/repositories/backtoshops.git"
requirement_file = "requirements/apps.txt"
www_user = "www-data"

apache_config = """
<VirtualHost *:80>
    ServerName bts.moonstrap.com
    WSGIScriptReloading On
    WSGIDaemonProcess bts-prod
    WSGIProcessGroup bts-prod
    WSGIApplicationGroup bts-prod
    WSGIPassAuthorization On

    WSGIScriptAlias / /var/www/backtoshops/backtoshops/apache/production.wsgi/

    <Location "/">
        Order Allow,Deny
        Allow from all
    </Location>

    <Location "/media">
        SetHandler None
    </Location>

    Alias /static /var/www/backtoshops/backtoshops/static
    Alias /site-media /var/www/backtoshops/backtoshops/media

    <Location "/admin-media">
        SetHandler None
    </Location>

    Alias /media /var/www/backtoshops/backtoshops/media/admin

    ErrorLog /var/www/backtoshops/backtoshops/log/error.log
    LogLevel info
    CustomLog /var/www/backtoshops/backtoshops.log/access.log combined
</VirtualHost>
"""


def activate_venv():
    sudo("python "+venv_path+"/bin/activate_this.py")

def reload_apache():
    sudo ("/etc/init.d/apache2 reload")

def prepare_server():
    with cd(www_dir):
        sudo("aptitude install python-dev libjpeg8 libjpeg8-dev libpq-dev libapache2-mod-wsgi")
        sudo("easy_install pip")
        sudo("pip install virtualenv")
        sudo("git clone "+git_rep, user=www_user)
        with cd(env.path):
            sudo("virtualenv --no-site-packages "+venv_name, user=www_user)
            activate_venv()
            sudo("pip -E "+venv_name+" install -r "+requirement_file, user=www_user)
    sudo("echo '"+apache_config+"' > /etc/init.d/apache2/sites-available/bts")
    sudo("a2ensite bts")
    reload_apache()
    

def activate_site():
    sudo("echo '"+apache_config+"' > /etc/init.d/apache2/sites-available/bts")
    sudo("a2ensite bts")
    reload_apache()

def deploy():
#    activate_venv()
    with cd(env.path):
        sudo("git pull", user=www_user)
        with prefix("source "+venv_path+"/bin/activate"):
            with cd(src_dir):
                sudo("./manage.py syncdb")
                sudo("./manage.py migrate")
    reload_apache()
        
