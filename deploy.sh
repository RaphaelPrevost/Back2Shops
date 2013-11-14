#! /bin/bash

# This script assumes the following commands have been executed:
# cd /home
# svn co http://trac.lbga.fr/svn/backtoshops/
# cd /home/backtoshops
#

set -ex

CWD=$(pwd)
DOMAIN=${DOMAIN:-sales.backtoshops.com}
INITDB=${INITDB:-""}
RESETDB=${RESETDB:-"$INITDB"}

DEPS=(libapache2-mod-wsgi python2.7-dev libpq-dev python-pip git \
      libtiff4-dev libjpeg8-dev zlib1g-dev libfreetype6-dev \
      liblcms1-dev libwebp-dev gettext libevent-dev swig python-lxml \
      libcairo2 libpango1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info \
      libxml2-dev libxslt1-dev)
DPKG=$(dpkg -l)
INST=""

# sanity checks
[ -r /etc/debian_version ] || echo "Warning: this script was made for Debian."
[ -r $CWD/requirements/apps.txt ] || echo "Warning: requirements not found."
grep -q 'UTF-8' /etc/postgresql/9.1/main/postgresql.conf || echo "Warning: postgresql needs to be configured in UTF-8"

for pkg in ${DEPS[*]}; do
    if echo $DPKG | grep -qw "ii $pkg"; then
        echo "(i) $pkg already installed."
    else
        INST="$INST $pkg"
    fi
done

if [ -n "$INST" ]; then
    echo "Warning: please install$INST"
    exit 1
fi

# assume availability of python2.7, python2.7-dev, libapache2-mod-wsgi,
# libpq-dev, python-pip, git but install virtualenv if it is not present
[ -z $(pip freeze 2> /dev/null | grep virtualenv) ] && \
pip install virtualenv

# add the backtoshops user if it does not already exists
[ -z $(grep backtoshops /etc/passwd) ] && \
useradd -d $CWD -g www-data -N -s /bin/false backtoshops

# make sure the user owns the folder
chown backtoshops.www-data .
chmod 750 .

# remove old sourcecode
[ -d $CWD/backtoshops -a -d $CWD/public_html ] && rm -rf $CWD/public_html

# remove unclean python environment
[ -d $CWD/env -a ! -r $CWD/env/.clean ] && rm -rf $CWD/env

# make the public_html directory
if [ -d $CWD/backtoshops -a ! -d $CWD/public_html ]; then
    mv $CWD/backtoshops $CWD/public_html
    chown -R backtoshops.www-data $CWD/public_html
    chmod -R 2750 $CWD/public_html
    # allow writing in the upload directories
    mkdir -p $CWD/public_html/media/cache
    mkdir -p $CWD/public_html/media/brand_logos
    mkdir -p $CWD/public_html/media/product_brands
    chmod -R 2770 $CWD/public_html/media/
fi

# make the logs directory
if [ ! -d $CWD/logs ]; then
    echo "(-) Setting up logs directory"
    mkdir $CWD/logs
    touch $CWD/logs/access.log
    touch $CWD/logs/error.log
    chown -R root.www-data $CWD/logs
    chmod -R 2770 $CWD/logs
    [ -d $CWD/public_html/logs ] && rm -rf $CWD/public_html/logs
else
    echo "(i) Logs directory OK"
fi

# create the python environment

if [ ! -d $CWD/env ]; then
    echo "(-) Creating Python environment..."
    usermod -s /bin/sh backtoshops
    PYENV="
    cd $CWD
    virtualenv --no-site-packages env
    python $CWD/env/bin/activate_this.py
    $CWD/env/bin/pip install -r $CWD/requirements/adm.backtoshops.com.requirements.txt -f $CWD/packages/dist/"
    ( su backtoshops -c "$PYENV" )
    # this user won't need shell anymore
    usermod -s /bin/false backtoshops
    touch $CWD/env/.clean
else
    source $CWD/env/bin/activate
    for i in $(cat $CWD/requirements/adm.backtoshops.com.requirements.txt); do
        lib_name=$i
        if [ ${i:0:4} = git+ ]; then
            lib_name=${i##*/}
            lib_name=$(echo $lib_name | cut -d '.' -f 1)
        fi
    
        if [ -z `pip freeze | grep $lib_name` ]; then
            echo "Missed python package ${lib_name}"
            usermod -s /bin/sh backtoshops
            PYENV="
            cd $CWD
            python $CWD/env/bin/activate_this.py
            $CWD/env/bin/pip install -r $CWD/requirements/adm.backtoshops.com.requirements.txt -f $CWD/packages/dist/"
            ( su backtoshops -c "$PYENV" )
            # this user won't need shell anymore
            usermod -s /bin/false backtoshops
            touch $CWD/env/.clean
        fi
    done
    deactivate
    echo "(i) Python environment OK"
fi

if [ ! -r /etc/apache2/sites-available/backtoshops ]; then
    echo "(-) Creating Apache VirtualHost..."
    cat > /etc/apache2/sites-available/backtoshops <<EOF
<VirtualHost *:80>
    ServerName $DOMAIN
    WSGIScriptReloading On
    WSGIDaemonProcess bts-prod
    WSGIProcessGroup bts-prod
    WSGIApplicationGroup bts-prod
    WSGIPassAuthorization On

    WSGIScriptAlias / $CWD/backtoshops.wsgi/

    <Location "/">
        Order Allow,Deny
        Allow from all
    </Location>

    <Location "/media">
        SetHandler None
    </Location>

    Alias /static $CWD/public_html/static
    Alias /site-media $CWD/public_html/media

    <Location "/admin-media">
        SetHandler None
    </Location>

    Alias /media $CWD/public_html/media/admin

    ErrorLog $CWD/logs/error.log
    LogLevel info
    CustomLog $CWD/logs/access.log combined
</VirtualHost>
EOF
    a2ensite backtoshops
else
    echo "(i) Apache VirtualHost OK"
fi

# setup the WSGI
if [ ! -r $CWD/backtoshops.wsgi ]; then
    echo "(-) Creating WSGI..."
    mv $CWD/production.wsgi $CWD/backtoshops.wsgi
    # edit the WSGI
    sed -i -e "s|backtoshops.settings|settings|g" $CWD/backtoshops.wsgi
    sed -i -e "s|backtoshops-env|env|g" $CWD/backtoshops.wsgi
    sed -i -e "s|'backtoshops'|'public_html'|g" $CWD/backtoshops.wsgi
else
    echo "(i) WSGI OK"
fi

# setup the database
if [ ! -z $RESETDB ]; then
    # possible errors related to the DB:
    # Peer/Ident authentication failed: check pg_hba.conf,
    # local connections should be trusted (or password)
    if [ ! -z $INITDB ]; then
        su postgres -c "psql postgres -tAc \"SELECT 1 FROM pg_roles WHERE rolname='bts'\" | grep -q 1 || createuser -P bts"
    else
        su postgres -c "dropdb backtoshops"
    fi
    su postgres -c "createdb -E UNICODE backtoshops -O bts"
    su postgres -c "psql -U bts backtoshops -c 'grant all on database backtoshops to bts;'"
fi

# edit the settings and urls
sed -i -e "s|/var/www/backtoshops/backtoshops/|$CWD/public_html|g" \
$CWD/public_html/settings_production.py
sed -i -e "s|'logs/error.log'|'../logs/error.log'|g" \
$CWD/public_html/settings_production.py
sed -i -e "s|SITE_NAME+'.|'|g" \
$CWD/public_html/settings_production.py
sed -i -e "s|settings.SITE_NAME+'.|'|g" \
$CWD/public_html/urls.py

# activate
source $CWD/env/bin/activate
( cd $CWD/public_html
  ./manage.py syncdb
  ./manage.py migrate
  ./manage.py compilemessages --locale=zh_CN
)

grep -q "export LANG=C" /etc/apache2/envvars && echo "Warning: using POSIX locale in /etc/apache2/envvars will break uploading files with unicode characters in their names."

# restart apache
/etc/init.d/apache2 restart
