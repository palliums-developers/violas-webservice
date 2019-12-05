ps -ef | grep -v grep | grep ViolasWebservice | awk '{print $2}' | xargs kill -9
