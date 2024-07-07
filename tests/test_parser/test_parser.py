import pytest
import requests

from app.validator_parser import ValidatorParser

class TestApp:
	def test_create(self):
		parser = ValidatorParser()
		assert True

	def test_one_file(self):
		parser = ValidatorParser()
		with open('tests/test_parser/one_file.html') as f:
			content = f.read()

		data = parser.feed('', content)

		assert data == {'dirs':[], 'files':[{'url':'file1', 'name':'file1'}]}
