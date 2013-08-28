import urllib2
from sgmllib import SGMLParser
import pymongo
import time
import smtplib
from email.mime.text import MIMEText
from apscheduler.scheduler import Scheduler
from apscheduler import events
import logging

class ListHref(SGMLParser):
	def __init__(self):
		self.is_a = ''
		self.name = []
		self.freehref = ''
		self.hrefs = []

	def start_a(self, attrs):
		self.is_a = 1
		href = [v for k, v in attrs if k == 'href']
		self.freehref = href[0]

	def end_a(self):
		self.is_a = ''

	def handle_data(self, text):
		if self.is_a and text.decode('utf8').encode('GBK') == "限时免费":
			self.hrefs.append(self.freehref)

class FreeBook(SGMLParser):
	"""docstring for FreeBook"""
	def __init__(self):
		SGMLParser.__init__(self)
		self.is_title = ''
		self.name = ''

	def start_title(self, attrs):
		self.is_title = 1

	def end_title(self):
		self.is_title = ''

	def handle_data(self, text):
		if self.is_title:
			self.name = text

class freeBookMod:
	"""docstring for freeBookMod"""
	def __init__(self, date, bookname, href):
		self.date = date
		self.bookname = bookname
		self.href = href

	def get_book(bookList):
		content = urllib2.urlopen('http://sale.jd.com/act/yufbrhZtjx6JTV.html').read()
		listhref = ListHref()
		listhref.feed(content)
		for href in listhref.hrefs:
			content = urllib2.urlopen(str(href)).read()
			listbook = FreeBook()
			listbook.feed(content)
			name = listbook.name
			n = name.index('>>')
			freebook = freeBookMod(time.strftime('%Y-%m-%d', time.localtime(time.time())), name[0:n+2], href)
			bookList.append(freebook)
		return bookList

	def record_book(bookList, context, isSendMail):
		mongoCon = pymongo.connection(host='127.0.0.1',port=27017)
		db = mongoCon.mydatabase
		for bookItem in bookList:
			bookInfo = db.book.find_one({'href':bookItem.href})
			if not bookInfo:
				b = {
					'bookname': bookItem.bookname.decode('gbk').encode('utf8'),
					'href': bookItem.href,
					'date': bookItem.date
				}
			db.book.insert(b, safe=True)
			isSendMail = True
			context = context + bookItem.bookname.decode('gbk').encode('utf8')+','
		return context, isSendMail

	def send_mail(mailto_list, sub, context):		
		COMMASPACE = ','
		mail_host = 'localhost'
		me = 'my@my.com'
		msg = MIMEText(context)
		msg['subject'] = sub
		msg['From'] = 'my@my.com'
		msg['To'] = COMMASPACE.join(mailto_list)
		send_smtp = smtplib.SMTP(mail_host)
		send_smtp.sendmail(me, mail_list, msg.as_string())
		send_smtp.close()

	def job():
		bookList = []
		isSendMail = False
		context = 'Today free books are'
		mailto_list = ['test@test.com']
		bookList = get_book(bookList)
		context, isSendMail = record_book(bookList, context, isSendMail)
		if isSendMail:
			send_mail(mailto_list, 'Free Book is Update', context)

	def job_listener(event):
		logging.basicConfig()
		if event.exception:
			print 'job failed'
		else:
			print 'job succeed'

if __name__ = '__main__':
	sched = Scheduler(daemonic = False)
	sched.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
	sched.add_interval_job(job, minutes=30)
	sched.start()