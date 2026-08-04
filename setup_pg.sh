sed -i 's/port = 5432/port = 5433/' /etc/postgresql/18/main/postgresql.conf
service postgresql start
su - postgres -c "psql -c \"CREATE USER platform_user WITH PASSWORD 'platform_pass';\""
su - postgres -c "psql -c \"CREATE DATABASE platform OWNER platform_user;\""
