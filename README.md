# Exploring Materialize

---
Dumping ground for Materialize use case exploration.
Born from the dope [hack day code](https://github.com/MaterializeInc/mz-hack-day-2022) that [Marta](https://github.com/morsapaes) put together.
### Setup
We use [Docker Compose](https://docs.docker.com/get-started/08_using_compose/) to bundle services relative to each use case. Make targets makes our lives easier.
Just the one use case, for now. :) 


## Use Cases

---
### [`alert`](doc/alert/alert.md)
Use materialize as the backend for sending alerts, in real time, based off of aggregated data sources.

## Future Work

---
mzcompose: https://github.com/MaterializeInc/materialize/blob/main/doc/developer/mzbuild.md#mzcompose
