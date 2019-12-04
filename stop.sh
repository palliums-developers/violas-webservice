ps -ef | grep -v grep | grep violas-webservice | awk '{print $2}' | xargs sudo kill -9
