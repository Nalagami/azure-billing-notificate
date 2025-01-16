# 参考：https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/function_app_function

resource "azurerm_resource_group" "rg" {
  location = var.resource_group_location
  name     = "billing-notification-rg"
}

resource "azurerm_storage_account" "example" {
  name                     = "billingnotifstor"
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}
resource "azurerm_service_plan" "example" {
  name                = "plan-billing-notification-prd-eastus-001"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  os_type             = "Linux"
  sku_name            = "Y1"
}

resource "azurerm_linux_function_app" "example" {
  name                = "functions-billing-notification"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  service_plan_id     = azurerm_service_plan.example.id

  storage_account_name       = azurerm_storage_account.example.name
  storage_account_access_key = azurerm_storage_account.example.primary_access_key

  site_config {
    application_stack {
      # Python のバージョン
      python_version = var.python_version
    }
    cors {
      # Azure Portal からのFunctionを呼び出すために必要
      allowed_origins = [
        "https://portal.azure.com"
      ]
      support_credentials = true # 必要に応じてクレデンシャルサポートを有効化
    }
    application_insights_key               = azurerm_application_insights.azure_functions_for_notice_application_insights.instrumentation_key
    application_insights_connection_string = azurerm_application_insights.azure_functions_for_notice_application_insights.connection_string
  }

  app_settings = {
    # Azure Functions の設定
    "BILLING_ACCOUNT_ID" = var.billing_account_id
    "WEBHOOK_URL"        = var.webhook_url
  }

  identity {
    type = "SystemAssigned" # システム割り当て ID を有効化
  }

}

# 「コスト管理の閲覧者」ロールを Function App に割り当て
resource "azurerm_role_assignment" "example" {
  principal_id = azurerm_linux_function_app.example.identity[0].principal_id
  # Billing Reader のロール定義 ID
  role_definition_id = "/providers/Microsoft.Authorization/roleDefinitions/72fafb9e-0641-4937-9268-a91bfd8191a3"
  scope              = "/subscriptions/${var.subscription_id}"
}

#billing の閲覧者ロールを割り当て
resource "azurerm_role_assignment" "example2" {
  principal_id = azurerm_linux_function_app.example.identity[0].principal_id
  # Billing Reader のロール定義 ID
  role_definition_id = "/providers/Microsoft.Authorization/roleDefinitions/fa23ad8b-c56e-40d8-ac0c-ce449e1d2c64"
  scope              = "/providers/Microsoft.Billing/billingAccounts/${var.billing_account_id}"
}

# ログなどを見たいので Azure Functions で  Application Insights を有効化
resource "azurerm_application_insights" "azure_functions_for_notice_application_insights" {
  application_type    = "other"
  name                = "functions-billing-notification-app-insights"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  sampling_percentage = 0
}
