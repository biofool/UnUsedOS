variable "project_id" {
  type = string
}

variable "zone" {
  type    = string
  default = "us-central1-a"
}

variable "region" {
  type    = string
  default = "us-central1"
}

variable "machine_type" {
  type    = string
  default = "n2-highcpu-8"
}

variable "disk_size_gb" {
  type    = number
  default = 100
}

variable "import_bucket" {
  type = string
}

variable "import_prefix" {
  type    = string
  default = "images/kicksecure-cli"
}

variable "kicksecure_version" {
  type    = string
  default = "18.1.4.2"
}

variable "gcp_image_name" {
  type    = string
  default = "kicksecure-cli-18-1-4-2"
}

variable "service_account_email" {
  type = string
}

variable "import_os" {
  type    = string
  default = "debian-12"
}

variable "builder_name_prefix" {
  type    = string
  default = "packer-kicksecure-import"
}
