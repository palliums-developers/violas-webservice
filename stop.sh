ps -ef | grep -v grep | grep gunicorn | awk '{print $2}' | xargs kill -9
