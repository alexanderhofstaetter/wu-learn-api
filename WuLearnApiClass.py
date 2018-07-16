#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests, dill, sys, base64, datetime, re, os, time, hashlib, pickle
from lxml import html
from datetime import timedelta
from dateutil import parser
from bs4 import BeautifulSoup

class WuLearnApi():

	URL = "https://learn.wu.ac.at"
	LOGIN_URL = URL + "/register/"
	headers = {
		'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:60.0) Gecko/20100101 Firefox/60.0',
		'referer': LOGIN_URL,
		'Accept-Encoding': 'utf-8'
	}
	sessionfile = "%s.bin"
	sessiontimeout = "2"

	def __init__(self, username=None, password=None, tor="false", sessiondir=None, new_session=None):
		self.username = username
		self.password = password
		self.matr_nr = username[1:]

		self.sessiondir = sessiondir
		self.new_session = new_session

		self.data = {}
		self.status = {}
		self.session = requests.session()
		self.session.hooks['response'].append(self.response_hook)

		if sessiondir:
			self.sessionfile = sessiondir + self.sessionfile % username
		else:
			self.sessionfile = "sessions/" + self.sessionfile % username

		if (tor == "true"):
			self.session.proxies = {}
			self.session.proxies['http'] = 'socks5://localhost:9050'
			self.session.proxies['https'] = 'socks5://localhost:9050'
		self.auth()

	def response_hook(self, r, *args, **kwargs):
		soup = BeautifulSoup(r.content.decode('utf-8', 'ignore'), 'html.parser')
		if soup.find("a", string="Abmelden") or "application/pdf" in r.headers['Content-Type']:
			self.status["logged_in"] = True
			self.status["last_logged_in"] = datetime.datetime.now()
			self.save_session()
		else:
			self.status["logged_in"] = False
		self.status["last_url"] = r.url
		self.status["last_method"] = r.request.method
		return r


	def auth(self):
		if self.load_session() and self.new_session != "true" and self.status["last_logged_in"] >= datetime.datetime.now()-timedelta(hours=int(self.sessiontimeout)):
			self.status["loaded_session_valid"] = True
		else:
			self.status["loaded_session_valid"] = False
			self.login()


	def clear_session(self):
		self.session.cookies.clear()
		if os.path.isfile(self.sessionfile):
			os.remove(self.sessionfile)
		return True
				

	def save_session(self):
		if not os.path.exists(os.path.dirname(self.sessionfile)):
			try:
				os.makedirs(os.path.dirname(self.sessionfile))
			except:
				if exc.errno != errno.EEXIST:
					raise
		with open(self.sessionfile, 'wb') as f:
			try:
				dill.dump([self.session, self.status], f)	
			except:
				return False
		return True


	def load_session(self):
		if os.path.isfile(self.sessionfile):
			with open(self.sessionfile, 'rb') as f:
				try:
					self.session, self.status = dill.load(f)
				except:
					return False
			return True


	def login(self):
		payload = self.loginpayload()
		self.data = {}
		self.session.post(self.LOGIN_URL, data = payload, headers = self.headers, allow_redirects=False)


	def loginpayload(self):
		self.clear_session()
		r = self.session.get(self.LOGIN_URL, headers = self.headers)
		tree = html.fromstring(r.text)
		self.data = {
			"username": self.username, 
			"password": self.password, 
			"form:mode": "edit", 
			"form:id": "login", 
			"return_url": "/",
			"time": list(set(tree.xpath("//input[@name='time']/@value")))[0],
			"token_id": list(set(tree.xpath("//input[@name='token_id']/@value")))[0],
			"hash": list(set(tree.xpath("//input[@name='hash']/@value")))[0],
		}
		return self.data


	def exams(self):
		self.exams = {}

		examlist = None;
		while examlist == None:
			r = self.session.get(self.URL + "/einsicht/", headers = self.headers)
			examlist = BeautifulSoup(r.content.decode('utf-8', 'ignore'), 'html.parser').find('table', {"class" : "list-table"}).find('tbody').find_all('tr')

		for i, entry in enumerate( [item for item in examlist if item.select('td[headers="exams_result_available"]')[0].text.strip() == "Ja"] ):
			self.exams[i] = {}

			self.exams[i]["date"] = entry.select('td[headers="exams_datum"]')[0].text.strip()
			self.exams[i]["title"] = entry.select('td[headers="exams_exam_title"]')[0].text.strip()
			self.exams[i]["number"] = entry.select('td[headers="exams_exam_title"] b a')[0]["href"][9:]

			if (i == 0):
				payload = {
					"matr_nr": self.matr_nr, 
					"password": self.password, 
					"form:mode": "edit", 
					"form:id": "confirmation",
					"id": self.exams[i]["number"]
				}
				self.session.post(self.URL + "/einsicht/index?id=" + self.exams[i]["number"], data = payload, headers = self.headers)
			r = self.session.get(self.URL + "/einsicht/file.pdf?id=" + self.exams[i]["number"] + "&matr_nr=" + self.matr_nr, headers = self.headers)

			self.exams[i]["pdf"] = base64.b64encode(r.content)

		self.data = self.exams
		return self.data


	def meta(self):
		self.meta = {}

		r = self.session.get(self.URL + "/dotlrn/control-panel", headers = self.headers)
		soup = BeautifulSoup(r.content.decode('utf-8', 'ignore'), 'html.parser')
		self.meta["wuidentification"] = soup.find('table', {"id" : "personal_data_table"}).select('tr')[1].select('td')[1].text.strip()
		self.meta["firstname"] = soup.find('table', {"id" : "personal_data_table"}).select('tr')[2].select('td')[1].text.strip()
		self.meta["lastname"] = soup.find('table', {"id" : "personal_data_table"}).select('tr')[3].select('td')[1].text.strip()
		self.meta["wuemail"] = soup.find('table', {"id" : "personal_data_table"}).select('tr')[4].select('td')[1].text.strip()

		r = self.session.get(self.URL + soup.find('a', {"class" : "percent85"})['href'], headers = self.headers)
		soup = BeautifulSoup(r.content.decode('utf-8', 'ignore'), 'html.parser')
		self.meta["wuregistered_at"] = soup.find('div', {"id" : "page-content"}).select('p')[0].text.strip()

		self.data = self.meta
		return self.data


	def news(self):
		r = self.session.get(self.URL + "/dotlrn/", headers = self.headers)
		soup = BeautifulSoup(r.content.decode('utf-8', 'ignore'), 'html.parser')

		self.news = {}
		for i,item in enumerate(soup.find("h3", string="Ankündigungen").parent.parent.find('div', {"class" : "panel-body"}).find_all('li')):
			self.news[i] = {}
			self.news[i]["number"] = re.findall("\\d+", item.a["href"])[-1]
			self.news[i]["lv"] = re.findall("\\d{4}[.]\\d{2}", item.a["href"])[0]
			self.news[i]["url"] = self.URL + item.a["href"]
			self.news[i]["date"] = item.contents[2].split("-")[1].replace('\n','').replace(')','').strip()
			self.news[i]["author"] = item.contents[2].split("-")[0].replace('\n','').replace('(','').replace('Von ','').strip()
			self.news[i]["title"] = item.a.text.strip()
  	
		self.data = self.news
		return self.data


	def lvs(self):
		r = self.session.get(self.URL + "/dotlrn/", headers = self.headers)
		soup = BeautifulSoup(r.content.decode('utf-8', 'ignore'), 'html.parser')
		
		self.lvs = {}
		for lv in soup.find('li', {"id" : re.compile('dotlrn_class_instance')}).find_all('a', href=True):
			key = str(lv['href'][-9:-1])
			number = str(lv['href'][-9:-5])
			url = self.URL + lv['href']
			
			self.lvs[key] = {}
			self.lvs[key]["key"] = key
			self.lvs[key]["url"] = url
			self.lvs[key]["number"] = number
			self.lvs[key]["semester"] = lv['href'][-4:-1]
			self.lvs[key]["name"] = lv.string[5:].strip()

			url_gradebook = self.URL + lv['href'] + "gradebook/student/"
			# to save requests, try to get the gradebook via the gradebook widget
			if soup.find("h3", string="Notenbuch"):
				self.lvs[key]["gradebook"] = '1' if soup.find("h3", string="Notenbuch").parent.parent.find("a", string=lv.string[5:]) else '0'
				self.lvs[key]["url_gradebook"] = url_gradebook if soup.find("h3", string="Notenbuch").parent.parent.find("a", string=lv.string[5:]) else ''
			else:
				r = self.session.get(url_gradebook, headers = self.headers)
				self.lvs[key]["gradebook"] = '1' if r.status_code == 200 else '0'
				self.lvs[key]["url_gradebook"] = url_gradebook if r.status_code == 200 else ''

		self.data = self.lvs
		return self.data


	def grades(self):
		if not ( self.lvs in vars() ):
			self.lvs()
		for key, lv in {key: lv for key, lv in self.lvs.items() if lv["gradebook"] == "1"}.items():
			r = self.session.get(lv["url_gradebook"], headers = self.headers)
			soup = BeautifulSoup(r.content.decode('utf-8', 'ignore'), 'html.parser')
			lv["grades"] = {}
			for i, row in enumerate(soup.find('table', {"class" : "list-table"}).find('tbody').find_all('tr')):
				lv["grades"][i] = {}
				for grade in row.find_all('td'):
					lv["grades"][i][str(grade.get("headers"))[18:-2]] = grade.text.strip()

		self.data = self.lvs
		return self.data


	def getResults(self):
		status = self.status
		if "last_logged_in" in status:
			status["last_logged_in"] = self.status["last_logged_in"].strftime("%Y-%m-%d %H:%M:%S")
		return {
			"data" : self.data, 
			"status" : self.status
		}

