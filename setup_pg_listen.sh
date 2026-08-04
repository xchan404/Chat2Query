#!/bin/bash
sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/" /etc/postgresql/18/main/postgresql.conf
echo 'host all all 0.0.0.0/0 scram-sha-256' >> /etc/postgresql/18/main/pg_hba.conf
su - postgres -c "/usr/lib/postgresql/18/bin/pg_ctl -D /var/lib/postgresql/18/main restart"
