FROM ubuntu

RUN apt-get update
RUN apt-get -y upgrade

RUN apt-get -y install git python3 python3-pip

RUN git clone -b v0.30 https://Xing-Huang:13583744689edc@github.com/palliums-developers/libra-client.git
RUN git clone -b v0.30 https://Xing-Huang:13583744689edc@github.com/palliums-developers/libra-client.git violas-client
RUN pip3 install -r /libra-client/requirements.txt

COPY . /violas-webservice
RUN pip3 install -r /violas-webservice/requirements.txt

WORKDIR /violas-webservice
RUN cp -rf ../libra-client/libra_client .
RUN cp -rf ../violas-client/violas_client .

EXPOSE 4005
CMD ["gunicorn", "-b", "127.0.0.1:4005", "-w", "4", "ViolasWebservice:app"]
