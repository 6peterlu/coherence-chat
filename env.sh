#!/bin/sh

export TWILIO_ACCOUNT_SID=invalid
export TWILIO_AUTH_TOKEN=invalid
# export SQLALCHEMY_DATABASE_URI=postgresql://cgrvtpmeywuwjh:c20e409089facf9b79556eaacbf64c635a5509ee767388a979905d663275f426@ec2-34-225-103-117.compute-1.amazonaws.com:5432/dfppluc3uq6qt0
export SQLALCHEMY_DATABASE_URI=postgresql://peterlu:hello@localhost:5432/analysis_db
export TEST_DATABASE_URI=postgresql://peterlu@/coherencetest
export FLASK_DEBUG=1
export FLASK_ENV=local
export NOALERTS=1
export REACT=1
export TOKEN_SECRET=narwhal