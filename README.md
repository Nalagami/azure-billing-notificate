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
3. Make Azure storage for the terraform state

```bash
STORAGE_ACCOUNT_NAME="billingnotificatestorage"
RESOURCE_GROUP_NAME="billingnotificate-rg"
CONTAINER_NAME="billingnotificatecontainer"
LOCATION=japaneast

az group create --name $RESOURCE_GROUP_NAME --location $LOCATION

az storage account create --name $STORAGE_ACCOUNT_NAME --resource-group $RESOURCE_GROUP_NAME --location $LOCATION --sku Standard_LRS

az storage container create --name $CONTAINER_NAME --account-name $STORAGE_ACCOUNT_NAME
```

4. Run the following commands

```bash
cd terraform
terraform init -reconfigure -backend-config=development.tfbackend
terraform plan
terraform apply
cd AppFunction
func azure functionapp publish "billingnotificate"
```

5, Assign the Billing Reader role to the created Managed Identity

- Open Cost Management and Billing -> Billing Account -> IAM.
- Add the Managed Identity of the Function App created earlier using Terraform as a Reader.
