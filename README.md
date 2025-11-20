# SMS Multi-Perfil Local

Aplicación de escritorio para gestión de perfiles de líneas telefónicas, procesamiento de archivos Excel y **envío automático** de campañas de SMS masivos a través de Google Messages Web.

## 📋 Características

- **Gestión de Perfiles**: Crea y administra múltiples perfiles de líneas telefónicas
- **Navegadores Independientes**: Abre Chrome con perfiles separados para cada línea
- **Procesamiento de Excel**: Importa y procesa archivos Excel/CSV con contactos
- **Plantillas de Mensajes**: Crea plantillas con variables dinámicas
- **Selección de Variables**: Interfaz visual para insertar variables del Excel
- **Selección Múltiple de Perfiles**: Elige qué perfiles usar en cada campaña
- **Envío Automático**: Envía mensajes automáticamente usando Selenium
- **Rotación de Perfiles**: Distribuye mensajes entre múltiples perfiles
- **Interfaz Oscura**: Diseño moderno con tema oscuro

## 🚀 Instalación

### Requisitos previos

- Python 3.8 o superior
- Google Chrome instalado
- ChromeDriver (se instala automáticamente con Selenium)
- Windows, macOS o Linux

### Pasos de instalación

1. **Crear entorno virtual**

```bash
python -m venv .venv
```

2. **Activar entorno virtual**

**Windows:**
```bash
.venv\Scripts\activate
```

**macOS/Linux:**
```bash
source .venv/bin/activate
```

3. **Instalar dependencias**

```bash
pip install -r requirements.txt
```

4. **Descargar navegadores de Playwright**

```bash
playwright install chromium
```

5. **Ejecutar la aplicación**

Puedes abrir la app de dos maneras:

- **Modo clásico:**

  ```bash
  python main.py
  ```

- **Windows | Doble clic:**

  Coloca el archivo `EJECUTAR.bat` dentro de la carpeta del programa y haz doble
  clic sobre él. El script cambia automáticamente al directorio correcto y
  lanza `main.py`, por lo que no necesitas abrir la terminal.

## 📁 Estructura del Proyecto

```
sms_multiperfil_local/
├── main.py                      # Punto de entrada de la aplicación
├── gui/                         # Interfaz gráfica
│   ├── main_window.py          # Ventana principal con pestañas
│   ├── profiles_tab.py         # Pestaña de perfiles (con carga de Excel)
│   ├── campaigns_tab.py        # Pestaña de campañas (CON ENVÍO)
│   └── status_tab.py           # Pestaña de estado de envíos
├── core/                        # Lógica de negocio
│   ├── profiles_manager.py     # Gestor de perfiles
│   ├── excel_processor.py      # Procesador de Excel
│   ├── templates_manager.py    # Gestor de plantillas
│   └── sending_engine.py       # Motor de envío con Selenium
├── data/                        # Datos de la aplicación
│   ├── perfiles.json           # Perfiles guardados
│   ├── plantillas.json         # Plantillas de mensajes
│   ├── uploads/                # Archivos Excel subidos
│   ├── processed/              # Archivos procesados (JSON)
│   └── campaigns/              # Campañas creadas
├── profiles_storage/            # Datos de perfiles de Chrome
├── requirements.txt             # Dependencias Python
└── README.md                    # Este archivo
```

## 🎯 Uso

### 1. Gestión de Perfiles

1. Ve a la pestaña **"Perfiles"**
2. Ingresa un nombre para el nuevo perfil (ej: "Línea 1")
3. Haz clic en **"Crear Perfil"**
4. Usa el checkbox **"Activo"** para habilitar/deshabilitar perfiles en campañas
5. Haz clic en **"Abrir Chrome"** para abrir Google Messages Web con ese perfil
6. **IMPORTANTE**: Inicia sesión en Google Messages la primera vez y vincula tu teléfono

### 2. Procesar Excel

1. Ve a la pestaña **"Perfiles"** y buscá el bloque **"Contactos desde Excel"**
2. Haz clic en **"Cargar y procesar Excel"**
3. Selecciona tu archivo con contactos
4. Espera el mensaje de confirmación indicando la cantidad de registros
5. ¡Listo! El archivo queda disponible automáticamente en la pestaña **Campañas**

#### Formato del Excel

El archivo debe tener las siguientes columnas:

- `Telefono_1`: Teléfono principal (puede contener múltiples separados por guión)
- `Telefono_2` a `Telefono_9`: Teléfonos adicionales (opcional)
- `Nombre`: Nombre del contacto (opcional)
- `$ Hist.`: Monto histórico (opcional)
- `$ Asig.`: Monto asignado (opcional)

**Ejemplo:**

| Telefono_1 | Nombre | $ Hist. | $ Asig. |
|------------|--------|---------|---------|
| 1167206128 | Juan   | $1000   | $500    |
| 1156925321-1145678901 | María | $2000 | $1500 |

### 3. Crear y Enviar Campañas

1. Ve a la pestaña **"Campañas"**
2. Ingresa un **nombre para la campaña**
3. Selecciona la **lista de contactos procesada**
4. Configura el **delay entre mensajes** (recomendado: 5-10 segundos)
5. Las **variables disponibles** aparecerán automáticamente del Excel
6. Haz clic en los botones de variables para insertarlas en el mensaje
7. Edita el **contenido del mensaje** usando las variables
8. **Selecciona los perfiles** que quieres usar (puedes seleccionar múltiples)
9. Haz clic en **"🚀 ENVIAR AHORA"**

#### Ejemplo de Mensaje con Variables

```
Hola {Nombre}, te recordamos que tenés un saldo pendiente de ${$ Asig.}. 
Para más información, comunicate al teléfono {Telefono_1}. ¡Gracias!
```

### 4. Proceso de Envío Automático

Cuando hagas clic en **"ENVIAR AHORA"**:

1. ✅ Se abrirán automáticamente los navegadores Chrome para cada perfil seleccionado
2. ✅ Los navegadores cargarán Google Messages Web
3. ✅ El sistema verificará que estén en la página correcta
4. ✅ Se comenzará a enviar mensajes automáticamente
5. ✅ Los mensajes se rotarán entre los perfiles seleccionados
6. ✅ Se aplicará el delay configurado entre cada mensaje
7. ✅ Verás el progreso en tiempo real en el log
8. ✅ Al finalizar, los navegadores se cerrarán automáticamente

### 5. Estado de Envíos

1. Ve a la pestaña **"Estado de Envíos"**
2. Visualiza las campañas creadas y su progreso
3. Haz clic en **"Refrescar"** para actualizar

## 🔧 Configuración Avanzada

### ChromeDriver

Selenium 4.15+ incluye **Selenium Manager** que descarga automáticamente ChromeDriver. No necesitas instalarlo manualmente.

### Múltiples Perfiles

Puedes usar múltiples perfiles simultáneamente:

- Los mensajes se distribuyen automáticamente entre todos los perfiles seleccionados
- Cada perfil mantiene su propia sesión de Google Messages
- Esto permite enviar más mensajes sin saturar una sola línea

### Delay entre Mensajes

Recomendaciones:

- **5-10 segundos**: Para envíos normales
- **15-30 segundos**: Para envíos más seguros
- **1-3 segundos**: Solo para pruebas (puede causar bloqueos)

## ⚠️ Notas Importantes

### Primera Configuración

1. **Crear perfiles**: Crea al menos un perfil en la pestaña "Perfiles"
2. **Abrir Chrome**: Haz clic en "Abrir Chrome" para cada perfil
3. **Iniciar sesión**: En cada navegador, inicia sesión en Google Messages
4. **Vincular teléfono**: Escanea el código QR con tu teléfono
5. **Verificar**: Asegúrate de que puedas ver tus conversaciones
6. **Cerrar**: Cierra los navegadores manualmente
7. **Listo**: La sesión quedará guardada para futuros envíos

### Seguridad

- ⚠️ **No compartas tus perfiles**: Contienen tus sesiones de Google
- ⚠️ **Usa delays razonables**: Evita bloqueos por spam
- ⚠️ **Prueba primero**: Haz pruebas con pocos contactos
- ⚠️ **Respeta la privacidad**: Solo envía mensajes a contactos que lo autoricen

### Limitaciones

- Google Messages puede tener límites de envío diarios
- Si envías demasiado rápido, Google puede bloquear temporalmente
- Cada perfil debe estar vinculado a un teléfono diferente
- Los navegadores deben permanecer abiertos durante el envío

## 🛠️ Solución de Problemas

### "Selenium no está instalado"

```bash
pip install selenium
```

### Chrome no se abre automáticamente

- Verifica que Chrome esté instalado
- Actualiza Chrome a la última versión
- Reinstala Selenium: `pip install --upgrade selenium`

### Error al enviar mensajes

- Verifica que hayas iniciado sesión en Google Messages
- Asegúrate de que el teléfono esté vinculado
- Abre Chrome manualmente desde "Perfiles" y verifica la sesión
- Aumenta el delay entre mensajes

### Los mensajes no se envían

- Verifica que el formato del teléfono sea correcto (sin espacios ni guiones)
- Asegúrate de que Google Messages esté funcionando
- Prueba enviar un mensaje manualmente desde el navegador
- Revisa el log de progreso para ver errores específicos

### Perfiles no se guardan

- Verifica permisos de escritura en la carpeta `data/`
- Revisa que no haya errores en la consola

## 📊 Variables del Excel

Puedes usar cualquier columna de tu Excel como variable en los mensajes:

- `{Nombre}` - Nombre del contacto
- `{Telefono_1}` - Teléfono principal
- `{$ Hist.}` - Monto histórico
- `{$ Asig.}` - Monto asignado
- Y cualquier otra columna que tengas en tu Excel

## 🎨 Características de la Interfaz

### Selección Visual de Variables

- Las variables del Excel aparecen como botones
- Haz clic en un botón para insertar la variable en el mensaje
- Las variables se insertan en la posición del cursor

### Selección Múltiple de Perfiles

- Puedes seleccionar uno o más perfiles para cada campaña
- Los mensajes se distribuyen automáticamente entre los perfiles
- Los perfiles activos se pre-seleccionan automáticamente

### Log de Progreso en Tiempo Real

- Ve el progreso de envío en tiempo real
- Mensajes detallados de cada paso
- Contador de enviados/fallidos
- Auto-scroll al final

## 📝 Licencia

Este proyecto es de uso libre para fines personales y educativos.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un issue o pull request en el repositorio.

## 📧 Soporte

Para reportar bugs o solicitar funcionalidades, abre un issue en el repositorio del proyecto.

---

## 🆕 Novedades en esta Versión

### ✨ Envío Automático Funcional

- ✅ Envío real de mensajes usando Selenium
- ✅ Apertura automática de navegadores
- ✅ Rotación entre múltiples perfiles
- ✅ Log de progreso en tiempo real
- ✅ Manejo de errores robusto

### ✨ Interfaz Mejorada

- ✅ Selección visual de variables del Excel
- ✅ Selección múltiple de perfiles
- ✅ Botón "ENVIAR AHORA" con confirmación
- ✅ Log de progreso con scroll automático
- ✅ Mensajes de estado detallados

### ✨ Funcionalidades Avanzadas

- ✅ Distribución automática de mensajes entre perfiles
- ✅ Delay configurable entre mensajes
- ✅ Aplicación de plantillas con variables
- ✅ Procesamiento de Excel mejorado
- ✅ Gestión de campañas completa

---

**Versión:** 2.0.0 - FUNCIONAL  
**Última actualización:** Noviembre 2025  
**Estado:** ✅ COMPLETAMENTE FUNCIONAL CON ENVÍO AUTOMÁTICO
