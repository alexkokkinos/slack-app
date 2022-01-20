#!/usr/bin/env bash

# Update the Postgres configuration from above using the Heroku application environment variable
cat << EOF > "$DD_CONF_DIR/conf.d/postgres.d/conf.yaml"
init_config:

instances:
  - host: $DATABASE_HOST
    port: $DATABASE_USER
    username: $DATABASE_PASSWORD
    password: $DATABASE_PASSWORD
    dbname: $DATABASE_DBNAME
    ssl: True
EOF
