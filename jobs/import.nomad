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
        POSTGRES_USER = "user1"
        POSTGRES_DB = "autowebcompat"
        SECRET_KEY = "fake"
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
