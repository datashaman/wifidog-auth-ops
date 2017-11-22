test:
	fab -A -H ubuntu@auth.datashaman.com test:origin/release/0.8.0

deploy-staging:
	fab -A -H ubuntu@auth.datashaman.com deploy:release/0.8.0

deploy-test:
	fab -A -H ubuntu@auth.datashaman.com test

downstream-staging:
	fab -A -H ubuntu@auth.datashaman.com downstream_db:auth,staging
