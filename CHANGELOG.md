## v2.2.0a0 (2022-02-03)

### Feat

- file processing
- add span to file processing
- add span to file processing
- add span to file processing
- add span to file processing
- add span to file processing
- add span to file processing
- add span to file processing
- add span to file processing
- :adhesive_bandage: Handle empty values in custom keys and file.
- bulk create coupons route.
- add handle to bulk create coupons (#126)
- add task wrapper (#120)
- creanting file upload service (#119)

### Refactor

- bulk create coupons improvement.
- change index pagition (#174)
- :recycle: added pydantic validators for customer_keys

### Fix

- validating if the file is csv type
- Nominal Type coupons must not allow max_amount attribute
- reorganized data storage order for S3 and pro DB

## v2.1.1 (2022-02-02)

### Fix

- change regular expression to set GITHUB_VERSION environment variable

## v2.1.0 (2022-02-01)

### Feat

- add observability with opentelemetry
- add log correlation (#178)
- add instrumentation (#177)
- configure opentelemetry with datadog exporter (#175)

## v2.0.1 (2022-01-28)

### Fix

- timezone conversions from UTC to localtime
- remove replace to timezone
- timezone conversions (#152)
- changing annotations by inserting security groups (#165)
- adjusts on Healthcheck Setup

## v2.0.0 (2022-01-11)

### Fix

- :bug: validate valid_from and valid_until by utc on coupon update (#118)
- query to confirm coupon usage (#112)
- v2 reserved route raising error 500 (#114)
- change utcnow to datetime.now with timezone utc (#110)
- update usage_history contraint to allow use multiples coupon for one transaction (#109)
- :bug: budget must be smaller or equals purchase amount (#107)
- validate coupon dates by utc (#98)
- error 500 when trying to reserve coupon with existent transaction_id (#94)
- :bug: verify if discount amount is bigger than purchase amount (#89)
- creating service to calculate discount value (#87)
- multiple head revisions
- alter column max_amount and min_purchase_amount to numeric type (#81)
- set decimal places to fields with decimal values (#79)
- update valid_from when coupon is unused. (#76)
- multiple head revisions (#82)
- set decimal places to fields with decimal values (#79)
- period of dates in duplicate checking (#78)
- update valid_from when coupon is unused. (#76)

### Feat

- task model repository (#117)
- implement commit hooks (#96)
- creating v2 endpoints for usage coupon with the coupon code in … (#92)
- :sparkles: make vaildate coupon for validate and reserved unique (#93)
- validations for per-customer limitation (#91)
- verify budget (#88)
- change reserved, unreserved and confirmed routes (#85)
- add budget column (#73)
- add accumulated_value to cupom (#77)
- add alembic commands to help merge migrations. (#74)
- usage history (#72)
- :sparkles: add limit per customer field (#63)

### BREAKING CHANGE

- the reserved_usage and confirmed_usage fields have been removed from the coupon model and schemas, changing the flow to the UsageHistory model

## v1.0.1 (2021-12-22)

### Fix

- alter column max_amount and min_purchase_amount to numeric type (#81)
- set decimal places to fields with decimal values (#79)
- period of dates in duplicate checking (#78)
- update valid_from when coupon is unused. (#76)

## v1.0.0 (2021-12-16)

### Fix

- check valid from in update (#64)
- change version (#70)
- version

### Feat

- Add pull request template (#55)
- adjust in cpu and memory k8s (#62)
- add support to commitizen
- Add pull request template (#55)

## v0.1.2 (2021-12-14)

### Fix

- change resouce in autoscale (#57)
- Set env var to CORS (#51)
- Set env var to CORS (#50)
- erro in return create (#49)

## v0.1.1 (2021-12-10)

### Feat

- add  uppercase in reserved, unserved and confirmed (#37)
- :sparkles: validate max_amount, max_usage, value (#36)
- :sparkles: add validate route and tests (#30)

### Fix

- :bug: fixing lower coupons (#35)
- :bug: validate coupon with max_usage is none (#32)
- :bug: add rules in validate route (#31)
- error in comparison dates (#29)
- change replicas counts (#24)

## v0.1.0 (2021-12-02)

### Fix

- error in make run build (#10)
