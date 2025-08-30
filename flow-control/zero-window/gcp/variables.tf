# zero-window specific variables
# Uses shared/gcp/terraform-base.tf

# Lab-specific configuration
locals {
  lab_name = "zero-window"
  apache_version = "2.4.55"
  attack_script = "zero_window_attack.py"
  default_connections = 512
}

# Import shared terraform base
module "lab_base" {
  source = "../../shared/gcp"
  
  project_id = var.project_id
  lab_name = local.lab_name
  apache_version = local.apache_version
  attack_script = local.attack_script
  default_connections = local.default_connections
}

# Pass through required variable
variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

# Pass through outputs
output "instance_ip" {
  value = module.lab_base.instance_ip
}

output "ssh_command" {
  value = module.lab_base.ssh_command
}

output "victim_url" {
  value = module.lab_base.victim_url
}