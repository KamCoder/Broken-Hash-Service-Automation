#!/bin/sh

echo "Launching broken-hashserve application."
export PORT=8088
#NETSTAT=$(netstat -a -n | grep 'LISTEN')
echo "NETSTAT : ${NETSTAT}"
/Users/rush/Downloads/broken-hashserve/broken-hashserve_darwin &
sleep 2
NETSTAT=$(netstat -a -n | grep '8088')
echo "NETSTAT after : ${NETSTAT}"
echo "Successfully launched application"

if [ -z "$1" ]
  then
    echo "No argument supplied"
    PASSWORD_STRING="passsword_raw"
  else

    PASSWORD_STRING=$1

fi
if [ -z "$2" ]
  then
    echo "No argument supplied"
    NUM_REQUESTS="20"
  else
    NUM_REQUESTS=$2
fi

pytest   -q -s test_password_hashing.py --cli_password "${PASSWORD_STRING}" --cli_numRequests "${NUM_REQUESTS}" --junitxml=results.xml


