# Remote Packer runner — provisions a GCP VM that runs packer build in the cloud.
#
# No local Packer required. From UnusedOS/:
#   bash scripts/kicksecure/run-packer-on-gce.sh

terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.4"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

locals {
  dev_terraform = pathexpand("~/projects/dev-terraform")
}

module "vm" {
  source = "${local.dev_terraform}/modules/gcp_test_vm"

  name_prefix           = var.name_prefix
  instance_count        = var.instance_count
  machine_type          = var.machine_type
  zone                  = var.zone
  service_account_email = var.service_account_email
  network_tags          = ["packer-runner", "http-server", "https-server"]
  boot_disk_image       = "projects/debian-cloud/global/images/family/debian-12"
  boot_disk_size_gb     = var.boot_disk_size_gb
  startup_script = templatefile("${path.module}/startup-packer-runner.sh.tpl", {
    bucket_name       = var.bucket_name
    gcs_packer_prefix = var.gcs_packer_prefix
  })
}

module "outputs" {
  source = "${local.dev_terraform}/modules/gcp_test_outputs"

  project_id         = var.project_id
  instances          = module.vm.instances
  verify_script_path = abspath("${path.module}/verify.sh")
  write_verify_all   = false
}

output "instance_names" {
  value = module.outputs.instance_names
}

output "instance_zones" {
  value = module.outputs.instance_zones
}

output "kicksecure_image_name" {
  value = var.kicksecure_image_name
}

output "ssh_user" {
  value = var.ssh_user
}
