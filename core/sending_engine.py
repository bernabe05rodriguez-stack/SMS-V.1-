"""
Motor de envío de mensajes.
Coordina el envío de mensajes a través de los perfiles activos usando Selenium.
"""

import json
import os
import time
import platform
import subprocess
import random
import re
from datetime import datetime
from pathlib import Path

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import (
        TimeoutException,
        NoSuchElementException,
        ElementClickInterceptedException,
    )
    from selenium.webdriver.common.action_chains import ActionChains
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


class SendingEngine:
    """Motor de envío de campañas de SMS."""
    
    def __init__(self):
        """Inicializa el motor de envío."""
        self.campaigns_dir = "data/campaigns"
        os.makedirs(self.campaigns_dir, exist_ok=True)
        self.drivers = {}  # Almacena los drivers por perfil
    
    def create_campaign(self, campaign_data):
        """
        Crea una nueva campaña.
        
        Args:
            campaign_data: Diccionario con datos de la campaña:
                - nombre: Nombre de la campaña
                - template_name: Nombre de la plantilla
                - template_content: Contenido de la plantilla
                - profiles: Lista de perfiles activos
                - contacts_file: Archivo de contactos procesados
                - delay_min: Delay mínimo entre mensajes en segundos
                - delay_max: Delay máximo entre mensajes en segundos
                
        Returns:
            tuple: (success, message)
        """
        try:
            # Generar ID único basado en timestamp
            campaign_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            campaign = {
                "id": campaign_id,
                "nombre": campaign_data['nombre'],
                "template_name": campaign_data['template_name'],
                "template_content": campaign_data['template_content'],
                "profiles": campaign_data['profiles'],
                "contacts_file": campaign_data['contacts_file'],
                "delay_min": campaign_data['delay_min'],
                "delay_max": campaign_data['delay_max'],
                "created_at": datetime.now().isoformat(),
                "status": "created",
                "total_messages": 0,
                "sent_messages": 0,
                "failed_messages": 0
            }
            
            # Guardar campaña
            campaign_file = os.path.join(self.campaigns_dir, f"{campaign_id}.json")
            
            with open(campaign_file, 'w', encoding='utf-8') as f:
                json.dump(campaign, f, indent=2, ensure_ascii=False)
            
            return True, f"Campaña creada exitosamente (ID: {campaign_id})"
            
        except Exception as e:
            return False, f"Error al crear campaña: {str(e)}"
    
    def get_campaigns(self):
        """Retorna lista de campañas creadas."""
        campaigns = []
        
        if not os.path.exists(self.campaigns_dir):
            return campaigns
        
        for file in os.listdir(self.campaigns_dir):
            if file.endswith('.json'):
                try:
                    filepath = os.path.join(self.campaigns_dir, file)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        campaign = json.load(f)
                        campaigns.append(campaign)
                except Exception as e:
                    print(f"Error al cargar campaña {file}: {e}")
        
        # Ordenar por fecha de creación descendente
        campaigns.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return campaigns
    
    def start_campaign(self, campaign_id, progress_callback=None):
        """
        Inicia el envío de una campaña.
        
        Args:
            campaign_id: ID de la campaña a iniciar
            progress_callback: Función callback para reportar progreso
            
        Returns:
            tuple: (success, message)
        """
        if not SELENIUM_AVAILABLE:
            return False, "Selenium no está instalado. Ejecuta: pip install selenium"
        
        def log(message):
            """Helper para logging."""
            if progress_callback:
                progress_callback.emit(message)
            print(message)
        
        try:
            # Cargar campaña
            campaign_file = os.path.join(self.campaigns_dir, f"{campaign_id}.json")
            
            if not os.path.exists(campaign_file):
                return False, "Campaña no encontrada"
            
            with open(campaign_file, 'r', encoding='utf-8') as f:
                campaign = json.load(f)
            
            # Cargar contactos
            from core.excel_processor import ExcelProcessor
            processor = ExcelProcessor()
            contacts = processor.load_processed_file(campaign['contacts_file'])
            
            if not contacts:
                return False, "No se pudieron cargar los contactos"
            
            campaign['total_messages'] = len(contacts)
            
            log(f"📊 Total de contactos: {len(contacts)}")
            log(f"👥 Perfiles a usar: {', '.join(campaign['profiles'])}")
            log("")
            
            # Abrir navegadores para cada perfil
            log("🌐 Abriendo navegadores...")
            
            for profile_name in campaign['profiles']:
                try:
                    driver = self._open_browser_for_profile(profile_name)
                    self.drivers[profile_name] = driver
                    log(f"✅ Navegador abierto para perfil: {profile_name}")
                    time.sleep(1.2)
                except Exception as e:
                    log(f"❌ Error al abrir navegador para {profile_name}: {str(e)}")
                    return False, f"Error al abrir navegador para {profile_name}"
            
            log("")
            log("⏳ Esperando 10 segundos para que carguen los navegadores...")
            time.sleep(10)
            
            # Verificar que estén en Google Messages
            log("")
            log("🔍 Verificando que los navegadores estén en Google Messages...")
            
            for profile_name, driver in self.drivers.items():
                try:
                    current_url = driver.current_url
                    if "messages.google.com" not in current_url:
                        log(f"⚠️ {profile_name}: No está en Google Messages, redirigiendo...")
                        driver.get("https://messages.google.com/web")
                        time.sleep(3)
                    else:
                        log(f"✅ {profile_name}: En Google Messages")
                except Exception as e:
                    log(f"❌ Error verificando {profile_name}: {str(e)}")
            
            log("")
            log("🚀 Iniciando envío de mensajes...")
            log("-" * 50)
            
            # Enviar mensajes
            profile_index = 0
            profile_names = list(self.drivers.keys())
            
            if not profile_names:
                return False, "No hay perfiles disponibles"
            
            delay_min = max(1, campaign.get('delay_min', 1))
            delay_max = max(delay_min, campaign.get('delay_max', delay_min))

            for idx, contact in enumerate(contacts, 1):
                # Rotar entre perfiles
                profile_name = profile_names[profile_index % len(profile_names)]
                driver = self.drivers[profile_name]
                
                # Obtener teléfono
                phone_raw = str(contact.get('Telefono_1', contact.get('Telefono', '')))
                phone = self._normalize_phone(phone_raw)

                if not phone:
                    log(f"⚠️ [{idx}/{len(contacts)}] Contacto sin teléfono válido, saltando...")
                    campaign['failed_messages'] += 1
                    continue
                
                # Aplicar plantilla
                from core.templates_manager import TemplatesManager
                templates_mgr = TemplatesManager()
                message = templates_mgr.apply_template(campaign['template_content'], contact)
                
                # Enviar mensaje
                try:
                    log(f"📤 [{idx}/{len(contacts)}] Enviando a {phone} con perfil {profile_name}...")
                    
                    success = self._send_message_via_browser(driver, phone, message, log)
                    
                    if success:
                        log(f"   ✅ Mensaje enviado exitosamente")
                        campaign['sent_messages'] += 1
                    else:
                        log(f"   ❌ Error al enviar mensaje")
                        campaign['failed_messages'] += 1
                    
                    # Delay entre mensajes
                    if idx < len(contacts):
                        delay_seconds = random.uniform(delay_min, delay_max)
                        delay_seconds = max(1, delay_seconds)
                        log(f"   ⏱️ Esperando {delay_seconds:.1f} segundos...")
                        time.sleep(delay_seconds)
                    
                    # Rotar al siguiente perfil
                    profile_index += 1
                    
                except Exception as e:
                    log(f"   ❌ Error: {str(e)}")
                    campaign['failed_messages'] += 1
            
            # Actualizar campaña
            campaign['status'] = 'completed'
            
            with open(campaign_file, 'w', encoding='utf-8') as f:
                json.dump(campaign, f, indent=2, ensure_ascii=False)
            
            log("-" * 50)
            log(f"✅ Campaña completada")
            log(f"📊 Enviados: {campaign['sent_messages']}/{campaign['total_messages']}")
            log(f"❌ Fallidos: {campaign['failed_messages']}")
            
            # Cerrar navegadores
            log("")
            log("🔒 Cerrando navegadores...")
            self._close_all_browsers()
            
            return True, f"Campaña completada: {campaign['sent_messages']} enviados, {campaign['failed_messages']} fallidos"
            
        except Exception as e:
            self._close_all_browsers()
            return False, f"Error en el envío: {str(e)}"

    def _normalize_phone(self, phone):
        """Limpia el número de teléfono, dejando solo dígitos y un prefijo + opcional."""
        if not phone:
            return ""

        # Mantener un posible "+" al inicio y eliminar cualquier carácter que no sea dígito
        phone = str(phone).strip()
        has_plus = phone.startswith("+")
        digits = re.sub(r"\D", "", phone)

        if not digits:
            return ""

        return f"+{digits}" if has_plus else digits
    
    def _open_browser_for_profile(self, profile_name):
        """Abre un navegador Chrome con el perfil especificado."""
        # Obtener ruta del perfil
        profile_path = Path("profiles_storage") / profile_name
        profile_path.mkdir(parents=True, exist_ok=True)
        
        # Configurar opciones de Chrome
        options = webdriver.ChromeOptions()
        options.add_argument(f"--user-data-dir={profile_path.absolute()}")
        options.add_argument("--profile-directory=Default")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Crear driver
        driver = webdriver.Chrome(options=options)
        driver.maximize_window()
        driver.get("https://messages.google.com/web")
        
        return driver
    
    def _send_message_via_browser(self, driver, phone, message, log):
        """
        Envía un mensaje a través del navegador usando Selenium.
        Estrategia mejorada para Google Messages Web.
        
        Args:
            driver: WebDriver de Selenium
            phone: Número de teléfono
            message: Mensaje a enviar
            log: Función de logging
            
        Returns:
            bool: True si se envió exitosamente
        """
        try:
            log(f"   🔍 Navegando a nueva conversación...")
            
            # Ir a la página principal primero
            driver.get("https://messages.google.com/web/conversations")
            time.sleep(1.5)
            
            # Buscar el botón "Start chat" o "Iniciar chat"
            wait = WebDriverWait(driver, 10)
            
            # Intentar diferentes selectores para el botón de nuevo chat
            start_chat_selectors = [
                "//button[@aria-label='Start chat']",
                "//button[@aria-label='Iniciar chat']",
                "//a[@href='/web/conversations/new']",
                "//button[contains(@class, 'start-chat')]",
                "//mw-fab-button",
                "//button[contains(., 'Start')]"
            ]
            
            start_chat_btn = None
            start_chat_locator = None
            for selector in start_chat_selectors:
                try:
                    start_chat_btn = wait.until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                    if start_chat_btn:
                        start_chat_locator = (By.XPATH, selector)
                        log(f"   ✅ Botón de nuevo chat encontrado")
                        break
                except Exception:
                    continue

            if start_chat_btn:
                try:
                    wait.until(EC.element_to_be_clickable(start_chat_locator)).click()
                except ElementClickInterceptedException:
                    log("   ⚠️ Botón bloqueado, reintentando con scroll y clic JS...")
                    driver.execute_script(
                        "arguments[0].scrollIntoView({block: 'center', inline: 'center'});",
                        start_chat_btn,
                    )
                    time.sleep(0.5)
                    driver.execute_script("arguments[0].click();", start_chat_btn)
                time.sleep(1.2)
            else:
                # Si no encuentra el botón, ir directamente a la URL
                log(f"   ⚠️ Botón no encontrado, usando URL directa...")
                driver.get("https://messages.google.com/web/conversations/new")
                time.sleep(1.5)
            
            # Buscar el campo "To" para ingresar el número
            log(f"   📝 Ingresando número de teléfono: {phone}")

            to_field_selectors = [
                "//input[@placeholder='Type a name, phone number, or email']",
                "//input[@placeholder='Escribe un nombre, número de teléfono o correo electrónico']",
                "//input[@type='text' and contains(@class, 'input')]",
                "//input[@aria-label='Type a name, phone number, or email']",
                "//mw-text-input//input",
                "//input[contains(@placeholder, 'name')]",
                "//input[contains(@placeholder, 'nombre')]"
            ]

            to_field = None
            for selector in to_field_selectors:
                try:
                    to_field = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                    if to_field:
                        log(f"   ✅ Campo 'To' encontrado")
                        break
                except Exception:
                    continue

            if not to_field:
                log(f"   ❌ No se encontró el campo 'To'")
                return False

            # Paso 3: pegar inmediatamente el número tal como indican las instrucciones
            log("   📋 Pegando número directamente en el campo activo")
            active_target = driver.switch_to.active_element
            try:
                active_target.send_keys(phone)
            except Exception:
                log("   ⚠️ No se pudo pegar en el campo activo, intentando con el campo 'To'")
                to_field.click()
                to_field.send_keys(phone)

            # Paso 4: seleccionar el contacto con Enter
            try:
                driver.switch_to.active_element.send_keys(Keys.ENTER)
            except Exception:
                to_field.send_keys(Keys.ENTER)

            # Paso 5: esperar 2 segundos antes de pegar el mensaje
            time.sleep(2)

            # Paso 5: pegar el mensaje sin mover el foco manualmente
            log(f"   ✍️ Pegando mensaje en el campo actual")
            message_target = driver.switch_to.active_element
            try:
                message_target.send_keys(message)
            except Exception:
                # Si falla, buscar el campo de texto como respaldo
                log("   ⚠️ No se pudo pegar en el campo activo, buscando campo de mensaje...")
                text_field_selectors = [
                    "//div[@contenteditable='true' and @role='textbox']",
                    "//div[@contenteditable='true' and contains(@aria-label, 'Text')]",
                    "//div[@contenteditable='true' and contains(@aria-label, 'Mensaje')]",
                    "//div[@contenteditable='true']",
                    "//textarea[@placeholder='Text message']",
                    "//textarea[@placeholder='Mensaje de texto']",
                    "//mw-message-compose-editor//div[@contenteditable='true']",
                    "//textarea[@aria-label='Mensaje']",
                    "//textarea[@aria-label='Text message']",
                    "//div[@aria-label='Escribe un mensaje']",
                    "//div[@aria-label='Message']",
                    "//div[@role='textbox' and contains(@aria-label, 'message')]",
                    "//div[contains(@data-placeholder, 'mensaje')]",
                ]

                message_target = None
                for selector in text_field_selectors:
                    try:
                        message_target = wait.until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        if message_target:
                            log("   ✅ Campo de mensaje encontrado como respaldo")
                            break
                    except Exception:
                        continue

                if not message_target:
                    log("   ❌ No se pudo localizar un campo de mensaje para pegar el texto")
                    return False

                try:
                    message_target.click()
                except Exception:
                    pass
                message_target.send_keys(message)

            # Paso 6: esperar 2 segundos y enviar con Enter
            log("   ⏳ Esperando 2 segundos antes de enviar...")
            time.sleep(2)
            try:
                driver.switch_to.active_element.send_keys(Keys.ENTER)
                log("   ✅ Enter enviado para mandar el mensaje")
            except Exception:
                # Fallback: intentar localizar botón de enviar
                log("   ⚠️ No se pudo usar Enter, buscando botón de enviar...")
                send_button_selectors = [
                    "//button[@aria-label='Send message']",
                    "//button[@aria-label='Enviar mensaje']",
                    "//button[contains(@aria-label, 'Send')]",
                    "//button[contains(@aria-label, 'Enviar')]",
                    "//button[contains(@class, 'send')]",
                    "//mw-send-button//button"
                ]

                send_button = None
                for selector in send_button_selectors:
                    try:
                        send_button = driver.find_element(By.XPATH, selector)
                        if send_button and send_button.is_enabled():
                            log(f"   ✅ Botón de enviar encontrado")
                            break
                    except Exception:
                        continue

                if send_button:
                    send_button.click()
                    log(f"   ✅ Clic en botón de enviar")
                else:
                    log(f"   ❌ No se encontró método para enviar el mensaje")
                    return False

            # Esperar confirmación
            time.sleep(3)
            
            return True
            
        except TimeoutException:
            log(f"   ❌ Timeout esperando elementos en la página")
            return False
        except Exception as e:
            log(f"   ❌ Error enviando mensaje: {str(e)}")
            return False
    
    def _close_all_browsers(self):
        """Cierra todos los navegadores abiertos."""
        for profile_name, driver in self.drivers.items():
            try:
                driver.quit()
            except:
                pass
        
        self.drivers.clear()
