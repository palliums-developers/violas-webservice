#!/bin/bash

sudo docker stop violas-webservice
sudo docker rm violas-webservice
sudo docker image rm violas-webservice
sudo docker image build -t violas-webservice .
sudo docker run --name=violas-webservice --network=host -d violas-webservice
