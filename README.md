# azure-billing-notificate/terraform

## Description
This repository contains the terraform code to deploy the Azure Function that will send the billing notification to the specified email.

## Requirements
- Terraform installed
- Azure CLI installed
- Azure Subscription
- Azure Storage Account
- Azure Function App

## How to use
1. Clone the repository
2. Change the values in the `variables.tf` file
3. Run the following commands:
```bash
cd terraform
terraform init
terraform plan
terraform apply
```