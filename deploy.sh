#! /bin/bash

# This script assumes the following commands have been executed:
# cd /home
# svn co http://trac.lbga.fr/svn/backtoshops/
# cd /home/backtoshops
#
# possible errors related to the DB:
# Peer/Ident authentication failed: check pg_hba.conf,
# local connections should be trusted (or password)

set -ex

CWD=$(pwd)
ADM_DOMAIN=${ADM_DOMAIN:-sales.backtoshops.com}
USR_DOMAIN=${USR_DOMAIN:-usr.backtoshops.com}
FIN_DOMAIN=''

ADM_REQUIREMENT=$CWD/requirements/adm.backtoshops.com.requirements.txt
USR_REQUIREMENT=$CWD/requirements/usr.backtoshops.com.requirements.txt
FIN_REQUIREMENT=$CWD/requirements/finance.backtoshops.com.requirements.txt

ADM_DEPS=(libapache2-mod-wsgi python2.7-dev libpq-dev python-pip git \
          libtiff4-dev libjpeg8-dev zlib1g-dev libfreetype6-dev \
          liblcms1-dev libwebp-dev gettext libevent-dev swig)
USR_DEPS=(python2.7-dev libpq-dev python-pip git \
          libtiff4-dev libjpeg8-dev zlib1g-dev libfreetype6-dev \
          liblcms1-dev libwebp-dev libevent-dev swig redis-server)
FIN_DEPS=(python2.7-dev libpq-dev python-pip git python-lxml \
          libcairo2 libpango1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info \
          libxml2-dev libxslt1-dev)
DPKG=$(dpkg -l)

INITDB=${INITDB:-""}
RESETDB=${RESETDB:-"$INITDB"}
INST=""


########## common functions ##########

function usage() {
    echo "Usage: $0 option"
    echo "option: everything - Deploy backoffice server, users server, finance server"
    echo "        backoffice - Deploy only the backoffice server"
    echo "        user       - Deploy only the user server"
    echo "        finance    - Deploy only the finance server"
    echo "        testdata   - Import backoffice test data into database"
    exit 1
}

function sanity_checks() {
    REQUIREMENT_FILE=$1
    DEPS=$2
    [ -r /etc/debian_version ] || echo "Warning: this script was made for Debian."
    [ -r $REQUIREMENT_FILE ] || echo "Warning: $REQUIREMENT_FILE requirements not found."
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

    # install virtualenv if it is not present
    deactivate || echo "Environment was not activated."
    [ -z $(pip freeze 2> /dev/null | grep virtualenv) ] && \
    pip install virtualenv

    # add the backtoshops user if it does not already exists
    [ -z $(grep backtoshops /etc/passwd) ] && \
    useradd -d $CWD -g www-data -N -s /bin/false backtoshops

    # make sure the user owns the folder
    chown backtoshops.www-data .
    chmod 750 .
}

function create_python_env() {
    REQUIREMENT_FILE=$1
    if [ ! -d $CWD/env ]; then
        echo "(-) Creating Python environment..."
        usermod -s /bin/sh backtoshops
        PYENV="
        cd $CWD
        virtualenv --no-site-packages env
        python $CWD/env/bin/activate_this.py
        [ -r $1 ] && $CWD/env/bin/pip install -r $1 -f $CWD/packages/dist/"
        ( su backtoshops -c "$PYENV" )
        # this user won't need shell anymore
        usermod -s /bin/false backtoshops
        touch $CWD/env/.clean
    else
        source $CWD/env/bin/activate
        for i in $(cat $1); do
            lib_name=$i
            if [ ${i:0:4} = git+ ]; then
                lib_name=${i##*/}
                lib_name=$(echo $lib_name | cut -d '.' -f 1)
            fi

            if [ -z `pip freeze | grep -i $lib_name` ]; then
                echo "Missed python package ${lib_name}"
                usermod -s /bin/sh backtoshops
                PYENV="
                cd $CWD
                python $CWD/env/bin/activate_this.py
                [ -r $1 ] && $CWD/env/bin/pip install -r $1 -f $CWD/packages/dist/"
                ( su backtoshops -c "$PYENV" )
                # this user won't need shell anymore
                usermod -s /bin/false backtoshops
                touch $CWD/env/.clean
            fi
        done
        deactivate
        echo "(i) Python environment OK"
    fi
}


########## adm related functions ##########

function setup_adm_db() {
    if [ ! -z $RESETDB ]; then
        if [ ! -z $INITDB ]; then
            su postgres -c "psql postgres -tAc \"SELECT 1 FROM pg_roles WHERE rolname='bts'\" | grep -q 1 || createuser -P bts"
        else
            su postgres -c "dropdb backtoshops"
        fi
        su postgres -c "createdb -E UNICODE backtoshops -O bts"
        su postgres -c "psql -U bts backtoshops -c 'grant all on database backtoshops to bts;'"
    fi
}

function make_adm_html_dir() {
    # remove old sourcecode
    [ -d $CWD/backtoshops -a -d $CWD/public_html ] && rm -rf $CWD/public_html

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
}

function make_adm_logs_dir() {
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
}

function setup_adm_wsgi() {
    if [ ! -r /etc/apache2/sites-available/backtoshops ]; then
        echo "(-) Creating Apache VirtualHost..."
        cat > /etc/apache2/sites-available/backtoshops <<EOF
<VirtualHost *:80>
    ServerName $ADM_DOMAIN
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

    # edit the settings and urls
    sed -i -e "s|/var/www/backtoshops/backtoshops/|$CWD/public_html|g" \
    $CWD/public_html/settings_production.py
    sed -i -e "s|'logs/error.log'|'../logs/error.log'|g" \
    $CWD/public_html/settings_production.py
    sed -i -e "s|SITE_NAME+'.|'|g" \
    $CWD/public_html/settings_production.py
    sed -i -e "s|settings.SITE_NAME+'.|'|g" \
    $CWD/public_html/urls.py

    grep -q "export LANG=C" /etc/apache2/envvars && echo "Warning: using POSIX locale in /etc/apache2/envvars will break uploading files with unicode characters in their names."

    # restart apache
    /etc/init.d/apache2 restart
}

function sync_adm() {
    source $CWD/env/bin/activate
    ( cd $CWD/public_html
      ./manage.py syncdb
      ./manage.py migrate
      ./manage.py compilemessages --locale=zh_CN
    )
}

function deploy_backoffice() {
    sanity_checks $ADM_REQUIREMENT "${ADM_DEPS[*]}"
    create_python_env $ADM_REQUIREMENT
    setup_adm_db
    make_adm_html_dir
    make_adm_logs_dir
    setup_adm_wsgi
    sync_adm
    echo "(i) Deploy backoffice server finished"
}


########## usr related functions ##########

function setup_usr_db() {
    if [ ! -z $RESETDB ]; then
        su postgres -c "dropdb users"
        su postgres -c "createdb -E UNICODE users -O postgres"
    fi
}

function make_usr_src_dir() {
    # remove old sourcecode
    [ -d $CWD/users -a -d $CWD/users_src ] && rm -rf $CWD/users_src

    if [ -d $CWD/users -a ! -d $CWD/users_src ]; then
        mv $CWD/users $CWD/users_src
        cp $CWD/users_src/settings_product.py $CWD/users_src/settings.py
        chown -R backtoshops.www-data $CWD/users_src
        chmod -R 2750 $CWD/users_src
    fi
}

function setup_usr() {
    cd $CWD/users_src/
    source $CWD/env/bin/activate

    # edit the settings if needed

    # db
    bash setupdb.sh

    # start redis
    bash start_redis.sh

    # generate HMAC key
    PYTHONPATH=$CWD/users_src python scripts/gen_hmac_key.py

    # start server
    nohup python server.py &
}

function deploy_user() {
    sanity_checks $USR_REQUIREMENT "${USR_DEPS[*]}"
    create_python_env $USR_REQUIREMENT
    setup_usr_db
    make_usr_src_dir
    setup_usr
    echo "(i) Deploy user server finished"
}

function deploy_test() {
    psql -U bts -d backtoshops -f $CWD/public_html/data/test_data.sql
}


########## finance related functions ##########

function setup_finance_db() {
    if [ ! -z $RESETDB ]; then
        su postgres -c "dropdb finance"
        su postgres -c "createdb -E UNICODE finance -O postgres"
    fi
}

function make_finance_src_dir() {
    # remove old sourcecode
    [ -d $CWD/finance -a -d $CWD/finance_src ] && rm -rf $CWD/finance_src

    if [ -d $CWD/finance -a ! -d $CWD/finance_src ]; then
        mv $CWD/finance $CWD/finance_src
        cp $CWD/finance_src/settings_product.py $CWD/finance_src/settings.py
        chown -R backtoshops.www-data $CWD/finance_src
        chmod -R 2750 $CWD/finance_src
    fi
}

function setup_finance() {
    cd $CWD/finance_src/
    source $CWD/env/bin/activate

    # db
    bash setupdb.sh

    # start server
    nohup python fin_server.py &
}

function deploy_finance() {
    sanity_checks $FIN_REQUIREMENT "${FIN_DEPS[*]}"
    create_python_env $FIN_REQUIREMENT
    setup_finance_db
    make_finance_src_dir
    setup_finance
    echo "(i) Deploy finance server finished"
}

########## main ##########
[ $1 ] || usage
case $1 in
        backoffice)
            deploy_backoffice
            ;;
        user)
            deploy_user
            ;;
        finance)
            deploy_finance
            ;;
        everything)
            deploy_backoffice
            deploy_user
            deploy_test
            deploy_finance
            ;;
        testdata)
            deploy_test
            ;;
        *)
            usage
            ;;
esac
