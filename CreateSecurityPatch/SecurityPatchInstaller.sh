# V 0.5 Alpha
# Create a patch from unattended-upgrades security patches
# This does not need to get deployed to production only needs to live on the patch generator

current_date="$(date +%Y%m%d)"
#sudo apt update || {  echo "apt update failed,  to Create user fc and set password and enable sudo check this script comments" }
# If already_downloaded is not = true, run apt-get install unattended-upgrades

if [ ! $(which unattended-upgrade) ]; then
  sudo apt-get install unattended-upgrades -y
  sudo dpkg-reconfigure unattended-upgrades
fi
sudo cp upgrade.conf /etc/apt/apt.conf.d/50unattended-upgrades

sudo apt clean
# count the number of .deb files in /var/cache/apt/archives
num_deb_files=$(find /var/cache/apt/archives -xdev -name "*.deb" | wc -l)
# exit if there are any .deb files in /var/cache/apt/archives
upgrades=$(apt-get -s --download-only upgrade|grep Inst|wc -l)
if [ "$upgrades" -gt 0 ]; then
  echo "There are ${upgrades} available"
else
  echo "No upgrades available. Exiting..."
  exit 1
fi
if [ "$num_deb_files" -gt 0 ]; then
  echo "There are security patches  /var/cache/apt/archives"
  echo "Exiting..."
  exit 1
fi

sudo unattended-upgrade --download-only
find /var/cache/apt/archives -xdev -name "*.deb">/var/tmp/$$.patchlist
num_deb_files=$(cat /var/tmp/$$.patchlist|wc -l)
if [ "$num_deb_files" -eq 0 ]; then
  echo "There are no .deb files in /var/cache/apt/archives"
  echo "Exiting..."
  exit 1
else
  echo ".deb files in /var/cache/apt/archives"
  cat /var/tmp/$$.patchlist
fi
sudo dpkg -i /var/tmp/$$.patchlist
rm /var/tmp/$$.patchlist
