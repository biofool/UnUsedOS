variable "project_id" {
  type    = string
  default = "project-135adecf-38fc-4e43-ae4"
}

variable "region" {
  type    = string
  default = "us-central1"
}

variable "zone" {
  type    = string
  default = "us-central1-a"
}

variable "name_prefix" {
  type    = string
  default = "packer-kicksecure-runner"
}

variable "machine_type" {
  type    = string
  default = "e2-standard-4"
}

variable "boot_disk_size_gb" {
  type    = number
  default = 30
}

variable "bucket_name" {
  type    = string
  default = "scraper-intl-deployments-239573"
}

variable "gcs_packer_prefix" {
  type    = string
  default = "deployments/packer-kicksecure/latest"
}

variable "service_account_email" {
  type    = string
  default = "scraper-intl-sheets@project-135adecf-38fc-4e43-ae4.iam.gserviceaccount.com"
}

variable "instance_count" {
  type    = number
  default = 1
}

variable "kicksecure_image_name" {
  type    = string
  default = "kicksecure-cli-18-1-4-2"
}

variable "ssh_user" {
  type    = string
  default = "admin"
}
