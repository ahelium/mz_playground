##Alert

Can we use Materialize to enable real time alerting on aggregated data?

---
### Producer
Use the python Faker library to create fake event data. 
Push an initial set of events to redpanda. Simulate a spike in deployments (every minute) for us to alert on!
### Redpanda
Accept our fake events
### Materialize
Create a kafka source. 
Do a little bit of data modeling to transform our events table into something we can peep aggregated data. 
In this case, we'll use [temporal filters](https://materialize.com/docs/guides/temporal-filters/#sliding-windows) 
and some logic of the underlying data to create a dimension table to aggregate the number of deployments per organization. 

[Optional]: Define a table to house only currently firing alerts. This makes our lives easier on the consumer side.

```
materialize=> select * from fct_customer_events limit 10;
 customer_id |  customer_name  | deployment_type |     event_type     | organization |  event_ts
-------------+-----------------+-----------------+--------------------+--------------+------------
           2 | Lisa White      | cloud           | deployment_created | D            | 1645736476
           0 | Jon Brown       | on_prem         | deployment_created | B            | 1645736476
           0 | Lisa Lopez      | on_prem         | deployment_created | A            | 1645736153
           2 | Tara Kirby      | on_prem         | deployment_created | D            | 1645736153
           4 | Antonio Fischer | cloud           | deployment_created | D            | 1645736290
           4 | Antonio Fischer | cloud           | deployment_created | D            | 1645736320
           4 | Antonio Fischer | cloud           | deployment_created | D            | 1645736350
           1 | Deborah Bell    | on_prem         | deployment_created | D            | 1645736153
           3 | Robert Smith    | on_prem         | deployment_created | C            | 1645736153
           4 | David Norman    | on_prem         | deployment_created | B            | 1645736521
(10 rows)

materialize=> select * from dim_deployments limit 10;
 organization | deployment_type | deployment_cnt | customer_cnt
--------------+-----------------+----------------+--------------
 B            | on_prem         |              8 |            1
(1 row)

materialize=> select * from organization_alert;
    alert_cond    | labels
------------------+--------
 deployment_spike | B
```
### Consumer
TAIL the alerts table and create prometheus metrics from the results. Export those events for prometheus to scrape.
### Prometheus
Set up prometheus to scrape our exporter and send alerts to our alertmanager instance. Define a condition to alert on.
### Alertmanager
Define a route and receiver for alerts to be set to.
### Grafana (w/ or instead of alertmanager)
Graph alert timeseries, send alerts from dashboard.

---


Notes:

To Run:
```
docker-compose -f alert.yml --build producer
docker-compose -f alert.yml --build consumer
docker-compose -f alert.yml up -d
```

Prometheus - what does this [look like](http://localhost:9090/graph?g0.expr=organization_alert%7Bjob%3D%22event_exporter%22%7D&g0.tab=0&g0.stacked=0&g0.show_exemplars=0&g0.range_input=1h)?

Alerts - what is [firing](http://localhost:9090/alerts)?  

TODO/Ideas
- disclaimer: _this isnt exactly how prometheus is supposed to be used_ - our TAIL feature got me thinking and made me want to see what things might look like
- materialize sink to file/stdout -> sinks https://vector.dev/docs/reference/configuration/sinks/ or https://docs.fluentbit.io/manual/concepts/data-pipeline/input (?)
- materialize sink back to kafka | but why not just use ksql
- use materialize observability image
- push from prometheus instead of writing an exporter
- avenue.so - direct connection, poll materialize on some cadence (TAIL support)