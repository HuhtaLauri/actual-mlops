VENV_PATH='.venv/bin/activate'
DOCKER_NAME='actual-mlops'
DOCKER_TAG='0.0.1'
AZURE_CONTAINER_REGISTRY='dndsregistry.azurecr.io'

lint:
	black src/

install:
	python3 -m pip install --upgrade pip
	# Used for packaging and publishing
	pip install setuptools wheel twine
	# Used for linting
	pip install black
	# Used for testing
	pip install pytest

env:
	. .env

build:
	docker build -f docker/Dockerfile -t $(AZURE_CONTAINER_REGISTRY)/$(DOCKER_NAME):$(DOCKER_TAG) .

push:
	docker push $(AZURE_CONTAINER_REGISTRY)/$(DOCKER_NAME):$(DOCKER_TAG)

pull:
	docker pull $(AZURE_CONTAINER_REGISTRY)/$(DOCKER_NAME):$(DOCKER_TAG)

run:
	docker run $(AZURE_CONTAINER_REGISTRY)/$(DOCKER_NAME):$(DOCKER_TAG)

run-it:
	docker run -it $(AZURE_CONTAINER_REGISTRY)/$(DOCKER_NAME):$(DOCKER_TAG) bash

collect-commits:
	python -m src.engineering.github.collector -s commits --repos src/engineering/github/repositories.txt
