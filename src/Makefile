IMAGE_NAME=box_uploader

# Check if .env file exists for variable parsing
ifneq ($(wildcard .env),)
    # Extract ROOT_DIR from .env file
    ROOT_DIR := $(shell grep -E '^ROOT_DIR=' .env 2>/dev/null | cut -d '=' -f2)
    ifneq ($(ROOT_DIR),)
        # If ROOT_DIR is defined, use it for data mount
        DATA_MOUNT := -v $(ROOT_DIR):/data
    else
        # Error out immediately if ROOT_DIR is missing
        $(error ERROR: ROOT_DIR is not defined in .env file. Please add ROOT_DIR=/path/to/your/data to your .env file)
    endif
else
    # Error out immediately if .env is missing
    $(error ERROR: .env file is missing. Please create a .env file based on env_template)
endif

# Add .env file to all docker commands
COMMON_DOCKER_ARGS=-v $(PWD):/app/src \
--env-file .env

.PHONY: build init-db scan-files run-upload status help watch-status inter

help:
	@echo "Box File Uploader"
	@echo "-----------------"
	@echo "Available commands:"
	@echo "  make build         - Build the Docker image"
	@echo "  make init-db       - Initialize the SQLite database"
	@echo "  make scan-files    - Scan files and populate the database (uses ROOT_DIR from .env or pass DIR=path/to/dir)"
	@echo "  make run-upload    - Run the uploader with 4 concurrent processes"
	@echo "  make status        - Check the current upload status"
	@echo "  make watch-status  - Watch upload status with live updates"
	@echo "  make inter         - Start an interactive shell in the container"
	@echo ""
	@echo "Current data mount: $(DATA_MOUNT)"

build:
	docker build -t $(IMAGE_NAME) .

init-db: build
	docker run --rm -it $(COMMON_DOCKER_ARGS) $(DATA_MOUNT) $(IMAGE_NAME) python src/scripts/db_setup.py

scan-files: build
	docker run --rm $(COMMON_DOCKER_ARGS) $(DATA_MOUNT) $(IMAGE_NAME) python src/scripts/scan_files.py

run-upload: build
	docker run --rm -it $(COMMON_DOCKER_ARGS) $(DATA_MOUNT) $(IMAGE_NAME) python src/scripts/upload.py

status: build
	docker run --rm $(COMMON_DOCKER_ARGS) $(DATA_MOUNT) $(IMAGE_NAME) python src/scripts/check_status.py

watch-status: build
	docker run --rm $(COMMON_DOCKER_ARGS) $(DATA_MOUNT) $(IMAGE_NAME) python src/scripts/check_status.py --watch

inter: build
	docker run --rm -it $(COMMON_DOCKER_ARGS) $(DATA_MOUNT) $(IMAGE_NAME) /bin/bash

flask: build
	docker run --rm -it -p 4999:4999 $(COMMON_DOCKER_ARGS) $(DATA_MOUNT) $(IMAGE_NAME) python src/scripts/app.py
