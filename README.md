## Architecture Overview

``` mermaid
graph LR
    Client["Client"]
    
    subgraph API["API Layer"]
        Gateway["API Orchestrator<br/>(FastAPI)"]
        REST["🔗 REST<br/>Endpoints"]
        GraphQL["📊 GraphQL<br/>Endpoints"]
        Metrics["📈 /metrics<br/>(OpenTelemetry)"]
    end
    
    subgraph Queue["Job Queue"]
        Redis["Redis Queue"]
    end
    
    subgraph Worker["Simulation Layer"]
        SimWorker["Sim Worker<br/>(Job Consumer)"]
    end
    
    subgraph Persistence["Data Layer"]
        DB["TimescaleDB<br/>(PostgreSQL)"]
    end
    
    Client -->|HTTP| REST
    Client -->|HTTP| GraphQL
    Gateway -->|Emits| Metrics
    Gateway -->|Queue Jobs| Redis
    Gateway -->|Read/Write| DB
    
    REST -.-> Gateway
    GraphQL -.-> Gateway
    
    Redis -->|Pull Jobs| SimWorker
    SimWorker -->|Write Results| DB
    
    style Gateway fill:#4CAF50,stroke:#333,stroke-width:2px,color:#fff
    style REST fill:#2196F3,stroke:#2196F3,stroke-width:2px,color:#fff
    style GraphQL fill:#E91E63,stroke:#E91E63,stroke-width:2px,color:#fff
    style Metrics fill:#FF9800,stroke:#FF9800,stroke-width:2px,color:#fff
    style Redis fill:#FF6B6B,stroke:#333,stroke-width:2px,color:#fff
    style SimWorker fill:#2196F3,stroke:#333,stroke-width:2px,color:#fff
    style DB fill:#FFC107,stroke:#333,stroke-width:2px,color:#000
```

The micro-service based solution developed to support the research of our bowling physics team is robust, observable, testable and easily extensible. The system exposes health checks, retry logic, role-based auth, metrics, and CI-backed builds to support production readiness.

## Getting Started

Once you have cloned this repository, you'll have a system up and running in no more than 5 minutes!

Follow these steps to launch the system locally:
1. If not already available on your workstation, install a modern version of Docker.
1. In the root of the repository, open `docker-compose.yml`. In here you will see the services that make up the system. You will find a number of `${ENVIRONMENT_VARIABLES}` in here, used to pass configurable and often sensitive values.
1. _(optional)_ The API Gateway defaults to listening on `localhost:8888`. Additionally, if you want to easily access the DB or any other services that are not configured to listen on host ports in production (for security reasons), now is a great time to temporarily bind those services to a localhost port.
1. Now, in `./api-orchestrator/app` directory copy (or rename) `.env.example` to `.env.dev` and populate values for all the sensitive parameters left blank by design to ensure security. You may also change other parameters if you like. Note that all values _must_ be populated before the system can run.
1. Finally, from the root of the repository simply run `docker compose --env-file ./api-orchestrator/app/.env.dev up --build`. And with that, you should have a running end-to-end system!

## Testing Your New Orchestrator

All of the following will assume you did not choose to change where the API Gateway listens within the compose file (`localhost:8888`).

### Seed Script

For simulation of many simulations, a simulation simulator has been provided. Invoke as follows:

```
python api-orchestrator/scripts/seed.py --base-url http://localhost:8888  --password <whatever you want here>
```

Script has successfully fed up to 500 sequential simulations at 200ms interval. Minor backlog occured, but that cleared within minutes.

### Create & Follow a Simulation

Navigate to http://localhost:8888/docs. This handy interface will let us test various endpoints without the need for any external tool such as cURL or Postman. That said, example queries used here can also be trivially converted for use there.

1. Scroll down until you find `POST /users Create User` green bar. Expand it.
1. Click "Try it out" button.
1. Here you'll provide any username and password you like.
1. You should quickly see an HTTP 201 success response appear and in the response body the `username` you provided plus an indication that your new user is active in the system.
1. _(optional)_ If you really want to run the cURL version of this same request, the UI provides that as well right above the "Server response" section.
1. Scroll down until you find the `POST /simulations Create Simulations`. Expand it.
1. Click "Try it out" button.
1. You should receive an HTTP 401 error at this point, indicating you're not authenticated. OOPS!
1. With the credentials you created above, let's fix that. Scroll back to the top of the `/simulations` block and click the 🔓 button. In the resulting popup, fill in your username and password. You may ignore all other fields.
1. Click the green "Authorize" button.
1. Now click the gray "Close" button. DO NOT CLICK LOGOUT!
1. You should now see that lock button you clicked at the top now looks like this 🔒
1. Paste the following request body and then click "Execute" below.
   ``` json
   {
      "velocity": 8.5,
      "rpm": 320,
      "friction": 0.044,
      "angle": 0.3,
      "lateral_offset": 0.0
    }
    ```
1. You should have received an HTTP 202 response, confirming your simulation has been queued. In that response will be a `simulation_id` of type UUIDv7. Save that somewhere. You will need it momentarily.
1. _(optional)_ If you like, at this time you can take a peek at the console where compose is running. You should see that the API gateway queued your simulation and moments later the worker finished it. Yay!
1. To now confirm our simulation has concluded, take that `simulation_id` that you pasted and use it to now execute `GET /simulations/{simulation_id} Get Simulation`. You should get a "completed" state.
1. Now that we know the simulation has completed, let's get the results! Again taking the simulation_id from above, navigate to `GET /simulations/{simulation_id}/results`. And you guessed it, try it out with the simulation ID.
1. You should have gotten something that looks like the following, with only the sim ID and exe time varying:
   ``` json
   {
     "simulation_id": "019c8832-7b6b-7113-b8a3-89b68aeca78c",
     "results": {
       "pins_knocked": 9,
       "hook_potential": 69.6,
       "impact_velocity": 7.49,
       "execution_time": 127.64
     }
   }
   ```
1. Finally, scroll down until you reach `GET /telemetry/{simulation_id}`.
1. Plug in that same sim ID, along with a stride of 100. Execute and confirm you just received 22 telemetry items in chronological order, ranging from time `0.099` to time `2.199`.
1. _(optional)_ If you want to go the extra step, connect to the system DB and query the Telemetry table for the simulation with that ID. Verify that 1/100 of the total telemetry values for that simulation (2250) is in fact 22.
1. Now, keep ahold of your sim ID as we head to the GraphQL side of the system: http://localhost:8888/graphql
1. Paste the following query:
   ``` graphql
   query {
      avgPinsByVelocity(minVelocity: 7, maxVelocity: 10){
        averagePins,
        simulationCount
      }
   }
   ```
1. Since you have only performed one simulation if you followed the above steps, averagePins will be 9 knocked over - that's not bad at all! 🎳

## System Architecture

### API Gateway & Orchestrator

These two components together control exposing REST/GraphQL/OpenTelemetry APIs. They also handle enqueuing new simulations to be run on the queue, which the Simulation Worker will later consume.

While conceptually they could be decoupled into separate microservices, for what we are trying to do that felt like it would create more complexity than value so they were left as a single service for now.

### Simulation Worker

The Simulation Worker has a single job: read simulation IDs off of the queue and run them to completion.

Due to the crude nature of required interface with the provided `sim.py`, a specialized wrapper was built to very briefly create a tempfile with appropriate configuration for a simulation run. This wrapper "drives" `sim.py`, providing the superset of all config values, injecting just the small subset we're exposing at this time. These JSON config are then dumped to a tempfile for `sim.py` to consume. Just as soon as sim is done with this tempfile, it's eliminated. _If the bowling physicists are open to slight tweaks, we could streamline this process and eliminate file IO entirely. While still exposing convenience method to initialize by file if that's what's preferred by the user._

**Retry Logic**: In order to handle unexpected errors during simulation process, the worker does allow for a configurable number of retries (default 3). Right now the retries happen as soon as the simulation reaches the front of the queue, but in future implementations an exponential backoff function might help maximize successful simulations overall. A dead letter queue would also be a nice feature for the future.

Simulation State Machine:
```
PENDING → RUNNING → COMPLETED
       ↘ RETRY ↘ FAILED
```

_Architecturally of note_, the Simulation Worker docker image is build from the same codebase as the API Gateway/Orchestrator image. At this time, the only distinction is a separate entrypoint: `sim_main.py`. This design is acceptable for sprint velocity, but warants a refactor into shared library package in a production roadmap.

### Queue

The queuing logic is currently built on a Redis docker container, however the system is lightly coupled to this design decision and could trivially be swapped out if that made sense in the future.

The docker container has very limited persistence configured at this time due to performance impact of regular disk I/O. Should persistence be deemed higher priority, these configurations are trivially changed to prioritize persistence at all (or more) cost.

### Database

<img width="675" height="832" alt="image" src="https://github.com/user-attachments/assets/0742d334-7ce7-4f18-8f2e-8a6ecfd645c2" />

The PostgreSQL (pg18) based database is actually sitting atop at TimescaleDB. While ultimately out of scope to take advantage of the time-series benefits this would provide in this sprint, should be trivial to bring in use of hypertables for the Telemetry table in a future sprint.

The database stores all simulation runs, the corresponding telemetry, and it also stores user data as shown here.

<img width="261" height="265" alt="image" src="https://github.com/user-attachments/assets/bbbbda38-4633-4cae-a001-55a6ff8e10fa" />

## System Interfaces to Explore

### REST

**REST OpenAPI Spec**: http://localhost:8888/openapi.json | **REST Sandbox/Docs**: http://localhost:8888/docs

Implemented with the industry-leading FastAPI, the provided REST interface exposes the ability to run new simulations, query past bowling simulation runs, and even inspect thousands of telemetry data points (including ability to rollup configurably).

In addition simulation-related functionality, the REST interface also provides a simple user management and authentication functionality. In order to protect our organization's valuable compute resources, the ability to create/run a new simulation is locked behind FastAPI's built-in Oauth2 functionality.

In order to maximize maintainability, separation of concerns was integral to the design. Lightweight routes were defined in `api/rest.py` and `api/auth.py`, while business logic was handled through dependency injection in our service layer in `service/simulation.py` and `service/auth.py`, facilitated by `api/deps.py`.

### GraphQL

**GraphQL Sandbox/Docs**: http://localhost:8888/graphql

The GraphQL implementation heavily leverages our robust FastAPI-based REST implementation for its base. The Strawberry GraphQL library supports building on top of the existing FastAPI server as well as easily tapping into the robust FastAPI DI functionality.

While the functionality provided in the single GraphQL interface being delivered is just a proof of concept, the plumbing is now in place to support expansive future functionality based on whatever use cases we hear from the physics team in the future.

### Telemetry

**Prometheus Metrics**: http://localhost:8888/metrics

As with GraphQL, the path to delivering a clean scalable telemetry framework fell cleanly from a solid base. Again leveraging the robust baseline provided by FastAPI, it was possible to roll out Prometheus-compatible metrics across the system with only a few lines of code. We were further able to validate that Prometheus was able to poll the `/metrics` endpoint, however with limited time we were not able to develop usable dashboards during this sprint.

### SQL

Our data layer is built on top of PostgreSQL. Or more precisely, the `TimescaleDB` docker image based on PostgreSQL version `pg18`. Time did not ultimately allow for wiring up the real reason for using PostgreSQL with the TimescaleDB add on - the creation of a `HYPERTABLE` to maximize efficient query of our `Telemetry` table. For this reason, the database currently mostly acts as any normal PostgreSQL database, however the plumbing is in place to spin up full time-series query efficiencies in the next sprint.

In order to maximize robust, error-free queries against the database, the SQLAlchemy ORM was used.

## Automated Testing

As part of this weekend sprint a comprehensive testing framework was built to support both unit and integration testing. This framework sits in the repository under `./api-orchestrator/tests`. While most tests were not able to be implemented during this weekend sprint, `tests/fixtures/models.py` mocks useful testing primitives and `tests/conftest.py` provides DB abstractions built on SQLite which cleanly function with our ORM-based ANSI SQL DB logic across the codebase!

As a proof of automated testing concept, `test_create_and_retrieve_simulation` which is located within `tests/integration/test_simulation_flow.py` runs and passes. It proves determinism, leveraging the identical parameters provided in the sample simulation input/output provided in the assignment.

Additionally, GitHub Actions provide CI functionality, and ultimately CD when we want to deploy. Current CI functionality includes the following, all triggered with PR or push:

* Docker images for orchestrator and worker are built
* Docker images for orchestrator and worker are vulnerability scanned with Trivy
  * recent output from this scan is available below, noting two libc **HIGH** vulnerabilities
* Python files are linted with Flake8
* Python unit & integration tests are run with PyUnit

```
api-orchestrator-image.tar (debian 13.3)
========================================
Total: 2 (HIGH: 2, CRITICAL: 0)

┌──────────┬───────────────┬──────────┬──────────┬───────────────────┬───────────────┬──────────────────────────────────────────────────────────────┐
│ Library  │ Vulnerability │ Severity │  Status  │ Installed Version │ Fixed Version │                            Title                             │
├──────────┼───────────────┼──────────┼──────────┼───────────────────┼───────────────┼──────────────────────────────────────────────────────────────┤
│ libc-bin │ CVE-2026-0861 │ HIGH     │ affected │ 2.41-12+deb13u1   │               │ glibc: Integer overflow in memalign leads to heap corruption │
│          │               │          │          │                   │               │ https://avd.aquasec.com/nvd/cve-2026-0861                    │
├──────────┤               │          │          │                   ├───────────────┤                                                              │
│ libc6    │               │          │          │                   │               │                                                              │
│          │               │          │          │                   │               │                                                              │
└──────────┴───────────────┴──────────┴──────────┴───────────────────┴───────────────┴──────────────────────────────────────────────────────────────┘
```

# Failure Modes

* **Simulation Crashes**: Initial retry logic is in place to allow for configurable retry and plans to further enhance with exponential backoff to maximize chance of eventual success.
* **DB Outage**: If this is deemed a critical enough system, hot or cold failover DB would need to be considered. Simple tradeoff between cost of duplicate systems, but clustering DBs is straightforward (relatively speaking) if needed.

# Architectural Design Records (ADRs)

Below documents _why_ the above-described architecture was built the way that it was.

* **Language Selection: Python**: The right tool for the right job. Besides the fact that the "client" (bowling physicists) are working in python already, which should be a factor, python just has a lot of really robust libraries due in large part to a massive worldwide userbase. That allow you to piece together a lot of functionality over a weekend sprint.
* **Redis vs Kafka**: Kafka is simply overkill and prioritizes differently than what I understand the requirements of this to be. Redis' in-memory, low-durability, hyper fast offering seemed inline given it's not a great loss if once in a million we have a simulation that gets dropped and has to be re-run. That said, queueing was by design left very loosly coupled to the architecture, with a mind toward ability to quickly swap in new tools in the future.
* **FastAPI**: When you look at modern Python-based REST libraries, there's really only one option. Particularly when you want a good option. That's particularly true if you also want something to play nice with GraphQL, OpenTelemetry, and SQLAlchemy - and whatever other functionality we need to integrate down the road.
