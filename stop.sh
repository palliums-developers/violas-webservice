ps -ef | grep -v grep | grep ViolasWebservice | awk '{print $2}' | xargs sudo kill -9
