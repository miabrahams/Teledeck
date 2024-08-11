BACKUP_DIR = ./data/db_backup
DATE := $(shell date +%Y%m%d)
DB_NAME = teledeck.db

backup-db:
	@mkdir -p $(BACKUP_DIR)
	cp $(DB_NAME) $(BACKUP_DIR)/database_$(DATE).db
	@echo "Database backed up to $(BACKUP_DIR)/database_$(DATE).db"


xo:
	xo schema -o ./data/xo $(DB_NAME)

update:
	python admin/admin.py --client-update

recycle:
	rm recyclebin/media/*

dump-schema:
	sqlite3 teledeck.db '.schema' > alembic/schema.sql

.PHONY: server tagger
server:
	@cd server && make dev

tagger:
	python tagger/server.py

.PHONY: grpc-update
grpc-update:
	python -m grpc_tools.protoc -I./AI/proto --python_out=./AI/proto --grpc_python_out=./AI/proto ./AI/proto/ai_server.proto
	protoc --go_out=./server/internal/genproto --go-grpc_out=./server/internal/genproto AI/proto/ai_server.proto

.PHONY: deploy-classifier
deploy-classifier:
	@cd AI && ./launch-classifier.sh

.PHONY: stop-classifier
stop-classifier:
	@cd AI && ./stop-classifier.sh
