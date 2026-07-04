# LLMproject

## Step 1: Create a GCP Project
### Open:
Google Cloud Console
### Sign in with your Google account.
### At the top of the page, click the Project Selector (it may show an existing project name).
### Click New Project.
### Fill in:
Project name: undp-project-documents
Project ID: (GCP generates one automatically; you can customize if available)
Organization: Leave as default if you don't have one.
### Click Create.
### Wait about 30 seconds and then select the new project from the project list.

## Step 2: Enable Billing

If this is your first GCP project:

### Go to:
Google Cloud Billing
### Link the project to a billing account.
If you don't have one yet, create a billing account and attach a payment method.


## Step 3: Enable Required APIs

### For your UNDP pipeline, enable:

### Go to:
APIs & Services Dashboard
### Click Enable APIs and Services.
### Enable:
Cloud Storage API
BigQuery API
Cloud Run API
Artifact Registry API
Cloud Composer API

## Step 4: Install gcloud CLI


## Step 5: Connect Your Local Machine

### Login:

gcloud auth login

### Set the project:

gcloud config set project undp-project-documents

### Verify:

gcloud config list


### Create a bucket. Bucket names must be globally unique, so use something like:

gcloud storage buckets create gs://undp-project-documents-llm-2026 --location=northamerica-northeast1

Then verify:

gcloud storage buckets list


