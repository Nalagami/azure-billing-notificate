variable "resource_group_location" {
  type        = string
  default     = "East US 2"
  description = "Location of the resource group."
}

variable "python_version" {
  type        = string
  default     = "3.11"
  description = "Python version to use."
}

variable "subscription_id" {
  type        = string
  description = "Azure subscription ID."
}

variable "billing_account_id" {
  type        = string
  description = "Billing account ID."
}

variable "webhook_url" {
  type        = string
  description = "Webhook URL to send notifications."
}
