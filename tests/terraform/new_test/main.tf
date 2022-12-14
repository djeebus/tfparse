// necessary to make repro valid
terraform {
  required_providers {
    aws = {
      source = "hashicorp/aws"
      version = "4.46.0"
    }
  }
}

provider "aws" {}
provider "aws" {
  alias = "shell"
}

locals {
  custom_certificate_body  = "--body--"
  custom_certificate_chain = "--chain--"
}

variable "env_name" {
  default = "--hello--"
}

variable "name" {
  default = "--name--"
}

variable "custom_certificate" {
  default = null
}

resource "aws_route53_zone" "zone" {
  name = "some-zone"
}

// actual repro
module "utils_naming_degradation" {
  source    = "./utils/naming_degradation"
  providers = {}
  env_name  = var.env_name
  names     = {
    name = {
      components = [var.name]
      max_length = -1
    }
    validate_certificate_name = {
      components = [var.name]
      max_length = 60
    }
  }
}

module "validate_certificate_files" {
  source    = "./utils/local_script"
  providers = {
    aws   = aws
    shell = shell
  }
  count    = var.custom_certificate == null ? 0 : 1
  env_name = var.env_name
  name     = module.utils_naming_degradation.names.validate_certificate_name[1]
  create   = {
    script_file = "${path.module}/script/validate_certificate_files/validate_certificate_files.py"
    arguments   = [
      aws_route53_zone.zone.name,
      var.custom_certificate.private_key,
      local.custom_certificate_body,
      local.custom_certificate_chain
    ]
  }
}

