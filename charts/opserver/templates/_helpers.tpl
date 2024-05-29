{{/*
Expand the name of the chart.
*/}}
{{- define "opserver.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "opserver.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "opserver.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Define Basic Labels
*/}}
{{- define "opserver.labels" -}}
helm.sh/chart: {{ include "opserver.chart" . }}
{{ include "opserver.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "opserver.selectorLabels" -}}
app.kubernetes.io/name: {{ include "opserver.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "opserver.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "opserver.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Set the Image Pull Secret if needed
*/}}
{{- define "imagePullSecret" }}
{{- printf "{\"auths\":{\"%s\":{\"username\":\"%s\",\"password\":\"%s\",\"email\":\"%s\",\"auth\":\"%s\"}}}" .registry .username .password .email (printf "%s:%s" .username .password | b64enc) | b64enc }}
{{- end }}


{{/*
Set the Security Context
*/}}
{{- define "securityContext" }}
runAsUser: {{ default 1668442480 (.Values.securityContext).runAsUser }}
runAsGroup: {{ default 1668442480 (.Values.securityContext).runAsGroup }}
fsGroup: {{ default 1668442480 (.Values.securityContext).fsGroup }}
fsGroupChangePolicy: "OnRootMismatch"
{{- end }}

{{/*
Set Pod Security Context
*/}}
{{- define "pod.securityContext" }}
allowPrivilegeEscalation: false
capabilities:
    drop:
    - ALL
privileged: false
readOnlyRootFilesystem: true
runAsNonRoot: true
{{- end }}