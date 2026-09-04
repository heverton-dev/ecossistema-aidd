#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD v6.0-Enterprise — Scaffolding de Infraestrutura Declarativa (Terraform + Helm)
=============================================================================
Gera infra/terraform/main.tf (provisionamento de PostgreSQL gerenciado, Redis
e VPC) e infra/helm/*.yaml (Deployment, Service, Ingress, HPA) parametrizados
pelo nome da suíte. Os arquivos são gerados de forma determinística e estática
— nenhum comando terraform/helm é executado por este script.
"""

import os
import re
import sys


def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "aidd-suite"


def _generate_terraform_main_tf(slug: str) -> str:
    return f"""terraform {{
  required_version = ">= 1.5.0"
  required_providers {{
    aws = {{
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }}
  }}
}}

variable "suite_name" {{
  description = "Nome da suíte AIDD (usado como prefixo dos recursos)"
  type        = string
  default     = "{slug}"
}}

variable "aws_region" {{
  description = "Região AWS de provisionamento"
  type        = string
  default     = "us-east-1"
}}

variable "db_password" {{
  description = "Senha do banco PostgreSQL (defina via TF_VAR_db_password, nunca hardcoded)"
  type        = string
  sensitive   = true
}}

provider "aws" {{
  region = var.aws_region
}}

resource "aws_vpc" "main" {{
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {{
    Name = "${{var.suite_name}}-vpc"
  }}
}}

resource "aws_subnet" "private_a" {{
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "${{var.aws_region}}a"

  tags = {{
    Name = "${{var.suite_name}}-subnet-a"
  }}
}}

resource "aws_subnet" "private_b" {{
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "${{var.aws_region}}b"

  tags = {{
    Name = "${{var.suite_name}}-subnet-b"
  }}
}}

resource "aws_db_subnet_group" "main" {{
  name       = "${{var.suite_name}}-db-subnet-group"
  subnet_ids = [aws_subnet.private_a.id, aws_subnet.private_b.id]
}}

resource "aws_security_group" "data_layer" {{
  name   = "${{var.suite_name}}-data-sg"
  vpc_id = aws_vpc.main.id

  ingress {{
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [aws_vpc.main.cidr_block]
  }}

  ingress {{
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = [aws_vpc.main.cidr_block]
  }}

  egress {{
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }}
}}

resource "aws_db_instance" "postgres" {{
  identifier              = "${{var.suite_name}}-postgres"
  engine                  = "postgres"
  engine_version          = "16"
  instance_class          = "db.t4g.micro"
  allocated_storage       = 20
  db_name                 = replace(var.suite_name, "-", "_")
  username                = "aidd_user"
  password                = var.db_password
  db_subnet_group_name    = aws_db_subnet_group.main.name
  vpc_security_group_ids  = [aws_security_group.data_layer.id]
  skip_final_snapshot     = true
  publicly_accessible     = false
}}

resource "aws_elasticache_subnet_group" "redis" {{
  name       = "${{var.suite_name}}-redis-subnet-group"
  subnet_ids = [aws_subnet.private_a.id, aws_subnet.private_b.id]
}}

resource "aws_elasticache_cluster" "redis" {{
  cluster_id           = "${{var.suite_name}}-redis"
  engine               = "redis"
  engine_version       = "7.0"
  node_type            = "cache.t4g.micro"
  num_cache_nodes      = 1
  subnet_group_name    = aws_elasticache_subnet_group.redis.name
  security_group_ids   = [aws_security_group.data_layer.id]
}}

output "database_url" {{
  description = "DATABASE_URL pronta para uso no AIDD Database Adapter (Onda 1)"
  value       = "postgresql://aidd_user:${{var.db_password}}@${{aws_db_instance.postgres.endpoint}}/${{replace(var.suite_name, "-", "_")}}"
  sensitive   = true
}}

output "eventbus_url" {{
  description = "EVENTBUS_URL pronta para uso no EventBus distribuído (Onda 2)"
  value       = "redis://${{aws_elasticache_cluster.redis.cache_nodes[0].address}}:6379/0"
}}
"""


def _generate_helm_chart_yaml(slug: str) -> str:
    return f"""apiVersion: v2
name: {slug}
description: Helm chart gerado automaticamente pelo AIDD Master Enterprise
type: application
version: 0.1.0
appVersion: "5.0.0"
"""


def _generate_helm_values_yaml(slug: str) -> str:
    return f"""replicaCount: 2

image:
  repository: {slug}
  tag: latest
  pullPolicy: IfNotPresent

service:
  type: ClusterIP
  port: 3000

ingress:
  className: nginx
  host: {slug}.exemplo.com

resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 500m
    memory: 512Mi

autoscaling:
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70

env:
  DATABASE_URL: ""
  EVENTBUS_URL: ""
  JWT_SECRET_KEY: ""
"""


def _generate_helm_deployment_yaml(slug: str) -> str:
    return f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {slug}
  labels:
    app: {slug}
spec:
  replicas: {{{{ .Values.replicaCount }}}}
  selector:
    matchLabels:
      app: {slug}
  template:
    metadata:
      labels:
        app: {slug}
    spec:
      containers:
        - name: {slug}
          image: "{{{{ .Values.image.repository }}}}:{{{{ .Values.image.tag }}}}"
          imagePullPolicy: {{{{ .Values.image.pullPolicy }}}}
          ports:
            - containerPort: 3000
          env:
            - name: DATABASE_URL
              value: "{{{{ .Values.env.DATABASE_URL }}}}"
            - name: EVENTBUS_URL
              value: "{{{{ .Values.env.EVENTBUS_URL }}}}"
            - name: JWT_SECRET_KEY
              value: "{{{{ .Values.env.JWT_SECRET_KEY }}}}"
          livenessProbe:
            httpGet:
              path: /health
              port: 3000
            initialDelaySeconds: 10
            periodSeconds: 15
          readinessProbe:
            httpGet:
              path: /health
              port: 3000
            initialDelaySeconds: 5
            periodSeconds: 10
          resources:
            {{{{- toYaml .Values.resources | nindent 12 }}}}
"""


def _generate_helm_service_yaml(slug: str) -> str:
    return f"""apiVersion: v1
kind: Service
metadata:
  name: {slug}
  labels:
    app: {slug}
spec:
  type: {{{{ .Values.service.type }}}}
  ports:
    - port: {{{{ .Values.service.port }}}}
      targetPort: 3000
      protocol: TCP
  selector:
    app: {slug}
"""


def _generate_helm_ingress_yaml(slug: str) -> str:
    return f"""apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {slug}
  annotations:
    kubernetes.io/ingress.class: {{{{ .Values.ingress.className }}}}
spec:
  rules:
    - host: {{{{ .Values.ingress.host }}}}
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: {slug}
                port:
                  number: {{{{ .Values.service.port }}}}
"""


def _generate_helm_hpa_yaml(slug: str) -> str:
    return f"""apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {slug}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {slug}
  minReplicas: {{{{ .Values.autoscaling.minReplicas }}}}
  maxReplicas: {{{{ .Values.autoscaling.maxReplicas }}}}
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: {{{{ .Values.autoscaling.targetCPUUtilizationPercentage }}}}
"""


def scaffold_infra(target_dir: str, suite_name: str = "AIDD Suite"):
    target_dir = os.path.abspath(target_dir)
    slug = _slugify(suite_name)

    terraform_dir = os.path.join(target_dir, "infra", "terraform")
    helm_dir = os.path.join(target_dir, "infra", "helm")
    helm_templates_dir = os.path.join(helm_dir, "templates")
    os.makedirs(terraform_dir, exist_ok=True)
    os.makedirs(helm_templates_dir, exist_ok=True)

    print("=" * 80)
    print(f"🏗️  [AIDD v6.0] Gerando Infraestrutura Declarativa (Terraform + Helm): {suite_name}")
    print("=" * 80)

    # infra/helm/ segue a estrutura real de um Helm chart (Chart.yaml + values.yaml
    # na raiz, manifestos parametrizados em templates/) para que `helm lint`/
    # `helm template` funcionem de verdade quando o binário estiver disponível.
    files = {
        os.path.join(terraform_dir, "main.tf"): _generate_terraform_main_tf(slug),
        os.path.join(helm_dir, "Chart.yaml"): _generate_helm_chart_yaml(slug),
        os.path.join(helm_dir, "values.yaml"): _generate_helm_values_yaml(slug),
        os.path.join(helm_templates_dir, "deployment.yaml"): _generate_helm_deployment_yaml(slug),
        os.path.join(helm_templates_dir, "service.yaml"): _generate_helm_service_yaml(slug),
        os.path.join(helm_templates_dir, "ingress.yaml"): _generate_helm_ingress_yaml(slug),
        os.path.join(helm_templates_dir, "hpa.yaml"): _generate_helm_hpa_yaml(slug),
    }

    for path, content in files.items():
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  [+] {os.path.relpath(path, target_dir)}")

    print("\n" + "=" * 80)
    print("🏆 [SUCESSO]: Infraestrutura declarativa gerada em infra/")
    print(f"   ➔ cd {terraform_dir} && terraform init && terraform validate")
    print(f"   ➔ helm lint {helm_dir}")
    print("=" * 80)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python scaffold_infra.py <target_dir> [suite_name]")
        sys.exit(1)
    scaffold_infra(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "AIDD Suite")
