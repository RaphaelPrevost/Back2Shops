## Create the dev environment:

0. Install Bitname Django stack:

   Mysql password: backtoshops
   Create a mysql user "backtoshops" and give it the password "backtoshops"

1. PIP and virtualenv are 2 required Python packages. To install them, run in the terminal installed by the django stack:

    easy_install pip virtualenv

2. Get the repository:

    git clone git@moonstrap.com:backtoshops.git

3. Go in the repository folder:

    cd backtoshops

4. Create the virtual environment:

    virtualenv --no-site-packages backtoshops-env

5. Activate the virtual environment:

    python backtoshops-env/bin/activate_this.py

6. Install required packages for BTS:

    pip -E backtoshops-env install -r requirements/apps.txt

7. Run the virutal environment:

    source backtoshops-env/bin/activate

8. Install the DB:

    cd backtoshops
    ./manage.py syncdb
    ./manage.py migrate

9. Import the fixtures:

    ./manage.py loaddata sale/fixtures.json

10. Run the serveur:

    ./manage.py runserver
