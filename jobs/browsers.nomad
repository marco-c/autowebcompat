job "autowebcompat-browsers" {
  datacenters = ["dc1"]
  type = "service"
  priority = 70

  group "chrome" {
    count = 3
    constraint {
      attribute = "${meta.crawler}"
      value = "true"
    }

    task "chrome" {
      driver = "docker"
      config {
        image = "selenium/node-chrome:3.141.59-neon"
        volumes = [
        #  "/dev/shm:/dev/shm",
        ]
        port_map {
          node = 5555
        }
      }
      template {
        data = <<EOF
          {{- range service "selenium-hub" }}
            HUB_HOST = {{ .Address }}
            HUB_PORT = {{ .Port }}
          {{- end }}
          REMOTE_HOST = "http://${NOMAD_ADDR_node}"
          SCREEN_HEIGHT = 900
          SCREEN_WIDTH = 500
          NODE_MAX_SESSION = 3
          NODE_MAX_INSTANCES = 3
        EOF
        destination = "local/generated.env"
        env = true
      }
      resources {
        memory = 1000
        cpu = 1000
        network {
          mbits = 50
          port "node" {}
        }
      }
    }
  }

  group "firefox" {
    count = 3
    constraint {
      attribute = "${meta.crawler}"
      value = "true"
    }
    task "firefox" {
      driver = "docker"
      config {
        image = "selenium/node-firefox:3.141.59-neon"
        volumes = [
        #  "/dev/shm:/dev/shm",
        ]
        port_map {
          node = 5555
        }
      }
      template {
        data = <<EOF
          {{- range service "selenium-hub" }}
            HUB_HOST = {{ .Address }}
            HUB_PORT = {{ .Port }}
          {{- end }}
          REMOTE_HOST = "http://${NOMAD_ADDR_node}"
          SCREEN_HEIGHT = 900
          SCREEN_WIDTH = 500
          NODE_MAX_SESSION = 3
          NODE_MAX_INSTANCES = 3
        EOF
        destination = "local/generated.env"
        env = true
      }
      resources {
        memory = 1000
        cpu = 1000
        network {
          mbits = 50
          port "node" {}
        }
      }
    }
  }
}
