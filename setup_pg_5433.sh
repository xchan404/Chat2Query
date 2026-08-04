#!/bin/bash
sed -i "s/#port = 5432/port = 5433/" /etc/postgresql/18/main/postgresql.conf
sed -i "s/port = 5432/port = 5433/" /etc/postgresql/18/main/postgresql.conf
su - postgres -c "/usr/lib/postgresql/18/bin/pg_ctl -D /var/lib/postgresql/18/main restart"
sleep 2
su - postgres -c "psql -p 5433 -c \"CREATE USER platform_user WITH SUPERUSER PASSWORD 'platform_pass';\""
su - postgres -c "psql -p 5433 -c \"CREATE DATABASE platform OWNER platform_user;\""
