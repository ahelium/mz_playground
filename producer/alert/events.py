#!/usr/bin/env python
import numpy as np
import faker as F
import sys
import schedule
import time
import json
from kafka import KafkaProducer


# fake event data
def fake_events(customer_cnt: int) -> list:
    fake = F.Faker()

    deployment_type = ['cloud', 'on_prem']
    organizations = ['A', 'B', 'C', 'D']

    # emulate a stream of events
    return [{'customer_id': x,
             'customer_name': fake.name(),
             'deployment_type': np.random.choice(deployment_type, p=[0.20, 0.80]),
             'organization': np.random.choice(organizations),
             'event_type': 'deployment_created'} for x in range(customer_cnt)]


class Producer:
    def __init__(self, topic, key):
        self.topic = topic
        self.key = key

    def run(self, data):
        producer = KafkaProducer(bootstrap_servers='redpanda:9092')

        dt = int(time.time())

        for i in data:
            i['event_ts'] = dt
            print(i)
            producer.send(topic=self.topic,
                          key=str(i[self.key]).encode('utf-8'),
                          value=json.dumps(i).encode('utf-8'))

        producer.close()


def main():
    num_customers = 5
    customer_events = fake_events(num_customers)

    p = Producer('customer_events', 'customer_id')
    p.run(customer_events)

    # push a random deployment event every 15 seconds
    schedule.every(15).seconds.do(p.run,
                                  [customer_events[np.random.choice([*range(0, num_customers, 1)])]])

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    main()

