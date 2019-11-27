ps -ef | grep -v grep | grep violas-webservice | awk '{print $2}' | xargs kill -9
