nohup gunicorn -b :4000 -w 4 server:app > log.out 2>&1 &
