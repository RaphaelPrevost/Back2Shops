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
FIN_DOMAIN=${FIN_DOMAIN:-finance.backtoshops.com}
AST_DOMAIN=${AST_DOMAIN:-assets.backtoshops.com}
FRT_DOMAIN=${FRT_DOMAIN:-front.backtoshops.com}

ADM_ADDR='37.187.48.33:80'
USR_ADDR='92.222.30.2:80'
FIN_ADDR='92.222.30.3:80'
AST_ADDR='92.222.30.4:80'
FRT_ADDR='92.222.30.5:80'

ADM_REQUIREMENT=$CWD/requirements/adm.backtoshops.com.requirements.txt
USR_REQUIREMENT=$CWD/requirements/usr.backtoshops.com.requirements.txt
FIN_REQUIREMENT=$CWD/requirements/finance.backtoshops.com.requirements.txt
AST_REQUIREMENT=$CWD/requirements/assets.backtoshops.com.requirements.txt
FRT_REQUIREMENT=$CWD/requirements/front.requirements.txt

ADM_DEPS=(libapache2-mod-wsgi python2.7-dev libpq-dev python-pip git \
          libtiff4-dev libjpeg8-dev zlib1g-dev libfreetype6-dev \
          liblcms1-dev libwebp-dev gettext libevent-dev swig)
USR_DEPS=(python2.7-dev libpq-dev python-pip git python-lxml \
          libtiff4-dev libjpeg8-dev zlib1g-dev libfreetype6-dev \
          liblcms1-dev libwebp-dev libevent-dev swig redis-server)
FIN_DEPS=(python2.7-dev libpq-dev python-pip git python-lxml \
          libcairo2 libpango1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info \
          libxml2-dev libxslt1-dev)
AST_DEPS=(python2.7-dev python-pip git)
FRT_DEPS=(python2.7-dev python-pip git sendmail sendmail-cf)
DPKG=$(dpkg -l)

INITDB=${INITDB:-""}
RESETDB=${RESETDB:-"$INITDB"}
INST=""


########## common functions ##########

function usage() {
    echo "Usage: $0 option"
    echo "option: everything - Deploy all servers"
    echo "        backoffice - Deploy only the backoffice server"
    echo "        user       - Deploy only the user server"
    echo "        finance    - Deploy only the finance server"
    echo "        assets     - Deploy only the assets server"
    echo "        front      - Deploy only the front server"
    echo "        restart    - Restart servers"
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
        cp -r $CWD/backtoshops $CWD/public_html
        chown -R backtoshops.www-data $CWD/public_html
        chmod -R 2750 $CWD/public_html
        # allow writing in the upload directories
        mkdir -p $CWD/public_html/media/cache
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

function make_usr_src_dir() {
    # remove old sourcecode
    [ -d $CWD/users -a -d $CWD/users_src ] && rm -rf $CWD/users_src

    if [ -d $CWD/users -a ! -d $CWD/users_src ]; then
        cp -r $CWD/users $CWD/users_src
        cp $CWD/users/settings_product.py $CWD/users_src/settings.py
        chown -R backtoshops.www-data $CWD/users_src
        chmod -R 2750 $CWD/users_src
    fi
}

function setup_usr() {
    cd $CWD/users_src/
    source $CWD/env/bin/activate

    # edit the settings if needed

    # db
    if [ ! -z $RESETDB ]; then
        source ./dbconf.sh
        bash setupdb.sh $DBNAME
    fi

    # start redis
    bash start_redis.sh

    # generate HMAC key
    PYTHONPATH=$CWD/users_src python scripts/gen_hmac_key.py

    # start server
    PORT=8100
    SERVER=server
    ps aux | grep $PORT | grep $SERVER | grep -v grep | awk '{print $2}' | xargs kill -9 || echo "no uwsgi process to kill"
    sleep 1
    start_uwsgi $PORT $SERVER

    # nginx
    if [ ! -r /etc/nginx/sites-available/users ]; then
        echo "(-) Creating Nginx Site..."
        cat > /etc/nginx/sites-available/users <<EOF
server {
    listen    $USR_ADDR;
    server_name    $USR_DOMAIN;
    location / {
        include uwsgi_params;
        uwsgi_pass 127.0.0.1:8100;
        uwsgi_param SCRIPT_NAME '';
    }
}
EOF
        ln -s /etc/nginx/sites-available/users /etc/nginx/sites-enabled/
    else
        echo "(i) Nginx Server OK"
    fi
    service nginx restart
}

function deploy_user() {
    sanity_checks $USR_REQUIREMENT "${USR_DEPS[*]}"
    create_python_env $USR_REQUIREMENT
    make_usr_src_dir
    setup_usr
    echo "(i) Deploy user server finished"
}

function deploy_test() {
    psql -U bts -d backtoshops -f $CWD/public_html/data/test_data.sql
}


########## finance related functions ##########

function make_finance_src_dir() {
    # remove old sourcecode
    [ -d $CWD/finance -a -d $CWD/finance_src ] && rm -rf $CWD/finance_src

    if [ -d $CWD/finance -a ! -d $CWD/finance_src ]; then
        cp -r $CWD/finance $CWD/finance_src
        cp $CWD/finance/settings_product.py $CWD/finance_src/settings.py
        chown -R backtoshops.www-data $CWD/finance_src
        chmod -R 2750 $CWD/finance_src
    fi
}

function setup_finance() {
    cd $CWD/finance_src/
    source $CWD/env/bin/activate

    # db
    if [ ! -z $RESETDB ]; then
        source ./dbconf.sh
        bash setupdb.sh $DBNAME
    fi

    # start server
    PORT=9000
    SERVER=fin_server
    ps aux | grep $PORT | grep $SERVER | grep -v grep | awk '{print $2}' | xargs kill -9 || echo "no uwsgi process to kill"
    sleep 1
    start_uwsgi $PORT $SERVER

    # nginx
    if [ ! -r /etc/nginx/sites-available/finance ]; then
        echo "(-) Creating Nginx Site..."
        cat > /etc/nginx/sites-available/finance <<EOF
server {
    listen    $FIN_ADDR;
    server_name    $FIN_DOMAIN;
    location / {
        include uwsgi_params;
        uwsgi_pass 127.0.0.1:9000;
        uwsgi_param SCRIPT_NAME '';
    }
}
EOF
        ln -s /etc/nginx/sites-available/finance /etc/nginx/sites-enabled/
    else
        echo "(i) Nginx Server OK"
    fi

    service nginx restart
}

function deploy_finance() {
    sanity_checks $FIN_REQUIREMENT "${FIN_DEPS[*]}"
    create_python_env $FIN_REQUIREMENT
    make_finance_src_dir
    setup_finance
    echo "(i) Deploy finance server finished"
}


########## assets related functions ##########

function make_assets_src_dir() {
    # remove old sourcecode
    [ -d $CWD/assets -a -d $CWD/assets_src ] && rm -rf $CWD/assets_src

    if [ -d $CWD/assets -a ! -d $CWD/assets_src ]; then
        cp -r $CWD/assets $CWD/assets_src
        cp $CWD/assets/settings_product.py $CWD/assets_src/settings.py
        chown -R backtoshops.www-data $CWD/assets_src
        chmod -R 2750 $CWD/assets_src
    fi

    if [ ! -d $CWD/assets_files ]; then
        mkdir $CWD/assets_files
        cp -r $CWD/assets/static/css $CWD/assets_files/
        cp -r $CWD/assets/static/js $CWD/assets_files/
        cp -r $CWD/assets/static/img $CWD/assets_files/
        cp -r $CWD/assets/static/html $CWD/assets_files/
        chown -R backtoshops.www-data $CWD/assets_files
        # allow writing in the upload directories
        chmod -R 2770 $CWD/assets_files
    fi
}

function setup_assets() {
    cd $CWD/assets_src/
    source $CWD/env/bin/activate

    # start server
    PORT=9300
    SERVER=assets_server
    ps aux | grep $PORT | grep $SERVER | grep -v grep | awk '{print $2}' | xargs kill -9 || echo "no uwsgi process to kill"
    sleep 1
    start_uwsgi $PORT $SERVER

    # nginx
    if [ ! -r /etc/nginx/sites-available/assets ]; then
        echo "(-) Creating Nginx Site..."
        cat > /etc/nginx/sites-available/assets <<EOF
server {
    listen    $AST_ADDR;
    server_name    $AST_DOMAIN;
    location /img/ {
        alias /home/backtoshops/assets_files/img/;
        autoindex off;
    }
    location /js/ {
        alias /home/backtoshops/assets_files/js/;
        autoindex off;
    }
    location /css/ {
        alias /home/backtoshops/assets_files/css/;
        autoindex off;
    }
    location /html/ {
        alias /home/backtoshops/assets_files/html/;
        autoindex off;
    }
    location / {
        include uwsgi_params;
        uwsgi_pass 127.0.0.1:9300;
        uwsgi_param SCRIPT_NAME '';
    }
}
EOF
        ln -s /etc/nginx/sites-available/assets /etc/nginx/sites-enabled/
    else
        echo "(i) Nginx Server OK"
    fi

    service nginx restart
}

function deploy_assets() {
    sanity_checks $AST_REQUIREMENT "${AST_DEPS[*]}"
    create_python_env $AST_REQUIREMENT
    make_assets_src_dir
    setup_assets
    echo "(i) Deploy assets server finished"
}


########## front related functions ##########

function setup_geoip_database() {
    if [ ! -d $CWD/env/data ]; then
        mkdir $CWD/env/data
    fi
    echo "(-) Downloading geoip free database..."
    cd $CWD/env/data
    wget http://geolite.maxmind.com/download/geoip/database/GeoLite2-City.mmdb.gz
    gzip -d GeoLite2-City.mmdb.gz
    wget http://geolite.maxmind.com/download/geoip/database/GeoLite2-Country.mmdb.gz
    gzip -d GeoLite2-Country.mmdb.gz
    echo "(-) Setup geoip free database for front server is done."
}

function make_front_src_dir() {
    # remove old sourcecode
    [ -d $CWD/front -a -d $CWD/front_src ] && rm -rf $CWD/front_src

    if [ -d $CWD/front -a ! -d $CWD/front_src ]; then
        cp -r $CWD/front $CWD/front_src
        cp $CWD/front/settings_product.py $CWD/front_src/settings.py
        chown -R backtoshops.www-data $CWD/front_src
        chmod -R 2750 $CWD/front_src
    fi

    if [ ! -d $CWD/front_files ]; then
        mkdir $CWD/front_files
        chown -R backtoshops.www-data $CWD/front_files
        chmod -R 2770 $CWD/front_files
    fi
    cp -r $CWD/front/static/css $CWD/front_files/
    cp -r $CWD/front/static/js $CWD/front_files/
    cp -r $CWD/front/static/img $CWD/front_files/
}

function setup_front() {
    cd $CWD/front_src/
    source $CWD/env/bin/activate

    # start server
    PORT=9500
    SERVER=front_server
    ps aux | grep $PORT | grep $SERVER | grep -v grep | awk '{print $2}' | xargs kill -9 || echo "no uwsgi process to kill"
    sleep 1
    start_uwsgi $PORT $SERVER

    # nginx
    if [ ! -r /etc/nginx/sites-available/front ]; then
        echo "(-) Creating Nginx Site..."
        cat > /etc/nginx/sites-available/front <<EOF
server {
    listen    $FRT_ADDR;
    server_name    $FRT_DOMAIN;
    location /img/ {
        alias /home/backtoshops/front_files/img/;
        autoindex off;
    }
    location /js/ {
        alias /home/backtoshops/front_files/js/;
        autoindex off;
    }
    location /css/ {
        alias /home/backtoshops/front_files/css/;
        autoindex off;
    }
    location /templates/ {
        alias /home/backtoshops/front_src/views/templates/;
        autoindex off;
    }
    location /webservice/1.0/pub/apikey.pem {
        alias /home/backtoshops/front_src/static/keys/front_pub.key;
        autoindex off;
    }
    location / {
        include uwsgi_params;
        uwsgi_pass 127.0.0.1:9500;
        uwsgi_param SCRIPT_NAME '';
    }
}
EOF
        ln -s /etc/nginx/sites-available/front /etc/nginx/sites-enabled/
    else
        echo "(i) Nginx Server OK"
    fi

    sleep 1
    service nginx restart
}

function deploy_front() {
    sanity_checks $FRT_REQUIREMENT "${FRT_DEPS[*]}"
    create_python_env $FRT_REQUIREMENT
    setup_geoip_database
    make_front_src_dir
    setup_front
    echo "(i) Deploy front server finished"
}


function restart_servers() {
    service apache2 restart

    killall -9 uwsgi
    source $CWD/env/bin/activate

    sleep 1
    cd $CWD/users_src
    start_uwsgi 8100 server
    sleep 1
    cd $CWD/finance_src
    start_uwsgi 9000 fin_server
    sleep 1
    cd $CWD/assets_src
    start_uwsgi 9300 assets_server
    sleep 1
    cd $CWD/front_src
    start_uwsgi 9500 front_server

    sleep 1
    #service nginx restart
}

function start_uwsgi() {
    uwsgi -s 127.0.0.1:$1 -w $2 -M -p4 --callable app -d uwsgi.log --gevent 100
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
        assets)
            deploy_assets
            ;;
        front)
            deploy_front
            ;;
        everything)
            deploy_backoffice
            deploy_user
            #deploy_test
            deploy_finance
            deploy_assets
            deploy_front
            ;;
        restart)
            restart_servers
            ;;
        testdata)
            deploy_test
            ;;
        *)
            usage
            ;;
esac
