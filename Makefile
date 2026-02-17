.PHONY: help \
	reference-implementation-setup-install-dependencies \
	reference-implementation-setup \
	reference-implementation-run-for-hurl \
	reference-implementation-test-with-hurl-and-already-launched-server \
	reference-implementation-test-with-hurl \
	reference-implementation-test-with-bruno-and-already-launched-server \
	reference-implementation-test-with-bruno \
	running-processes-clean \
	non-default-files-clean \
	documentation-setup \
	documentation-dev \
	documentation-dev-host \
	documentation-build \
	documentation-preview \
	documentation-clean \
	bruno-generate \
	bruno-check

help:
	@echo "Reference Implementation:"
	@echo "  reference-implementation-setup"
	@echo "  reference-implementation-run-for-hurl"
	@echo "  reference-implementation-test-with-hurl"
	@echo "  reference-implementation-test-with-bruno"
	@echo "  running-processes-clean"
	@echo "  non-default-files-clean"
	@echo ""
	@echo "Bruno Collection:"
	@echo "  bruno-generate"
	@echo "  bruno-check"
	@echo ""
	@echo "Documentation:"
	@echo "  documentation-setup"
	@echo "  documentation-dev"
	@echo "  documentation-dev-host"
	@echo "  documentation-build"
	@echo "  documentation-preview"
	@echo "  documentation-clean"

########################
# Reference Implementation - Setup

reference-implementation-setup-install-dependencies:
	cd apps/api && pip install -r requirements.txt

reference-implementation-setup:
	make reference-implementation-setup-install-dependencies
	echo -e '\n\033[0;32m    INSTALLED DEPENDENCIES\033[0m\n'

########################
# Reference Implementation - Run

reference-implementation-run-for-hurl:  # WARNING clearly not production ready
	cd apps/api && JWT_SECRET=dxLmhnE0pRY2+vUlu+i5Pxh8LTxLBTgBWdp82W74mMs= uvicorn app.main:app --host 0.0.0.0 --port 3000

########################
# Reference Implementation - Tests

reference-implementation-test-with-hurl-and-already-launched-server:
	HOST=http://localhost:3000/api api/run-api-tests-hurl.sh

reference-implementation-test-with-hurl:
	@set -e; \
	cd apps/api && JWT_SECRET=dxLmhnE0pRY2+vUlu+i5Pxh8LTxLBTgBWdp82W74mMs= uvicorn app.main:app --host 0.0.0.0 --port 3000 & \
	SERVER_PID=$$!; \
	trap "kill $$SERVER_PID 2>/dev/null || true" EXIT; \
	sleep 1; \
	kill -0 "$$SERVER_PID" 2>/dev/null || exit 4; \
	make reference-implementation-test-with-hurl-and-already-launched-server && ( \
		make running-processes-clean; echo -e '\n\033[0;32m    TESTS OK\033[0m\n' && exit 0 \
	) || ( \
		make running-processes-clean; echo -e '\n\033[0;31m    TESTS FAILED\033[0m\n' && exit 1 \
	)

reference-implementation-test-with-bruno-and-already-launched-server:
	HOST=http://localhost:3000/api api/run-api-tests-bruno.sh

reference-implementation-test-with-bruno:
	@set -e; \
	cd apps/api && JWT_SECRET=dxLmhnE0pRY2+vUlu+i5Pxh8LTxLBTgBWdp82W74mMs= uvicorn app.main:app --host 0.0.0.0 --port 3000 & \
	SERVER_PID=$$!; \
	trap "kill $$SERVER_PID 2>/dev/null || true" EXIT; \
	sleep 1; \
	kill -0 "$$SERVER_PID" 2>/dev/null || exit 4; \
	make reference-implementation-test-with-bruno-and-already-launched-server && ( \
		make running-processes-clean; echo -e '\n\033[0;32m    TESTS OK\033[0m\n' && exit 0 \
	) || ( \
		make running-processes-clean; echo -e '\n\033[0;31m    TESTS FAILED\033[0m\n' && exit 1 \
	)

########################
# Cleaning

running-processes-clean:  # killing the parent is usually not enough, we should kill through this helper
	ps a -A -o pid,cmd \
	| grep "uvicorn app.main:app" \
	| grep -v grep \
	| awk '{print $$1}' \
	| xargs -I {} kill -9 {} \
	|| true

non-default-files-clean:
	rm -f apps/api/prisma/dev.db  # dev database

########################
# Bruno Collection

bruno-generate:
	bun api/hurl-to-bruno.js

bruno-check:
	bun api/hurl-to-bruno.js --check

########################
# Documentation

documentation-setup:
	cd apps/documentation && bun install

documentation-dev:
	cd apps/documentation && bun run dev

documentation-dev-host:
	cd apps/documentation && bun run dev --host

documentation-build:
	cd apps/documentation && bun run build

documentation-preview:
	cd apps/documentation && bun run preview

documentation-clean:
	rm -rf apps/documentation/.astro apps/documentation/dist apps/documentation/node_modules
