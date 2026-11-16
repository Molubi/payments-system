variable "owner" {
  description = "Team or individual owning the service"
  type        = string

  validation {
    condition     = length(trimspace(var.owner)) > 0
    error_message = "The 'owner' cost tag must not be empty."
  }
}

variable "service" {
  description = "Name of the service"
  type        = string

  validation {
    condition     = length(trimspace(var.service)) > 0
    error_message = "The 'service' cost tag must not be empty."
  }
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "The 'environment' cost tag must be one of: dev, staging, prod."
  }
}

variable "cost_centre" {
  description = "Finance cost centre code"
  type        = string

  validation {
    condition     = length(trimspace(var.cost_centre)) > 0
    error_message = "The 'cost_centre' cost tag must not be empty."
  }
}
