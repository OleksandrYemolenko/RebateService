## This is an application with basic rebate management system implementation

You can find postman collection in the `postman_collection.json` file

### Deployment

To run application:

``` bash
docker-compose up
```

Now, you can access the API on `127.0.0.1:8000`
And DB can be accessed via `jdbc:postgresql://localhost:5432/postgres`

### Structure

Project is build with the Django recommended structure:

- urls.py represents API URLs
- models.py represents all DB entities
- serializers.py has all needed serializers for entities
- views.py represents handling of API requests
- specifications.py represents specification pattern implementation for checking transaction eligibility

Also caching was added to the calculate_rebate endpoint, and while parsing create transaction request in
`TransactionSerializer.to_internal_value()`.

### API

#### HTTP method list:

`/api/v1`:

- `/rebate-programs`: `POST`, create rebate program
- `/transactions`: `POST`, create a transaction
    - `/{id}/rebate`: `GET` calculate rebate for a given transaction
- `/report?{period_start}&{period_end}`: `GET` get a summary of total rebate claims, and the amount approved for a given
  time period
- `/claim/{id}/approve`: `PUT` to approve a claim
- `/claim/{id}/reject`: `PUT` to reject a claim
- `/claim`: `POST` claim open transactions

#### Examples:

##### Create rebate program

Request:

```json
http://127.0.0.1:8000/api/v1/rebate-programs

{
"program_name": "test name",
"rebate_percentage": "10",
"start_date": "2025-01-01",
"end_date": "2025-01-20",
"eligibility_criteria": {
"minimal_count": 10
}
}
```

Response:

```json
{
  "rebate_program_id": "4ffde0ad-54c0-4599-8f50-e1f1b092a036",
  "program_name": "test name",
  "rebate_percentage": 10,
  "start_date": "2025-01-01",
  "end_date": "2025-01-20",
  "eligibility_criteria": {
    "minimal_count": 10
  }
}
```

##### Create transaction

Request:

```json 
http://127.0.0.1:8000/api/v1/transactions

{
"amount": 200,
"transaction_date": "2025-01-15",
"rebate_program": "{{rebate_program_id}}"
}
```

Response:

```json 
{
  "transaction_id": "18f8267d-1aa6-4bad-a54f-c5334a65372f",
  "amount": 200,
  "transaction_date": "2025-01-15",
  "rebate_program": "4ffde0ad-54c0-4599-8f50-e1f1b092a036",
  "eligibility_status": "eligible"
}
```

##### Calculate transaction rebate

Request:

```json
http://127.0.0.1:8000/api/v1/transactions/{{transaction_id}}/rebate
```

Response:

```json
{
  "rebate_amount": 20.0
}
```

##### Claim rebate for open transactions

Request:

```json
http://127.0.0.1:8000/api/v1/rebate-programs/claim
```

Response:

```json
{
  "message": "1 rebate claims successfully created.[UUID('ef1c6ba0-58cc-4b38-bf57-eb812ee6975f')]"
}
```

##### Get report for dates

Request:

```json
http://127.0.0.1:8000/api/v1/report?period_start=2025-01-01&period_end=2025-01-30
```

Response:

```json
{
  "total_claims": 2,
  "approved_amount": 140
}
```

##### Reject/approve claim

Request:

```json
http://127.0.0.1:8000/api/v1/claim/3892f038-7d26-41f8-b54e-21a6d0292eda/reject
http: //127.0.0.1:8000/api/v1/claim/3892f038-7d26-41f8-b54e-21a6d0292eda/approve
```

### Possible improvements:

- Add indexes to the DB to improve speed of search
- Separate claim functionality into another microservice, and communicate with it via message queue, to ensure claim
  processing process of transaction will be finished
- Introduce eligibility check for group of transactions. For example rebate eligibility criteria could be "performed 10+
  transactions each $500K+".
- Add versioning to the rebate
- Create a report microservice, and connect it to the claim processing service via pub-sub system, so the report data
  will be live and up to date
- If transaction creation is a heavy operation, don't process it right after submission. Create a queue of transactions,
  and update it's status live