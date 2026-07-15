# GUIOS+

GUIOS+ es una aplicación web para evaluar alternativas de software libre y de código abierto mediante dimensiones, factores y subfactores del método GUIOS. Permite combinar el criterio del decisor con evidencia bibliográfica, clasificar resultados y generar informes en PDF.

## Funcionalidades

- Administración de usuarios, roles y accesos iniciales por correo.
- Creación y seguimiento de evaluaciones de software.
- Valoración de factores y subfactores.
- Clasificación de resultados y generación de recomendaciones.
- Consulta de evidencia bibliográfica mediante OpenAlex y Scopus.
- Historial de evaluaciones e informes PDF.
- Carga automática de los datos iniciales GUIOS desde CSV.

## Requisitos

- Python 3.14 o compatible con Django 6.
- PostgreSQL.
- Node.js y npm para compilar Tailwind CSS.

## Instalación

### 1. Clonar el proyecto

```powershell
git clone https://github.com/GabrielHasqui/GUIOSS_PLUS.git
cd GUIOSS_PLUS
```

### 2. Crear el entorno virtual

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

En CMD usa:

```bat
.venv\Scripts\activate.bat
```

### 3. Instalar dependencias

```powershell
python -m pip install -r requirements.txt
npm install
```

### 4. Configurar las variables de entorno

```powershell
Copy-Item .env.example .env
```

Edita `.env` y configura como mínimo:

- `SECRET_KEY`: clave privada de Django.
- `POSTGRES_DB`: nombre de la base de datos.
- `POSTGRES_USER`: usuario de PostgreSQL.
- `POSTGRES_PASSWORD`: contraseña del usuario.
- `EMAIL_HOST_USER` y `EMAIL_HOST_PASSWORD`: credenciales para enviar correos.

Puedes generar una clave para Django con:

```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

#### Configurar las APIs bibliográficas

GUIOS+ utiliza OpenAlex y Scopus para buscar publicaciones relacionadas con los factores de una evaluación. Las claves deben guardarse únicamente en `.env`.

**OpenAlex**

1. Crea una cuenta o inicia sesión en [OpenAlex](https://openalex.org/).
2. Abre la sección oficial [API settings](https://openalex.org/settings/api) y genera una clave.
3. Copia la clave y el correo asociado a tu cuenta:

```env
OPENALEX_EMAIL=tu-correo@example.com
OPENALEX_API_KEY=tu-clave-openalex
```

La documentación oficial está disponible en [OpenAlex Developers](https://developers.openalex.org/).

**Scopus**

1. Inicia sesión o crea una cuenta en [Elsevier Developer Portal](https://dev.elsevier.com/).
2. Entra en [Manage API Keys](https://dev.elsevier.com/apikey/manage) y registra una aplicación.
3. Copia la clave generada:

```env
SCOPUS_API_KEY=tu-clave-scopus
```

El acceso a ciertos datos de Scopus puede depender de la suscripción o red de tu institución.

Para comprobar OpenAlex o Scopus desde el proyecto:

```powershell
python manage.py test_literature_apis --source openalex --count 1
python manage.py test_literature_apis --source scopus --count 1
```

#### Configurar el correo electrónico

El correo se utiliza para enviar el enlace de acceso inicial cuando un administrador crea un usuario. El proveedor debe permitir conexiones SMTP con usuario y contraseña.

Ejemplo para Outlook:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp-mail.outlook.com
EMAIL_PORT=587
EMAIL_HOST_USER=tu-cuenta@outlook.com
EMAIL_HOST_PASSWORD=tu-contraseña-o-contraseña-de-aplicación
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
DEFAULT_FROM_EMAIL=tu-cuenta@outlook.com
```

1. Revisa los [datos SMTP oficiales de Outlook](https://support.microsoft.com/en-us/office/pop-imap-and-smtp-settings-for-outlook-com-d088b986-291d-42b8-9564-9c414e2aa040).
2. Si tu cuenta usa verificación en dos pasos, consulta cómo [crear una contraseña de aplicación](https://support.microsoft.com/en-us/account-billing/how-to-get-and-use-app-passwords-5896ed9b-4263-e681-128a-a6f2979a7944).
3. Coloca el correo en `EMAIL_HOST_USER` y `DEFAULT_FROM_EMAIL`.
4. Coloca la contraseña normal o de aplicación en `EMAIL_HOST_PASSWORD`.

Para otro proveedor, sustituye `EMAIL_HOST`, `EMAIL_PORT` y el tipo de seguridad por los valores indicados en su documentación SMTP. No uses `EMAIL_USE_TLS=True` y `EMAIL_USE_SSL=True` al mismo tiempo.

### 5. Crear la base PostgreSQL

Desde PostgreSQL crea la base indicada en `.env`. Con el nombre predeterminado:

```sql
CREATE DATABASE guios_plus;
```

### 6. Aplicar las migraciones

```powershell
python manage.py migrate
```

La primera migración de una base nueva carga automáticamente 3 dimensiones, 18 factores y 61 subfactores desde los CSV del proyecto.

### 7. Crear un administrador

```powershell
python manage.py createsuperuser
```

### 8. Iniciar el proyecto

```powershell
python manage.py runserver
```

Abre `http://127.0.0.1:8000/` en el navegador. Al iniciar `runserver`, Tailwind queda observando las plantillas y recompila los estilos automáticamente. `Ctrl+C` detiene ambos procesos.

## Comandos útiles

```powershell
# Verificar la configuración de Django
python manage.py check

# Ejecutar las pruebas
python manage.py test

# Compilar Tailwind para distribución
npm run tailwind:build

# Ejecutar Django mediante npm
npm run dev
```

## Módulos principales

- `apps/users`: autenticación, perfiles, roles y administración de usuarios.
- `apps/evaluations`: flujo de evaluación, cálculos, resultados e informes.
- `apps/literature`: consultas bibliográficas, documentos y métricas de evidencia.
- `templates`: interfaz HTML del sistema.
- `static`: estilos Tailwind y comportamiento JavaScript.
