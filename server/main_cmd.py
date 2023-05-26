from ClaudeApp.claude_web import ClaudeApp
from websocket import WebSocketApp
from threading import Thread
import json
import time
import sys

email = ""
flag = False  # wait for reply


# print message
def updateMsg(js):
	global flag
	status = js["status"]  # status stands for whether the message complete or still generating.
	msg = js["msg"]  # message it self with 'Typing...'.
	user = js["user"]  # whether this message is sent by user or claude.
	if status:
		print(f"({user}): {msg}")
		if user == "claude":
			flag = False


# parse response
def on_message(wsapp, data):
	data = json.loads(data)
	type = data["type"]
	if type == "text":
		updateMsg(data)
	elif type == "error":
		print("error occurred: ", data["msg"])
	# match type:
	# 	case "text":
	# 		updateMsg(data)
	# 	case "error":
	# 		print("error occurred: ", data["msg"])


# create ClaudeApp and connect to WebSocketServer
print(f"Using email: {email}")
while not email:
	email = input("empty email, please provide one: ")
url, claude = ClaudeApp.createApp(email)
wsa = WebSocketApp(url, on_message=on_message)
Thread(target=wsa.run_forever, daemon=True).start()


# login if not authorized
def login(claude: ClaudeApp) -> int:
	if claude.xoxd.Login_init():  # init and send code to your email
		code = input("verification code: ")
		if claude.xoxd.Login_sendCode(code):  # input code and get cookies
			teamlist = claude.xoxd.teamlist  # select teams from team list
			string = ""
			for i in range(len(teamlist)):
				string += str(i) + ". workspace - " + teamlist[i]['name'] + "\n"
			string += "choose your work space (index): "
			while 1:
				try:
					option = int(input(string))  # choose a team by input the index of it
					if 0 <= option <= len(teamlist) - 1:
						break
				except:
					pass
			if claude.xoxd.Login_selTeam(option):  # choose team and get login url
				if claude.xoxd.Login_getDAndSave():  # get cookies and api-token through login url
					return 1
	return 0


if claude.xoxd.checkEnv():  # check if the account has been logged in before
	claude.xoxd.getEnv()  # load the cookies and profiles from saved files
if not claude.checkAuth():  # check if the current account has the authorization to send request
	while 1:
		option = input("Not Authorized, login? (y/n)").lower()
		if option == "y" or option == "yes":
			if not login(claude):  # login
				print("login fatal")
				sys.exit()
			else:
				print("done.")
				break
		elif option == "n" or option == "no":
			sys.exit()
		else:
			print("only y or n")
		# match option:
		# 	case "y" | "yes":
		# 		if not login(claude):  # login
		# 			print("login fatal")
		# 			sys.exit()
		# 		else:
		# 			print("done.")
		# 			break
		# 	case "n" | "no":
		# 		sys.exit()
		# 	case _:
		# 		print("only y or n")
claude.connect()  # automatically match the channel which have claude and connect to slack wss when it's done
while 1:
	text = input(">>>")
	flag = True
	claude.sendMessage(text)
	while flag:  # wait for the reply
		time.sleep(1)
