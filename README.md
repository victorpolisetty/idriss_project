# IDRISS AI Token Finder for Farcaster

## Getting Started

- Make sure you have Python 3.11.10
- Make sure you have Poetry installed

### Installation and Setup for Development

```shell
git clone https://github.com/victorpolisetty/idriss_project.git
cd visualisation_station
poetry env use 3.11.10
poetry install && poetry shell
make install
```

## How to run agent

```shell
./scripts/run_single_agent.sh victorpolisetty/idriss_frontend --force
```
Warning: Docker must be running

## How to run frontend (tested using Brave Browser)

```shell
http://localhost:5555/
```

## How to generate DB file

```shell
cd packages/victorpolisetty/customs/idriss_token_finder/database
python db_setup.db
```

## How to deploy

Work in progress...

## Commands

Here are common commands you might need while working with the project:

### Resetting Docker

```shell
curl localhost:8080/hard_reset
```

### Formatting

```shell
make fmt
```

### Linting

```shell
make lint
```

### Testing

```shell
make test
```

### Locking

```shell
make hashes
```

### all

```shell
make all
```

## License

This project is licensed under the [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0)

