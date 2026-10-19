{{- define "tb.name" -}}
{{ .Release.Name }}-tb
{{- end -}}
{{- define "tb.container" -}}
- name: tb-node
  image: {{ required "TB image digest is required" .Values.image | quote }}
  imagePullPolicy: IfNotPresent
  securityContext:
    allowPrivilegeEscalation: false
    readOnlyRootFilesystem: true
    runAsNonRoot: true
    capabilities:
      drop: [ALL]
    seccompProfile:
      type: RuntimeDefault
    {{- if .Values.tb.rehearsalUid }}
    runAsUser: {{ .Values.tb.rehearsalUid }}
    {{- end }}
  env:
    - {name: TB_SERVICE_TYPE, value: monolith}
    - {name: TB_QUEUE_TYPE, value: in-memory}
    - {name: DATABASE_TS_TYPE, value: sql}
    - {name: DATABASE_TS_LATEST_TYPE, value: sql}
    - {name: HOME, value: /tmp}
    - name: JAVA_OPTS
      value: "-Xms512m -Xmx2g -Duser.home=/tmp -Djava.io.tmpdir=/tmp"
    - name: SPRING_DATASOURCE_URL
      value: jdbc:postgresql://{{ .Release.Name }}-db-rw:5432/thingsboard
    - name: SPRING_DATASOURCE_USERNAME
      valueFrom:
        secretKeyRef: {name: {{ .Release.Name }}-db-app, key: username}
    - name: SPRING_DATASOURCE_PASSWORD
      valueFrom:
        secretKeyRef: {name: {{ .Release.Name }}-db-app, key: password}
    {{- if .Values.bootstrap.enabled }}
    - {name: INSTALL_TB, value: "true"}
    - {name: LOAD_DEMO, value: "false"}
    {{- end }}
  ports:
    - {name: http, containerPort: 8080}
  resources:
    {{- toYaml .Values.tb.resources | nindent 4 }}
  volumeMounts:
    - {name: temporary, mountPath: /tmp}
    - {name: temporary, mountPath: /var/log/thingsboard}
  {{- if not .Values.bootstrap.enabled }}
  startupProbe:
    tcpSocket: {port: http}
    periodSeconds: 10
    failureThreshold: 90
  readinessProbe:
    httpGet: {path: /actuator/health, port: http}
    periodSeconds: 10
  livenessProbe:
    tcpSocket: {port: http}
    periodSeconds: 20
  {{- end }}
{{- end -}}
