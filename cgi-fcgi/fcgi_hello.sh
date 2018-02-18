#!/bin/bash

echo -ne 'Status: 200\r\n'
echo -ne 'Content-Type: text/plain\r\n'
echo -ne '\r\n'

echo 'REQUEST METHOD: ' $REQUEST_METHOD
echo 'PATH_INFO: ' $PATH_INFO
echo 'QUERY_STRING: ' $QUERY_STRING

exit 0
