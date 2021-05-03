#!/bin/sh

export TWILIO_ACCOUNT_SID=AC70e9d77ba9c36fb3ebc8480504d83f9f
export TWILIO_AUTH_TOKEN=d88cc146ae8f88882f4f9a9b5ce778ba
# export SQLALCHEMY_DATABASE_URI=postgresql://cgrvtpmeywuwjh:c20e409089facf9b79556eaacbf64c635a5509ee767388a979905d663275f426@ec2-34-225-103-117.compute-1.amazonaws.com:5432/dfppluc3uq6qt0
export SQLALCHEMY_DATABASE_URI=postgresql://peterlu@/local_db
export TEST_DATABASE_URI=postgresql://peterlu@/coherencetest
export FLASK_DEBUG=1
export FLASK_ENV=local
export NOALERTS=1
export REACT=1