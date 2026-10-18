# UnusedOS GCP VM build + deploy test
#
# Shared VM module: ~/projects/dev-terraform
# Usage:
#   cd UnusedOS/terraform-test
#   cp terraform.tfvars.example terraform.tfvars
#   bash ../scripts/run_vm_build_deploy_test.sh

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
  network_tags          = ["unusedos-test", "http-server", "https-server"]
  boot_disk_size_gb     = var.boot_disk_size_gb
  startup_script = join("\n\n", [
    file("${local.dev_terraform}/scripts/install-gcloud-cli.sh"),
    templatefile("${path.module}/startup-unusedos.sh.tpl", {
      bucket_name            = var.bucket_name
      gcs_deployments_prefix = var.gcs_deployments_prefix
      collect_paths          = var.collect_paths
    }),
  ])
}

module "outputs" {
  source = "${local.dev_terraform}/modules/gcp_test_outputs"

  project_id         = var.project_id
  instances          = module.vm.instances
  verify_script_path = abspath("${path.module}/verify.sh")
  write_verify_all   = true
  verify_all_path    = "${path.module}/verify_all.sh"
}

output "instance_names" {
  value = module.outputs.instance_names
}

output "instance_zones" {
  value = module.outputs.instance_zones
}

output "instance_ips" {
  value = module.vm.instance_ips
}

output "ssh_commands" {
  value = module.outputs.ssh_commands
}

output "verify_commands" {
  value = module.outputs.verify_commands
}
