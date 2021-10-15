now=$1
echo 'BACKUP LOG FROM: '$now
echo '*******************************************'
echo
echo 'BACKUPING: pero-ocr.fit.vutbr.cz:/mnt/data/pero_ocr_web_data/'
echo 'RUNNING: rsync -av -e ssh /mnt/data/pero_ocr_web_data/ ikohut@merlin.fit.vutbr.cz:/mnt/matylda1/hradis/PERO/pero-ocr.fit.vutbr.cz_backup/pero_ocr_web_data/'
echo
echo 'RSYNC LOG'
echo '###########################################'
rsync -av -e ssh /mnt/data/pero_ocr_web_data/ ikohut@merlin.fit.vutbr.cz:/mnt/matylda1/hradis/PERO/pero-ocr.fit.vutbr.cz_backup/pero_ocr_web_data/
echo '###########################################'
database_timestamp=$now'_db.sql'
echo
echo 'BACKUPING DATABASE: pero_ocr_web'
echo 'RUNNING: pg_dump --host=localhost --dbname=pero_ocr_web --username=postgres -Fc > '$database_timestamp
PGPASSWORD=$PASSWORD pg_dump --host=localhost --dbname=pero_ocr_web --username=postgres -Fc > /home/pero/backup/$database_timestamp || { rm /home/pero/backup/$database_timestamp; echo 'DUMP FAILED'; exit 1; }
echo 'RUNNING: scp /home/pero/backup/'$database_timestamp' ikohut@merlin.fit.vutbr.cz:/mnt/matylda1/hradis/PERO/pero-ocr.fit.vutbr.cz_backup/database_timestamps/'$database_timestamp
echo 
echo 'SCP LOG'
echo '###########################################'
scp /home/pero/backup/$database_timestamp ikohut@merlin.fit.vutbr.cz:/mnt/matylda1/hradis/PERO/pero-ocr.fit.vutbr.cz_backup/database_timestamps/$database_timestamp && echo 'SUCCESS'
rm /home/pero/backup/$database_timestamp
echo '###########################################'
echo
echo '*******************************************'

