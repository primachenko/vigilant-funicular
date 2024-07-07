import re
from html.parser import HTMLParser

class ValidatorParser(HTMLParser):
	def __init__(self):
		HTMLParser.__init__(self)
		self.wait_size = False
		self.wait_data = False
		self.tags = ['a']
		self.entry = dict()
		self.dirs = list()
		self.files = list()
		self.url = None

	def write_entry(self):
		if self.entry:
			size = self.entry.get('size')
			if not size:
				pass
			elif size != '-':
				self.files.append(self.entry)
			else:
				self.dirs.append(self.entry)
			self.entry = dict()

	def handle_starttag(self, tag, attrs):
		if tag in self.tags:
			self.write_entry()
			self.entry['url'] = self.url + attrs[0][1]
			self.wait_size = False
			self.wait_data = True

	def handle_endtag(self, tag):
		if tag in self.tags:
			self.wait_data = False
			self.wait_size = True

	def handle_data(self, data):
		if self.wait_data:
			self.entry['name'] = data
		if self.wait_size:
			data = re.sub(r"\s\s+", " ", data)
			data = data.split(' ')
			if len(data) == 5:
				self.entry['date'] = data[1]
				self.entry['time'] = data[2]
				self.entry['size'] = data[3]
				self.write_entry()
			self.wait_size = False

	def feed(self, url, data):
		self.url = url
		super(ValidatorParser, self).feed(data)
		data = {'dirs': self.dirs, 'files':self.files}
		super(ValidatorParser, self).reset()
		self.dirs = list()
		self.files = list()
		self.url = None
		return data
