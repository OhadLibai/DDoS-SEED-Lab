# Shared GCP Infrastructure for HTTP/2 Labs
# Base terraform configuration used by all labs

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

# Base variables - can be overridden by labs
variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "GCP Zone"
  type        = string
  default     = "us-central1-a"
}

variable "lab_name" {
  description = "Lab name for resource naming"
  type        = string
}

variable "apache_version" {
  description = "Apache version to deploy"
  type        = string
  default     = "2.4.55"
}

variable "attack_script" {
  description = "Attack script filename"
  type        = string
}

variable "default_connections" {
  description = "Default number of connections for the attack"
  type        = number
  default     = 512
}

# Shared firewall rules
resource "google_compute_firewall" "lab_firewall" {
  name    = "${var.lab_name}-firewall"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["22", "80", "8080"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["${var.lab_name}-lab"]
}

# Shared VM instance template
resource "google_compute_instance" "lab_instance" {
  name         = "${var.lab_name}-instance"
  machine_type = "f1-micro"
  zone         = var.zone
  tags         = ["${var.lab_name}-lab"]

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2204-lts"
      size  = 10
      type  = "pd-standard"
    }
  }

  network_interface {
    network = "default"
    access_config {}
  }

  metadata = {
    startup-script = templatefile("${path.root}/../shared/gcp/startup-base.sh", {
      lab_name = var.lab_name
      apache_version = var.apache_version
      attack_script = var.attack_script
      default_connections = var.default_connections
    })
  }

  labels = {
    lab = var.lab_name
    environment = "free-tier"
  }
}

# Shared outputs
output "instance_ip" {
  value = google_compute_instance.lab_instance.network_interface[0].access_config[0].nat_ip
}

output "ssh_command" {
  value = "ssh ubuntu@${google_compute_instance.lab_instance.network_interface[0].access_config[0].nat_ip}"
}

output "victim_url" {
  value = "http://${google_compute_instance.lab_instance.network_interface[0].access_config[0].nat_ip}"
}