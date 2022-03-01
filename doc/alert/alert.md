## Materialize Powered Alerting

OR: The argument for using materialize in between a data warehouse or event stream and an alerting system. 


There are tons of great options out there we can use to observe what our systems are up to. 
Grafana, DataDog, NewRelic, and others all take care of ingesting time series data and providing an interactive way to structure it for alerting.
There also already exist a number of great ways to alert off of in app event triggers - segment.io, customer.io. and others. 
These platforms out of the box integrate with our favorite alert mechanisms: Slack, PagerDuty, Email etc. 

Materialize is uniquely suited to solve an additional class of alerting problems. 
It can be used to define views on the database layer that:
- aggregate information
- join information from multiple data sources

We can then listen to how these views have _changed_ using Materializes TAIL feature, and either: 
- create time-series data from those changes, to be consumed by our observability friends
- [future work] [TODO: Research] integrate directly with the alert mechanisms themselves

The following setup demonstrates the first use case. We create a bunch of fake event data, in this case, 'deployment' events. 
We aggregate these to the customer level using a Materialized view and some nice time window functionality. 
A little helper (exporter) listens for changes to this view, consumes the change events in real time, and turns them into prometheus metrics. 
We hook up prometheus to scrape those metrics and define our alerts. We can then use alertmanager to route those alerts
either directly or from within grafana.

---
### Producer
- Use the python Faker library to create fake event data. 
- Push an initial set of events to redpanda. 
- Simulate a spike in deployments (every minute) for us to alert on!
### Redpanda
- Accept our fake events
### Materialize
- Create a kafka source. 
- Do a little bit of data modeling to transform our events table into something we can peep aggregated data. 
In this case, we'll use [temporal filters](https://materialize.com/docs/guides/temporal-filters/#sliding-windows) 
and some logic of the underlying data to create a dimension table to aggregate the number of deployments per organization. 
- [Optional]: Define a table to house only currently firing alerts. This makes our lives easier on the consumer side.

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
- TAIL the alerts table and create prometheus metrics from the results. Export those events for prometheus to scrape.
### Prometheus
- Set up prometheus to scrape our exporter and send alerts to our alertmanager instance. Define a condition to alert on.

- what does this [look like](http://localhost:9090/graph?g0.expr=organization_alert%7Bjob%3D%22event_exporter%22%7D&g0.tab=0&g0.stacked=0&g0.show_exemplars=0&g0.range_input=1h)?

![image](https://user-images.githubusercontent.com/8192401/155733430-d6fe0e8d-0c2a-49b6-b7ff-6c88e1fbd7d3.png)

### Alertmanager
- Define a route and receiver for alerts to be set to.
- Alerts - what is [firing](http://localhost:9090/alerts)?  

![image](https://user-images.githubusercontent.com/8192401/155733836-388ff14c-7fe4-4d34-8b16-deb6c69819c5.png)
- Slack Alert: 

![image](https://user-images.githubusercontent.com/8192401/156078275-d7349aee-abdd-48c4-a931-8a984cfbc902.png)

- NOTE: trying this demo out? You'll need a slack API key to include with your alertmanager [`config`](../../alertmanager/alertmanager.yml). 
- NOTE: we default to use #devex-toilet for alerting. Update if need be. 
### Grafana (w/ or instead of alertmanager)
Graph alert timeseries, send alerts from dashboard.

- NOTE: sign into grafana using username: admin, password: admin. 
- The prometheus datasource will already be configured for you. 
![image](https://user-images.githubusercontent.com/8192401/156211297-55402105-ecdd-4958-b8f7-d458e5f6dc48.png)

Interact with our datasource like so: 
![image](https://user-images.githubusercontent.com/8192401/156211719-f6d7dc53-8e93-4508-b2f1-2db2f01e6ac9.png)

Set up the alerting destination, using the same API key you grabbed for alertmanager: 
![image](https://user-images.githubusercontent.com/8192401/156214036-7af3fedf-63a5-4d22-b768-ea45c86e9617.png)

And define alerts: 
![image](https://user-images.githubusercontent.com/8192401/156211602-b798b19d-0c22-44b6-a241-a9ea25aa459d.png)



---


Notes:

To Run:

Build first if developing the consumer/producer
```
docker-compose -f alert.yml --build producer
docker-compose -f alert.yml --build consumer
docker-compose -f alert.yml up -d
```
We use volumes for alertmanager, grafana, and prometheus. 
Run `docker prune containers` and/or `docker prune volumes` to wipe the data. 


TODO/Ideas
- disclaimer: _this isnt exactly how prometheus is supposed to be used_ - our TAIL feature got me thinking and made me want to see what things might look like
- materialize sink to file/stdout -> sinks https://vector.dev/docs/reference/configuration/sinks/ or https://docs.fluentbit.io/manual/concepts/data-pipeline/input (?)
- materialize sink back to kafka | but why not just use ksql
- use materialize observability image
- push from prometheus instead of writing an exporter
- avenue.so - direct connection, poll materialize on some cadence (TAIL support)
- This could be a REALLY NEAT HACK DAY! Could we provide our community slack api key so folks could develop alerts? 

Competitive Research: 
