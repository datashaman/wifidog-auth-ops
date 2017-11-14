deploy-staging:
	fab -A -H ubuntu@auth.datashaman.com deploy:staging,feature/remove-riot,etc/users.csv

deploy-test:
	fab -A -H ubuntu@auth.datashaman.com test
