import logging
import requests


class Request:
	def __init__(self):
		self.headers = {
			"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36 Edg/113.0.1774.42",
			"x-forwarded-for": "4.2.2.2",
		}
		self.proxies = {
			"http": "http://127.0.0.1:7890",
			"https": "http://127.0.0.1:7890",
		}
	
	def reqPost(self, url, cookies, data=None, params=None, allow_redirects=True):
		for _ in range(3):
			try:
				res = requests.post(
					url,
					headers=self.headers,
					cookies=cookies,
					# proxies=self.proxies,
					data=data,
					params=params,
					allow_redirects=allow_redirects
				)
				return res
			except Exception as e:
				logging.error(e)
		raise Exception("requests fatal")
	
	def reqGet(self, url, cookies, params=None, allow_redirects=True):
		for _ in range(3):
			try:
				res = requests.get(
					url,
					headers=self.headers,
					cookies=cookies,
					params=params,
					allow_redirects=allow_redirects,
				)
				return res
			except Exception as e:
				logging.error(e)
		raise Exception("requests fatal")
