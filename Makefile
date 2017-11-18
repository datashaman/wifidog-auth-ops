test:
	fab -A -H ubuntu@auth.datashaman.com test:release/0.8.0

deploy-staging:
	fab -A -H ubuntu@auth.datashaman.com deploy:staging,release/0.8.0,etc/users.csv

deploy-test:
	fab -A -H ubuntu@auth.datashaman.com test
