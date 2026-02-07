#!/bin/bash

# Exit on any error
set -e

# Step a: Install Zabbix repository
wget https://repo.zabbix.com/zabbix/6.4/ubuntu/pool/main/z/zabbix-release/zabbix-release_6.4-1+ubuntu22.04_all.deb
dpkg -i zabbix-release_6.4-1+ubuntu22.04_all.deb
apt update

# Step b: Install Zabbix server, frontend, agent
apt install zabbix-server-mysql zabbix-frontend-php zabbix-apache-conf zabbix-sql-scripts zabbix-agent

# Step c: Create initial database
# Ensure you have PostgreSQL installed and running before executing these commands
sudo -u postgres createuser --pwprompt zabbix
sudo -u postgres createdb -O zabbix zabbix

# Import initial schema and data
zcat /usr/share/zabbix-sql-scripts/postgresql/server.sql.gz | sudo -u zabbix psql zabbix

# Step d: Configure the database for Zabbix server
# Replace 'password' with your actual database password
echo "DBPassword=password" >> /etc/zabbix/zabbix_server.conf
apt install mysql-server
systemctl start mysql
# MySQL root password
MYSQL_ROOT_PASS

# Exit on any error
set -e

# Step a: Install Zabbix repository
wget https://repo.zabbix.com/zabbix/6.4/ubuntu/pool/main/z/zabbix-release/zabbix-release_6.4-1+ubuntu22.04_all.deb
dpkg -i zabbix-release_6.4-1+ubuntu22.04_all.deb
apt update

# Step b: Install Zabbix server, frontend, agent
apt install zabbix-server-mysql zabbix-frontend-php zabbix-apache-conf zabbix-sql-scripts zabbix-agent

# Step c: Create initial database
# Ensure you have PostgreSQL installed and running before executing these commands
sudo -u postgres createuser --pwprompt zabbix
sudo -u postgres createdb -O zabbix zabbix

# Import initial schema and data
zcat /usr/share/zabbix-sql-scripts/postgresql/server.sql.gz | sudo -u zabbix psql zabbix

# Step d: Configure the database for Zabbix server
# Replace 'password' with your actual database password
echo "DBPassword=password" >> /etc/zabbix/zabbix_server.conf
apt install mysql-server
systemctl start mysql
# MySQL root password
MYSQL_ROOT_PASSWORD='password'

# MySQL Zabbix user password
ZABBIX_USER_PASSWORD='password'

# Command to log into MySQL and execute commands
#mysqlql -uroot -p$MYSQL_ROOT_PASSWORD <<EOF
#create database zabbix character set utf8mb4 collate utf8mb4_bin;
mysql -uroot  <<EOF
create user zabbix@localhost identified by '$ZABBIX_USER_PASSWORD';
grant all privileges on zabbix.* to zabbix@localhost;
set global log_bin_trust_function_creators = 1;
EOF

echo "Zabbix MySQL setup is complete."

# Step e: Configure PHP for Zabbix frontend
#  and set 'listen' and 'server_name' in /etc/zabbix/nginx.conf
# This step requires manual editing, example:

# Backup the current nginx.conf file
cp /etc/zabbix/nginx.conf /tmp/nginx.conf.backup

# Prepend new settings to nginx.conf
echo -e "# New settings\nlisten 8080;\nserver_name zabbix.vigilent.com;\n$(cat /tmp/nginx.conf.backup)" | sudo tee /etc/zabbix/nginx.conf > /dev/null


echo "Zabbix installation is complete. Please review and finalize your Nginx and Zabbix server configurations as needed."

# Step f: Start Zabbix server and agent processes
systemctl restart zabbix-server zabbix-agent nginx php8.1-fpm
systemctl enable zabbix-server zabbix-agent nginx php8.1-fpm

echo "Zabbix installation is complete. PlWORD='password'

# MySQL Zabbix user password
ZABBIX_USER_PASSWORD='password'

# Command to log into MySQL and execute commands
#mysqlql -uroot -p$MYSQL_ROOT_PASSWORD <<EOF
#create database zabbix character set utf8mb4 collate utf8mb4_bin;
mysql -uroot  <<EOF
create user zabbix@localhost identified by '$ZABBIX_USER_PASSWORD';
grant all privileges on zabbix.* to zabbix@localhost;
set global log_bin_trust_function_creators = 1;
EOF

echo "Zabbix MySQL setup is complete."

# Step e: Configure PHP for Zabbix frontend
#  and set 'listen' and 'server_name' in /etc/zabbix/nginx.conf
# This step requires manual editing, example:

# Backup the current nginx.conf file
cp /etc/zabbix/nginx.conf /tmp/nginx.conf.backup

# Prepend new settings to nginx.conf
echo -e "# New settings\nlisten 8080;\nserver_name zabbix.vigilent.com;\n$(cat /tmp/nginx.conf.backup)" | sudo tee /etc/zabbix/nginx.conf > /dev/null


echo "Zabbix installation is complete. Please review and finalize your Nginx and Zabbix server configurations as needed."

# Step f: Start Zabbix server and agent processes
systemctl restart zabbix-server zabbix-agent nginx php8.1-fpm
systemctl enable zabbix-server zabbix-agent nginx php8.1-fpm

echo "Zabbix installation is complete. Please configure your Nginx and Zabbix server as needed."
