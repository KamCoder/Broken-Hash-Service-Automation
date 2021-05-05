

def pytest_addoption(parser):
  # To send number of requests from command line.
  parser.addoption("--cli_numRequests", action="store", default="default "
                                                                "cli_numRequests")
  # To send password_string from command line.
  parser.addoption("--cli_password", action="store", default="default "
                                                                "cli_password")
