# CLaude-in-slack 网页端接口
> 最近发现claude-in-slack不再提供加入到slack里，去官网看了一下原因貌似是太多需求  
> 现在发出来这个脚本是不是有些太晚了

在我自己的服务器上测试了许多遍之后，暂时没什么问题了，把python3.10的'match'语法也改成了elif，如果使用上还有什么问题，请告知我

这个项目仅以学习为目的，如果有使用claude的需求可以直接使用slack_sdk连接claude app

## 项目结构
**这张图画的可能并不专业，但我希望它可以帮助你更好的了解我写的代码**
![架构_中文](https://github.com/ogios/claude-in-slack-web-api/assets/96933655/a86a0dce-4f0a-46d5-91f1-4666252ce4f0)



## 第一次登录与对话流程
**这张图画的可能并不专业，但我希望它可以帮助你更好的了解我写的代码**
![流程_中文](https://github.com/ogios/claude-in-slack-web-api/assets/96933655/151e92ca-4035-4c17-80f0-55d26b859d53)



## 保存登录状态
每次登陆成功之后，cookies、api-token、user_id、team_id这些信息会被保存在json文件中，文件名为邮箱名
使用 `checkEnv()` 方法保存登录状态，使用 `getEnv()` 保存加载。

## 使用方法
在config.json文件中设置fastapi server的地址和端口：
```
{
  "HOST": "fastapi的host, 默认 127.0.0.1",
  "API_PORT": fastapi的端口, 默认 8011,
  "WEB_PORT": nodejs的端口, 默认 80
}
```
如果你想使用我用vue写的web的话，记得在 `web_vue/claude_vue/config.js` 里修改 `baseurl`


运行下面的命令来运行nodejs server
```shell
// static html
$ node ./web/index.js

// vue3
$ cd ./web_vue/claude_vue
$ serve 
```
fastapi:
```shell
$ pip3 install -r requirements.txt
$ python3 ./server/main_fastapi.py
```

这是写的另外一个版本，在命令行中提供对话的版本：
[Claude in command line](server/main_cmd.py)


## 聊天

### 创建ClaudeApp
在使用 `createApp()` 创建ClaudeApp之后会创建一个WebSocketServer并返回其url和还未连接至slack的ClaudeApp本身

### 登录或加载登录状态
暂时只支持使用邮箱验证码登录，密码登录功能可能会在以后的某一天加上

对邮箱登录的来说，所有流程都在XOXD.py中
```python
xoxd.Login_init()
xoxd.Login_sendCode(code)

teamlist = xoxd.teamlist
option = teamlist[index] # choose a team

xoxd.Login_selTeam(option)
xoxd.Login_getDAndSave()
```
登陆成功之后，登录状态会被保存

### 自动查找channel并连接wss
使用创建好的ClaudeApp中的 `connect()`, 这个方法会自动匹配有claude的channel然后连接slack提供的wss连接 

### 对话
使用 `postMessage` 发送信息，每条信息会从wss连接中返回，并通过先前创建好的WebSocketServer向所有已连接的web端转发信息

## 执行命令
现在的claude只有一个命令，清空对话记忆，但是我设置了一个通用的以防止它以后新增加别的命令

通过调用ClaudeApp下面的 `execCmd()` 方法来执行命令，例如reset，清除记忆的通知会在wss中接收

## 历史对话记录
接口找到了，但是还没做解析，没想好该怎么写这个逻辑，它是按时间戳和返回对话条数来的，在给定时间戳之前的最大几条数据会被返回，我设置的是30条

如果有需求可以自行尝试解析，方法是ClaudeApp里的 `getHistory()`
