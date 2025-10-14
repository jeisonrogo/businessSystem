# =============================================================================
# APP RUNNER MODULE VARIABLES
# =============================================================================

variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID for App Runner VPC connector"
  type        = string
}

variable "subnet_ids" {
  description = "Subnet IDs for App Runner VPC connector"
  type        = list(string)
}

variable "container_image_uri" {
  description = "Container image URI for the application"
  type        = string
}

variable "container_port" {
  description = "Container port for the application"
  type        = number
  default     = 8000
}

variable "environment_variables" {
  description = "Environment variables for the application"
  type        = map(string)
  default     = {}
}

variable "max_concurrency" {
  description = "Maximum concurrent requests per instance"
  type        = number
  default     = 100
}

variable "max_size" {
  description = "Maximum number of instances"
  type        = number
  default     = 10
}

variable "min_size" {
  description = "Minimum number of instances"
  type        = number
  default     = 1
}

variable "auto_scaling_enabled" {
  description = "Enable auto scaling"
  type        = bool
  default     = true
}

variable "auto_scaling_max_concurrency" {
  description = "Auto scaling maximum concurrency"
  type        = number
  default     = 100
}

variable "auto_scaling_min_size" {
  description = "Auto scaling minimum size"
  type        = number
  default     = 1
}

variable "auto_scaling_max_size" {
  description = "Auto scaling maximum size"
  type        = number
  default     = 10
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
