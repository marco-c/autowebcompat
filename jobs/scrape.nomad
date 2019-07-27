job "autowebcompat-scrape" {
  datacenters = ["dc1"]
  type = "batch"
  parameterized {
    payload = "forbidden"
    meta_required = ["dataset_path"]
  }

  group "collect" {
    reschedule {
      attempts = 0
      unlimited = false
    }
    restart {
      attempts = 0
    }

    constraint {
      attribute = "${meta.code_path}"
      operator = "is_set"
    }
    task "collect.py" {
      driver = "docker"
      config {
        image = "gabrielv/autowebcompat:web"
        args = ["python", "scraper/collect.py"]
        volumes = [
          "${meta.code_path}:/autowebcompat",
          "${NOMAD_META_dataset_path}:/data",
        ]
      }
      env {
        POSTGRES_USER = "user1"
        POSTGRES_DB = "autowebcompat"
        SECRET_KEY = "fake"
        DATA_DIR = "/data"
        TIMESTAMP = "${meta.timestamp}"
      }
      template {
        data = <<-EOF
          {{- range service "postgres" }}
            POSTGRES_HOST = {{ .Address | toJSON}}
            POSTGRES_PORT = {{ .Port | toJSON}}
          {{- end }}
          {{- with secret "autowebcompat/web/postgres_password" }}
            POSTGRES_PASSWORD = {{.Data.val | toJSON}}
          {{- end }}
          {{- range service "selenium-hub" }}
            HUB_HOST = {{ .Address | toJSON}}
            HUB_PORT = {{ .Port | toJSON}}
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
