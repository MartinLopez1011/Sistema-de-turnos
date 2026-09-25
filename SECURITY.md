# Directiva de Seguridad del Repositorio

Para consultar las políticas completas de seguridad de la información, protección de datos personales (PII), manejo de credenciales y pautas de desarrollo seguro, consulte el documento:

👉 **[POLITICAS_Y_SEGURIDAD.md](POLITICAS_Y_SEGURIDAD.md)**

## Resumen Ejecutivo de Seguridad

1. **Datos Sensibles Prohibidos en Git**:
   - Queda estrictamente prohibido subir nombres de funcionarios, correos reales (`@institucion.cl`), números de contacto o motivos personales/médicos al repositorio.
   - El archivo `config.json` de operación local y la carpeta `backups/` están permanentemente excluidos mediante `.gitignore`.
2. **Uso de Plantillas**:
   - Utilice `config.example.json` y `.env.example` como plantilla para desplegar nuevas instancias del sistema.
3. **Manejo de Credenciales**:
   - Las credenciales SMTP de Gmail y Webhooks deben residir exclusivamente en el archivo local `.env` y nunca ser subidas a GitHub.
4. **Reporte de Incidentes de Seguridad**:
   - En caso de detectar cualquier filtración inadvertida de credenciales o datos sensibles, consulte el protocolo de purga y rotación en `POLITICAS_Y_SEGURIDAD.md`.
