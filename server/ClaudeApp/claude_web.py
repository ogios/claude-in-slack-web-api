import gc
import json
import logging
import os.path
import re
import traceback
import math
import random
import time
import socket
import websocket
import uuid
import random
from threading import Thread
from websocket_server import WebsocketServer, WebSocketHandler

from ClaudeApp import XOXD

PATH = os.path.dirname(__file__)
with open(PATH + "/../../config.json", "r") as f:
	HOST = json.loads(f.read())["HOST"]


def dictToString(cookies: dict):
	cookie = ""
	for i in cookies:
		cookie += f"{i}={cookies[i]}; "
	return cookie


def try_port(port):
	"""获取可用的端口"""
	tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	try:
		tcp.bind(("", port))
		_, port = tcp.getsockname()
		tcp.close()
		return 1
	except Exception as e:
		print(e)
		return 0


def getRandomPort():
	while 1:
		port = random.randint(49152, 65535)
		if try_port(port):
			return port


def get_free_tcp_port():
	"""获取可用的端口"""
	tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	tcp.bind(("", 0))
	_, port = tcp.getsockname()
	tcp.close()
	return port


class WSOut:
	def __init__(self, xoxd: XOXD, email: str, claudeApp, port: int = None):
		self.IP_PORT: int = port if port != None else getRandomPort()
		self.IP_ADDR: str = "0.0.0.0"
		self.email: str = email
		self.xoxd: XOXD = xoxd
		self.claudeApp = claudeApp
		self.server: WebsocketServer = None
		self.message_list = []
		
		self.step = None
		Thread(target=self._sendMessage, daemon=True).start()
	
	def failureRequest(self, handler: WebSocketHandler, status=None, msg=None, type=""):
		data = {
			"ok": False,
			"status": status,
			"msg": msg,
			"type": type
		}
		handler.send_message(json.dumps(data, ensure_ascii=False))
	
	def successRequest(self, handler: WebSocketHandler, status=None, msg=None, type=""):
		data = {
			"ok": True,
			"status": status,
			"msg": msg,
			"type": type
		}
		handler.send_message(json.dumps(data, ensure_ascii=False))
	
	def checkIfLogin(self, client: dict, server: WebsocketServer, js):
		if js["msg"] != None:
			ok = self.xoxd.Login_init()
			if ok:
				self.successRequest(
					handler=client["handler"],
					msg="",
					type="checkIfLogin",
				)
				self.step = "checkIfLogin"
			else:
				self.failureRequest(
					handler=client["handler"],
					msg="Some thing went wrong!",
					type="checkIfLogin",
				)
		else:
			self.failureRequest(
				handler=client["handler"],
				msg="no message received",
				type="checkIfLogin",
			)
	
	def sendCode(self, client: dict, server: WebsocketServer, js):
		code: str = js["msg"].replace("-", "")
		if code and len(code) == 6:
			ok = self.xoxd.Login_sendCode(code.upper())
			if ok == 0:
				self.failureRequest(
					handler=client["handler"],
					msg="some thing went wrong!",
					type="sendCode",
				)
			else:
				self.successRequest(
					handler=client["handler"],
					msg="",
					type="sendCode",
				)
				self.step = "sendCode"
		else:
			self.failureRequest(
				handler=client["handler"],
				msg="wrong code format, the code should be 6 or 7 uppercase!",
				type="sendCode",
			)
	
	def getTeamList(self, client: dict, server: WebsocketServer, js):
		teamlist = self.xoxd.teamlist
		
		self.successRequest(
			handler=client["handler"],
			msg=json.dumps(teamlist) if isinstance(teamlist, list) else None,
			type="getTeamList",
		)
	
	def selectTeam(self, client: dict, server: WebsocketServer, js):
		if isinstance(js["msg"], int):
			ok = self.xoxd.Login_selTeam(js["msg"])
			if ok:
				ok = self.xoxd.Login_getDAndSave()
				if ok:
					self.successRequest(
						handler=client["handler"],
						msg="",
						type="selectTeam",
					)
					self.step = "done"
					self.claudeApp.connect()
				else:
					self.failureRequest(
						handler=client["handler"],
						msg="Get d cookie and api_token fatal!",
						type="selectTeam",
					)
			else:
				self.failureRequest(
					handler=client["handler"],
					msg="Some thing went wrong!",
					type="selectTeam",
				)
		else:
			self.failureRequest(
				handler=client["handler"],
				msg="no message received or wrong input format!",
				type="selectTeam",
			)
	
	def startWebsocketServer(self):
		def on_open(client: dict, server: WebsocketServer):
			if self.xoxd.done:
				self.successRequest(
					handler=client["handler"],
					msg="slack login success.",
					type="slackLogin",
				)
			else:
				self.successRequest(
					handler=client["handler"],
					msg="slack isn't online.",
					type="slackLogin",
				)
		
		def on_message(client: dict, server: WebsocketServer, msg):
			print("recv_text=" + msg)
			js = json.loads(msg)
			if js["type"] == "checkIfLogin":
				if js["msg"]:
					self.xoxd.getEnv()
					self.step = "done"
				else:
					self.checkIfLogin(client, server, js)
			elif js["type"] == "sendCode":
				self.sendCode(client, server, js)
			elif js["type"] == "getTeamList":
				self.getTeamList(client, server, js)
			elif js["type"] == "selectTeam":
				self.selectTeam(client, server, js)
		
		# match js["type"]:
		# 	case "checkIfLogin":
		# 		if js["msg"]:
		# 			self.xoxd.getEnv()
		# 			self.step = "done"
		# 		else:
		# 			self.checkIfLogin(client, server, js)
		# 	case "sendCode":
		# 		self.sendCode(client, server, js)
		# 	case "getTeamList":
		# 		self.getTeamList(client, server, js)
		# 	case "selectTeam":
		# 		self.selectTeam(client, server, js)
		
		server = WebsocketServer(host=self.IP_ADDR, port=self.IP_PORT, loglevel=logging.INFO)
		
		server.set_fn_new_client(on_open)
		server.set_fn_message_received(on_message)
		self.server = server
		self.server.run_forever()
		self.server.server_close()
	
	def _sendMessage(self):
		while 1:
			if self.server:
				if len(self.server.clients) > 0:
					while len(self.message_list) > 0:
						self.server.send_message_to_all(self.message_list[0])
						del self.message_list[0]
			time.sleep(0.01)
	
	def sendMessage(self, status, msg, user):
		data = {
			"type": "text",
			"status": status,
			"msg": msg,
			"user": user,
		}
		self.message_list.append(json.dumps(data, ensure_ascii=False))
	
	# try:
	# 	self.server.send_message_to_all(json.dumps(data, ensure_ascii=False))
	# 	return 1
	# except:
	# 	return 0
	
	def sendError(self, status=None, msg=None):
		data = {
			"type": "error",
			"status": status,
			"msg": msg,
		}
		self.message_list.append(json.dumps(data, ensure_ascii=False))
	# try:
	# 	self.server.send_message_to_all(json.dumps(data, ensure_ascii=False))
	# except:
	# 	traceback.print_exc()


class ClaudeApp:
	def __init__(self, email, port=None):
		self.email = email
		self.app_id = None
		self.conversaion_id = None
		self.xoxd = XOXD.XOXD(self.email)
		self.sessionID = self.initSessionID()
		self.wss_primary: websocket.WebSocketApp = None
		self.wss_on: bool = False
		self.WSOut: WSOut = WSOut(self.xoxd, self.email, self, port)
		self.wss_redirect: str = None
	
	def getUUID(self):
		'''
		随机生成对话标识id
		:return: uuid的十六进制配上8-4-4-4-12的分隔
		'''
		uid = uuid.uuid4().hex
		return f"{uid[:8]}-{uid[8:12]}-{uid[12:16]}-{uid[16:20]}-{uid[20:]}"
	
	def initSessionID(self, length=11):
		Z = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
		x = ""
		for q in range(length - 1):
			x += Z[math.floor(random.random() * 64)]
		x += Z[math.floor(random.random() * 64) & 60]
		return x
	
	def getBootData(self):
		'''
		获取初始信息
		:return: dict(初始工作区以及个人信息)
		'''
		url = "https://aueco.slack.com/api/client.boot"
		params = {
			"_x_id": f"noversion-{str(time.time)[:-4]}",
			"_x_version_ts": "noversion",
			"_x_gantry": "true",
			"fp": "80",
		}
		data = {
			"token": self.xoxd.api_token,
			"version": "5",
			"_x_reason": "initial-data",
			"include_min_version_bump_check": 1,
			"version_ts": int(time.time()),
			"build_version_ts": int(time.time()),
			"_x_sonic": True,
		}
		res = self.xoxd.reqPost(url, params=params, data=data)
		return res.json()
	
	def matchClaude(self, js: dict):
		'''
		从工作区中匹配出claude的app对应信息
		:param js:
		:return:
		'''
		user_ids = {}
		app_ids = {}
		for i in js["ims"]:
			user_ids[i["user"]] = i["id"]
		for i in js["app_homes"]:
			app_ids[i["conversation_id"]] = i["app_id"]
		
		url = f"https://edgeapi.slack.com/cache/{self.xoxd.teamID}/users/info"
		params = {
			"fp": 80
		}
		data = {
			"check_interaction": True,
			"include_profile_only_users": True,
			"token": self.xoxd.api_token,
			"updated_ids": {}
		}
		for i in user_ids:
			data["updated_ids"][i] = 0
		data = json.dumps(data)
		res = self.xoxd.reqPost(url, data=data, params=params)
		js = res.json()
		for i in js["results"]:
			if i["name"] == "claude":
				self.conversaion_id = user_ids[i["id"]]
				self.user_bot_id = i["id"]
				self.app_id = app_ids[self.conversaion_id]
				return 1
		return 0
	
	def getHistory(self):
		url = "https://aueco.slack.com/api/conversations.history"
		params = {
			"_x_id": f"09d906bc-{str(time.time)[:-4]}",
			"_x_version_ts": int(time.time()),
			"fp": "30",
			"_x_csid": self.sessionID,
			"slack_route": self.xoxd.teamID,
			"_x_gantry": "true",
		}
		data = {
			"token": self.xoxd.api_token,
			"channel": self.conversaion_id,
			"limit": 50,
			"ignore_replies": True,
			"include_pin_count": True,
			"inclusive": True,
			"no_user_profile": True,
			"include_stories": True,
			"_x_reason": True,
			"_x_mode": True,
			"_x_sonic": True,
		}
		res = self.xoxd.reqPost(url, params=params, data=data)
	
	def createWSSConnection(self):
		
		def on_open(wsapp):
			self.wss_on = True
			
			def ping(wsapp):
				sid = 16385
				while 1:
					time.sleep(30)
					wsapp.send(json.dumps({"type": "ping", "id": sid}))
					sid += 1
			
			Thread(target=ping, args=(wsapp,), daemon=True).start()
		
		def on_message(wsapp, data):
			logging.info(data)
			try:
				data = re.sub("\n\n", r"\\n\\n", data)
				js = json.loads(data)
				if js["type"] == "error":
					self.wss_on = False
					raise Exception(f"wss connection lost: {data}")
				elif js["type"] == "message":
					if js.__contains__("message"):
						message = js["message"]
					else:
						message = js
					if message["user"] == self.xoxd.user_id:
						self.WSOut.sendMessage(
							# email=self.email,
							status=True,
							msg=message["text"],
							user="user",
						)
					if message.__contains__("app_id"):
						if message["app_id"] == self.app_id:
							status = False
							check = message["blocks"][0]["elements"][-1]["elements"][-1]
							if check["text"] != "Typing…" and check["text"] != r"Typing\u2026" and check[
								"text"] != "Typing\u2026":
								status = True
							self.WSOut.sendMessage(
								# email=self.email,
								status=status,
								msg=message["text"],
								user="claude",
							)
			except:
				traceback.print_exc()
				print(data)
		
		def on_close(wsapp, close_status_code, close_reason):
			self.wss_on = False
			print("on_close", close_status_code, close_reason, sep=",")
		
		url = "wss://wss-primary.slack.com/?"
		url += f"token={self.xoxd.api_token}&"
		url += f"sync_desync=1&"
		url += f"slack_client=desktop&"
		url += f"start_args=%3Fagent%3Dclient%26org_wide_aware%3Dtrue%26agent_version%3D1683947252%26eac_cache_ts%3Dtrue%26cache_ts%3D0%26name_tagging%3Dtrue%26only_self_subteams%3Dtrue%26connect_only%3Dtrue%26ms_latest%3Dtrue&"
		url += f"no_query_on_subscribe=1&"
		url += f"flannel=3&"
		url += f"lazy_channels=1&"
		url += f"gateway_server={self.xoxd.teamID}-5&"
		url += f"batch_presence_aware=1"
		
		self.wss_primary = websocket.WebSocketApp(
			url=url,
			cookie=dictToString(self.xoxd.cookies.get_dict()),
			on_close=on_close,
			on_message=on_message,
			on_open=on_open,
		)
		
		Thread(target=self.wss_primary.run_forever, daemon=True).start()
	
	def execCmd(self, cmd):
		url = "https://aueco.slack.com/api/chat.command"
		params = {
			"_x_id": f"badfe8bf-{str(time.time)[:-4]}",
			"_x_version_ts": int(time.time()),
			"fp": "80",
			"_x_csid": self.sessionID,
			"slack_route": self.xoxd.teamID,
			"_x_gantry": "true",
		}
		data = {
			"token": self.xoxd.api_token,
			"command": cmd,
			"disp": cmd,
			"channel": self.conversaion_id,
			"client_token": f"web-{int(time.time() * 1000)}",
			"_x_reason": "executeCommand",
			"_x_mode": "online",
			"_x_sonic": "true",
		}
		res = self.xoxd.reqPost(url, params=params, data=data)
		js = res.json()
		if js["ok"]:
			return 1
		else:
			return 0
	
	def sendMessage(self, text):
		url = "https://aueco.slack.com/api/chat.postMessage"
		params = {
			"_x_id": f"badfe8bf-{str(time.time)[:-4]}",
			"_x_version_ts": int(time.time()),
			"fp": "80",
			"_x_csid": self.sessionID,
			"slack_route": self.xoxd.teamID,
			"_x_gantry": "true",
		}
		draft_id = self.initSessionID(length=12)
		data = {
			"token": self.xoxd.api_token,
			"ts": f"{int(time.time())}.xxxxx3",
			"type": "message",
			"_x_reason": "webapp_message_send",
			"_x_mode": "online",
			"_x_sonic": "true",
			"channel": self.conversaion_id,
			"xArgs": json.dumps({
				"draft_id": f"{draft_id}",
			}),
			"unfurl": "[]",
			"blocks": json.dumps([{
				"type": "rich_text",
				"elements": [{
					"type": "rich_text_section",
					"elements": [{
						"type": "text",
						"text": text,
					}]
				}]
			}], ensure_ascii=False),
			"draft_id": draft_id,
			"include_channel_perm_error": True,
			"client_msg_id": self.getUUID(),
		}
		res = self.xoxd.reqPost(url, params=params, data=data)
		js = res.json()
		if js["ok"]:
			return js
		else:
			return 0
	
	def checkAuth(self) -> bool:
		boot_data = self.getBootData()
		if boot_data["ok"] == False and boot_data.__contains__("error"):
			return False
		gc.collect()
		return True
	
	def connect(self) -> int:
		boot_data = self.getBootData()
		if boot_data["ok"] == False and boot_data.__contains__("error"):
			if boot_data["error"] == "not_authed":
				logging.info(f"user {self.email}'s authorization has expired")
				return 2
			return 0
		
		self.matchClaude(boot_data)
		self.createWSSConnection()
		self.wss_on = True
		return 1
	
	@staticmethod
	def createApp(email, port=None):
		claude = ClaudeApp(email, port)
		Thread(target=claude.WSOut.startWebsocketServer, daemon=True).start()
		url = f"ws://{HOST}:{claude.WSOut.IP_PORT}"
		return url, claude


if __name__ == "__main__":
	pass
