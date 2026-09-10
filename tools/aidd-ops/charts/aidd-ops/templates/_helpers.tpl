{{- define "aidd-ops.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "aidd-ops.labels" -}}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version | replace "+" "_" }}
app.kubernetes.io/name: {{ include "aidd-ops.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{- define "aidd-ops.namespace" -}}
{{- default "aidd-ops" .Values.global.namespace }}
{{- end }}

{{- define "aidd-ops.selectorLabels" -}}
app.kubernetes.io/name: {{ .svcName }}
app.kubernetes.io/instance: {{ .releaseName }}
{{- end }}
