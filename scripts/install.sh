#!/bin/bash
# echo "installing brew services"
# brew tap homebrew/services
# brew install sleepwatcher

# echo "install script"
PRJ="$(dirname "$PWD")"
# place the script in the home with correct folder
sed -e "s@\${PRJ}@$PRJ@"  shutdown.tmpl > $HOME/.shutdown
chmod +x $HOME/.shutdown
sed -e "s@\${PRJ}@$PRJ@"  sleep.tmpl > $HOME/.sleep
chmod +x $HOME/.sleep
sed -e "s@\${PRJ}@$PRJ@"  wakeup.tmpl > $HOME/.wakeup
chmod +x $HOME/.wakeup
# place the plist
echo "Install plist"
sed -e "s@\${HOME}@$HOME@"  com.stefanotranquillini.sleepwatcher.plist.tmpl > $HOME/Library/LaunchAgents/com.stefanotranquillini.sleepwatcher.plist
launchctl load -w $HOME/Library/LaunchAgents/com.stefanotranquillini.sleepwatcher.plist
sed -e "s@\${HOME}@$HOME@"  com.stefanotranquillini.login.plist.tmpl > $HOME/Library/LaunchAgents/com.stefanotranquillini.login.plist
launchctl load -w $HOME/Library/LaunchAgents/com.stefanotranquillini.login.plist
# place the plist in shared folder and as a root
sudo sh -c 'sed -e "s@\${HOME}@$HOME@" com.stefanotranquillini.shutdown.plist.tmpl > /Library/LaunchDaemons/com.stefanotranquillini.shutdown.plist'
sleep 1
sudo chown root:wheel /Library/LaunchDaemons/com.stefanotranquillini.shutdown.plist
sudo launchctl load -w /Library/LaunchDaemons/com.stefanotranquillini.shutdown.plist
DATA="${1:-$PRJ}"
echo $DATA
sudo sed -e "s@\${DATA}@$DATA@"  config.tmpl > $PRJ/config.py
echo "Testing the script"
$HOME/.wakeup
python3 $PRJ/show.py
