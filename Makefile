.PHONY: help install test run down clean tar

help:
	@echo "make install   - install python deps"
	@echo "make test      - run tests"
	@echo "make run       - run the service in Docker (builds image)"
	@echo "make down      - stop Docker services"
	@echo "make clean     - teardown + prune docker leftovers"
	@echo "make tar       - create source tarball (includes git history)"

install:
	@python -m pip install -U pip
	pip install -r requirements.txt

test:
	PYTHONPATH=. pytest -q

run:
	docker compose up --build -d
	@echo "App running at http://localhost:8000"

down:
	docker compose down

clean:
	-docker compose down -v --remove-orphans
	-docker system prune -f

tar:
	@mkdir -p build
	@name=kopi_challenge_$$(date +%Y%m%d%H%M).tar.gz; \
	echo "Creating build/$$name (with commit history)"; \
	tar -czf build/$$name . --exclude './.venv' --exclude './build' --exclude './__pycache__'
	@ls -lh build/
