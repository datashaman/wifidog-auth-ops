test:
	fab -A -H ubuntu@auth.datashaman.com test:origin/release/0.8.0

deploy-staging:
	drone deploy datashaman/wifidog-auth-flask $(BUILD) staging

deploy-test:
	fab -A -H ubuntu@auth.datashaman.com test

downstream-staging:
	fab -A -H ubuntu@auth.datashaman.com downstream_db:auth,staging
