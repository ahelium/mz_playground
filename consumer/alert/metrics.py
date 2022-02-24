#!/usr/bin/env python3

import prometheus_client as prom
import psycopg2

# This is jank. The goal here, initially, is to enable consumption of whatever alert we want, in real time.
# In past job, we surfaced data from relational databases to prometheus using exporters:
# little helpers that were responsible for querying on some cadence and producing prometheus metrcs.
# With materialize, we can write these without needing to batch query our RDBMS


# Instantiate our counter. Define a metric to emulate the increases we see from our Materialized view.
# This will reset if our consumer restarts, but we'll pick up the correct increment on restart.
ORG_ALERTS = prom.Gauge('organization_alert', 'Organization level alerts', ["organization", "alert_name"])


if __name__ == '__main__':

    # Prometheus Server
    prom.start_http_server(80)

    # Materialize has a neat TAIL feature. This code is ripped directly from the docs
    # https://materialize.com/docs/sql/tail/
    dsn = "postgresql://materialize@materialized:6875/materialize?sslmode=disable"
    conn = psycopg2.connect(dsn)

    # TODO: be clear about data struct
    # TODO: mock handle update and delete rows better
    with conn.cursor() as cur:
        cur.execute("DECLARE c CURSOR FOR TAIL organization_alert")
        while True:
            cur.execute("FETCH ALL c")
            for row in cur:
                if row[1] == 1:
                    ORG_ALERTS.labels(organization=row[3], alert_name=row[2]).set(1)
                if row[1] == -1:
                    ORG_ALERTS.labels(organization=row[3], alert_name=row[2]).set(0)
