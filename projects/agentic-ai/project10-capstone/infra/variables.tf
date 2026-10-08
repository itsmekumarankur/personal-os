variable "region" {
  type    = string
  default = "ap-south-1"
}

variable "name" {
  description = "Prefix for every resource. Also the prefix of the two secrets."
  type        = string
  default     = "agentic-platform"
}

variable "image_tag" {
  description = "Image tag to run. The pipeline passes the git commit id."
  type        = string
}

variable "model" {
  type    = string
  default = "claude-sonnet-4-5"
}

variable "alarm_email" {
  description = "Email that receives alarms. Leave empty to create the alarms without a subscriber."
  type        = string
  default     = ""
}

variable "certificate_arn" {
  description = "ACM certificate for HTTPS. Empty means HTTP only, which is fine for a learning stack and not for real traffic."
  type        = string
  default     = ""
}

variable "log_retention_days" {
  type    = number
  default = 30
}
