# CLaude in slack api from slack web

English | [中文](README_zh.md)

> Since claude2 is free to use, this script may not be useful and will not be updated.

**Since the claude will not be available for free slack workspaces, this repo may not be updated anymore**

After several tests on my server, i've fixed most of the bugs and convert 'match' to 'elif', it now works just fine.
please let me know if there's something wrong on your computer.

This project is for study purposes only, if you just want claude-in-slack's API, then slack_sdk would be a pretty good option.

## Structure
**This graph may not be professional but i hope it makes it much easier for you to understand the code**
![架构_英文](https://github.com/ogios/claude-in-slack-web-api/assets/96933655/e31c33a8-8bb4-4fe2-802d-1c6008681cc0)


## Login for the first time
**This graph may not be professional but i hope it makes it much easier for you to understand the code**
![流程_英文](https://github.com/ogios/claude-in-slack-web-api/assets/96933655/8a346be2-eeb8-4d3d-a165-73890073530f)


## Saved login status
Every time after a successful login, the cookies, api-token, user_id, team_id will be saved into a json file named by your email.
use `checkEnv()` to see if it's been saved and use `getEnv()` to load it.

## Usage

Setup fastapi and nodejs server's host and port in config.json:
```
{
  "HOST": "fastapi server's host, default to 127.0.0.1",
  "API_PORT": fastapi server's port, default to 8011,
  "WEB_PORT": nodejs server's port, default to 80
}
```
and if you decides to use the vue app in `web_vue/claude_vue` remember to change the `baseurl` in `config.js` 

and run this to start the nodejs server:
```shell
// static html
$ node ./web/index.js

// vue3
$ cd ./web_vue/claude_vue
$ serve 
```
fastapi server:
```shell
$ pip3 install -r requirements.txt
$ python3 ./server/main_fastapi.py
```


Here's another version that provides a command-line usage:  
[Claude in command line](server/main_cmd.py)


## Chat

### Create a ClaudeApp
After a ClaudeApp is created using `createApp()`, it will setup a WebSocketServer and returns the websocket url and a ClaudeApp which hasn't been connected to the slack.

### Login or load login status
For now, it only supports email login, which requires a verification code, login by password may be supported soon.

For email login, each login process will take place in XOXD.py:
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
use `connect()` in ClaudeApp, this will automatically match the channel which claude is in and connect to the wss that slack provides

### chat
use `postMessage` to send a message to claude. Every chat message will be received through wss and then be parsed and forward to WebSocketServer.

## Execute cmd
Claude has only one command `/reset`, but i manage to make a function for that just in case it updates some new commands.

To do it, you just have to call the function under the ClaudeApp `execCmd(cmd)`, if it's "/reset", it will be noticed in wss.

## Chat Histories
I got the API but I haven't done anything to it, haven't figured out how to write it. the responses depend on timestamp and fp(i set it to 30), it returns a maximum of 30 messages which happens before a specific timestamp.

you can try to do it on your own, the function is `ClaudeApp.getHistory()`.
