# CLaude-in-slack web api

English | [中文](README_zh.md)

> Recently I found that claude can not be installed into slack anymore due to high demand.
> Maybe releasing this script now is a bit late.

This project is for study purposes only, if you just want claude-in-slack's API, slack_sdk is a pretty good option.

## Structure
图片

## Login for the first time
图片

## Saved login status
Every time after a successful login, the cookies, api-token, user_id, team_id will be saved into a json file named by your email.
use `checkEnv()` to see if it's been saved and use `getEnv()` to load it.

## Usage
Please check this for how to use it:  
[Claude in command line](server/main_cmd.py)

And there's a web server version i made:  
[Claude in FastAPI](server/main_fastapi.py)

## Chat

### Create a ClaudeApp
After a ClaudeApp is created using `createApp()`, it creates a WebSocketServer and returns a websocket url and a ClaudeApp which hasn't been connected to the slack.

### Login or load login status
For now, it only supports email login, which requires a verification code, the way to login by password may be supported soon.

For email logins, each login process will take place in XOXD.py:
```python
xoxd.Login_init()
xoxd.Login_sendCode(code)

teamlist = xoxd.teamlist
option = teamlist[index] # choose a team

xoxd.Login_selTeam(option)
xoxd.Login_getDAndSave()
```
After this, the login status will be saved.

### Match channel and connect to wss
use `connect()` in ClaudeApp, this will automatically match the channel that claude is in and connect to the wss that slack provides

### chat
use `postMessage` to send a message to claude, and every chat message will be received through wss and then parse and forward to WebSocketServer.

## Execute cmd
Claude only has one command `/reset`, but i manage to make a function for that just in case it updates some new commands.

To do it, you just have to call the function under the ClaudeApp `execCmd(cmd)`, the command will be sent and if it's "reset", it will be noticed in wss.

## Chat Histories
I got the API but I haven't done anything to it, haven't figured out how to write it. the responses depend on timestamp and fp(i set it to 30), it returns a maximum of 30 messages before the specific timestamp.

you can try to do it on your own, the function refers to it is in `ClaudeApp.getHistory()`
