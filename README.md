# -schrodinger
Tracks the time spent on the MAC.

it does so by tracking:

- screen On/Off
- Startup
- Shutdown

It's written in python and uses few plist to trigger the scripts.

## Demo
[![asciicast](https://asciinema.org/a/lUJejik5apHJIA8wI8H9S98K0.svg)](https://asciinema.org/a/lUJejik5apHJIA8wI8H9S98K0)


## Install
The script to create the files (`status.py`) is in python2, compatible with python3
the `show.py` script is python3 only

### For collecting data:

- Clone this repo
- Configure the `config.py` file copying `config_base.py`, set the folder where you want the data of the day stored (I store them in dropbox), use the full path. This can be any folder. we call it `DATA FOLDER`

- Install sleepwatcher `brew install sleepwatcher` (install (brew services first)[https://superuser.com/questions/1075956/homebrew-installed-sleepwatcher-wanted-to-run-suggested-service-command-got])
- copy the `com.stefanotranquillini.sleepwatcher.plist` to `~/Library/LaunchAgent`
- edit the `plist` file changing `<FULL PATH TO YOUR HOME FOLDER>` to the path of your `HOME FOLDER`
- Copy `.wakeup` and `.sleep` to your `HOME FOLDER`
- edit the two files and set `<FULL PATH TO YOUR PROJECT FOLDER>` to the path where the repository is cloned `PROJECT FOLDER`
- run the command in the `~/Library/LaunchAgent` `launchctl load com.stefanotranquillini.sleepwatcher.plist`

- copy the `com.stefanotranquillini.shutdown.plist` to `~/Library/LaunchAgent`
- edit the `plist` file changing `<FULL PATH TO YOUR HOME FOLDER>` to the path of your `HOME FOLDER`
- Copy `.shutdown`  to your `HOME FOLDER`
- edit the file and set `<FULL PATH TO YOUR PROJECT FOLDER>` to the path where the repository is cloned `PROJECT FOLDER`
- run the command in the `~/Library/LaunchAgent` `sudo launchctl load -w me.stefanotranquillini.shutdown.plist` (note the `sudo` and `-w`)

Now, every time your screen sleeps or you start/shutdown the MAC you will find an entry in a file in the `DATA FOLDER`. The file has `YYYYMMDD` as name.

### For displaying the data

- install the `requirements.txt`
- launch `python show.py` (you can make an alias, it's handy)

the parameters are the following:

- `-a`: prints all the day that are found in the `DATA FOLDER`
- `-m`: the interval in minute, default is `5` for small terminal use `10` or more
- `-d`: the day to print, in the form of `YYYYMMDD` if not specified, it's `today`
- `-v`: enable the `verbose version`, works only for single day (not with the `-a`)
- `-b`: the hour from where the printing start (default `8`)
- `-e`: the hour till the print ends (default: `20`)
