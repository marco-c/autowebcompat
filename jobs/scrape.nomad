job "autowebcompat-scrape" {
  datacenters = ["dc1"]
  type = "batch"
  parameterized {
    payload = "forbidden"
    meta_required = ["dataset_path"]
  }

  group "collect" {
    task "collect.py" {
      driver = "docker"
      config {
        image = "gabrielv/autowebcompat:web"
        args = ["python", "scraper/collect.py"]
        volumes = [
          "${NOMAD_META_dataset_path}:/data",
        ]
      }
      template {
        data = <<EOF
          DATA_DIR = "/data"
          {{- range service "selenium-hub" }}
            HUB_HOST = {{ .Address }}
            HUB_PORT = {{ .Port }}
          {{- end }}
        EOF
        destination = "local/generated.env"
        env = true
      }
      resources {
        cpu = 1000
        memory = 800
      }
    }
  }
}
