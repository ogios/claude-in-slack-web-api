import json
import logging
from threading import Thread
import fastapi
from fastapi import Body, Request

from ClaudeApp.claude_web import ClaudeApp
from fastapi.middleware.cors import CORSMiddleware

logging.getLogger().setLevel(logging.INFO)

app = fastapi.FastAPI()
app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"]
)

sessions: dict[str:dict[str:str, str:ClaudeApp]] = {}


@app.get("/check")
def check(email: str):
	data = {}
	if sessions.__contains__(email):
		logging.info(f"{email} - return claude from sessions")
		data["ok"] = True
		data["url"] = sessions[email]["url"],
		data["next_step"] = sessions[email]["claude"].xoxd.next_step
		data["env"] = sessions[email]["claude"].xoxd.checkEnv()
	# status = sessions[email]["status"]
	else:
		logging.info(f"{email} - create claude using email login!")
		(url, claudeApp) = ClaudeApp.createApp(email, None)
		sessions[email] = {
			"url": url,
			"claude": claudeApp,
			# "status": status,
		}
		data["ok"] = True
		data["url"] = sessions[email]["url"],
		data["next_step"] = sessions[email]["claude"].xoxd.next_step
		data["env"] = sessions[email]["claude"].xoxd.checkEnv()
	
	return json.dumps(data, ensure_ascii=False)


@app.post("/postMessage")
async def postMessage(js: dict):
	if not js.__contains__("email") or not js.__contains__("text"):
		data = {
			"ok": False,
			"msg": "no email or text provided",
		}
		return json.dumps(data, ensure_ascii=False)
	email = js["email"]
	text = js["text"]
	try:
		sessions[email]["claude"].sendMessage(text)
		return json.dumps({"ok": True}, ensure_ascii=False)
	except Exception as e:
		return json.dumps({"ok": False, "msg": e}, ensure_ascii=False)


@app.post("/login")
async def login(type: str, step: str, js: dict):
	if not js.__contains__("email"):
		return json.dumps({"ok": False, "msg": "no email provided"}, ensure_ascii=False)
	email = js['email']
	if not sessions.__contains__(email):
		return json.dumps({"ok": False, "msg": "no claude app created in sessions"}, ensure_ascii=False)
	if type == "email":
		claude: ClaudeApp = sessions[email]["claude"]
		if step == "init":
			ok = claude.xoxd.Login_init()
		elif step == "sendCode":
			if not js.__contains__("code"):
				return json.dumps({"ok": False, "msg": "No code provided"}, ensure_ascii=False)
			code = js["code"]
			ok = claude.xoxd.Login_sendCode(code)
		elif step == "selectTeam":
			if not js.__contains__("option"):
				return json.dumps({"ok": False, "msg": "No option provided"}, ensure_ascii=False)
			option = js["option"]
			ok = claude.xoxd.Login_selTeam(option)
		elif step == "getDAndSave":
			ok = claude.xoxd.Login_getDAndSave()
		else:
			return json.dumps({"ok": False, "msg": "wrong step"}, ensure_ascii=False)

		# match step:
		# 	case "init":
		# 		ok = claude.xoxd.Login_init()
		# 	case "sendCode":
		# 		if not js.__contains__("code"):
		# 			return json.dumps({"ok": False, "msg": "No code provided"}, ensure_ascii=False)
		# 		code = js["code"]
		# 		ok = claude.xoxd.Login_sendCode(code)
		# 	case "selectTeam":
		# 		if not js.__contains__("option"):
		# 			return json.dumps({"ok": False, "msg": "No option provided"}, ensure_ascii=False)
		# 		option = js["option"]
		# 		ok = claude.xoxd.Login_selTeam(option)
		# 	case "getDAndSave":
		# 		ok = claude.xoxd.Login_getDAndSave()
		# 	case _:
		# 		return json.dumps({"ok": False, "msg": "wrong step"}, ensure_ascii=False)
		if ok:
			data = {"ok": True, "next_step": claude.xoxd.next_step}
			return json.dumps(data, ensure_ascii=False)
		else:
			return json.dumps({"ok": False, "msg": "Unknown error"}, ensure_ascii=False)


@app.get("/env")
async def env(email: str):
	if not sessions.__contains__(email):
		return json.dumps(
			{"ok": False, "msg": "no claude app in sessions, send GET request to /check to connect to claude app"},
			ensure_ascii=False)
	claude: ClaudeApp = sessions[email]["claude"]
	if claude.xoxd.next_step == "done":
		return json.dumps({"ok": True, "msg": "successfully loaded the env", "auth": True}, ensure_ascii=False)
	if claude.xoxd.checkEnv():
		claude.xoxd.getEnv()
		auth = claude.checkAuth()
		return json.dumps({"ok": True, "msg": "successfully loaded the env", "auth": auth}, ensure_ascii=False)
	else:
		return json.dumps({"ok": False, "msg": "No env can be referred to this account"}, ensure_ascii=False)


@app.get("/getTeamList")
async def getTeamList(email: str):
	if not sessions.__contains__(email):
		return json.dumps(
			{
				"ok": False,
				"msg": "no claude app in sessions, send GET request to url '/check' to connect to claude app"
			},
			ensure_ascii=False
		)
	claude: ClaudeApp = sessions[email]["claude"]
	teamlist = claude.xoxd.teamlist
	return json.dumps(teamlist, ensure_ascii=False)


@app.get("/connect")
async def connect(email: str):
	if not sessions.__contains__(email):
		return json.dumps(
			{"ok": False, "msg": "no claude app in sessions, send GET request to /check to connect to claude app"},
			ensure_ascii=False)
	claude: ClaudeApp = sessions[email]["claude"]
	if claude.wss_on:
		return json.dumps(
			{"ok": True, "msg": "already open"},
			ensure_ascii=False)
	else:
		status = claude.connect()
		if status == 1:
			return json.dumps({
				"ok": True,
				"msg": "connected",
			}, ensure_ascii=False)
		else:
			return json.dumps({
				"ok": False,
				"msg": "connect fatal"
			})

@app.get("/execCmd")
async def execCmd(email: str, cmd: str):
	if not sessions.__contains__(email):
		return json.dumps(
			{"ok": False, "msg": "no claude app in sessions, send GET request to /check to connect to claude app"},
			ensure_ascii=False)
	claude: ClaudeApp = sessions[email]["claude"]
	ok = claude.execCmd(cmd)
	if ok:
		return json.dumps({
			"ok": True,
			"msg": "cmd executed"
		}, ensure_ascii=False)
	else:
		return json.dumps({
			"ok": False,
			"msg": "something went wrong"
		})


if __name__ == "__main__":
	import uvicorn
	
	uvicorn.run(app, host="0.0.0.0", port=80)
