now=$(date +'%Y_%m_%d_%H_%M')
/home/pero/backup/backup_now.sh $now 2>&1 | tee /home/pero/backup/$now.log
scp /home/pero/backup/$now.log ikohut@merlin.fit.vutbr.cz:/mnt/matylda1/hradis/PERO/pero-ocr.fit.vutbr.cz_backup/log_timestamps/$now.log
(cat /home/pero/backup/$now.log | head -n 8; cat /home/pero/backup/$now.log | tail -n 15) | mail -s "PERO OCR - SERVER Bot - Backup LOG" ikohut@fit.vutbr.cz
rm /home/pero/backup/$now.log
 
