# 🧩 acad_micros

🎯 **Plantilla base para aplicaciones del DCC**  
Esta plantilla proporciona una **estructura reutilizable y escalable** para desarrollar módulos dentro del ecosistema del DCC (Departamento de Ciencias de la Computación, Universidad de Chile). Está pensada para facilitar el desarrollo ágil y mantener buenas prácticas, integrando componentes comunes, configuraciones iniciales optimizadas y una base sólida para construir nuevas aplicaciones.

---

## 🚀 ¿Qué incluye esta plantilla?

- Estructura modular y organizada de proyecto.
- Configuración base para desarrollo local con Docker.
- Componentes compartidos utilizados frecuentemente en el ecosistema DCC.
- Integración con servicios comunes como autenticación con U-Pasaporte y obtención de datos de usuarios.
- Buenas prácticas preconfiguradas: formato de código, administración de dependencias, etc.

---

## 📦 Clonación del repositorio

Para obtener una copia funcional del proyecto, **no olvides clonar el repositorio con sus submódulos**. Esto es importante, ya que incluye dependencias adicionales necesarias para que todo funcione correctamente (como la conexión con Pasaporte y utilidades compartidas).

```bash
git clone --recursive https://github.com/DCC-FCFM-UCHILE/<repositorio>.git
```

---

## ⚙️ Ejecución del proyecto

Una vez clonado el repositorio, entra al directorio `.docker/` y ejecuta:

```bash
# no olvidar el _ ya que para nosotros significa (local)
make _build
```

Este comando se encargará de construir la imagen, levantar los servicios de Docker y dejar el entorno listo para usar.

Una vez finalizado, deberías ver algo como lo siguiente:

```
[+] Running 3/3
 ✔ Network acad_micros_default  Created
 ✔ Container postgresql               Healthy
 ✔ Container acad_micros        Started
```

Puedes verificar los contenedores con:

```bash
docker ps
```

Ejemplo de salida:

```
CONTAINER ID   IMAGE                      COMMAND                  CREATED          STATUS                    PORTS                                            NAMES
cfa17ae1392b   acad_micros-django   "sh -c 'python -m de…"   11 seconds ago   Up Less than a second     0.0.0.0:5678->5678/tcp, 0.0.0.0:8000->8000/tcp   acad_micros
3857b1945b6f   postgres:13.3              "docker-entrypoint.s…"   11 seconds ago   Up 11 seconds (healthy)   5432/tcp                                         postgresql
```

Para acceder al contenedor principal, puedes usar:

```bash
make ssh
```

Y ejecutar los siguientes comandos dentro del contenedor para aplicar las migraciones:

```bash
python manage.py makemigrations
python manage.py migrate
```

Ejemplo de salida esperada (resumen):

```
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying contenttypes.0002_remove_content_type_name... OK
  Applying auth.0001_initial... OK
  ...
  Applying polls.0001_initial... OK
  Applying sessions.0001_initial... OK
```

Luego puedes cargar datos de prueba:

```bash
make loaddata
```

Este comando ejecutará:

```bash
python manage.py loaddata _fixtures/users.json
python manage.py loaddata _fixtures/polls.json
```

Resultado:

```
Installed 1 object(s) from 1 fixture(s)
Installed 3 object(s) from 1 fixture(s)
```

---

## 🌐 Acceso vía navegador

Finalmente, abre tu navegador y accede a:

```
http://localhost:8000/
```

¡Listo! Ya tienes la aplicación en funcionamiento localmente y puedes comenzar a trabajar o explorar el entorno.

---

## 🙋‍♀️ ¿Tienes dudas o necesitas ayuda?

💬 **Este proyecto está pensado para ser colaborativo y servir de base común.**  
Si tienes preguntas o deseas proponer mejoras, no dudes en abrir un issue 🐛 o contactar al equipo de desarrollo 👥.

---

## 🏁 ¡A construir juntos!

Con esta plantilla, buscamos facilitar el desarrollo de sistemas robustos, integrados y mantenibles dentro del ecosistema DCC. ¡Esperamos que te sea útil y puedas contribuir con nuevas ideas y mejoras!
