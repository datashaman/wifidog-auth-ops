update gateways
set id = random();

update gateways
set title = 'Gateway ' || id,
    subtitle = 'Subtitle for gateway ' || id,
    description = 'Description for gateway ' || id,
    contact_email = 'gateway-' || id || '@example.com',
    contact_phone = substr('0000000000'||id, -10, 10),
    url_home = 'http://gateway-' || id || '.example.com',
    url_facebook = 'http://facebook.com/gateway-' || id,
    logo = null;

update networks
set id = random();

update networks
set title = 'Network ' || id,
    description = 'Description for network ' || id,
    ga_tracking_id = 'GA-' || substr('0000000'||id, -7, 7);

update users
set email = 'user-' || id || '@example.com',
    password = '$6$rounds=656000$ydJG52B6JMeK/Yca$z.eNNOgdc/P6CRp.8OPw4LtLH.k7LkFbHbCgTch9UNkF96BdXxfqFcDzTOlog3PhGfhJkUjNZhUrS5aDBp.Pg0';

update vouchers
set code = random(),
    email = 'voucher-' || id || '@example.com';

update vouchers
set name = 'Voucher Person ' || id
where name is not null and name <> '';
