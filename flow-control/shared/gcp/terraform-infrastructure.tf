# GCP Infrastructure for HTTP/2 Labs - Reusable Base Infrastructure
# Creates one f1-micro instance that can run all attack labs

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

# Variables
variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "infrastructure_name" {
  description = "Name for the infrastructure"
  type        = string
  default     = "http2-lab-infrastructure"
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

# Firewall rules
resource "google_compute_firewall" "lab_infrastructure" {
  name    = "${var.infrastructure_name}-firewall"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["22", "80", "8080", "8055", "8062"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["${var.infrastructure_name}"]
}

# Reusable VM instance
resource "google_compute_instance" "lab_infrastructure" {
  name         = var.infrastructure_name
  machine_type = "f1-micro"
  zone         = var.zone
  tags         = [var.infrastructure_name]

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2204-lts"
      size  = 20  # Slightly larger for multiple lab containers
      type  = "pd-standard"
    }
  }

  network_interface {
    network = "default"
    access_config {}
  }

  metadata = {
    startup-script = file("${path.module}/infrastructure-startup.sh")
  }

  labels = {
    purpose = "http2-attack-labs"
    environment = "educational"
    tier = "free"
  }
}

# Outputs
output "instance_external_ip" {
  description = "External IP of the lab infrastructure"
  value       = google_compute_instance.lab_infrastructure.network_interface[0].access_config[0].nat_ip
}

output "instance_internal_ip" {
  description = "Internal IP of the lab infrastructure"
  value       = google_compute_instance.lab_infrastructure.network_interface[0].network_ip
}

output "instance_name" {
  description = "Name of the infrastructure instance"
  value       = google_compute_instance.lab_infrastructure.name
}

output "ssh_command" {
  description = "SSH command to connect to the instance"
  value       = "gcloud compute ssh ${var.infrastructure_name} --zone=${var.zone}"
}

output "instance_zone" {
  description = "Zone of the instance"
  value       = var.zone
}