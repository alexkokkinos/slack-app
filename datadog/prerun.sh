#!/usr/bin/env bash

# Update the Postgres configuration from above using the Heroku application environment variable
sed -i "s/<YOUR HOSTNAME>/${DATABASE_HOST}/" "$DD_CONF_DIR/conf.d/postgres.d/conf.yaml"
sed -i "s/<YOUR USERNAME>/$DATABASE_USER}/" "$DD_CONF_DIR/conf.d/postgres.d/conf.yaml"
sed -i "s/<YOUR PASSWORD>/${DATABASE_PASSWORD}/" "$DD_CONF_DIR/conf.d/postgres.d/conf.yaml"
sed -i "s/<YOUR PORT>/${DATABASE_PORT}/" "$DD_CONF_DIR/conf.d/postgres.d/conf.yaml"
sed -i "s/<YOUR DBNAME>/${DATABASE_DBNAME}/" "$DD_CONF_DIR/conf.d/postgres.d/conf.yaml"
