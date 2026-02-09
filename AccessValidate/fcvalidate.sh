#!/bin/bash
source config.sh

hydra -W 1 -t 1 -l "${USERNAME}" -P "${PASSWORD_FILE}"  -M "${HOST_FILE}" ssh  -o HydraResults
rm -rf "${PASSWORD_FILE}"
# gpg --passphrase "${KEY}" passwords.txt > passwords.txt.gpg
#gpg --passphrase "${KEY}" --output decrypted_file.txt --decrypt encrypted_file.gpg
# Loop through each server in the hosts file
#while read -r host; do
## Loop through each password in the password file
#  while read -r PASSWORD; do
#      # Use sshpass to attempt login
#      # Install with `sudo apt-get install sshpass` on Debian/Ubuntu
#      # or `sudo yum install sshpass` on Red Hat/CentOS
#      sshpass -p "`vlt secrets get --plaintext key`" ssh -o StrictHostKeyChecking=no -o PreferredAuthentications=password -l "$USERNAME" localhost exit &>/dev/null
#
#      if [ $? -eq 0 ]; then
#          echo "Login successful with password: $PASSWORD"
#      else
#          echo "Login failed with password: $PASSWORD"
#      fi
#    done < "$PASSWORD_FILE"
#  done < "$HOST_FILE"
