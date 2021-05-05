# Test Automation for Broken-Hash-Serve Service
This project is to test Broken-Hash-Serve Service. These tests are built using Python
 and Pytest

## Project Structure
This project contains:

### launch_application.sh : 
    Shell script does following things:
    1. Shell script to set PORT to 8088\n
    2. Launch broken_hash_serve_darwin.exe file.
    3. Calls pytest to run python script. 
  
### test_password_hassing.py :
    Python script contains following tests:
    1. test_application_launch,
    2. test_get_request_to_stats,  
    3. test_get_response_contains_base64,
    4. test_get_response_from_stats,
    5. test_graceful_shutdown,
    6.test_password_encryption,
    7.test_post_response_contains_job_id,
    8.test_post_response_wait_time,
    9.test_service_exists,
    10.test_shutdown.
 
### conftest.py:
    Pytest configuration settings file. It has function to accept and pass command line
     options to the test script.
     command line options :
     --cli_numRequests : Pass numerical value. Based on this value number of post
      requests are created.
     --cli_password    : Pass string value. Based on this value, post request input
      data is constructed.
      
### pytest.ini :
    Added live logs option to the test script.
 
## Running Tests:
```bash
$ ./launch_application.sh angryman 5
```

## Test Reports:
html report : ./report

junitxml report : results.xml
   