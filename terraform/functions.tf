# 参考：https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/function_app_function

resource "azurerm_service_plan" "example" {
  name                = "example-service-plan"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  os_type             = "Linux"
  sku_name            = "Y1"
}

resource "azurerm_linux_function_app" "example" {
  name                = "bill-notification-function-app"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name

  storage_account_name       = azurerm_storage_account.example.name
  storage_account_access_key = azurerm_storage_account.example.primary_access_key
  service_plan_id            = azurerm_service_plan.example.id

  site_config {
    application_stack {
      python_version = "3.9"
    }
  }

  app_settings = {
    "APPINSIGHTS_INSTRUMENTATIONKEY" = azurerm_application_insights.example.instrumentation_key
  }

}

resource "azurerm_function_app_function" "example" {
  name            = "billing-notification-function"
  function_app_id = azurerm_linux_function_app.example.id
  language        = "Python"
  file {
    name    = "index.py"
    content = file("../src/index.py")
  }
  config_json = jsonencode({
    scriptFile = "index.py"
    bindings = [
      {
        name     = "myTimer",
        type     = "timerTrigger",
        schedule = "0 */5 * * * *"
      }
    ]
  })

}

resource "azurerm_log_analytics_workspace" "example" {
  name                = "example-workspace"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
}

resource "azurerm_monitor_diagnostic_setting" "example" {
  name               = "example"
  target_resource_id = azurerm_linux_function_app.example.id
  storage_account_id = azurerm_storage_account.example.id

  enabled_log {
    category = "FunctionAppLogs"
  }
  metric {
    category = "AllMetrics"
    enabled = false
  }
}

# application insights
resource "azurerm_application_insights" "example" {
  name                = "example-app-insights"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  application_type    = "other"
}
