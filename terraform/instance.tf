resource "oci_core_instance" "weather_platform_k3s" {
  compartment_id      = var.compartment_id
  availability_domain = "lFqA:UK-LONDON-1-AD-1"
  display_name        = "weather-platform-k3s"
  shape               = "VM.Standard.A1.Flex"

  shape_config {
    ocpus         = 4
    memory_in_gbs = 24
  }

  source_details {
    source_type = "image"
    source_id   = "ocid1.image.oc1.uk-london-1.aaaaaaaafq3nyno7a72qsi6kkehqbpidfumkwwxjqapsj5l6qlojhrqn6mqa"
  }

  create_vnic_details {
    subnet_id        = oci_core_subnet.weather_platform_public_subnet.id
    assign_public_ip = true
    hostname_label   = "weather-platform-k3s"
  }
}