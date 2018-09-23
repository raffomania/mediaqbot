.PHONY: run

debug: dev-setup
	pipenv run python mediaq-server/main.py

dev-setup:
	pipenv install

deploy-setup:
	test -d venv || virtualenv venv
	./venv/bin/pip install -Ur requirements.txt
