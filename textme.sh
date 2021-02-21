#!/usr/bin/env bash
source env.sh

msg=$@
curl -X POST -d "Body=${msg}" \
    -d "From=${TWILIO_FROM_NUMBER}" -d "To=${MAINTAINER_NUM}" \
    "https://api.twilio.com/2010-04-01/Accounts/${TWILIO_ACCOUNT_SID}/Messages" \
    -u "${TWILIO_ACCOUNT_SID}:${TWILIO_AUTH_TOKEN}"
