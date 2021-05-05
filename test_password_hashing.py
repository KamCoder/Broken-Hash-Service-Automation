import base64
import hashlib
import json
import re
import threading
import time

import pytest
import logging
import requests
import subprocess

LOGGER = logging.getLogger(__name__)
POST_URL = 'http://localhost:8088/hash'

# Command Line option for cli_numRequests.
# cli_numRequests is used by test_shutdown_gracefully
@pytest.fixture()
def cli_numRequests(pytestconfig):
  return pytestconfig.getoption("cli_numRequests")

# Command Line option for cli_password
# cli_password is password string.
@pytest.fixture()
def cli_password(pytestconfig):
  return pytestconfig.getoption("cli_password")


# Checks whether given string is valid Base64 string.
def isBase64(base64_str):
  try:
    base64.b64decode(base64_str, validate=True)
    return True
  except ValueError as e:
    LOGGER.error("Not a valid base64 string. Given string = %s" % base64_str)
    return False


# Check for service up and listening on 8088 or not. Returns bool
def is_service_alive():
  cmd = "netstat -a -n | grep '8088'"
  out = subprocess.getoutput(cmd)
  if 'LISTEN' in out:
    LOGGER.info("Service is still up and Listening onto port 8088 ")
    return True
  else:
    LOGGER.info("Connection to port 8088 is in TIME_WAIT")
    return False
  
# Sending post request for shutdown.
def shutdown():
  response = requests.post(POST_URL, data="shutdown")
  LOGGER.info(response.status_code)
  LOGGER.info(response.text)
  return response.status_code, response.text


# Takes str and sends post request.
def send_post_request(password):
  payload = {"password": password}
  return requests.post(url=POST_URL, json=payload)


# Takes int, password and fills results = list of tuples(password, status_code, job_id)
def create_post_requests(request_id, cli_password, results):
  LOGGER.info("Thread %s: starting", request_id)
  
  cmd = "netstat -a -n | grep '8088'"
  out = subprocess.getoutput(cmd)
  if 'LISTEN' in out:
    LOGGER.info("Service is still up and Listening onto port "
                "8088 for Thread %s" % request_id)
  else:
    LOGGER.info("Connection to port 8088 is in TIME_WAIT for thread %s " % request_id)
  password = "{0}_{1}".format(request_id, cli_password)
  post_resp = send_post_request(password)
  results.append((password, post_resp.status_code, post_resp.text))


# Sends post request for service shutdown.
@pytest.mark.skip
def test_shutdown():
  LOGGER.info('Test for Service shutdown')
  shutdown()
  assert (not is_service_alive()), "Service is up and listening on port 8088, " \
                                   "which shouldn't be."
 

# The shell script which invokes this test_password_hashing.py script has
# already launched the Service. Hence this test will check whether the
# Service is listening in PORT 8088 or not.
def test_service_exists():
  LOGGER.info('Test to check whether service is up or not?')
  assert is_service_alive(), "Service is not Launched and not listening on port 8088"
  LOGGER.info("Service is Launched and Listening onto port 8088")


# Takes str as input and sends post request.
def test_post_response_contains_job_id(cli_password):
  LOGGER.info('Test for sending post request.')
  response = send_post_request(cli_password)
  assert response.status_code == 200, "Post request didn't went through " \
                                      "successfully. Received = %d"\
                                      % response.status_code
  assert response.text.isdigit(), "Received response is not a digit.Received text = %s "\
                                  % response.text


# Takes str as input and sends get request.
def test_get_response_contains_base64(cli_password):
  LOGGER.info('Test for sending get request and response received as Base64 string '
              'with status code 200.')
  post_resp = send_post_request(cli_password)
  job_id = post_resp.text
  get_url = POST_URL + '/%s' % job_id
  get_resp = requests.get(get_url)
  assert get_resp.status_code == 200, "Should receive 200, but received = %d"\
                                      % get_resp.status_code
  assert isBase64(get_resp.text), \
    "Should receive Base64 string, but received = %s" % get_resp.text


# Tests service functionality of password encryption.
# Converts cli_password -> SHA512 binary and encodes to base64
# Compares generated base64 string with service get request output.
def test_password_encryption(cli_password):
  LOGGER.info('Test for service to do successful password encryption using SHA512.')
  post_resp = send_post_request(cli_password)
  job_id = post_resp.text
  get_url = POST_URL + '/%s' % job_id
  get_resp = requests.get(get_url)
  sha_hash = hashlib.sha512(cli_password.encode("utf-8")).digest()
  expected_base64 = base64.b64encode(sha_hash)
  actual_base64 = bytes(get_resp.text, 'utf-8')
  assert expected_base64 == actual_base64, "Password encryption is not successful as " \
                                           "Expected_base64 : %s \n" \
                                           "Actual_base64 : %s \n" % (expected_base64,
                                                                      actual_base64)
                                           
# Tests time taken for processing post request should be between 3 seconds to 5 seconds.
def test_post_response_wait_time(cli_password):
  LOGGER.info('Test for sending post request and measuring the response time to be '
              'within 5 seconds.')
  start = time.time()
  post_resp = send_post_request(cli_password)
  end = time.time()
  LOGGER.info("Total time taken for post request and response received in  %s: -->" %
              (end - start))
  process_time = end - start
  assert (3.0 < process_time and process_time < 7.0), "Allowed wait time for post " \
                                                     "request to send " \
                                   "response is 5 seconds, but received response " \
                                   "time  is %s which is not " \
                                   "between 3.0 to 5.0 seconds." % \
                                   process_time

# Tests /stats endpoint to assert that it accepts no data.
def test_get_request_to_stats():
    LOGGER.info("Test for sending get request to /stats endpoint to assert that it "
                "accepts no data.")
    get_stat_url = 'http://127.0.0.1:8088/stats'
    get_stat_url_with_data = get_stat_url +'/1'
    resp = requests.get(get_stat_url)
    assert resp.status_code == 200, "Should receive 200, but status received is %s" % \
                                    resp.status_code
    data_resp = requests.get(get_stat_url_with_data)
    assert data_resp.status_code != 200, "Should not receive 200, but status received " \
                                         "is %s" % data_resp.status_code


# Tests /stats endpoint to assert that it sends json datastructure in response.
def test_get_response_from_stats():
    LOGGER.info("Test for sending get request to /stats, and response received as"
                " json data structure")
    get_stats_url_data =  'http://127.0.0.1:8088/stats'
    stats_resp = requests.get(get_stats_url_data)
    assert stats_resp.status_code == 200, "Should receive 200, but status received is %s"\
                                          % stats_resp.status_code
    expected_string = r'{"TotalRequests":\d+,"AverageTime":\d+}'
    assert re.fullmatch(expected_string, stats_resp.text), "Should receive a JSON " \
                                                           "datastructure, " \
                                                           "but received" \
                                                   "response text is -->%s " % \
                                                   stats_resp.text


# Tests graceful shutdown and asserts inflight operation while shutdown.
# threads list will have all list of all threads.
# results list will store (password, status_code, job_id) from each post request
# Step1: Sends post requests creating cli_numRequests threads before calling shutdown.
# Step2: Calls shutdown.
# Step3: Sends post requests creating cli_numRequests threads before calling shutdown.
# Step4: Asserts all requests should receive 200 before calling shutdown and requests
# should not receive 200 after calling shutdown.
# Step6: Logs no of failed requests out of total requests sent before shutdown.
# Step7: Logs no of failed requests out of total requests sent after shutdown.

def test_graceful_shutdown(cli_numRequests, cli_password):
  LOGGER.info('Test for graceful shutdown of Service.')
  LOGGER.info('Number of requests received from user to process are %s' % cli_numRequests)
  threads = []
  results = []
  nRequests = int(cli_numRequests)
  for i in range(nRequests):
    th = threading.Thread(target=create_post_requests, args=(i, cli_password,
                                                             results))
    threads.append(th)
    th.start()

  shutdown_status_code, shutdown_resp_msg = shutdown()
  
  for i in range(nRequests, 2 * nRequests):
    th = threading.Thread(target=create_post_requests, args=(i, cli_password,
                                                             results))
    threads.append(th)
    th.start()
  
  for index, thread in enumerate(threads):
    thread.join()
  passed_successfully = True

  before_shutdown_failed_count = 0
  after_shutdown_failed_count = 0
  
  for pwd, status_code, job_id in results:
    # Extracting request number from password. Eg password = "3_angryman" request_id
    # = 3
    match = re.match(r'(\d+)', pwd)
    request_id = match.group(1)
    LOGGER.info("request_id=%s" % request_id)
    
    if int(request_id) < nRequests:
        if status_code != 200:
          passed_successfully=False
          before_shutdown_failed_count += 1
          LOGGER.error("Should receive 200 before shutdown. Received %s for job_id = %s,"
                       " cli_password = %s" % (status_code, job_id, pwd))
    else:
        assert nRequests <= int(request_id)
        assert int(request_id) < (2*nRequests)
        if status_code == 200:
          passed_successfully = False
          after_shutdown_failed_count += 1
          LOGGER.error("Should not receive 200 after shutdown. Received %s "\
                                   "for job_id = %s, cli_password = %s" % \
                                   (status_code, job_id, pwd))
  
  LOGGER.error("%s out of %s requests sent before shutdown failed." % (
    before_shutdown_failed_count, nRequests))
  LOGGER.error("%s out of %s requests sent after shutdown failed." % (
    after_shutdown_failed_count, (2*nRequests - nRequests)))
 
  assert passed_successfully, "inflight operation didn't happen as expected."
  assert (not is_service_alive()), "Service is still alive."

