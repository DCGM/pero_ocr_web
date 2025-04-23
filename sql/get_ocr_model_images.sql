SELECT I.id FROM ocr_training_documents AS OTD
JOIN documents AS D ON OTD.document_id = D.id
JOIN images AS I ON D.id = I.document_id
WHERE OTD.ocr_id='e64aab60-1b91-4796-8453-d8911c1bd3f2'