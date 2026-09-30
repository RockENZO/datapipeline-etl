CREATE SCHEMA gnaf_test;
CREATE TABLE gnaf_test.address_principals (latitude numeric, longitude numeric, number_first integer, street_name text, street_type text, state text);
INSERT INTO gnaf_test.address_principals VALUES (-33.86,151.20,95,'BALO','STREET','NSW'),(-37.81,144.96,95,'BALO','STREET','VIC');
