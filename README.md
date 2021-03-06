# -schrodinger
Tracks the time spent on the MAC.

it does so by tracking:

- screen On/Off
- Startup (same as screen on)
- Shutdown (specific command)

It's written in python and uses few plist to trigger the scripts.

## log
the new version also manages logs, so you can log your activity in a semi-autoamted way, check log.py (with `-t` `-s` options)

## Demo
[![asciicast](https://asciinema.org/a/294226.svg)](https://asciinema.org/a/294226)

## Install
The script to create the files (`status.py`) is in python2, compatible with python3
the `show.py` script is python3 only

### For collecting data:

- Clone this repo
- go to `scripts`
- `chmod +x install.sh`
- run `bash install.sh` (optionally specify the folder where the data must be stored, such as a dropbox folder)
- it will ask for root password at some point
<!-- - Configure the `config.py` file copying `config_base.py`, set the folder where you want the data of the day stored (I store them in dropbox), use the full path. This can be any folder. we call it `DATA FOLDER`

- Install sleepwatcher `brew install sleepwatcher` (install (brew services first)[hp])
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

Now, every time your screen sleeps or you start/shutdown the MAC you will find an entry in a file in the `DATA FOLDER`. The file has `YYYYMMDD` as name. -->

### For logging data
- launch `python3 log.py` (you can make an alias)

the parameters are the following:

- `-s`: how many mitues ago it started
- `-t`: when it started (hh:mm)
- `--last`: use as description the previous status (eg: you did `writing` then `lunch` with --last it stores `writing`. It ignores `-` status)

Note: status starting with `-` will be set as `sleep`

### For displaying the data

- install the `requirements.txt`
- launch `python3 show.py` (you can make an alias)

the parameters are the following:

- `-a`: prints all the day that are found in the `DATA FOLDER`
- `-m`: the interval in minute, default is `5` for small terminal use `10` or more
- `-d`: the day to print, in the form of `YYYYMMDD` if not specified, it's `today`
- `-v`: enable the `verbose version`, works only for single day (not with the `-a`)
- `-b`: the hour from where the printing start (default `8`)
- `-e`: the hour till the print ends (default: `20`)
- `-dh`: Do NOT show the detail per hour
- `-dc`: Do NOT show the detail per category
- `-l`: Print detail of the daily log to be easily copied.
- `--cron`:  cron notification for OSX