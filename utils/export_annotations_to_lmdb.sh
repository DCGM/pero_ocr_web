
# docuements (id) to export
DOCUMENTS="3f1ff962d0774b2988dead1a831013c1 91000d1e3fe2413f94e18ce3d5dd270c 094528f36996402d9ddcc05d8b2a2d57 f113b88c63744dfb90a0029eccb48473"

PERO_PATH=/home/ihradis/projects/2018-01-15_PERO/pero-master

#LMDB to add lines to
LMDB_PATH=./DATA/lmdb_czech_1024.2019-10-21.all

# source dataset path
DATASET=./DATA/
TRN_DATASET_FILE=data.trn

# these will be deleted and rewritten
# path with the created dataset
OUTPUT_PATH=./DATA_OUT/
# path with  parse_folder output
FOLDER_PATH=./out/



rm -r $OUTPUT_PATH
rm -r "$FOLDER_PATH"
mkdir -p ./$FOLDER_PATH/images
mkdir -p ./$FOLDER_PATH/page

rm *.zip
for i in $DOCUMENTS
do 
    wget -T 1000 -O ${i}.zip https://pchradis-stud.fit.vutbr.cz:2000/document/get_document_annotated_pages/${i/.xml/}
    mkdir -p ${i}
    rm -r ${i}/
    unzip ${i}.zip -d ${i}/

    for j in `ls ${i}/ | grep xml`
    do 
       wget -O ./$FOLDER_PATH/images/${j/.xml/}.jpg https://pchradis-stud.fit.vutbr.cz:2000/document/get_image/${i}/${j/.xml/}
    done
    cp ${i}/*.xml ./$FOLDER_PATH/page
done

mkdir -p "$OUTPUT_PATH"
cp -r $LMDB_PATH $OUTPUT_PATH

python $PERO_PATH/utils/extract_transcriptions_from_page_xml.py --input-dir ./$FOLDER_PATH/page --output $OUTPUT_PATH/new_data.ann

python $PERO_PATH/user_scripts/parse_folder.py -c config1.ini


python $PERO_PATH/utils/lmdb_add_images.py -i $OUTPUT_PATH/new_data.ann --image-path $FOLDER_PATH/lines --lmdb $OUTPUT_PATH/lmdb_*/

cp $DATASET/*.* $OUTPUT_PATH
for i in `seq 5`
do
    cat $OUTPUT_PATH/new_data.ann >> $OUTPUT_PATH/$TRN_DATASET_FILE
done
cat $OUTPUT_PATH/$TRN_DATASET_FILE | shuf > temp.trn
mv temp.trn $OUTPUT_PATH/$TRN_DATASET_FILE



