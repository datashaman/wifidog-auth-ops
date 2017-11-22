test:
	fab -A -H ubuntu@auth.datashaman.com test:master

deploy-master:
	fab -A -H ubuntu@auth.datashaman.com deploy:master

downstream-staging:
	fab -A -H ubuntu@auth.datashaman.com downstream_db:auth,staging
