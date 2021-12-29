# dequa-telegram-bot
A telegram bot for dequa services

# Get it to run

## As python script ()
Simply run
```
python3 dequa_bot.py
```
And check that everything works as expected

## As service

##### Edit the .service file
Edit the `dequa-bot.service` file. Most likely you need to change
- `WorkingDirectory` (line 13): find it using the `pwd` command on linux
- `ExecStart` (line 14): find python using `which python` and the path to where you saved the python file, the full path to `/dequa-telegram-bot/dequa_bot.py`
- `ExecStop` (line 15): find pkill using `which pkill` and copy the full path (sometimes pkill alone is not working)
- `StandardOutput` and `StandardError` (line 21 and 22): change the fulll path to something existing on your server

##### Launch the service
First, reload the daemon system (it may require `sudo`, but not sure)
```
systemctl daemon-reload
```
and then start the service (also here same with `sudo`)
```
systemctl start dequa-bot.service
```
If it does not say anything, it worked! Otherwise check errors.
Use
```
systemctl status dequa-bot.service
```
to check the status.
