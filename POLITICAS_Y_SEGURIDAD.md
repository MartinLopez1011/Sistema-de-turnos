# POLÍTICAS DE SEGURIDAD DE LA INFORMACIÓN Y PRIVACIDAD DE DATOS
## Sistema de Gestión y Planificación de Turnos

**Código de Documento:** POL-SEG-TURNOS-2026-01  
**Versión:** 1.0  
**Fecha de Emisión:** Septiembre 2026  
**Clasificación:** Confidencial / Uso Interno y Desarrollo Seguro  
**Aplicabilidad:** Todos los colaboradores, desarrolladores, administradores y mantenedores del repositorio de código fuente y del entorno de ejecución.

---

## 1. OBJETIVO Y PROPÓSITO

El presente documento establece las directrices, responsabilidades, controles técnicos y procedimientos obligatorios para garantizar la **confidencialidad, integridad y disponibilidad** de la información gestionada por el Sistema de Gestión y Planificación de Turnos, así como la protección estricta de la privacidad de los funcionarios y la custodia de credenciales y secretos en el entorno de desarrollo y en plataformas de control de versiones públicas y privadas (GitHub).

---

## 2. MARCO LEGAL Y NORMATIVO

Las directrices aquí contenidas se fundamentan en las mejores prácticas de la industria y la legislación chilena vigente:
- **Ley N° 19.628 sobre Protección de la Vida Privada** (Chile): Regula el tratamiento automatizado de datos de carácter personal en organismos públicos y privados.
- **Principio de Finalidad y Confidencialidad**: Los datos de dotación, turnos, excepciones y contactos deben tratarse exclusivamente para los fines operativos del servicio y bajo reserva profesional.
- **OWASP Secure Coding Practices & Top 10**: Prevención de fugas de datos, exposición de credenciales y manejo inseguro de configuraciones.

---

## 3. CLASIFICACIÓN DE LA INFORMACIÓN Y DATOS SENSIBLES (PII)

Se define como **Información Sensible y Protegida** todo dato que permita individualizar a un funcionario o que exponga accesos a infraestructuras informáticas:

| Categoría | Elementos Incluidos | Nivel de Riesgo | Tratamiento Requerido |
| :--- | :--- | :--- | :--- |
| **Datos Personales (PII)** | Nombres y apellidos completos, cargos o funciones operativas, identificadores de personal y asignaciones de servicio. | **Alto** | Prohibido almacenar en repositorios remotos. En pruebas y plantillas debe usarse únicamente información sintética / ficticia. |
| **Datos de Contacto** | Correos electrónicos laborales o corporativos (`@ejemplo.com`), correos particulares, teléfonos de contacto. | **Crítico** | Prohibido exponer en GitHub o archivos versionados. En configuración de prueba usar dominios genéricos de ejemplo (`usuario@ejemplo.com`). |
| **Datos Médicos y Personales** | Motivos de excepciones de guardia (licencias médicas `LIC`, duelos, accidentes, situaciones familiares `OTR`). | **Crítico** | Confidencialidad médica/laboral. Nunca incluir descripciones reales en archivos de prueba ni en el control de versiones. |
| **Credenciales y Secretos** | Contraseñas de Aplicación de Google (16 caracteres), URLs de Webhooks de Google Apps Script (`/exec`), credenciales SMTP. | **Crítico** | Almacenar exclusivamente en variables de entorno locales (`.env`). Prohibido subirlas al repositorio. |
| **Historial y Auditoría** | Registros de rotación de turnos, bitácora de auditoría de cierres mensuales (`auditoria[]`), archivos `turnos.log`. | **Medio / Alto** | Excluir del control de versiones. Conservar localmente bajo permisos restrictivos. |

---

## 4. POLÍTICA DE CONTROL DE VERSIONES Y REPOSITORIOS (GIT & GITHUB)

### 4.1 Principio de Exclusión Obligatoria
Bajo ninguna circunstancia se incorporarán al árbol de seguimiento de Git (`git add`) archivos que contengan datos de producción, datos personales reales o credenciales activas.

### 4.2 Configuración del Archivo `.gitignore`
El archivo `.gitignore` del proyecto debe mantener como mínimo las siguientes reglas de exclusión activas:
```gitignore
# Archivos de configuración locales con datos operativos reales
config.json
temp_config.json
.env

# Respaldos generados por el sistema (contienen PII de funcionarios)
backups/

# Archivos de bitácora y diagnóstico
*.log
turnos.log

# Planillas de cálculo con dotaciones reales
*.xlsx

# Artefactos de compilación y empaquetado
dist/
build/
*.spec
*.exe

# Caché de Python y entornos virtuales
__pycache__/
*.pyc
.venv/
.pytest_cache/
```

### 4.3 Política de Plantillas ("Solo la Idea")
Para permitir la clonación, despliegue y desarrollo del proyecto sin comprometer datos reales:
1. **Plantilla de Configuración (`config.example.json`)**: Es el único archivo de configuración que debe versionarse en Git. Contiene la estructura JSON completa (esquema v2), pero con dotación sintética e ilustrativa (ej. `JUAN PEREZ`, `MARIA GONZALEZ`), webhook deshabilitado y estructuras de historial y excepciones vacías.
2. **Plantilla de Variables de Entorno (`.env.example`)**: Provee los nombres de las variables requeridas (`SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD`, `WEBHOOK_URL`) con valores de ejemplo genéricos (`xxxx xxxx xxxx xxxx`, `tu_correo@gmail.com`).
3. **Instalación en Producción**: El administrador debe copiar `config.example.json` a `config.json` y `.env.example` a `.env` en su entorno local antes de iniciar la aplicación.

---

## 5. DIRECTRICES DE CONFIGURACIÓN SEGURA (`config.json`)

### 5.1 Estructura Estándar Autorizada para Plantillas
El archivo de configuración debe estructurarse conforme a las siguientes pautas:
- **`personal`**: Contiene únicamente identificadores secuenciales enteros y nombres ficticios descriptivos:
  ```json
  {
    "id": 1,
    "nombre": "JUAN PEREZ",
    "email": "juan.perez@ejemplo.com"
  }
  ```
- **`notificaciones`**: Webhook URL en cadena vacía y estado inactivo (`activo: false`).
- **`historial` y `excepciones`**: Diccionarios limpios `{}` para que el usuario inicie desde el mes operativo de su elección.
- **`siguiente_id`**: Apuntando al ID inicial (1).
- **`schema_version`**: Declarado explícitamente en `2` para validación de compatibilidad con `ConfigValidator`.

### 5.2 Resiliencia y Escritura Atómica en Disco
Para evitar corrupción de datos por fallas de energía o bloqueos del sistema operativo:
- Toda persistencia en `config.json` se realiza mediante archivo temporal (`config.json.tmp`) con forzado de escritura a disco (`os.fsync`) y reemplazo atómico mediante `os.replace`.
- Si se detecta un archivo corrupto, el motor genera un respaldo con extensión `.corrupted_TIMESTAMP` antes de reinicializar los valores por defecto.

---

## 6. GESTIÓN SEGURA DE CREDENCIALES Y CANALES DE COMUNICACIÓN

### 6.1 Política de Credenciales SMTP (Google Workspace / Gmail)
1. **Prohibición de Contraseñas Maestras**: Nunca debe configurarse la contraseña personal de la cuenta de correo Google en el archivo `.env`.
2. **Uso Exclusivo de Contraseñas de Aplicación (App Passwords)**:
   - Debe activarse la Verificación en 2 Pasos (2FA) en la cuenta institucional o de servicio.
   - Generar una clave de 16 caracteres exclusiva para el Sistema de Turnos desde `myaccount.google.com/apppasswords`.
   - Dicha clave debe colocarse únicamente en el archivo local `.env` (`SMTP_PASSWORD`).
   - La clave de aplicación puede ser revocada en cualquier momento desde el panel de Google sin comprometer la cuenta.

### 6.2 Cifrado de Comunicaciones en Tránsito
- **SMTP**: Conexión forzada con TLS criptográfico (`SMTP_USE_TLS=true`) en el puerto 587 (`smtp.gmail.com`).
- **Google Apps Script Webhook**: Comunicación exclusiva bajo protocolo HTTPS cifrado (puerto 443).
- **Verificación Previa**: Antes de cualquier intento de conexión SMTP o HTTP, el sistema ejecuta una verificación de conectividad de bajo nivel para prevenir bloqueos de interfaz gráfica en entornos sin red.

### 6.3 Privacidad en Envíos de Correo Masivo
- Al despachar avisos automáticos a la dotación, si existen múltiples destinatarios, el sistema debe utilizar **Copia Oculta (CCO / BCC)** para que ningún funcionario visualice las direcciones personales o privadas de los demás miembros de la guardia.

---

## 7. PROTOCOLO DE INCIDENTES Y PURGA DEL HISTORIAL DE GIT

### 7.1 Alerta Crítica sobre el Historial de Git
> [!WARNING]
> Un commit convencional (`git rm` o edición de archivo) **NO elimina** los datos sensibles de los commits anteriores. Si un archivo con nombres, correos o contraseñas fue subido a GitHub en el pasado, permanece visible y descargable a través del historial de commits de la rama o de la API de GitHub.

### 7.2 Procedimiento de Purga del Historial de Git (Git Filter-Repo)
Si se requiere eliminar definitivamente rastros históricos de archivos con PII o secretos en un repositorio remoto, se debe ejecutar el siguiente procedimiento:

1. **Respaldar el repositorio completo**:
   ```bash
   cp -r "Sistema de turnos" "Sistema de turnos_backup_seguridad"
   ```

2. **Instalar la herramienta oficial de purga**:
   ```bash
   pip install git-filter-repo
   ```

3. **Purgar carpetas y archivos sensibles del historial completo**:
   ```bash
   # Eliminar del historial la carpeta backups que contenía datos operativos
   git filter-repo --path backups --invert-paths --force

   # Eliminar del historial versiones antiguas de config.json si tuvieron PII
   git filter-repo --path config.json --invert-paths --force
   ```

4. **Sincronizar el repositorio limpio con GitHub (Sobreescritura controlada)**:
   ```bash
   git remote add origin https://github.com/MartinLopez1011/Sistema-de-turnos.git
   git push origin --force --all
   git push origin --force --tags
   ```

### 7.3 Protocolo Inmediato de Rotación de Credenciales
Ante cualquier sospecha o evidencia de que credenciales fueron expuestas en commits públicos o compartidos:
1. **Revocar inmediatamente la Contraseña de Aplicación de Gmail**:
   - Ingresar a `https://myaccount.google.com/apppasswords`.
   - Eliminar la clave "Sistema de Turnos".
   - Generar una nueva clave y actualizar el archivo local `.env`.
2. **Revocar la URL del Webhook de Google Apps Script**:
   - Ingresar a `script.google.com` > Proyecto > Administrar implementaciones.
   - Archivar o eliminar la implementación expuesta.
   - Crear una nueva versión de implementación y copiar la nueva URL en el `.env` local.

---

## 8. CHECKLIST DE SEGURIDAD PARA EL DESARROLLADOR

Antes de ejecutar `git add .` o `git commit`, verifique la siguiente lista de control:

- [ ] **1. Sin PII en código o pruebas:** ¿Se verificó que no existan nombres reales de funcionarios ni correos institucionales en tests, scripts o comentarios?
- [ ] **2. `config.json` no está en staged:** ¿Se confirmó mediante `git status` que `config.json` no aparece como archivo nuevo o modificado para commit?
- [ ] **3. Carpeta `backups/` excluida:** ¿Está la carpeta `backups/` fuera del control de versiones (`.gitignore`)?
- [ ] **4. `.env` protegido:** ¿Se confirmó que el archivo `.env` con contraseñas de correo nunca esté rastreado por Git?
- [ ] **5. `.env.example` sanitizado:** ¿Las variables en `.env.example` contienen solo textos explicativos y placeholders (`TU_WEBHOOK_URL_AQUI`)?
- [ ] **6. Planillas Excel sanitizadas:** ¿Se confirmó que `ejemplo.xlsx` o cualquier archivo adjunto tenga únicamente funcionarios genéricos?
- [ ] **7. Manuales y documentación limpios:** ¿El manual PDF y el HTML contienen capturas y ejemplos con dotación de prueba?

---

*Documento aprobado y vigente para el repositorio del Sistema de Gestión de Turnos.*
