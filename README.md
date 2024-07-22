# Sticknet Engine

Backend system for [Sticknet](https://github.com/sticknet/sticknet-mobile) built using Django.

## Mobile app

You can find Sticknet's mobile apps and main repo [here](https://github.com/sticknet/sticknet-mobile).

## Contributing

### Prerequisites

- Python (>= Python 3.8)
- PostgreSQL (>= 14)

### Setup

1. Git clone: `git clone git@github.com:sticknet/sticknet-engine.git && cd sticknet-engine`
2. Create virtual environment: `python3 -m venv env && source env/bin/activate`
3. Install pip modules: `pip3 install -r requirements.txt`
4. Create local database: `psql` then `CREATE DATABASE sticknet;` then `exit`
5. Run database migrations: `python ./src/manage.py migrate`
6. Run server: `python ./src/manage.py runserver`

### Testing

- Run tests: `cd test_src && python ../src/manage.py test`

### Connect sticknet-mobile to local server

When running sticknet-mobile it will be communicating with the remote server. To connect sticknet-mobile to a local
server, follow these steps:

1. Find the ipv4 address of your machine, or
   run: `ipv4=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -n 1)`
2. Start server using the ipv4 address: `python ./src/manage.py runserver "$ipv4:8000"`
3. Under 'sticknet-mobile/src/actions/URL.ts' edit `URL` to be `http://$ipv4:8000` where `$ipv4` is your ipv4 address
4. If running on android, add your ipv4 to the
   file `sticknet-mobile/android/app/src/main/res/xml/network_security_config.xml`

## Other repos:

1. Mobile apps: [Sticknet mobile](https://github.com/sticknet/sticknet-mobile)
2. Web app: [Sticknet web](https://github.com/sticknet/sticknet-web)
3. End-to-end encryption protocol: [Stick protocol](https://github.com/sticknet/stick-protocl)

## Contact Us

You can email us as at contact@sticknet.org
