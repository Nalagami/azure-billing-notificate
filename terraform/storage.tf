resource "azurerm_storage_account" "example" {
  # storageの命名規則は意外と厳しいので注意が必要
  name                     = "azurebillingnotification"
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}
