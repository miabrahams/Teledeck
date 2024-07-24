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
	python admin/tl_client_update.py

recycle:
	rm recyclebin/media/*

dump-schema:
	sqlite3 teledeck.db '.schema' > alembic/schema.sql

.PHONY: server tagger
server:
	@cd server && make dev

tagger:
	python tagger/server.py