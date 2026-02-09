NEW_PASSWORD_FILE="new_passwords.txt"
PASSWORD_FILE="passwords.txt"
encrypted_file="passwords.txt,gpg"
gpg_decrypt="gpg --batch -d"
CIPHER="--cipher-algo AES256"
USERNAME="fc"
HOST_FILE="hosts.txt"
KEY=$(vlt secrets get --plaintext key)
VLT_App=ssh
VLT_Project_ID=07b41797-230a-4453-a336-f3a428a4009a
VLT_Organization_ID=35c7e423-60c7-4406-a179-ffb1dc2af82b
# Encrypt the new password file only if it exists and is newer than the encrypted file
if [ -f "$NEW_PASSWORD_FILE" ] && [ "$NEW_PASSWORD_FILE" -nt "$encrypted_file" ]; then
    gpg --batch "${CIPHER}" --encrypt "$NEW_PASSWORD_FILE" --passphrase "$KEY" -o "$encrypted_file"
    rm "$NEW_PASSWORD_FILE"
fi
#gpg --batch  --encrypt passwords.txt --cipher-algo AES256 --passphrase "${KEY}" > "${encrypted_file}"
[ ! -f ${PASSWORD_FILE} ] && gpg -c --batch  ${CIPHER} --passphrase "${KEY}" "${encrypted_file}"|tee ${PASSWORD_FILE}
