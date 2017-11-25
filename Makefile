deploy-master:
	fab -A -H ubuntu@auth.datashaman.com deploy:master

deploy-staging:
	fab -A -H ubuntu@auth.datashaman.com deploy:staging

downstream-staging:
	fab -A -H ubuntu@auth.datashaman.com downstream_db:auth,staging,false

downstream-staging-anonymise:
	fab -A -H ubuntu@auth.datashaman.com downstream_db:auth,staging,true
