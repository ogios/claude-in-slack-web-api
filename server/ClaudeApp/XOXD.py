import json
import os
import re
import time
import traceback

import requests
import requests.utils

from ClaudeApp import Request


class XOXD:
	def __init__(self, email) -> None:
		self.email = email
		self.env_path = os.path.dirname(__file__) + "/env"
		if not os.path.exists(self.env_path):
			os.mkdir(self.env_path)
		self.env_file_path = self.env_path + f"/env_{self.email}.json"
		self.cookies: requests.sessions.RequestsCookieJar = requests.utils.cookiejar_from_dict({})
		self.Request = Request.Request()
		self.teamID = None
		self.api_token = None
		self.user_id = None
		self.done = False
		
		self.url_redirect = None
		self.teamlist = None
		
		self.next_step = "init"
	
	def saveEnv(self):
		with open(self.env_file_path, "w") as f:
			js = {
				"teamID": self.teamID,
				"api_token": self.api_token,
				"cookies": self.cookies.get_dict(),
				"user_id": self.user_id,
			}
			f.write(json.dumps(js))
			self.done = True
	
	def getEnv(self):
		with open(self.env_file_path, "r") as f:
			js = json.loads(f.read())
			self.teamID = js["teamID"]
			self.api_token = js["api_token"]
			self.cookies = requests.utils.cookiejar_from_dict(js["cookies"])
			self.user_id = js["user_id"]
			self.done = True
	
	def refreshCookies(self, cookies):
		cookies = cookies.get_dict()
		for i in cookies:
			self.cookies.set(i, cookies[i])
	
	def reqPost(self, url, data=None, params=None, allow_redirects=True):
		res = self.Request.reqPost(url, params=params, data=data, allow_redirects=allow_redirects, cookies=self.cookies)
		self.refreshCookies(res.cookies)
		return res
	
	def reqGet(self, url, params=None, allow_redirects=True):
		res = self.Request.reqGet(url, params=params, allow_redirects=allow_redirects, cookies=self.cookies)
		self.refreshCookies(res.cookies)
		return res
	
	def sendCode(self):
		# 发送code
		print("正在获取验证码...")
		url_send_email = f"https://slack.com/api/signup.confirmEmail?_x_id=noversion-{str(time.time())[:-4]}"
		data = {
			"email": self.email,
			"locale": "zh-CN",
		}
		res = self.reqPost(url_send_email, data=data)
		js = res.json()
		if js["ok"]:
			print("done.")
		else:
			raise Exception(f"发送有误: {js}")
	
	def getVisitorID(self):
		print("正在获取visitor_id...")
		url_get_visitor_id = "https://pi.pardot.com/analytics"
		params = {
			"ver": "3",
			"visitor_id": "",
			"visitor_id_sign": "",
			"pi_opt_in": "",
			"campaign_id": "2520",
			"account_id": "756253",
			"title": "登录 | Slack",
			"url": "https://slack.com/signin#/confirmemail",
			"referrer": "https://slack.com/",
		}
		
		res = self.reqGet(url_get_visitor_id, params=params)
		cookies: dict = self.cookies.get_dict()
		for i in cookies:
			if "visitor_id" in i:
				print("done.")
				return
		raise Exception(f"get visitor_id fatal: {self.cookies}")
	
	def putCode(self, code):
		print("正在发送验证码...")
		code = code.replace("-", "")
		url_confrim_code = f"https://slack.com/api/signin.confirmCode?_x_id=noversion-{str(time.time)[:-4]}"
		data = {
			"email": "jhx16901690@gmail.com",
			"code": code
		}
		res = self.reqPost(url_confrim_code, data=data)
		cookies: dict = self.cookies.get_dict()
		for i in cookies:
			if "ec" in i:
				print("done.")
				return
		raise Exception(f"get ec cookie fatal: {self.cookies}\n{res.text}")
	
	def getLoginUrl(self):
		# 获取登录链接
		print("正在获取登录链接...")
		url_get_login_url = "https://slack.com/api/signin.findWorkspaces"
		params = {
			"_x_id": f"noversion-{str(time.time)[:-4]}",
			"slack_route": "T00000000",
			"_x_version_ts": "no-version",
			"fp": "80",
		}
		data = {
			"commingled_response": False,
			"ssb_signin": False,
			"_x_reason": "get_started_workspaces",
			"_x_mode": "online",
		}
		
		res = self.reqPost(url_get_login_url, params=params, data=data)
		js = res.json()
		if js["ok"]:
			print("done.")
		return js
	
	def getD(self, location):
		print("正在获取xoxd...")
		print("初始url(带工作区名):", location)
		res = self.reqGet(location, allow_redirects=False)
		location = res.headers.get("location")
		print("重定向url(app-redir)", location)
		res = self.reqGet(location, allow_redirects=False)
		location = res.headers.get("location")
		print("获取d的url", location)
		res = self.reqGet(location, allow_redirects=False)
		location = res.headers.get("location")
		print("checkcookie的url", location)
		res = self.reqGet(location, allow_redirects=False)
		location = res.headers.get("location")
		print("ssb与api-token的url", location)
		res = self.reqGet(location, allow_redirects=False)
		self.api_token = re.findall('api_token":"(.*?)",', res.text)[0]
		self.user_id = re.findall('"user_id":"(.*?)"', res.text)[0]
		
		cookies: dict = self.cookies.get_dict()
		for i in cookies:
			if i == "d":
				print("done.")
				return
		raise Exception(f"get d cookie fatal: {self.cookies}")
	
	def parseLoginData(self, js: dict):
		url_redirect = js["redirect_url"]
		currentteams = js["current_teams"]
		return (url_redirect, currentteams)
	
	def reload(self):
		if os.path.exists(self.env_file_path):
			os.remove(self.env_file_path)
		self.main()
	
	def checkEnv(self):
		if os.path.exists(self.env_file_path):
			return True
		else:
			return False
	
	def Login_init(self) -> int:
		"""
		first step to login (send email code and get visitor_id cookie)
		:return: Bool
		"""
		try:
			self.sendCode()
			self.getVisitorID()
			self.next_step = "sendCode"
			return 1
		except:
			traceback.print_exc()
			return 0
	
	def Login_sendCode(self, code: str) -> int:
		"""
		send code that has been sent to your email.
		:param code: (String) code in your email.
		:return: list of teams that you're in.
		"""
		try:
			self.putCode(code)
			js = self.getLoginUrl()
			(url_redirect, currentteams) = self.parseLoginData(js)
			self.url_redirect = url_redirect
			teamlist = []
			for currentteam in currentteams:
				teams = currentteam["teams"]
				for i in range(len(teams)):
					# print(f"{i}. 工作区 - {teams[i]['name']}")
					teamlist.append({
						"name": teams[i]['name'],
						"id": teams[i]["id"],
					})
			self.teamlist = teamlist
			self.next_step = "selectTeam"
			return 1
		except:
			traceback.print_exc()
			return 0
	
	def Login_selTeam(self, option: int) -> int:
		"""
		select team what team you want to go.
		:param option: team's index in list.
		:return: Bool
		"""
		try:
			# option = int(input("数字>>>"))
			self.teamID = self.teamlist[option]["id"]
			self.next_step = "getDAndSave"
			return 1
		except:
			traceback.print_exc()
			return 0
	
	def Login_getDAndSave(self):
		"""
		get cookie and api_token then save to env.
		:return: Bool
		"""
		try:
			self.getD(self.url_redirect)
			self.saveEnv()
			self.next_step = "done"
			return 1
		except:
			traceback.print_exc()
			return 0
	
	def main(self):
		if os.path.exists(self.env_file_path):
			while 1:
				option = input("检测到存在已建立的环境，是否使用使用该环境？(y/n)").lower()
				if option == "y":
					self.getEnv()
					return
				elif option == "n":
					break
				else:
					continue
		self.sendCode()
		self.getVisitorID()
		while 1:
			code = input("请输入验证码>>>").replace("-", "")
			if code and len(code) == 6:
				break
		self.putCode(code)
		js = self.getLoginUrl()
		(url_redirect, currentteams) = self.parseLoginData(js)
		teamlist = []
		for currentteam in currentteams:
			teams = currentteam["teams"]
			for i in range(len(teams)):
				print(f"{i}. 工作区 - {teams[i]['name']}")
				teamlist.append({
					"name": teams[i]['name'],
					"id": teams[i]["id"],
				})
		while 1:
			try:
				option = int(input("数字>>>"))
				self.teamID = teamlist[option]["id"]
				break
			except:
				continue
		self.getD(url_redirect)
		self.saveEnv()


if __name__ == "__main__":
	email = ""
	xoxd = XOXD(email)
	xoxd.main()
	print(xoxd)
