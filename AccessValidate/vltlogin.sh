#!/bin/bash

# Check if X environment is available
if [ -z "$DISPLAY" ]; then
  echo "No X environment detected. Installing LastPass CLI and links..."

  # Check if lastpass-cli is installed
  if ! command -v lpass &>/dev/null; then
    echo "lastpass-cli not found. Installing..."
    sudo apt-get install lastpass-cli -y
    echo "lastpass-cli installed."
  fi

  # Check if links is installed
  if ! command -v links &>/dev/null; then
    echo "links not found. Installing..."
    sudo apt-get install links -y
    echo "links installed."
  fi

# Continue with the rest of your script
# Log in to LastPass CLI, set passwords, etc.

export vlt_pass=$(lpass show --password "https://flow.idp.hashicorp.com/")
export vlt_project=8be7d7b2-0151-4cad-a879-8423014c110e
#  HCP_ORGANIZATION         HCP Organization (ID or Name) that the app is in
export VLT_APPLICATION_NAME=ssh
#  HCP_CLIENT_ID            HCP client ID used for headless login
#  HCP_CLIENT_SECRET        HCP client secret used for headless login

# Set "links" as the default browser
sudo update-alternatives --set x-www-browser /usr/bin/links

# Log in to Vault using vlt login
vlt login

# Set Firefox as the default browser
sudo update-alternatives --set x-www-browser /usr/bin/firefox
fi

# Log in to the LastPass CLI
# Add your LastPass CLI login command here

# Set password for a specific URL
