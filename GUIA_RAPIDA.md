# 🚀 Guía Rápida de Inicio

## Instalación (5 minutos)

### 1. Instalar dependencias

```bash
# Crear entorno virtual
python -m venv .venv

# Activar (Windows)
.venv\Scripts\activate

# Activar (Mac/Linux)
source .venv/bin/activate

# Instalar
pip install -r requirements.txt
```

### 2. Ejecutar

```bash
# Opción tradicional
python main.py

# Windows (doble clic)
# Ejecuta el archivo EJECUTAR.bat para abrir la app sin usar la terminal
```

---

## Primera Configuración (10 minutos)

### Paso 1: Crear Perfiles

1. Ve a la pestaña **"Perfiles"**
2. Ingresa un nombre: `Línea 1`
3. Clic en **"Crear Perfil"**
4. Repite para crear más perfiles si tienes más líneas

### Paso 2: Vincular Google Messages

1. En la pestaña **"Perfiles"**, selecciona un perfil
2. Clic en **"Abrir Chrome"**
3. Se abrirá Google Messages Web
4. **Inicia sesión con tu cuenta de Google**
5. **Escanea el código QR con tu teléfono** (en la app de Google Messages)
6. Verifica que puedas ver tus conversaciones
7. Cierra el navegador
8. Repite para cada perfil con diferentes teléfonos

### Paso 3: Subir Contactos

1. Ve a la pestaña **"Excel / Contactos"**
2. Clic en **"Subir archivo Excel/CSV"**
3. Selecciona tu archivo (usa `EJEMPLO_CONTACTOS.csv` para probar)
4. Selecciona el archivo en la lista
5. Clic en **"Procesar archivo seleccionado"**

---

## Enviar Campaña (2 minutos)

### Paso 1: Configurar Campaña

1. Ve a la pestaña **"Campañas"**
2. Ingresa nombre: `Prueba 1`
3. Selecciona lista de contactos procesada
4. Configura delay: `5 segundos`

### Paso 2: Crear Mensaje

1. Haz clic en las **variables disponibles** para insertarlas
2. Ejemplo de mensaje:

```
Hola {Nombre}, te recordamos tu saldo de ${$ Asig.}. ¡Gracias!
```

### Paso 3: Seleccionar Perfiles

1. En la lista de perfiles, **selecciona uno o más** (Ctrl+Click para múltiples)
2. Los perfiles activos ya están pre-seleccionados

### Paso 4: Enviar

1. Clic en **"🚀 ENVIAR AHORA"**
2. Confirma el envío
3. Los navegadores se abrirán automáticamente
4. Ve el progreso en el log
5. ¡Listo! Los mensajes se enviarán automáticamente

---

## 💡 Consejos

### Para Pruebas

- Usa solo 2-3 contactos al principio
- Delay de 5-10 segundos
- Verifica que los mensajes lleguen correctamente

### Para Producción

- Usa delay de 10-15 segundos para evitar bloqueos
- Distribuye mensajes entre múltiples perfiles
- Envía en horarios razonables
- Respeta las políticas de Google

### Solución Rápida de Problemas

**No se abren los navegadores:**
- Verifica que Chrome esté instalado
- Ejecuta: `pip install --upgrade selenium`

**No se envían mensajes:**
- Verifica que hayas iniciado sesión en Google Messages
- Abre Chrome manualmente y verifica la sesión
- Aumenta el delay entre mensajes

**Error de Selenium:**
- Ejecuta: `pip install selenium`
- Actualiza Chrome a la última versión

---

## 📊 Formato del Excel

Tu archivo Excel/CSV debe tener estas columnas:

| Columna | Descripción | Obligatorio |
|---------|-------------|-------------|
| `Telefono_1` | Número de teléfono | ✅ Sí |
| `Nombre` | Nombre del contacto | ❌ No |
| `$ Hist.` | Monto histórico | ❌ No |
| `$ Asig.` | Monto asignado | ❌ No |

Puedes agregar más columnas y usarlas como variables en los mensajes.

---

## 🎯 Ejemplo Completo

### 1. Crear perfil "Línea 1"
### 2. Abrir Chrome y vincular teléfono
### 3. Subir `EJEMPLO_CONTACTOS.csv`
### 4. Procesar archivo
### 5. Crear campaña "Prueba"
### 6. Mensaje: `Hola {Nombre}, tu saldo es ${$ Asig.}`
### 7. Seleccionar perfil "Línea 1"
### 8. Delay: 5 segundos
### 9. Clic en "🚀 ENVIAR AHORA"
### 10. ¡Listo!

---

## ⚠️ Importante

- **Primera vez**: Debes vincular cada perfil con Google Messages
- **Sesión**: La sesión se guarda, no necesitas volver a vincular
- **Múltiples perfiles**: Cada perfil debe usar un teléfono diferente
- **Delay**: Usa al menos 5 segundos para evitar bloqueos
- **Pruebas**: Siempre prueba con pocos contactos primero

---

## 🆘 Soporte

Si tienes problemas, revisa:

1. `README.md` - Documentación completa
2. Log de progreso en la pestaña Campañas
3. Consola de Python para errores detallados

---

**¡Listo para enviar mensajes automáticamente!** 🚀
