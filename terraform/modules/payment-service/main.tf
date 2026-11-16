resource "azurerm_resource_group" "this" {
  name     = "${var.service}-${var.environment}"
  location = "South Africa North"

  tags = {
    owner       = var.owner
    service     = var.service
    environment = var.environment
    cost_centre = var.cost_centre
  }
}