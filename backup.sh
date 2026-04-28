#!/bin/bash
# EntokMart Backup Script
# Usage: ./backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/indra/backups"
DB_PATH="/home/indra/.local/share/opencode/worktree/7dde875492ee88cb7096a08a608792e33bff079a/sunny-star/instance/entokmart.db"
UPLOADS_DIR="/home/indra/.local/share/opencode/worktree/7dde875492ee88cb7096a08a608792e33bff079a/sunny-star/static/uploads"

# Create backup directory if not exists
mkdir -p $BACKUP_DIR

# Backup database
echo "Backup database..."
cp $DB_PATH $BACKUP_DIR/entokmart_db_$DATE.sqlite

# Backup uploads
echo "Backup uploads..."
tar -czf $BACKUP_dir/entokmart_uploads_$DATE.tar.gz -C "$(dirname $UPLOADS_DIR)" uploads 2>/dev/null

# Keep only last 7 backups
echo "Cleaning old backups..."
find $BACKUP_DIR -name "entokmart_*" -mtime +7 -delete

echo "✅ Backup completed: $DATE"
echo "📁 Files: entokmart_db_$DATE.sqlite, entokmart_uploads_$DATE.tar.gz"