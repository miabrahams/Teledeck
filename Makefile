BACKUP_DIR = ./data/db_backup
DATE := $(shell date +%Y%m%d)
DB_NAME = teledeck.db

backup_db:
	@mkdir -p $(BACKUP_DIR)
	cp $(DB_NAME) $(BACKUP_DIR)/database_$(DATE).db
	@echo "Database backed up to $(BACKUP_DIR)/database_$(DATE).db"


xo:
	xo schema -o ./data/xo $(DB_NAME)