{{/*
Common labels applied to every object. Pass a dict:
  (dict "root" . "component" "<name>")
*/}}
{{- define "tripla-apps.labels" -}}
helm.sh/chart: {{ printf "%s-%s" .root.Chart.Name .root.Chart.Version }}
app.kubernetes.io/managed-by: {{ .root.Release.Service }}
app.kubernetes.io/instance: {{ .root.Release.Name }}
app.kubernetes.io/name: {{ .component }}
{{- end }}

{{/*
Selector labels: the immutable subset shared by Deployment selectors,
pod templates and Services. Must stay in sync on all three or the
Service routes to nothing.
*/}}
{{- define "tripla-apps.selectorLabels" -}}
app.kubernetes.io/instance: {{ .root.Release.Name }}
app.kubernetes.io/name: {{ .component }}
{{- end }}