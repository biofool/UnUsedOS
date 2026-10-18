locals {
  kicksecure_url = "https://www.kicksecure.com/download/libvirt/${var.kicksecure_version}/Kicksecure-CLI-${var.kicksecure_version}.Intel_AMD64.qcow2.libvirt.xz"
}

source "googlecompute" "converter" {
  project_id   = var.project_id
  zone         = var.zone
  region       = var.region
  machine_type = var.machine_type

  source_image_family     = "debian-12"
  source_image_project_id = "debian-cloud"

  disk_size = var.disk_size_gb
  disk_type = "pd-ssd"

  image_name        = "${var.builder_name_prefix}-${formatdate("YYYYMMDDhhmmss", timestamp())}"
  skip_create_image = true

  ssh_username = "admin"
  use_os_login = false
  use_google_compute_credentials = true

  service_account_email = var.service_account_email
  scopes = [
    "https://www.googleapis.com/auth/cloud-platform",
  ]

  metadata = {
    block-project-ssh-keys = "true"
  }

  network            = "default"
  subnetwork         = "default"
  use_internal_ip    = false
  omit_external_ip   = false
  disable_default_service_account = false
}

build {
  name    = "kicksecure-gcp-import"
  sources = ["source.googlecompute.converter"]

  provisioner "shell" {
    script          = "${path.root}/scripts/cloud-convert-import.sh"
    execute_command = "{{ .Vars }} sudo -E bash '{{ .Path }}'"
    environment_vars = [
      "PROJECT_ID=${var.project_id}",
      "ZONE=${var.zone}",
      "IMPORT_BUCKET=${var.import_bucket}",
      "IMPORT_PREFIX=${var.import_prefix}",
      "KICKSECURE_URL=${local.kicksecure_url}",
      "GCP_IMAGE_NAME=${var.gcp_image_name}",
      "IMPORT_OS=${var.import_os}",
    ]
  }

  post-processor "manifest" {
    output     = "manifest.json"
    strip_path = true
    custom_data = {
      gcp_image_name = var.gcp_image_name
      project_id     = var.project_id
      image_self_link = "projects/${var.project_id}/global/images/${var.gcp_image_name}"
    }
  }
}
