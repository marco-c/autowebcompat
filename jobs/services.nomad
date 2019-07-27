job "autowebcompat-services" {
  datacenters = ["dc1"]
  type = "service"
  priority = 80

  group "ingress" {
    constraint {
      attribute = "${meta.ingress}"
      operator = "is_set"
    }
    task "traefik" {
      driver = "docker"
      config {
        image = "traefik:1.7"
        port_map {
          http = 80
          admin = 8080
          {%- if https_enabled %}
          https = 443
          {%- endif %}
        }
        volumes = [
          "local/traefik.toml:/etc/traefik/traefik.toml:ro",
        ]
      }
      template {
        data = <<-EOF
          debug = true
          {%- if https_enabled %}
          defaultEntryPoints = ["http", "https"]
          {%- else %}
          defaultEntryPoints = ["http"]
          {%- endif %}

          [api]
          entryPoint = "admin"

          [entryPoints]
            [entryPoints.http]
            address = ":80"

              {%- if https_enabled %}
              [entryPoints.http.redirect]
              entryPoint = "https"
              {%- endif %}

            [entryPoints.admin]
            address = ":8080"

            {%- if https_enabled %}
            [entryPoints.https]
            address = ":443"
              [entryPoints.https.tls]
            {%- endif %}

          {%- if https_enabled %}
          [acme]
            email = "%{acme_email}"
            entryPoint = "https"
            storage = "traefik/acme"
            onHostRule = true
            caServer = "%{acme_caServer}"
            acmeLogging = true
            [acme.httpChallenge]
              entryPoint = "http"
          {%- endif %}


          [consulCatalog]
          endpoint = "%{consul_url}"
          prefix = "traefik"
          exposedByDefault = false

          [consul]
          endpoint = "%{consul_url}"
          prefix = "traefik"
        EOF
        destination = "local/traefik.toml"
      }
      resources {
        cpu = 300
        memory = 100
        network {
          port "http" {
            static = 80
          }
          port "admin" {}

          {%- if https_enabled %}
          port "https" {
            static = 443
          }
          {%- endif %}
        }
      }
      service {
        name = "traefik-http"
        port = "http"
        {%- if not https_enabled %}
        check {
          name = "traefik alive on http - home page"
          initial_status = "critical"
          type = "http"
          path = "/"
          interval = "7s"
          timeout = "4s"
          header {
            Host = ["%{domain}"]
          }
        }
        {%- endif %}
      }

      {%- if https_enabled %}
      service {
        name = "traefik-https"
        port = "https"
        check {
          name = "traefik alive on https - home page"
          initial_status = "critical"
          type = "http"
          protocol = "https"
          path = "/"
          interval = "7s"
          timeout = "4s"
          tls_skip_verify = true
          header {
            Host = ["%{domain}"]
          }
        }
      }
      {%- endif %}

      service {
        name = "traefik-admin"
        port = "admin"
        check {
          name = "traefik alive on http admin"
          initial_status = "critical"
          type = "http"
          path = "/"
          interval = "7s"
          timeout = "4s"
        }
      }
    }
  }
  group "db" {
    constraint {
      attribute = "${meta.storage_path}"
      operator = "is_set"
    }

    task "postgres" {
      driver = "docker"
      config {
        image = "postgres:11.2"
        volumes = [
          "${meta.storage_path}/postgres:/var/lib/postgresql/data",
        ]
        port_map {
          pg = 5432
        }
      }
      env {
        POSTGRES_USER = "user1"
        POSTGRES_DB = "autowebcompat"
      }
      template {
        data = <<-EOF
          {{- with secret "autowebcompat/web/postgres_password" }}
            POSTGRES_PASSWORD = {{.Data.val | toJSON}}
          {{- end }}
        EOF
        destination = "local/db.env"
        env = true
      }
      resources {
        memory = 500
        cpu = 2000
        network {
          port "pg" {}
        }
      }
      service {
        name = "postgres"
        port = "pg"
        check {
          name = "postgres alive on tcp"
          initial_status = "critical"
          type = "tcp"
          interval = "7s"
          timeout = "4s"
        }
      }
    }
  }


  group "backend" {
    {% if run_backend_locally %}
    constraint {
      attribute = "${meta.code_path}"
      operator = "is_set"
    }
    {% else %}
    count = 2
    {% endif %}
    task "django" {
      driver = "docker"
      config {
        image = "gabrielv/autowebcompat:web"
        force_pull = true
        args = ["bash", "/local/run.sh"]
        port_map {
          http = 8000
        }

        {% if run_backend_locally %}
        volumes = [
          "${meta.code_path}:/autowebcompat",
        ]
        {% endif %}
      }
      env {
        {% if debug %}
        DJANGO_DEBUG = "true"
        {% endif %}

        CONFIG_INI = "/local/config.ini"
        DJANGO_SETTINGS_MODULE = "website.settings"
        UWSGI_WSGI_FILE = "/autowebcompat/web/website/wsgi.py"
        UWSGI_WORKERS = "2"
        UWSGI_THREADS = "20"
        UWSGI_HTTP = ":8000"
        UWSGI_MASTER = "1"
        UWSGI_HTTP_AUTO_CHUNKED = "1"
        UWSGI_HTTP_KEEPALIVE = "1"
        UWSGI_SHOW_CONFIG = "1"
        POSTGRES_USER = "user1"
        POSTGRES_DB = "autowebcompat"
        TIMESTAMP = "%{timestamp}"
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
          {{- with secret "autowebcompat/web/django_secret_key" }}
            SECRET_KEY = {{.Data.val | toJSON}}
          {{- end }}
          {{- with secret "autowebcompat/web/auth_gh_key" }}
            GITHUB_KEY = {{.Data.val | toJSON}}
          {{- end }}
          {{- with secret "autowebcompat/web/auth_gh_secret" }}
            GITHUB_SECRET = {{.Data.val | toJSON}}
          {{- end }}
        EOF
        destination = "local/envs.env"
        env = true
      }
      template {
        data = <<-EOF
          set -ex
          cd /autowebcompat/web
          until python ./manage.py migrate --noinput; do sleep 3; done
          python ./manage.py collectstatic --noinput

          {% if run_backend_locally %}
          exec python ./manage.py runserver 0.0.0.0:8000
          {% else %}
          exec uwsgi
          {% endif %}
        EOF
        destination = "local/run.sh"
      }
      template {
        data = <<-EOF
%{config_ini_content}
        EOF
        destination = "local/config.ini"
      }
      resources {
        memory = 700
        cpu = 2000
        network {
          port "http" {}
        }
      }
      service {
        name = "django"
        port = "http"
        tags = [
          "traefik.enable=true",
          "traefik.frontend.rule=Host:%{domain}",
        ]
        check {
          name = "django alive on http /"
          initial_status = "critical"
          type = "http"
          path = "/"
          interval = "7s"
          timeout = "4s"
        }
      }
    }
  }

  group "selenium" {
    task "hub" {
      driver = "docker"
      config {
        image = "selenium/hub:3.141.59-neon"
        port_map {
          http = 4444
        }
        volumes = [
          "/dev/shm:/dev/shm",
        ]
      }
      resources {
        memory = 500
        cpu = 500
        network {
          port "http" {}
        }
      }
      env {
        GRID_TIMEOUT = 180
        GRID_BROWSER_TIMEOUT = 180
      }
      service {
        name = "selenium-hub"
        port = "http"
        check {
          name = "selenium-hub alive on http"
          initial_status = "critical"
          type = "http"
          path = "/"
          interval = "7s"
          timeout = "4s"
        }
      }
    }
  }
}
