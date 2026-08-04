#!/bin/bash
su - postgres -c "/usr/lib/postgresql/18/bin/pg_ctl -D /var/lib/postgresql/18/main -l /tmp/pg.log start"
sleep 2
su - postgres -c "psql -p 5433 -c \"CREATE USER platform_user WITH PASSWORD 'platform_pass';\""
su - postgres -c "psql -p 5433 -c \"CREATE DATABASE platform OWNER platform_user;\""
