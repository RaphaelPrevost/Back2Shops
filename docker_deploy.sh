#! /bin/bash

# This script assumes the following commands have been executed:
# cd /home
# hg clone https://dragondollar.kilnhg.com/Code/Repositories/Group/Dragon-Dollar backtoshops
# cd /home/backtoshops
#
# install docker
# $ curl -s https://get.docker.io/ubuntu/ | sudo sh
#

set -ex
CWD=$(pwd)
AST=/var/local/assets
BASE_IMG=baseimage
DB_IMG=database-image
DB_CONTAINER_NAME=database

INITDB=${INITDB:-""}
RESETDB=${RESETDB:-"$INITDB"}


function usage() {
    echo "Usage: $0 option [action]"
    echo "option: backoffice - Deploy only the backoffice server"
    echo "        user       - Deploy only the user server"
    echo "        finance    - Deploy only the finance server"
    echo "        vessel     - Deploy only the vessel server"
    echo "        assets     - Deploy only the assets server"
    echo "        front      - Deploy only the front servers"
    echo "        everything - Deploy all servers"
    echo "        baseimage  - Make a base image"
    echo "        db         - Start db container"
    echo "action: N/A        - Make an image and run the specific server"
    echo "        make       - Make an image for the specific server"
    echo "        run        - Run the specific server"
    exit 1
}


function check_deploy_settings() {
    if [ -a deploy_settings.sh ]; then
        echo "Please check current deployment: "
        echo
        cat deploy_settings.sh
        echo
        read -p "Need edit? (y/N) " edit
        if [ $edit == "y" ]; then
            set_deploy_settings
        fi
    else
        set_deploy_settings
    fi
    source ./deploy_settings.sh
}

function set_deploy_settings() {
    read -p "Please input backoffice domain: " ADM_DOMAIN
    read -p "Please input backoffice address: " ADM_ADDR
    read -p "Please input user server domain: " USR_DOMAIN
    read -p "Please input user server address: " USR_ADDR
    read -p "Please input finance server domain: " FIN_DOMAIN
    read -p "Please input finance server address: " FIN_ADDR
    read -p "Please input assets server domain: " AST_DOMAIN
    read -p "Please input assets server address: " AST_ADDR
    read -p "Please input vessel server domain: " VSL_DOMAIN
    read -p "Please input vessel server address: " VSL_ADDR
    read -p "Please input front server brand (breuer/vessel/dragon): " BRAND
    read -p "Please input front server domain: " FRT_DOMAIN
    read -p "Please input front server address: " FRT_ADDR
    read -p "Please input dragon dollar blog ip address: " DRAGON_BLOG_IP

    cat > $CWD/deploy_settings.sh <<EOF
export ADM_DOMAIN='$ADM_DOMAIN'
export ADM_ADDR='$ADM_ADDR'
export USR_DOMAIN='$USR_DOMAIN'
export USR_ADDR='$USR_ADDR'
export FIN_DOMAIN='$FIN_DOMAIN'
export FIN_ADDR='$FIN_ADDR'
export AST_DOMAIN='$AST_DOMAIN'
export AST_ADDR='$AST_ADDR'
export VSL_DOMAIN='$VSL_DOMAIN'
export VSL_ADDR='$VSL_ADDR'
export MAIN_BRAND='$BRAND'
export $(echo $BRAND)_FRT_DOMAIN='$FRT_DOMAIN'
export $(echo $BRAND)_FRT_ADDR='$FRT_ADDR'
export DRAGON_BLOG_IP='$DRAGON_BLOG_IP'
EOF

    set_more_front
}

function set_more_front() {
    read -p "Need more front for other brand ? (y/n) " yes
    if [ $yes == "y" ]; then
        read -p "Please input front server brand (breuer/vessel/dragon): " BRAND
        read -p "Please input front server domain: " FRT_DOMAIN
        read -p "Please input front server address: " FRT_ADDR
        cat >> $CWD/deploy_settings.sh <<EOF
export $(echo $BRAND)_FRT_DOMAIN='$FRT_DOMAIN'
export $(echo $BRAND)_FRT_ADDR='$FRT_ADDR'
EOF
        set_more_front
    fi
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

function create_assets_dir() {
    if [ ! -d $AST ]; then
        mkdir $AST
    fi
    chown -R backtoshops.www-data $AST
    chmod -R 2750 $AST
}

function docker_pull() {
    result=$(docker images | grep $1 | wc -l)
    if [ $result -eq "0" ]; then
        echo "pulling $1"
        docker pull $1
    fi
}

function docker_stop_container() {
    exist=$(docker ps -a | awk '{print $(NF)}' | grep ^$1$ | wc -l)
    if [ $exist != "0" ]; then
        docker exec -it $1 service postgresql stop || echo ""
        docker rm -f $1
    fi
}

function make_image() {
    fname=docker/"$1"_docker_file
    if [ -a $fname ]; then
        docker build -t $1 - < $fname
        docker save $1 > docker/$1
    fi
}

function load_image() {
    SELF_IMG=$1

    if [ -a docker/$SELF_IMG ]; then
        docker load < docker/$SELF_IMG || (rm docker/$SELF_IMG; load_image $SELF_IMG)
    else
        if [ -a docker/$BASE_IMG ]; then
            docker load < docker/$BASE_IMG
        else
            make_image $BASE_IMG
            docker load < docker/$BASE_IMG
        fi
    fi
}

function start_db_container() {
    exist=$(docker ps -a | awk '{print $(NF)}' | grep ^$DB_CONTAINER_NAME$ | wc -l)
    if [ $exist == "0" ]; then
        docker_pull debian:wheezy
        docker_stop_container $DB_CONTAINER_NAME
        docker run --name $DB_CONTAINER_NAME -v /var/lib/postgresql/:/var/lib/container_pg/ debian:wheezy true
    fi
}

function copy_src() {
    CONTAINER_ID=$1
    CONTAINER_ROOT_DIR=/var/lib/docker/devicemapper/mnt/$CONTAINER_ID/rootfs
    if [ ! -d $CONTAINER_ROOT_DIR ]; then
        CONTAINER_ROOT_DIR=/var/lib/docker/aufs/mnt/$CONTAINER_ID
    fi
    rsync -a --exclude=docker/*-image $CWD $CONTAINER_ROOT_DIR/home
}

function make_container_image() {
    SERVER_NAME=$1
    CONTAINER_NAME=$2
    SELF_IMG=$3

    if [ $SERVER_NAME == 'front' ]; then
        BRAND=$4
        docker exec -it $CONTAINER_NAME /bin/bash -c "cd /home/backtoshops; BRAND=$BRAND bash container_deploy.sh deploy $SERVER_NAME"
    else
        docker exec -it $CONTAINER_NAME /bin/bash -c "cd /home/backtoshops; bash container_deploy.sh deploy $SERVER_NAME"
    fi

    docker commit $CONTAINER_NAME $SELF_IMG && docker save $SELF_IMG > docker/$SELF_IMG
}

function run_container_server() {
    SERVER_NAME=$1
    CONTAINER_NAME=$2

    if [ $SERVER_NAME == 'front' ]; then
        BRAND=$3
        docker exec -it $CONTAINER_NAME /bin/bash -c "cd /home/backtoshops; BRAND=$BRAND INITDB=$INITDB RESETDB=$RESETDB bash container_deploy.sh restart $SERVER_NAME"
    else
        docker exec -it $CONTAINER_NAME /bin/bash -c "cd /home/backtoshops; INITDB=$INITDB RESETDB=$RESETDB bash container_deploy.sh restart $SERVER_NAME"
    fi
}

function make_or_run() {
    SERVER_NAME=$1
    SELF_IMG=$2
    CONTAINER_NAME=$3
    CONTAINER_ID=$4
    STEP=$5
    BRAND=$6

    if [ $STEP == 'make' ]; then
        copy_src $CONTAINER_ID
        make_container_image $SERVER_NAME $CONTAINER_NAME $SELF_IMG $BRAND
        docker_stop_container $CONTAINER_NAME

    elif [ $STEP == 'run' ]; then
        run_container_server $SERVER_NAME $CONTAINER_NAME $BRAND

    else
        copy_src $CONTAINER_ID
        make_container_image $SERVER_NAME $CONTAINER_NAME $SELF_IMG $BRAND
        run_container_server $SERVER_NAME $CONTAINER_NAME $BRAND
    fi
}

function setup_nginx() {
    if [ ! -f /etc/nginx/nginx.conf ]; then
        apt-get install -y nginx
    fi

    sed -i -e's|[^#]gzip_disable \"msie6\"\;|\
    #gzip_disable \"msie6\"\;\
    ##CHANGES START \
    gzip_disable \"MSIE [1-6]\.(?!.*SV1)\";\
    gzip_vary on;\
    gzip_proxied any;\
    gzip_comp_level 9;\
    gzip_buffers 16 8k;\
    gzip_http_version 1.1;\
    gzip_types text/plain text/html text/xml text/css text/javascript application/javascript application/xml application/xml+rss application/json application/x-javascript;\
    \
    large_client_header_buffers 4 16k;\
    client_max_body_size 5m;\
    client_body_buffer_size 128k;\
    proxy_connect_timeout 300;\
    proxy_read_timeout 300;\
    proxy_send_timeout 300;\
    proxy_buffer_size 64k;\
    proxy_buffers   4 32k;\
    proxy_busy_buffers_size 64k;\
    proxy_temp_file_write_size 64k;\
    ##CHANGES END \
    |' /etc/nginx/nginx.conf
}

### backoffice ###

function prepare_bo_image() {
    SELF_IMG=$1
    CONTAINER_NAME=$2
    PORT=$3
    STEP=$4
    
    load_image $SELF_IMG
    docker_stop_container $CONTAINER_NAME
    if [ -a docker/$SELF_IMG ]; then
        IMG=$SELF_IMG
    else
        IMG=$BASE_IMG
    fi
    CONTAINER_ID=$(docker run -itd \
           --volumes-from=$DB_CONTAINER_NAME \
           -v /tmp/logs:/tmp/logs \
           -p 127.0.0.1:$PORT:$PORT --name=$CONTAINER_NAME $IMG)

    docker exec -it $CONTAINER_NAME chown -R postgres:postgres /var/lib/container_pg
    docker exec -it $CONTAINER_NAME service postgresql restart

    make_or_run "backoffice" $SELF_IMG $CONTAINER_NAME $CONTAINER_ID $STEP
}

function setup_bo_server() {
    PORT=$1

    setup_nginx()
    # nginx
    if [ ! -r /etc/nginx/sites-available/backoffice ]; then
        echo "(-) Creating Nginx Site..."
        cat > /etc/nginx/sites-available/backoffice <<EOF
server {
    listen    $ADM_ADDR;
    server_name    $ADM_DOMAIN;
    location / {
        proxy_pass http://127.0.0.1:$PORT;
    }
}
EOF
        ln -s /etc/nginx/sites-available/backoffice /etc/nginx/sites-enabled/
    else
        echo "(i) Nginx Server OK"
    fi
    service nginx restart
}

function deploy_bo() {
    SELF_IMG="backoffice-image"
    CONTAINER_NAME="backoffice"
    PORT=$(server_local_port backoffice)
    STEP=${1:-""}

    if [ $STEP == 'make' ]; then
        prepare_bo_image $SELF_IMG $CONTAINER_NAME $PORT $STEP
    elif [ $STEP == 'run' ]; then
        start_db_container
        prepare_bo_image $SELF_IMG $CONTAINER_NAME $PORT $STEP
        setup_bo_server $PORT
    else
        start_db_container
        prepare_bo_image $SELF_IMG $CONTAINER_NAME $PORT
        setup_bo_server $PORT
    fi
}


### user ###

function prepare_user_image() {
    SELF_IMG=$1
    CONTAINER_NAME=$2
    PORT=$3
    STEP=$4
    
    load_image $SELF_IMG
    docker_stop_container $CONTAINER_NAME
    if [ -a docker/$SELF_IMG ]; then
        IMG=$SELF_IMG
    else
        IMG=$BASE_IMG
    fi
    CONTAINER_ID=$(docker run -itd \
           --volumes-from=$DB_CONTAINER_NAME \
           -v /tmp/logs:/tmp/logs \
           -p 6379:6379 \
           -p 127.0.0.1:$PORT:$PORT --name=$CONTAINER_NAME $IMG)

    docker exec -it $CONTAINER_NAME chown -R postgres:postgres /var/lib/container_pg
    docker exec -it $CONTAINER_NAME service postgresql restart

    make_or_run "user" $SELF_IMG $CONTAINER_NAME $CONTAINER_ID $STEP
}

function setup_user_server() {
    PORT=$1

    setup_nginx()
    # nginx
    if [ ! -r /etc/nginx/sites-available/users ]; then
        echo "(-) Creating Nginx Site..."
        cat > /etc/nginx/sites-available/users <<EOF
server {
    listen    $USR_ADDR;
    server_name    $USR_DOMAIN;
    location / {
        include uwsgi_params;
        uwsgi_pass 127.0.0.1:$PORT;
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
    SELF_IMG="user-image"
    CONTAINER_NAME="user"
    PORT=$(server_local_port user)
    STEP=$1

    if [ $STEP == 'make' ]; then
        prepare_user_image $SELF_IMG $CONTAINER_NAME $PORT $STEP
    elif [ $STEP == 'run' ]; then
        start_db_container
        prepare_user_image $SELF_IMG $CONTAINER_NAME $PORT $STEP
        setup_user_server $PORT
    else
        start_db_container
        prepare_user_image $SELF_IMG $CONTAINER_NAME $PORT
        setup_user_server $PORT
    fi
}

### finance ###

function prepare_finance_image() {
    SELF_IMG=$1
    CONTAINER_NAME=$2
    PORT=$3
    STEP=$4
    
    load_image $SELF_IMG
    docker_stop_container $CONTAINER_NAME
    if [ -a docker/$SELF_IMG ]; then
        IMG=$SELF_IMG
    else
        IMG=$BASE_IMG
    fi
    CONTAINER_ID=$(docker run -itd \
           --volumes-from=$DB_CONTAINER_NAME \
           -v /tmp/logs:/tmp/logs \
           -p 127.0.0.1:$PORT:$PORT --name=$CONTAINER_NAME $IMG)

    docker exec -it $CONTAINER_NAME chown -R postgres:postgres /var/lib/container_pg
    docker exec -it $CONTAINER_NAME service postgresql restart

    make_or_run "finance" $SELF_IMG $CONTAINER_NAME $CONTAINER_ID $STEP
}

function setup_finance_server() {
    PORT=$1

    setup_nginx()
    # nginx
    if [ ! -r /etc/nginx/sites-available/finance ]; then
        echo "(-) Creating Nginx Site..."
        cat > /etc/nginx/sites-available/finance <<EOF
server {
    listen    $FIN_ADDR;
    server_name    $FIN_DOMAIN;
    location / {
        include uwsgi_params;
        uwsgi_pass 127.0.0.1:$PORT;
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
    SELF_IMG="finance-image"
    CONTAINER_NAME="finance"
    PORT=$(server_local_port finance)
    STEP=$1

    if [ $STEP == 'make' ]; then
        prepare_finance_image $SELF_IMG $CONTAINER_NAME $PORT $STEP
    elif [ $STEP == 'run' ]; then
        start_db_container
        prepare_finance_image $SELF_IMG $CONTAINER_NAME $PORT $STEP
        setup_finance_server $PORT
    else
        start_db_container
        prepare_finance_image $SELF_IMG $CONTAINER_NAME $PORT
        setup_finance_server $PORT
    fi
}

function prepare_vessel_image() {
    SELF_IMG=$1
    CONTAINER_NAME=$2
    PORT=$3
    STEP=$4
    
    load_image $SELF_IMG
    docker_stop_container $CONTAINER_NAME
    if [ -a docker/$SELF_IMG ]; then
        IMG=$SELF_IMG
    else
        IMG=$BASE_IMG
    fi
    CONTAINER_ID=$(docker run -itd \
           --volumes-from=$DB_CONTAINER_NAME \
           -v /tmp/logs:/tmp/logs \
           -p 127.0.0.1:$PORT:$PORT --name=$CONTAINER_NAME $IMG)

    docker exec -it $CONTAINER_NAME chown -R postgres:postgres /var/lib/container_pg
    docker exec -it $CONTAINER_NAME service postgresql restart

    make_or_run "vessel" $SELF_IMG $CONTAINER_NAME $CONTAINER_ID $STEP
}

function setup_vessel_server() {
    PORT=$1

    setup_nginx()
    # nginx
    if [ ! -r /etc/nginx/sites-available/vessel ]; then
        echo "(-) Creating Nginx Site..."
        cat > /etc/nginx/sites-available/vessel <<EOF
server {
    listen    $VSL_ADDR;
    server_name    $VSL_DOMAIN;
    location / {
        include uwsgi_params;
        uwsgi_pass 127.0.0.1:$PORT;
        uwsgi_param SCRIPT_NAME '';
    }
}
EOF
        ln -s /etc/nginx/sites-available/vessel /etc/nginx/sites-enabled/
    else
        echo "(i) Nginx Server OK"
    fi
    service nginx restart
}

function deploy_vessel() {
    STEP=$1

    if [ -n $VSL_ADDR ]; then
        SELF_IMG="vessel-image"
        CONTAINER_NAME="vessel"
        PORT=$(server_local_port vessel)

        if [ $STEP == 'make' ]; then
            prepare_vessel_image $SELF_IMG $CONTAINER_NAME $PORT $STEP
        elif [ $STEP == 'run' ]; then
            start_db_container
            prepare_vessel_image $SELF_IMG $CONTAINER_NAME $PORT $STEP
            setup_vessel_server $PORT
        else
            start_db_container
            prepare_vessel_image $SELF_IMG $CONTAINER_NAME $PORT
            setup_vessel_server $PORT
        fi
    fi
}

function prepare_assets_image() {
    SELF_IMG=$1
    CONTAINER_NAME=$2
    PORT=$3
    STEP=$4
    
    load_image $SELF_IMG
    docker_stop_container $CONTAINER_NAME
    if [ -a docker/$SELF_IMG ]; then
        IMG=$SELF_IMG
    else
        IMG=$BASE_IMG
    fi
    CONTAINER_ID=$(docker run -itd \
           -v /tmp/logs:/tmp/logs \
           -v /var/local/assets:/var/local/assets \
           -p 127.0.0.1:$PORT:$PORT --name=$CONTAINER_NAME $IMG)

    make_or_run "assets" $SELF_IMG $CONTAINER_NAME $CONTAINER_ID $STEP
}

function setup_assets_server() {
    PORT=$1

    setup_nginx()
    # nginx
    if [ ! -r /etc/nginx/sites-available/assets ]; then
        echo "(-) Creating Nginx Site..."
        cat > /etc/nginx/sites-available/assets <<EOF
server {
    listen    $AST_ADDR;
    server_name    $AST_DOMAIN;
    location /img/ {
        alias /var/local/assets/assets_files/img/;
        autoindex off;
    }
    location /js/ {
        alias /var/local/assets/assets_files/js/;
        autoindex off;
    }
    location /css/ {
        alias /var/local/assets/assets_files/css/;
        autoindex off;
    }
    location /html/ {
        alias /var/local/assets/assets_files/html/;
        autoindex off;
    }
    location / {
        include uwsgi_params;
        uwsgi_pass 127.0.0.1:$PORT;
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
    SELF_IMG="assets-image"
    CONTAINER_NAME="assets"
    PORT=$(server_local_port assets)
    STEP=$1

    create_user
    create_assets_dir
    if [ $STEP == 'make' ]; then
        prepare_assets_image $SELF_IMG $CONTAINER_NAME $PORT $STEP
    elif [ $STEP == 'run' ]; then
        prepare_assets_image $SELF_IMG $CONTAINER_NAME $PORT $STEP
        setup_assets_server $PORT
    else
        prepare_assets_image $SELF_IMG $CONTAINER_NAME $PORT
        setup_assets_server $PORT
    fi
}

### front ###

function prepare_front_image() {
    PORT=$3
    BRAND=$4
    SELF_IMG=$4_$1
    CONTAINER_NAME=$4_$2
    STEP=$5
    if [ -z $STEP ]; then
        STEP=all
    fi
    
    load_image $SELF_IMG
    docker_stop_container $CONTAINER_NAME
    if [ -a docker/$SELF_IMG ]; then
        IMG=$SELF_IMG
    else
        IMG=$BASE_IMG
    fi
    CONTAINER_ID=$(docker run -itd \
           -v /tmp/logs:/tmp/logs \
           -v /var/local/assets:/var/local/assets \
           -p 127.0.0.1:$PORT:$PORT --name=$CONTAINER_NAME $IMG)

    make_or_run "front" $SELF_IMG $CONTAINER_NAME $CONTAINER_ID $STEP $BRAND
}

function setup_front_server() {
    PORT=$1
    SITE_NAME=$2_front
    SERVER_ADDR=$2_FRT_ADDR
    SERVER_ADDR=$(eval echo "\$${SERVER_ADDR}")
    SERVER_NAME=$2_FRT_DOMAIN
    SERVER_NAME=$(eval echo "\$${SERVER_NAME}")

    COIN_PROXY=''
    if [ $SITE_NAME == 'dragon_front' ]; then
        COIN_PROXY="
        location /coins/ {
            proxy_pass http://$DRAGON_BLOG_IP/;
            autoindex off;
        }"
    fi

    setup_nginx()
    # nginx
    if [ ! -r /etc/nginx/sites-available/$SITE_NAME ]; then
        echo "(-) Creating Nginx Site..."
        cat > /etc/nginx/sites-available/$SITE_NAME <<EOF
server {
    listen    $SERVER_ADDR;
    server_name    $SERVER_NAME;

    location /img/ {
        alias /var/local/assets/front_files/img/;
        autoindex off;
        expires 720h;
        add_header Pragma public;
        add_header Cache-Control "public, must-revalidate, proxy-revalidate";
    }
    location /js/ {
        alias /var/local/assets/front_files/js/;
        autoindex off;
        expires 720h;
        add_header Pragma public;
        add_header Cache-Control "public, must-revalidate, proxy-revalidate";
    }
    location /css/ {
        alias /var/local/assets/front_files/css/;
        autoindex off;
        expires 720h;
        add_header Pragma public;
        add_header Cache-Control "public, must-revalidate, proxy-revalidate";
    }
    location /templates/ {
        alias $CWD/front_$2/views/templates/;
        autoindex off;
        expires 720h;
        add_header Pragma public;
        add_header Cache-Control "public, must-revalidate, proxy-revalidate";
    }
    $COIN_PROXY
    location / {
        include uwsgi_params;
        uwsgi_pass 127.0.0.1:$PORT;
        uwsgi_param SCRIPT_NAME '';
    }
}
EOF
        ln -s /etc/nginx/sites-available/$SITE_NAME /etc/nginx/sites-enabled/
    else
        echo "(i) Nginx Server OK"
    fi

    sleep 1
    service nginx restart
}

function deploy_front() {
    BRAND=$1
    STEP=$2
    SELF_IMG="front-image"
    CONTAINER_NAME="front"
    PORT=$(server_local_port front $BRAND)

    create_user
    create_assets_dir
    if [ $STEP == 'make' ]; then
        prepare_front_image $SELF_IMG $CONTAINER_NAME $PORT $BRAND $STEP
    elif [ $STEP == 'run' ]; then
        prepare_front_image $SELF_IMG $CONTAINER_NAME $PORT $BRAND $STEP
        setup_front_server $PORT $BRAND
    else
        prepare_front_image $SELF_IMG $CONTAINER_NAME $PORT $BRAND
        setup_front_server $PORT $BRAND
    fi
}

function deploy_all_fronts() {
    if [ $breuer_FRT_ADDR != '' ]; then
        deploy_front "breuer" $1
    fi
    if [ $vessel_FRT_ADDR != '' ]; then
        deploy_front "vessel" $1
    fi
    if [ $dragon_FRT_ADDR != '' ]; then
        deploy_front "dragon" $1
    fi
}

########## main ##########
[ $1 ] || usage
case $1 in
        baseimage)
            docker_pull debian:wheezy
            make_image $BASE_IMG
            ;;

        db)
            start_db_container
            ;;

        backoffice)
            check_deploy_settings
            deploy_bo $2
            ;;
        
        user)
            check_deploy_settings
            deploy_user $2
            ;;
        
        finance)
            check_deploy_settings
            deploy_finance $2
            ;;
        
        vessel)
            check_deploy_settings
            deploy_vessel $2
            ;;
        
        assets)
            check_deploy_settings
            deploy_assets $2
            ;;

        front)
            check_deploy_settings
            deploy_all_fronts $2
            ;;

        everything)
            check_deploy_settings
            deploy_bo $2
            deploy_user $2
            deploy_finance $2
            deploy_assets $2
            deploy_vessel $2
            deploy_all_fronts $2
            ;;

        *)
            usage
            ;;
esac
