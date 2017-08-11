#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# GitHub Automerger Script
# https://github.com/sebavenditti/github-automerger-script
# Created by SebaVenditti
#
# This script allows you to merge 2 branches of your GitHub repository. 
# It uses the GitHub API to create a Pull Request and attempt to accept it. 
# If it fails, it exits with a non-zero exit code (so, for example, you can use it to make a Jenkins job to fail).
#


import sys
import requests
import json


#-------------------------------
# Constants
#-------------------------------

VERBOSE_MODE = False

BASE_URL = 'https://api.github.com/repos/' + sys.argv[2] + '/'

AUTH_TOKEN = sys.argv[1]

ERROR = 1

PULL_REQUEST_CREATED = 201
COULD_NOT_CREATE_PULL_REQUEST_BECAUSE_IT_ALREADY_EXISTS = 4221
COULD_NOT_CREATE_PULL_REQUEST_BECAUSE_THERE_IS_NOTHING_TO_MERGE = 4222

PULL_REQUEST_FOUND = 200

PULL_REQUEST_MERGED = 200
COULD_NOT_MERGE_PULL_REQUEST_BECAUSE_IT_IS_NOT_MERGEABLE = 405

PULL_REQUEST_ASSIGNED = 200


#-------------------------------
# Main
#-------------------------------

def main():

	# TODO: (nice to have) process command line arguments this way: http://www.diveintopython.net/scripts_and_streams/command_line_arguments.html or http://www.tutorialspoint.com/python/python_command_line_arguments.htm
	if len(sys.argv) < 5:
		usage()
		sys.exit(1)

	base_branch = sys.argv[3]
	head_branch = sys.argv[4]

	if len(sys.argv) > 5:
		assignee_login = sys.argv[5]
	else:
		assignee_login = ''

	creation_result = create_pull_request(base_branch, head_branch)

	if creation_result['result'] == PULL_REQUEST_CREATED:
		
		merging_result = merge_pull_request(creation_result['number'])

		if merging_result['result'] == PULL_REQUEST_MERGED:
			print 'The pull request was successfully created and merged.'
			sys.exit()

		elif merging_result['result'] == COULD_NOT_MERGE_PULL_REQUEST_BECAUSE_IT_IS_NOT_MERGEABLE:

			if len(assignee_login) > 0:  # A username was provided. Assign the PR.

				assignation_result = assign_pull_request(creation_result['number'], assignee_login)

				if assignation_result['result'] == PULL_REQUEST_ASSIGNED:

					print 'The pull request was created but could not be merged because it is not mergeable. It has been assigned to "' + assignee_login + '".'
					sys.exit(1)

				else:

					print 'The pull request was created but could not be merged because it is not mergeable. Also, an error occurred while trying to assign it to "' + assignee_login + '".'
					sys.exit(1)

			else:

				print 'The pull request was created but could not be merged because it is not mergeable.'
				sys.exit(1)

		else:
			print 'Unexpected error while attempting to merge the pull request.'
			sys.exit(1)

	elif creation_result['result'] == COULD_NOT_CREATE_PULL_REQUEST_BECAUSE_IT_ALREADY_EXISTS:
		print 'Could not create the pull request because a pull request between these branches already exists. Attempting to find it...'

		get_pull_request_result = get_pull_request(base_branch, head_branch)

		if get_pull_request_result['result'] == PULL_REQUEST_FOUND:
			print 'The existing pull request was found. Attempting to merge it...'
			
			merging_result = merge_pull_request(get_pull_request_result['number'])

			if merging_result['result'] == PULL_REQUEST_MERGED:
				print 'The pull request was successfully merged.'
				sys.exit()

			else:
				print 'The pull request is still unmergeable. :('
				sys.exit()

		else:
			print 'The pull request was not found. :('
			sys.exit(1)

			

	elif creation_result['result'] == COULD_NOT_CREATE_PULL_REQUEST_BECAUSE_THERE_IS_NOTHING_TO_MERGE:
		print 'Could not create the pull request because there is nothing to merge between these branches.'
		sys.exit()

	else:
		print 'Unexpected error while attempting to create the pull request.'
		print ''
		print 'Please make sure that the branches "' + base_branch + '" and "' + head_branch + '" exist.'
		print ''
		print 'GitHub API returned: '
		print creation_result['message']
		print ''
		sys.exit(1)


#-------------------------------
# Functions
#-------------------------------

def usage():

	print '--------------------------------------------------------------------------'
	print 'Usage: ', sys.argv[0], '<auth_token> <repo> <base-branch> <head-branch> [<assignee-login>]'
	print ''
	print ' ↳  auth_token: an auth token to access the GitHub API (see: https://github.com/settings/tokens).'
	print ' ↳  repo: the repository that should be used.'
	print ' ↳  base-branch: the branch where you want the changes to be applied.'
	print ' ↳  head-branch: the branch that contains what you would like to be applied.'
	print ' ↳  assignee-login: optional parameter that can be used to specify the login (username) of the user to which the pull request should be assigned in case of a conflict while attempting to merge. If not provided, the pull request will be unassigned.'
	print ''
	print 'Recommended reading: https://help.github.com/articles/using-pull-requests/'
	print ''
	print '--------------------------------------------------------------------------'

def create_pull_request(base_branch, head_branch):

	url = BASE_URL + 'pulls'
	headers = {'Authorization': 'token ' + AUTH_TOKEN}
	payload = {
				'title': 'Automerging ' + head_branch + ' into ' + base_branch,
				'body': 'This pull request was created by the automerger.',
				'head': head_branch,
				'base': base_branch
			}
	response = requests.post(url, headers=headers, data=json.dumps(payload))
	print_response_if_needed(url, response)
	response_json = response.json()

	if response.status_code == 201: # Created
		return {'result' : PULL_REQUEST_CREATED, 'number' : response_json.get('number')}
	elif is_no_diff_error(response):
		return {'result' : COULD_NOT_CREATE_PULL_REQUEST_BECAUSE_THERE_IS_NOTHING_TO_MERGE}
	elif is_pull_request_already_exists_error(response):
		return {'result' : COULD_NOT_CREATE_PULL_REQUEST_BECAUSE_IT_ALREADY_EXISTS}
	else:
		return {'result' : ERROR, 'message' : 'Response code: ' + str(response.status_code) + '. Body: ' + str(response_json)}


def get_pull_request(base_branch, head_branch):

	url = BASE_URL + 'pulls'
	headers = {'Authorization': 'token ' + AUTH_TOKEN}
	payload = {
				'state': 'open',
				'head': head_branch,
				'base': base_branch
			}
	response = requests.get(url, headers=headers, params=payload)
	print_response_if_needed(url, response)
	response_json = response.json()

	if response.status_code == requests.codes.ok: # OK
		if len(response_json) == 1:
			return {'result' : PULL_REQUEST_FOUND, 'number' : response_json[0]['number']}
		else:
			print 'Response code is OK but the length of the array is not 1.'
			return {'result' : ERROR, 'message' : 'Response code is OK but the length of the array is not 1.'}
	else:
		print 'Response code is not OK: ' + str(response.status_code)
		return {'result' : ERROR, 'message' : 'Response code: ' + str(response.status_code) + '. Body: ' + str(response_json)}


def merge_pull_request(pull_request_number):

	url = BASE_URL + 'pulls/' + str(pull_request_number) + '/merge'
	headers = {'Authorization': 'token ' + AUTH_TOKEN}
	payload = {
				'commit_message': 'Automerging pull request #' + str(pull_request_number) + ' (this was done automatically by the automerger).'
			}
	response = requests.put(url, headers=headers, data=json.dumps(payload))
	print_response_if_needed(url, response)
	if response.status_code == requests.codes.ok: # OK
		return {'result' : PULL_REQUEST_MERGED}
	elif response.status_code == 405: # Method Not Allowed
		return {'result' : COULD_NOT_MERGE_PULL_REQUEST_BECAUSE_IT_IS_NOT_MERGEABLE}
	else:
		return {'result' : ERROR}


def assign_pull_request(pull_request_number, assignee_login):

	url = BASE_URL + 'issues/' + str(pull_request_number)
	headers = {'Authorization': 'token ' + AUTH_TOKEN}
	payload = {
				'assignee': assignee_login
			}
	response = requests.patch(url, headers=headers, data=json.dumps(payload))
	print_response_if_needed(url, response)
	if response.status_code == requests.codes.ok: # OK
		return {'result' : PULL_REQUEST_ASSIGNED}
	else:
		return {'result' : ERROR}


def is_no_diff_error(response):

	if response.status_code != 422: # Unprocessable Entity
		return False

	error_message = response.json().get('errors')[0].get('message')
	if error_message:
		if 'No commits between' in error_message:
			return True

	return False


def is_pull_request_already_exists_error(response):

	if response.status_code != 422: # Unprocessable Entity
		return False

	error_message = response.json().get('errors')[0].get('message')
	if error_message:
		if 'A pull request already exists' in error_message:
			return True

	return False


def print_response_if_needed(url, response):

	if VERBOSE_MODE == True:
		print ''
		print 'Request to: ' + url
		print 'Returned status code: ' + str(response.status_code)
		print 'And response body: ' + str(response.json())
		print ''


#-------------------------------


if __name__ == "__main__":
    main()


