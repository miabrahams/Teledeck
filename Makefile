BACKUP_DIR = ./data/db_backup
DATE := $(shell date +%Y%m%d)

backup_db:
	@mkdir -p $(BACKUP_DIR)
	cp teledeck.db $(BACKUP_DIR)/database_$(DATE).db
	@echo "Database backed up to $(BACKUP_DIR)/database_$(DATE).db"