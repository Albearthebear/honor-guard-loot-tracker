# Google Cloud Run Setup Guide

This guide will help you set up the necessary Google Cloud resources and GitHub Secrets for deploying the Honor Guard Loot Tracker to Google Cloud Run.

## Prerequisites

1. A Google Cloud Platform account
2. The `gcloud` CLI installed locally (optional, but helpful for testing)
3. Admin access to the GitHub repository

## Step 1: Create a Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Click on the project dropdown at the top of the page
3. Click "New Project"
4. Enter a name for your project (e.g., "honor-guard-loot-tracker")
5. Click "Create"

## Step 2: Enable Required APIs

1. In the Google Cloud Console, go to "APIs & Services" > "Library"
2. Search for and enable the following APIs:
   - Cloud Run API
   - Container Registry API
   - Cloud Build API
   - IAM API

## Step 3: Create a Service Account

1. In the Google Cloud Console, go to "IAM & Admin" > "Service Accounts"
2. Click "Create Service Account"
3. Enter a name (e.g., "github-actions")
4. Click "Create and Continue"
5. Add the following roles:
   - Cloud Run Admin
   - Storage Admin
   - Service Account User
   - Cloud Build Editor
6. Click "Continue" and then "Done"

## Step 4: Create and Download a Service Account Key

1. In the service accounts list, find the service account you just created
2. Click the three dots menu on the right and select "Manage keys"
3. Click "Add Key" > "Create new key"
4. Select "JSON" and click "Create"
5. The key file will be downloaded to your computer

## Step 5: Add GitHub Secrets

1. Go to your GitHub repository
2. Click on "Settings" > "Secrets and variables" > "Actions"
3. Click "New repository secret"
4. Add the following secrets:
   - Name: `GCP_PROJECT_ID`
     - Value: Your Google Cloud Project ID (found in the Google Cloud Console)
   - Name: `GCP_SA_KEY`
     - Value: The entire contents of the JSON key file you downloaded

## Step 6: Verify Setup

1. Make a small change to your repository and push it to the main branch
2. Go to the "Actions" tab in your GitHub repository
3. You should see the workflow running
4. Once completed, you can find the deployed URL in the Google Cloud Console under "Cloud Run"

## Troubleshooting

If the deployment fails, check the following:

1. Ensure all required APIs are enabled
2. Verify the service account has the correct permissions
3. Check that the GitHub Secrets are correctly set up
4. Look at the workflow logs in the GitHub Actions tab for specific error messages 