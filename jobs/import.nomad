job "autowebcompat-import" {
  datacenters = ["dc1"]
  type = "batch"
  parameterized {
    payload = "forbidden"
    meta_required = ["dataset_path", "dataset_slug"]
  }

  group "manage.py" {
    constraint {
      attribute = "${meta.code_path}"
      operator = "is_set"
    }
    task "import" {
      driver = "docker"
      config {
        image = "gabrielv/autowebcompat:web"
        args = ["python", "web/manage.py", "import_dataset", "${NOMAD_META_dataset_slug}", "/data"]
        volumes = [
          "${NOMAD_META_dataset_path}:/data:ro",
        ]
      }
      env {
        TIMESTAMP = "${meta.timestamp}"
      }
      template {
        data = <<EOF
          {{- range service "postgres" }}
            PG_IP = {{ .Address }}
            PG_PORT = {{ .Port }}
          {{- end }}
        EOF
        destination = "local/generated.env"
        env = true
      }
      resources {
        cpu = 1200
        memory = 1000
      }
    }
  }
}
