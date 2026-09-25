resource "oci_core_vcn" "weather_platform_vcn" {
  compartment_id = var.compartment_id
  display_name   = "weather-platform-vcn"
  cidr_blocks    = ["10.0.0.0/16"]
  dns_label      = "vcn08191939"
}

resource "oci_core_internet_gateway" "weather_platform_igw" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.weather_platform_vcn.id
  display_name   = "Internet Gateway weather-platform-vcn"
  enabled        = true
}

resource "oci_core_route_table" "weather_platform_route_table" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.weather_platform_vcn.id

  display_name = "Default Route Table for weather-platform-vcn"

  route_rules {
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
    network_entity_id = oci_core_internet_gateway.weather_platform_igw.id
  }
}

resource "oci_core_default_security_list" "weather_platform_security_list" {
  manage_default_resource_id = oci_core_vcn.weather_platform_vcn.default_security_list_id

  egress_security_rules {
    protocol    = "all"
    destination = "0.0.0.0/0"
    stateless   = false
  }

  ingress_security_rules {
    protocol  = "6"
    source    = "0.0.0.0/0"
    stateless = false

    tcp_options {
      min = 22
      max = 22
    }
  }

  ingress_security_rules {
    protocol  = "1"
    source    = "0.0.0.0/0"
    stateless = false

    icmp_options {
      type = 3
      code = 4
    }
  }

  ingress_security_rules {
    protocol  = "1"
    source    = "10.0.0.0/16"
    stateless = false

    icmp_options {
      type = 3
    }
  }

  ingress_security_rules {
    protocol    = "6"
    source      = "0.0.0.0/0"
    stateless   = false
    description = "Airflow NodePort"

    tcp_options {
      min = 30080
      max = 30080
    }
  }

  ingress_security_rules {
    protocol    = "6"
    source      = "0.0.0.0/0"
    stateless   = false
    description = "FastAPI NodePort"

    tcp_options {
      min = 30001
      max = 30001
    }
  }

  ingress_security_rules {
    protocol    = "6"
    source      = "0.0.0.0/0"
    stateless   = false
    description = "Prediction Dashboard NodePort"

    tcp_options {
      min = 30002
      max = 30002
    }
  }
}
resource "oci_core_subnet" "weather_platform_public_subnet" {
  compartment_id             = var.compartment_id
  vcn_id                     = oci_core_vcn.weather_platform_vcn.id
  cidr_block                 = "10.0.0.0/24"
  display_name               = "weather-platform-public-subnet"
  dns_label                  = "subnet08191939"
  prohibit_internet_ingress  = false
  prohibit_public_ip_on_vnic = false

  route_table_id = oci_core_route_table.weather_platform_route_table.id

  security_list_ids = [
    oci_core_default_security_list.weather_platform_security_list.id
  ]
}