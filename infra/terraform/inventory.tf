locals {
  existing_ecs_services = {
    backend  = var.backend_service_name
    frontend = var.frontend_service_name
  }

  existing_backend_autoscaling = {
    predefined_metric = "ALBRequestCountPerTarget"
    target_value      = 100
    scale_out_seconds = 60
    scale_in_seconds  = 300
  }

  existing_sre_configuration = {
    cloudwatch_dashboard_source = "../../cloudwatch-dashboard.json"
    backend_log_group           = var.backend_log_group_name
  }
}
