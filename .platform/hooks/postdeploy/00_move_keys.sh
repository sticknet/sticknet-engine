#!/usr/bin/bash

sudo mv /etc/pki/tls/certs/cloudfront-key.pem /var/app/current/cloudfront-key.pem
sudo mv /etc/pki/tls/certs/firebase-admin.json /var/app/current/firebase-admin.json
sudo mv /etc/pki/tls/certs/iap-android.json /var/app/current/iap-android.json
sudo chmod 755 /var/app/current/cloudfront-key.pem
sudo chmod 755 /var/app/current/firebase-admin.json
sudo chmod 755 /var/app/current/iap-android.json
