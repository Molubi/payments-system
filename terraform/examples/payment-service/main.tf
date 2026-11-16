module "payment_service" {
  source = "../../modules/payment-service"

  owner       = "kgotso"
  service     = "payments"
  environment = "dev"
  cost_centre = "finance"
}