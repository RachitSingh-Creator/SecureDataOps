# These blocks describe infrastructure that already exists in production.
# They are deliberately protected from deletion and MUST be imported manually
# before any normal Terraform plan or apply. See README.md for the import order.

resource "aws_ecr_repository" "backend" {
  name                 = data.aws_ecr_repository.backend.name
  image_tag_mutability = data.aws_ecr_repository.backend.image_tag_mutability
  force_delete         = false
  tags                 = data.aws_ecr_repository.backend.tags

  dynamic "encryption_configuration" {
    for_each = data.aws_ecr_repository.backend.encryption_configuration
    content {
      encryption_type = encryption_configuration.value.encryption_type
      kms_key         = encryption_configuration.value.kms_key
    }
  }

  dynamic "image_scanning_configuration" {
    for_each = data.aws_ecr_repository.backend.image_scanning_configuration
    content {
      scan_on_push = image_scanning_configuration.value.scan_on_push
    }
  }

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_ecr_repository" "frontend" {
  name                 = data.aws_ecr_repository.frontend.name
  image_tag_mutability = data.aws_ecr_repository.frontend.image_tag_mutability
  force_delete         = false
  tags                 = data.aws_ecr_repository.frontend.tags

  dynamic "encryption_configuration" {
    for_each = data.aws_ecr_repository.frontend.encryption_configuration
    content {
      encryption_type = encryption_configuration.value.encryption_type
      kms_key         = encryption_configuration.value.kms_key
    }
  }

  dynamic "image_scanning_configuration" {
    for_each = data.aws_ecr_repository.frontend.image_scanning_configuration
    content {
      scan_on_push = image_scanning_configuration.value.scan_on_push
    }
  }

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_lb" "backend" {
  name                                        = data.aws_lb.backend.name
  load_balancer_type                          = data.aws_lb.backend.load_balancer_type
  internal                                    = data.aws_lb.backend.internal
  ip_address_type                             = data.aws_lb.backend.ip_address_type
  security_groups                             = data.aws_lb.backend.security_groups
  subnets                                     = data.aws_lb.backend.subnets
  enable_deletion_protection                  = data.aws_lb.backend.enable_deletion_protection
  enable_cross_zone_load_balancing            = data.aws_lb.backend.enable_cross_zone_load_balancing
  enable_http2                                = data.aws_lb.backend.enable_http2
  enable_waf_fail_open                        = data.aws_lb.backend.enable_waf_fail_open
  enable_xff_client_port                      = data.aws_lb.backend.enable_xff_client_port
  enable_zonal_shift                          = data.aws_lb.backend.enable_zonal_shift
  enable_tls_version_and_cipher_suite_headers = data.aws_lb.backend.enable_tls_version_and_cipher_suite_headers
  drop_invalid_header_fields                  = data.aws_lb.backend.drop_invalid_header_fields
  desync_mitigation_mode                      = data.aws_lb.backend.desync_mitigation_mode
  idle_timeout                                = data.aws_lb.backend.idle_timeout
  client_keep_alive                           = data.aws_lb.backend.client_keep_alive
  preserve_host_header                        = data.aws_lb.backend.preserve_host_header
  xff_header_processing_mode                  = data.aws_lb.backend.xff_header_processing_mode
  dns_record_client_routing_policy            = data.aws_lb.backend.dns_record_client_routing_policy
  # The data source returns an empty string when AWS does not expose this
  # PrivateLink-only setting. Null omits the optional argument rather than
  # inventing an "on" or "off" value.
  enforce_security_group_inbound_rules_on_private_link_traffic = trimspace(data.aws_lb.backend.enforce_security_group_inbound_rules_on_private_link_traffic) != "" ? data.aws_lb.backend.enforce_security_group_inbound_rules_on_private_link_traffic : null
  tags                                                         = data.aws_lb.backend.tags

  dynamic "access_logs" {
    for_each = data.aws_lb.backend.access_logs
    content {
      bucket  = access_logs.value.bucket
      enabled = access_logs.value.enabled
      prefix  = access_logs.value.prefix
    }
  }

  dynamic "connection_logs" {
    for_each = data.aws_lb.backend.connection_logs
    content {
      bucket  = connection_logs.value.bucket
      enabled = connection_logs.value.enabled
      prefix  = connection_logs.value.prefix
    }
  }

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_lb_target_group" "backend" {
  name                               = data.aws_lb_target_group.backend.name
  port                               = data.aws_lb_target_group.backend.port
  protocol                           = data.aws_lb_target_group.backend.protocol
  protocol_version                   = data.aws_lb_target_group.backend.protocol_version
  target_type                        = data.aws_lb_target_group.backend.target_type
  vpc_id                             = data.aws_lb_target_group.backend.vpc_id
  deregistration_delay               = data.aws_lb_target_group.backend.deregistration_delay
  slow_start                         = data.aws_lb_target_group.backend.slow_start
  load_balancing_algorithm_type      = data.aws_lb_target_group.backend.load_balancing_algorithm_type
  load_balancing_anomaly_mitigation  = data.aws_lb_target_group.backend.load_balancing_anomaly_mitigation
  load_balancing_cross_zone_enabled  = data.aws_lb_target_group.backend.load_balancing_cross_zone_enabled
  preserve_client_ip                 = data.aws_lb_target_group.backend.preserve_client_ip
  proxy_protocol_v2                  = data.aws_lb_target_group.backend.proxy_protocol_v2
  lambda_multi_value_headers_enabled = data.aws_lb_target_group.backend.lambda_multi_value_headers_enabled
  connection_termination             = data.aws_lb_target_group.backend.connection_termination
  tags                               = data.aws_lb_target_group.backend.tags

  dynamic "health_check" {
    for_each = data.aws_lb_target_group.backend.health_check
    content {
      enabled             = health_check.value.enabled
      healthy_threshold   = health_check.value.healthy_threshold
      interval            = health_check.value.interval
      matcher             = health_check.value.matcher
      path                = health_check.value.path
      port                = health_check.value.port
      protocol            = health_check.value.protocol
      timeout             = health_check.value.timeout
      unhealthy_threshold = health_check.value.unhealthy_threshold
    }
  }

  dynamic "stickiness" {
    for_each = data.aws_lb_target_group.backend.stickiness
    content {
      type            = stickiness.value.type
      enabled         = stickiness.value.enabled
      cookie_duration = stickiness.value.cookie_duration
      cookie_name     = stickiness.value.cookie_name
    }
  }

  lifecycle {
    prevent_destroy = true
  }
}

# The default action is copied from the existing listener data source. This
# resource does not define listener rules; rules require a separate migration.
resource "aws_lb_listener" "backend" {
  load_balancer_arn = data.aws_lb_listener.backend.load_balancer_arn
  port              = data.aws_lb_listener.backend.port
  protocol          = data.aws_lb_listener.backend.protocol
  certificate_arn   = data.aws_lb_listener.backend.certificate_arn
  ssl_policy        = data.aws_lb_listener.backend.ssl_policy
  alpn_policy       = data.aws_lb_listener.backend.alpn_policy
  tags              = data.aws_lb_listener.backend.tags

  dynamic "default_action" {
    for_each = data.aws_lb_listener.backend.default_action
    content {
      type             = default_action.value.type
      order            = default_action.value.order
      target_group_arn = default_action.value.target_group_arn

      dynamic "authenticate_cognito" {
        for_each = default_action.value.authenticate_cognito
        content {
          authentication_request_extra_params = authenticate_cognito.value.authentication_request_extra_params
          on_unauthenticated_request          = authenticate_cognito.value.on_unauthenticated_request
          scope                               = authenticate_cognito.value.scope
          session_cookie_name                 = authenticate_cognito.value.session_cookie_name
          session_timeout                     = authenticate_cognito.value.session_timeout
          user_pool_arn                       = authenticate_cognito.value.user_pool_arn
          user_pool_client_id                 = authenticate_cognito.value.user_pool_client_id
          user_pool_domain                    = authenticate_cognito.value.user_pool_domain
        }
      }

      dynamic "authenticate_oidc" {
        for_each = default_action.value.authenticate_oidc
        content {
          authentication_request_extra_params = authenticate_oidc.value.authentication_request_extra_params
          authorization_endpoint              = authenticate_oidc.value.authorization_endpoint
          client_id                           = authenticate_oidc.value.client_id
          client_secret                       = authenticate_oidc.value.client_secret
          issuer                              = authenticate_oidc.value.issuer
          on_unauthenticated_request          = authenticate_oidc.value.on_unauthenticated_request
          scope                               = authenticate_oidc.value.scope
          session_cookie_name                 = authenticate_oidc.value.session_cookie_name
          session_timeout                     = authenticate_oidc.value.session_timeout
          token_endpoint                      = authenticate_oidc.value.token_endpoint
          user_info_endpoint                  = authenticate_oidc.value.user_info_endpoint
        }
      }

      dynamic "fixed_response" {
        for_each = default_action.value.fixed_response
        content {
          content_type = fixed_response.value.content_type
          message_body = fixed_response.value.message_body
          status_code  = fixed_response.value.status_code
        }
      }

      dynamic "redirect" {
        for_each = default_action.value.redirect
        content {
          host        = redirect.value.host
          path        = redirect.value.path
          port        = redirect.value.port
          protocol    = redirect.value.protocol
          query       = redirect.value.query
          status_code = redirect.value.status_code
        }
      }

      dynamic "forward" {
        for_each = default_action.value.forward
        content {
          dynamic "target_group" {
            for_each = forward.value.target_group
            content {
              arn    = target_group.value.arn
              weight = target_group.value.weight
            }
          }

          dynamic "stickiness" {
            for_each = forward.value.stickiness
            content {
              duration = stickiness.value.duration
              enabled  = stickiness.value.enabled
            }
          }
        }
      }
    }
  }

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_ecs_cluster" "securedataops" {
  name = data.aws_ecs_cluster.securedataops.cluster_name
  tags = data.aws_ecs_cluster.securedataops.tags

  # Preserves the execute-command configuration recorded in the imported
  # production cluster state. No KMS key is configured for DEFAULT logging.
  configuration {
    execute_command_configuration {
      logging = "DEFAULT"
    }
  }

  dynamic "service_connect_defaults" {
    for_each = data.aws_ecs_cluster.securedataops.service_connect_defaults
    content {
      namespace = service_connect_defaults.value.namespace
    }
  }

  dynamic "setting" {
    for_each = data.aws_ecs_cluster.securedataops.setting
    content {
      name  = setting.value.name
      value = setting.value.value
    }
  }

  # Capacity-provider associations are managed by aws_ecs_cluster_capacity_providers,
  # not this resource. They remain outside this phase until live inventory is reviewed.
  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_iam_role" "ecs_execution" {
  name                 = data.aws_iam_role.ecs_execution.name
  assume_role_policy   = data.aws_iam_role.ecs_execution.assume_role_policy
  description          = data.aws_iam_role.ecs_execution.description
  max_session_duration = data.aws_iam_role.ecs_execution.max_session_duration
  path                 = data.aws_iam_role.ecs_execution.path
  permissions_boundary = data.aws_iam_role.ecs_execution.permissions_boundary
  tags                 = data.aws_iam_role.ecs_execution.tags

  # Attached and inline policies need separate inventory and migration so this
  # role resource cannot accidentally reconcile policy attachments in this phase.
  lifecycle {
    prevent_destroy = true
  }
}
