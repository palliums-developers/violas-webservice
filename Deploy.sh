#!/bin/bash

sudo docker stop violas-webservice
sudo docker rm violas-webservice
sudo docker image rm violas-webservice
sudo docker image build -t violas-webservice .
sudo docker run --name=violas-webservice --rm --network=host -itd violas-webservice python3 CreateTable.py
sudo docker stop violas-webservice
sudo docker run --name=violas-webservice --network=host -d violas-webservice
