import requests
import json
import re
import os
import logging
from app.validator_parser import ValidatorParser

class ValidatorExplorer():
	release_dir = 'release/'
	debug_dir = 'debug/'

	def __init__(self, url, user):
		self.base_url = f'{url}/checkerusers/{user}/files/'
		self.parser = ValidatorParser()
		self.session = requests.Session()
		self.log = logging.getLogger('ValidatorExplorer')

	def parse(self, endpoint=''):
		url = self.base_url + endpoint
		r = self.session.get(url)
		if r.status_code != 200:
			raise RuntimeError

		return self.parser.feed(url, r.text)

	def get_branches(self, include_feature=False):
		data = self.parse(self.release_dir)
		branches = data['dirs']
		if not include_feature:
			branches = list(filter(lambda x: re.search("((\d\.\d{1,3})\.(\d{1,3}|x))/", x['url']), branches))
		return branches

	def get_debug_builds(self, issue=None, board=''):
		data = self.parse(self.debug_dir)
		branches=data['files']
		if issue:
			branches = list(filter(lambda x: re.search(f".*%23{issue}", x['url']), branches))
		if board:
			branches = list(filter(lambda x: re.search(f".*{board}", x['url']), branches))
		return branches

	def get_release_builds(self, branch='', board='', build=0):
		filter_branch = branch
		filter_board = board
		filter_build = build

		data = self.parse(self.release_dir)
		branches=data['dirs']
		branches = list(filter(lambda x: re.search("((\d\.\d{1,3})\.(\d{1,3}|x))/", x['name']), branches))

		if filter_branch:
			branches = list(filter(lambda x: re.search(f"{branch}", x['name']), branches))

		target_builds = []

		for branch_entry in branches:
			if not filter_branch:
				branch = branch_entry['name'][:-1]

			data = self.parse(branch_entry['url'].removeprefix(self.base_url))
			boards=data['dirs']
			if filter_board:
				boards = list(filter(lambda x: re.search(f"{board}", x['name']), boards))
			for board_entry in boards:
				if not filter_board:
					board = board_entry['name'][:-1]

				data = self.parse(board_entry['url'].removeprefix(self.base_url))
				builds=data['dirs']

				if filter_build:
					builds = list(filter(lambda x: re.search(f"{branch}/{board}/{build}/", x['url']), builds))

				for build_entry in builds:
					if not filter_build:
						build = build_entry['name'][:-1]

					build_entry['branch'] = branch
					build_entry['board'] = board
					build_entry['build'] = int(build)

				if builds:
					target_builds += builds

		return target_builds

	def get_latest_builds(self, branch, board, limit=1):
		builds = self.get_release_builds(branch, board)
		return sorted(builds, key=lambda x: x['build'])[len(builds)-limit:]

	def download_build(self, file, path=''):
		self.log.info(f"\t\tDownloading {file['name']} ...")
		r = self.session.get(file['url'], stream=True)
		if r.status_code != 200:
			raise RuntimeError

		filepath = f"{path}/{file['name']}"
		open(filepath, 'wb').write(r.content)
		self.log.info(f"\t\t{file['name']} downloaded to {os.path.realpath(filepath)}")

	def download_release_builds(self, path='', grep='', branch='', board='', build=0):
		builds = self.get_release_builds(branch, board, build)
		self.log.info(f"Matched {len(builds)} builds")
		for build in builds:
			self.log.info(f"\tHandle {build['branch']} {build['board']} build {build['build']}")
			data = self.parse(build['url'].removeprefix(self.base_url))
			files = data['files']
			if grep:
				files = list(filter(lambda x: grep in x['url'], files))
			self.log.info(f"\t{build['branch']} {build['board']} build {build['build']} contain {len(files)} files")
			for file in files:
				self.download_build(file, path)
