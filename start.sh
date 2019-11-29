nohup gunicorn -b :4000 -w 4 Server:app > log.out 2>&1 &
