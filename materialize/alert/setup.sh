#!/bin/sh
psql -U materialize -h materialized -p 6875 -d materialize << EOF
--- kafka source
CREATE MATERIALIZED SOURCE if not exists stg_customer_events
FROM KAFKA BROKER 'redpanda:9092' TOPIC 'customer_events'
KEY FORMAT BYTES
VALUE FORMAT BYTES;

--- for use while developing
DROP VIEW IF EXISTS organization_alert;
DROP VIEW IF EXISTS dim_deployments;
DROP VIEW IF EXISTS fct_customer_events;

--- fact table, deployment created events
--- TODO: address memory consumption
CREATE MATERIALIZED VIEW fct_customer_events as
select
    (data->>'customer_id')::int as customer_id,
    (data->>'customer_name')::string as customer_name,
    (data->>'deployment_type')::string as deployment_type,
    (data->>'event_type')::string as event_type,
    (data->>'organization')::string as organization,
    (data->>'event_ts')::numeric as event_ts

from (
      SELECT
             cast(convert_from(data, 'utf8') as jsonb) as data
      from stg_customer_events
      );

--- dimension table, deployments, last two minutes
CREATE MATERIALIZED VIEW dim_deployments as
select organization,
       deployment_type,
       count(event_type) as deployment_cnt,
       count(distinct customer_id) as customer_cnt
from fct_customer_events
WHERE mz_logical_timestamp() < (event_ts * 1000 + 120000)::numeric
group by organization, deployment_type;

--- alert view
CREATE MATERIALIZED VIEW organization_alert as
select
       'deployment_spike' as alert_cond,
       organization as labels
from dim_deployments
where deployment_cnt > 2
UNION
select
      'new_user' as alert_cond,
      organization as labels
from dim_deployments
where customer_cnt > 1
EOF

