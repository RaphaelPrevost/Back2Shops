#! /bin/bash

set -ex

CWD=$(pwd)
AST=/var/local/assets

ADM_REQUIREMENT=$CWD/requirements/adm.backtoshops.com.requirements.txt
USR_REQUIREMENT=$CWD/requirements/usr.backtoshops.com.requirements.txt
FIN_REQUIREMENT=$CWD/requirements/finance.backtoshops.com.requirements.txt
AST_REQUIREMENT=$CWD/requirements/assets.backtoshops.com.requirements.txt
FRT_REQUIREMENT=$CWD/requirements/front.requirements.txt
VSL_REQUIREMENT=$CWD/requirements/vessel.backtoshops.com.requirements.txt

ADM_DEPS=(psmisc apache2 libapache2-mod-wsgi python2.7-dev libpq-dev python-pip \
          libtiff4-dev libjpeg8-dev zlib1g-dev libfreetype6-dev git redis-server \
          liblcms1-dev libwebp-dev gettext libevent-dev swig memcached postgresql-contrib)
USR_DEPS=(psmisc python2.7-dev libpq-dev python-pip git python-lxml \
          libtiff4-dev libjpeg8-dev zlib1g-dev libfreetype6-dev \
          liblcms1-dev libwebp-dev libevent-dev swig redis-server \
          sendmail sendmail-cf)
FIN_DEPS=(psmisc python2.7-dev libpq-dev python-pip git python-lxml \
          libcairo2 libpango1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info \
          libxml2-dev libxslt1-dev)
AST_DEPS=(psmisc python2.7-dev python-pip git)
FRT_DEPS=(psmisc python2.7-dev python-pip git sendmail sendmail-cf)
VSL_DEPS=(psmisc python2.7-dev python-requests python-pip git sendmail sendmail-cf)
DPKG=$(dpkg -l)

BRAND=${BRAND:-"$MAIN_BRAND"}
INITDB=${INITDB:-""}
RESETDB=${RESETDB:-"$INITDB"}
INST=""

source ./deploy_settings.sh

########## common functions ##########

function edit_product_settings() {
    sed -i -e "s|37.187.48.33|$ADM_ADDR|g" $1
    sed -i -e "s|92.222.30.2|$USR_ADDR|g" $1
    sed -i -e "s|92.222.30.3|$FIN_ADDR|g" $1
    sed -i -e "s|92.222.30.4|$AST_ADDR|g" $1
    sed -i -e "s|92.222.30.6|$VSL_ADDR|g" $1

    SERVER_ADDR=$(echo $BRAND)_FRT_ADDR
    SERVER_ADDR=$(eval echo "\$${SERVER_ADDR}")
    sed -i -e "s|92.222.30.5|$SERVER_ADDR|g" $1
}

function usage() {
    echo "Usage: $0 option [server]"
    echo "option: deploy     - deploy specific server (backoffice, user, finance, vessel, assets, front)"
    echo "        restart    - restart specific server (backoffice, user, finance, vessel, assets, front)"
    echo "        testdata   - Import backoffice test data into database"
    exit 1
}

function server_local_port() {
    SERVER=$1
    BRAND=$2
    case $SERVER in
        backoffice)
            echo "8000"
            ;;
        user)
            echo "8100"
            ;;
        finance)
            echo "9000"
            ;;
        vessel)
            echo "8700"
            ;;
        assets)
            echo "9300"
            ;;
        front)
            case $BRAND in
                breuer)
                    echo "9500"
                    ;;
                vessel)
                    echo "9501"
                    ;;
                dragon)
                    echo "9502"
                    ;;
            esac
            ;;
    esac
}

function create_user() {
    # add the backtoshops user if it does not already exists
    if [ -z $(grep backtoshops /etc/passwd) ]; then
        useradd -d $CWD -g www-data -N -s /bin/false backtoshops
    fi
}

function gen_keys() {
    cd static/keys
    openssl genrsa -out $1_pri.key 2048
    openssl rsa -in $1_pri.key -out $1_pub.key -outform PEM -pubout
    cd -
}

function sanity_checks() {
    REQUIREMENT_FILE=$1
    DEPS=$2
    [ -r /etc/debian_version ] || echo "Warning: this script was made for Debian."
    [ -r $REQUIREMENT_FILE ] || echo "Warning: $REQUIREMENT_FILE requirements not found."
    grep -q 'UTF-8' /etc/postgresql/9.1/main/postgresql.conf || echo "Warning: postgresql needs to be configured in UTF-8"

    for pkg in ${DEPS[*]}; do
        if echo $DPKG | grep -qw "ii $pkg "; then
            echo "(i) $pkg already installed."
        else
            INST="$INST $pkg"
        fi
    done

    if [ -n "$INST" ]; then
        echo "install python packages $INST"
        apt-get install -y $INST
    fi

    create_user
    # make sure the user owns the folder
    chown backtoshops.www-data .
    chmod 750 .
}

function create_python_env() {
    for i in $(cat $REQUIREMENT_FILE); do
        lib_name=$i
        if [ ${i:0:4} = git+ ]; then
            lib_name=${i##*/}
            lib_name=$(echo $lib_name | cut -d '.' -f 1)
        fi

        if [ -z `pip freeze | grep -i $lib_name` ]; then
            echo "Missed python package ${lib_name}"
            cd $CWD
            [ -r $REQUIREMENT_FILE ] && pip install -r $REQUIREMENT_FILE -f file://$CWD/packages/dist/
        fi
    done
}

function create_assets_dir() {
    if [ ! -d $AST ]; then
        mkdir $AST
    fi
    chown -R backtoshops.www-data $AST
    chmod -R 2750 $AST
}

function compile_i18n_labels() {
    (
        cd $CWD
        python i18nmessages.py --locale=fr_FR --domain=$1 make
        python i18nmessages.py --locale=zh_CN --domain=$1 make
        python i18nmessages.py --domain=$1 compile
        chown -R backtoshops.www-data $CWD/locale
        chmod -R 2770 $CWD/locale

        cd -
    )
}

function create_db_role() {
    su postgres -c "psql postgres -tAc \"SELECT 1 FROM pg_roles WHERE rolname='bts'\" | grep -q 1 || createuser -s bts"
}

########## adm related functions ##########

function setup_adm_db() {
    if [ ! -z $RESETDB ]; then
        if [ ! -z $INITDB ]; then
            create_db_role
        else
            su postgres -c "dropdb backtoshops"
        fi
        su postgres -c "createdb -E UNICODE backtoshops -O bts"
        su postgres -c "psql -U bts backtoshops -c 'grant all on database backtoshops to bts;'"
        su postgres -c "psql -U bts backtoshops -c 'CREATE EXTENSION unaccent;'"
    fi
}

function make_adm_html_dir() {
    # copy locale directory back
    [ -d $CWD/backtoshops -a -d $CWD/public_html/locale ] && cp -r $CWD/public_html/locale $CWD/backtoshops/
    # make and compile po files
    compile_i18n_labels "backoffice"
    compile_i18n_labels "front"

    # remove old sourcecode
    [ -d $CWD/backtoshops -a -d $CWD/public_html ] && rm -rf $CWD/public_html

    if [ -d $CWD/backtoshops -a ! -d $CWD/public_html ]; then
        cp -r $CWD/backtoshops $CWD/public_html

        chown -R backtoshops.www-data $CWD/public_html
        chmod -R 2750 $CWD/public_html
        # allow writing in the upload directories
        mkdir -p $CWD/public_html/media/cache
        chmod -R 2770 $CWD/public_html/media/
        chmod -R 2770 $CWD/public_html/locale/
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
    else
        echo "(i) Logs directory OK"
    fi
}

function setup_adm_wsgi() {
    if [ ! -r /etc/apache2/sites-available/backoffice.conf ]; then
        echo "(-) Creating Apache VirtualHost..."
        cat > /etc/apache2/sites-available/backoffice.conf <<EOF
Listen 8000
<VirtualHost *:8000>
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

    Alias /static/admin $CWD/public_html/static/admin
    Alias /static/css $CWD/public_html/static/css
    Alias /static/fonts $CWD/public_html/static/fonts
    Alias /static/img $CWD/public_html/static/img
    Alias /static/js $CWD/public_html/static/js
    Alias /webservice/1.0/pub/apikey.pem $CWD/public_html/static/keys/adm_pub.key
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
        a2enmod wsgi
        a2ensite backoffice.conf
        sed -i -e "s|Require all denied|#Require all denied|g" /etc/apache2/apache2.conf
    else
        echo "(i) Apache VirtualHost OK"
    fi

    # setup the WSGI
    if [ ! -r $CWD/backtoshops.wsgi ]; then
        echo "(-) Creating WSGI..."
        cp $CWD/production.wsgi $CWD/backtoshops.wsgi
        # edit the WSGI
        sed -i -e "s|backtoshops.settings|settings|g" $CWD/backtoshops.wsgi
        sed -i -e "s|backtoshops-env|env|g" $CWD/backtoshops.wsgi
        sed -i -e "s|'backtoshops'|'public_html'|g" $CWD/backtoshops.wsgi
    else
        echo "(i) WSGI OK"
    fi

    # edit the settings and urls
    edit_product_settings $CWD/public_html/settings_production.py
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
    ( cd $CWD/public_html
      ./manage.py syncdb
      ./manage.py migrate
    )
}

function adm_redis() {
    ( cd $CWD/public_html
      ps aux | grep 'start_stats_redis' | grep -v grep | awk '{print $2}' | xargs kill -9 || echo "no similarity redis process to kill"
      sleep 1
      PORT=8001
      redis-cli -p $PORT shutdown || echo "no running redis"
      sleep 1
      ./manage.py start_stats_redis &
    )
}

function adm_batch () {
    ( cd $CWD/public_html
        ps aux | grep 'batch_start' | grep -v grep | awk '{print $2}' | xargs kill -9 || echo "no batch process to kill"
        sleep 1
      ./manage.py batch_start &
    )
}

function adm_gen_keys() {
    ( cd $CWD/public_html
      gen_keys "adm"
    )
}

function deploy_backoffice() {
    sanity_checks $ADM_REQUIREMENT "${ADM_DEPS[*]}"
    create_python_env $ADM_REQUIREMENT
    make_adm_logs_dir
    make_adm_html_dir
    setup_adm_wsgi
    echo "(i) Deploy backoffice server finished"
}

function setup_backoffice() {
    setup_adm_db
    sync_adm
    adm_redis
    adm_gen_keys
    adm_batch
    service memcached restart
    service apache2 restart
}


########## usr related functions ##########

function make_usr_src_dir() {
    # remove old sourcecode
    [ -d $CWD/users -a -d $CWD/users_src ] && rm -rf $CWD/users_src

    if [ -d $CWD/users -a ! -d $CWD/users_src ]; then
        cp -r $CWD/users $CWD/users_src
        cp $CWD/users/settings_product.py $CWD/users_src/settings.py
        edit_product_settings $CWD/users_src/settings.py

        chown -R backtoshops.www-data $CWD/users_src
        chmod -R 2750 $CWD/users_src
    fi
}

function setup_usr() {
    cd $CWD/users_src/

    # db
    create_db_role

    if [ ! -z $RESETDB ]; then
        source ./dbconf.sh
        bash setupdb.sh $DBNAME
    fi

    # start redis
    bash start_redis.sh

    # generate HMAC key
    PYTHONPATH=$CWD/users_src python scripts/gen_hmac_key.py

    gen_keys "usr"

    # start server
    PORT=$(server_local_port user)
    SERVER=server
    ps aux | grep $PORT | grep $SERVER | grep -v grep | awk '{print $2}' | xargs kill -9 || echo "no uwsgi process to kill"
    sleep 1
    start_uwsgi $PORT $SERVER
}

function deploy_usr() {
    sanity_checks $USR_REQUIREMENT "${USR_DEPS[*]}"
    create_python_env $USR_REQUIREMENT
    make_usr_src_dir
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
        edit_product_settings $CWD/finance_src/settings.py

        chown -R backtoshops.www-data $CWD/finance_src
        chmod -R 2750 $CWD/finance_src
    fi
}

function setup_finance() {
    cd $CWD/finance_src/

    # db
    create_db_role

    if [ ! -z $RESETDB ]; then
        source ./dbconf.sh
        bash setupdb.sh $DBNAME
    fi

    gen_keys "finance"

    # start server
    PORT=$(server_local_port finance)
    SERVER=fin_server
    ps aux | grep $PORT | grep $SERVER | grep -v grep | awk '{print $2}' | xargs kill -9 || echo "no uwsgi process to kill"
    sleep 1
    start_uwsgi $PORT $SERVER
}

function deploy_finance() {
    sanity_checks $FIN_REQUIREMENT "${FIN_DEPS[*]}"
    create_python_env $FIN_REQUIREMENT
    make_finance_src_dir
    echo "(i) Deploy finance server finished"
}


########## assets related functions ##########

function make_assets_src_dir() {
    # remove old sourcecode
    [ -d $CWD/assets -a -d $CWD/assets_src ] && rm -rf $CWD/assets_src

    if [ -d $CWD/assets -a ! -d $CWD/assets_src ]; then
        cp -r $CWD/assets $CWD/assets_src
        cp $CWD/assets/settings_product.py $CWD/assets_src/settings.py
        edit_product_settings $CWD/assets_src/settings.py

        chown -R backtoshops.www-data $CWD/assets_src
        chmod -R 2750 $CWD/assets_src
    fi
}

function make_assets_dir() {
    create_assets_dir

    if [ ! -d $AST/assets_files ]; then
        mkdir $AST/assets_files
        chown -R backtoshops.www-data $AST/assets_files
        # allow writing in the upload directories
        chmod -R 2770 $AST/assets_files
    fi

    cp -r $CWD/assets/static/css $AST/assets_files/
    cp -r $CWD/assets/static/js $AST/assets_files/
    cp -r $CWD/assets/static/img $AST/assets_files/
    cp -r $CWD/assets/static/html $AST/assets_files/
}

function setup_assets() {
    make_assets_dir

    cd $CWD/assets_src/
    gen_keys "ast"

    # start server
    PORT=$(server_local_port assets)
    SERVER=assets_server
    ps aux | grep $PORT | grep $SERVER | grep -v grep | awk '{print $2}' | xargs kill -9 || echo "no uwsgi process to kill"
    sleep 1
    start_uwsgi $PORT $SERVER

}

function deploy_assets() {
    sanity_checks $AST_REQUIREMENT "${AST_DEPS[*]}"
    create_python_env $AST_REQUIREMENT
    make_assets_src_dir
    echo "(i) Deploy assets server finished"
}


########## front related functions ##########

function setup_geoip_database() {
    if [ ! -d /usr/data ]; then
        mkdir /usr/data
    fi
    echo "(-) Downloading geoip free database..."
    cd /usr/data
    wget http://geolite.maxmind.com/download/geoip/database/GeoLite2-City.mmdb.gz
    gzip -df GeoLite2-City.mmdb.gz
    wget http://geolite.maxmind.com/download/geoip/database/GeoLite2-Country.mmdb.gz
    gzip -df GeoLite2-Country.mmdb.gz
    echo "(-) Setup geoip free database for front server is done."
}

function make_front_src_dir() {
    src_name=$CWD/front_$(echo $BRAND)_src

    # remove old sourcecode
    [ -d $CWD/front -a -d $src_name ] && rm -rf $src_name
    # make and compile po files
    #compile_i18n_labels "front"

    settings_file=$CWD/front/settings_product.py
    if [ -a $CWD/front/settings_product_$(echo $BRAND).py ]; then
        settings_file=$CWD/front/settings_product_$(echo $BRAND).py
    fi

    if [ -d $CWD/front -a ! -d $src_name ]; then
        cp -r $CWD/front $src_name
        cp $settings_file $src_name/settings.py
        edit_product_settings $src_name/settings.py
        edit_product_settings $src_name/settings_product.py
        if [ -a $src_name/settings_product_$(echo $BRAND).py ]; then
            edit_product_settings $src_name/settings_product_$(echo $BRAND).py
        fi

        chown -R backtoshops.www-data $src_name
        chmod -R 2750 $src_name
    fi
}

function make_front_dir() {
    create_assets_dir

    if [ ! -d $AST/front_files ]; then
        mkdir $AST/front_files
        chown -R backtoshops.www-data $AST/front_files
        chmod -R 2770 $AST/front_files
    fi
    cp -r $CWD/front/static/css $AST/front_files/
    cp -r $CWD/front/static/js $AST/front_files/
    cp -r $CWD/front/static/img $AST/front_files/
}

function setup_front() {
    make_front_dir

    src_name=$CWD/front_$(echo $BRAND)_src
    cd $src_name
    #gen_keys "front"

    # start server
    PORT=$(server_local_port front $BRAND)
    SERVER=front_server
    ps aux | grep $PORT | grep $SERVER | grep -v grep | awk '{print $2}' | xargs kill -9 || echo "no uwsgi process to kill"
    sleep 1
    start_uwsgi $PORT $SERVER
}

function deploy_front() {
    sanity_checks $FRT_REQUIREMENT "${FRT_DEPS[*]}"
    create_python_env $FRT_REQUIREMENT
    setup_geoip_database
    make_front_src_dir
    echo "(i) Deploy front server finished"
}


########## vessel related functions ##########
function make_vsl_src_dir() {
    # remove old sourcecode
    [ -d $CWD/vessel -a -d $CWD/vessel_src ] && rm -rf $CWD/vessel_src

    if [ -d $CWD/vessel -a ! -d $CWD/vessel_src ]; then
        cp -r $CWD/vessel $CWD/vessel_src
        cp $CWD/vessel/settings_product.py $CWD/vessel_src/settings.py
        edit_product_settings $CWD/vessel_src/settings.py

        chown -R backtoshops.www-data $CWD/vessel_src
        chmod -R 2750 $CWD/vessel_src
    fi
}

function setup_vsl() {
    cd $CWD/vessel_src/

    # db
    create_db_role

    if [ ! -z $RESETDB ]; then
        source ./dbconf.sh
        bash setupdb.sh $DBNAME
    fi

    gen_keys "vessel"

    # start server
    PORT=$(server_local_port vessel)
    SERVER=vessel_server
    ps aux | grep $PORT | grep $SERVER | grep -v grep | awk '{print $2}' | xargs kill -9 || echo "no uwsgi process to kill"
    sleep 1
    start_uwsgi $PORT $SERVER 1
}

function deploy_vessel() {
    sanity_checks $VSL_REQUIREMENT "${VSL_DEPS[*]}"
    create_python_env $VSL_REQUIREMENT
    make_vsl_src_dir
    echo "(i) Deploy vessel server finished"
}


########## ##########

function deploy_server() {
    case $1 in
            backoffice)
                deploy_backoffice
                ;;
            user)
                deploy_usr
                ;;
            finance)
                deploy_finance
                ;;
            vessel)
                deploy_vsl
                ;;
            assets)
                deploy_assets
                ;;
            front)
                deploy_front
                ;;
    esac
}

function restart_server() {
    case $1 in
            backoffice)
                setup_backoffice
                ;;
            user)
                setup_usr
                ;;
            finance)
                setup_finance
                ;;
            vessel)
                setup_vsl
                ;;
            assets)
                setup_assets
                ;;
            front)
                setup_front
                ;;
    esac
}

function start_uwsgi() {
    p_num=${3:-"4"}
    uwsgi -s 0.0.0.0:$1 -w $2 -M -p$p_num --callable app -d uwsgi.log --gevent 100
}

########## main ##########
[ $1 ] || usage
case $1 in
        deploy)
            deploy_server $2
            ;;
        restart)
            restart_server $2
            ;;
        testdata)
            deploy_test
            ;;
        *)
            usage
            ;;
esac
