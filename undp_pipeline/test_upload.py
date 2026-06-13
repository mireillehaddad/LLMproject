from google.cloud import storage

bucket_name = "undp-project-documents-llm-2026"

client = storage.Client()
bucket = client.bucket(bucket_name)

blob = bucket.blob("test.txt")
blob.upload_from_string("Hello UNDP")

print("Uploaded successfully")