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

## Seguridad

El archivo `.env` contiene secretos y no debe subirse al repositorio. Usa `.env.example` únicamente como guía y reemplaza todos los valores de ejemplo en cada instalación.
