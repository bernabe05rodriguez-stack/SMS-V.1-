"""
Motor de envío de mensajes.
Refactorizado para usar Playwright con sesiones persistentes por perfil.
"""

import json
import os
import random
import re
import subprocess
import sys
import time
from time import monotonic
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, Optional

from playwright.sync_api import (
    BrowserContext,
    Error as PlaywrightError,
    Frame,
    Page,
    TimeoutError as PlaywrightTimeoutError,
    sync_playwright,
)


class SendingEngine:
    """Motor de envío de campañas de SMS utilizando Playwright."""

    def __init__(self):
        """Inicializa el motor de envío y los contenedores de sesión."""
        self.campaigns_dir = "data/campaigns"
        os.makedirs(self.campaigns_dir, exist_ok=True)
        self.playwright = None
        self.sessions: Dict[str, Dict[str, object]] = {}

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

    def delete_campaign(self, campaign_id):
        """Elimina una campaña almacenada por su ID."""
        try:
            campaign_file = os.path.join(self.campaigns_dir, f"{campaign_id}.json")

            if not os.path.exists(campaign_file):
                return False, "Campaña no encontrada"

            os.remove(campaign_file)
            return True, "Campaña eliminada correctamente"
        except Exception as e:
            return False, f"Error al eliminar campaña: {str(e)}"

    def start_campaign(self, campaign_id, progress_callback=None, stop_event=None, pause_event=None):
        """
        Inicia el envío de una campaña.

        Args:
            campaign_id: ID de la campaña a iniciar
            progress_callback: Función callback para reportar progreso
            stop_event: Event para cancelar el envío
            pause_event: Event para pausar/reanudar el envío

        Returns:
            tuple: (success, message)
        """

        def log(message):
            """Helper para logging en UI y consola."""
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
            campaign['status'] = 'running'

            with open(campaign_file, 'w', encoding='utf-8') as f:
                json.dump(campaign, f, indent=2, ensure_ascii=False)

            log(f"📊 Total de contactos: {len(contacts)}")
            log(f"👥 Perfiles a usar: {', '.join(campaign['profiles'])}")
            log("")

            # Iniciar Playwright una sola vez
            if not self.playwright:
                self._start_playwright(log)

            log("🌐 Abriendo navegadores persistentes por perfil...")

            for profile_name in campaign['profiles']:
                try:
                    page = self._open_browser_for_profile(profile_name, log)
                    self.sessions[profile_name] = {"page": page}
                    log(f"✅ Navegador listo para perfil: {profile_name}")
                except Exception as e:
                    log(f"❌ Error al abrir navegador para {profile_name}: {str(e)}")
                    self._close_all_browsers()
                    return False, f"Error al abrir navegador para {profile_name}"

            log("")
            log("🚀 Iniciando envío de mensajes...")
            log("-" * 50)

            profile_index = 0
            profile_names = list(self.sessions.keys())

            if not profile_names:
                return False, "No hay perfiles disponibles"

            delay_min = max(0, campaign.get('delay_min', 0.2))
            delay_max = max(delay_min, campaign.get('delay_max', delay_min))

            from core.templates_manager import TemplatesManager
            templates_mgr = TemplatesManager()

            paused_logged = False

            for idx, contact in enumerate(contacts, 1):
                if stop_event and stop_event.is_set():
                    campaign['status'] = 'cancelled'
                    with open(campaign_file, 'w', encoding='utf-8') as f:
                        json.dump(campaign, f, indent=2, ensure_ascii=False)
                    self._close_all_browsers()
                    return False, "Campaña cancelada por el usuario"

                if pause_event and pause_event.is_set():
                    if not paused_logged:
                        log("⏸️ Campaña en pausa")
                        paused_logged = True
                    while pause_event.is_set():
                        if stop_event and stop_event.is_set():
                            campaign['status'] = 'cancelled'
                            with open(campaign_file, 'w', encoding='utf-8') as f:
                                json.dump(campaign, f, indent=2, ensure_ascii=False)
                            self._close_all_browsers()
                            return False, "Campaña cancelada por el usuario"
                        time.sleep(0.1)
                    log("▶️ Reanudando campaña")
                    paused_logged = False

                profile_name = profile_names[profile_index % len(profile_names)]
                page: Page = self.sessions[profile_name]["page"]

                phone_raw = str(contact.get('Telefono_1', contact.get('Telefono', '')))
                phone = self._normalize_phone(phone_raw)

                if not phone:
                    log(f"⚠️ [{idx}/{len(contacts)}] Contacto sin teléfono válido, saltando...")
                    campaign['failed_messages'] += 1
                    profile_index += 1
                    continue

                message = templates_mgr.apply_template(campaign['template_content'], contact)

                try:
                    log(f"📤 [{idx}/{len(contacts)}] Enviando a {phone} con perfil {profile_name}...")

                    success = self._send_with_retry(page, phone, message, log)

                    if success:
                        log("   ✅ Mensaje enviado exitosamente")
                        campaign['sent_messages'] += 1
                    else:
                        log("   ❌ Error al enviar mensaje")
                        campaign['failed_messages'] += 1

                    if idx < len(contacts):
                        delay_seconds = random.uniform(delay_min, delay_max)
                        delay_seconds = max(0.2, delay_seconds)
                        log(f"   ⏱️ Esperando {delay_seconds:.1f} segundos...")

                        waited = 0.0
                        while waited < delay_seconds:
                            if stop_event and stop_event.is_set():
                                campaign['status'] = 'cancelled'
                                with open(campaign_file, 'w', encoding='utf-8') as f:
                                    json.dump(campaign, f, indent=2, ensure_ascii=False)
                                self._close_all_browsers()
                                return False, "Campaña cancelada por el usuario"

                            if pause_event and pause_event.is_set():
                                if not paused_logged:
                                    log("⏸️ Campaña en pausa")
                                    paused_logged = True
                                while pause_event.is_set():
                                    if stop_event and stop_event.is_set():
                                        campaign['status'] = 'cancelled'
                                        with open(campaign_file, 'w', encoding='utf-8') as f:
                                            json.dump(campaign, f, indent=2, ensure_ascii=False)
                                        self._close_all_browsers()
                                        return False, "Campaña cancelada por el usuario"
                                    time.sleep(0.1)
                                log("▶️ Reanudando campaña")
                                paused_logged = False

                            chunk = min(0.25, delay_seconds - waited)
                            page.wait_for_timeout(chunk * 1000)
                            waited += chunk

                    profile_index += 1

                except Exception as e:
                    log(f"   ❌ Error: {str(e)}")
                    campaign['failed_messages'] += 1
                    profile_index += 1

            campaign['status'] = 'completed'

            with open(campaign_file, 'w', encoding='utf-8') as f:
                json.dump(campaign, f, indent=2, ensure_ascii=False)

            log("-" * 50)
            log("✅ Campaña completada")
            log(f"📊 Enviados: {campaign['sent_messages']}/{campaign['total_messages']}")
            log(f"❌ Fallidos: {campaign['failed_messages']}")

            log("")
            log("🔒 Cerrando navegadores...")
            self._close_all_browsers()

            return True, (
                f"Campaña completada: {campaign['sent_messages']} enviados, "
                f"{campaign['failed_messages']} fallidos"
            )

        except Exception as e:
            self._close_all_browsers()
            return False, f"Error en el envío: {str(e)}"

    def _normalize_phone(self, phone):
        """Limpia el número de teléfono, dejando solo dígitos y un prefijo + opcional."""
        if not phone:
            return ""

        phone = str(phone).strip()
        has_plus = phone.startswith("+")
        digits = re.sub(r"\D", "", phone)

        if not digits:
            return ""

        return f"+{digits}" if has_plus else digits

    def _start_playwright(self, log: Callable[[str], None]) -> None:
        """Inicializa Playwright y muestra un mensaje claro si faltan los navegadores."""

        try:
            self.playwright = sync_playwright().start()
        except PlaywrightError as e:
            log("❌ Playwright no encontró el ejecutable de Chromium necesario para iniciar.")
            log("   Ejecuta este comando y vuelve a intentarlo:")
            log("   👉 playwright install chromium")
            raise RuntimeError(
                "Playwright requiere descargar los navegadores. Ejecuta 'playwright install chromium'."
            ) from e

    def _install_browsers(self, log: Callable[[str], None]) -> None:
        """Descarga los binarios de Playwright cuando faltan."""

        log("⚠️ No se encontró el navegador de Playwright. Descargando Chromium...")
        install_cmd = ["playwright", "install", "chromium"]
        try:
            result = subprocess.run(
                install_cmd,
                capture_output=True,
                text=True,
                check=True,
            )
            if result.stdout:
                log(result.stdout.strip())
            log("✅ Descarga de Chromium completada")
        except FileNotFoundError:
            fallback_cmd = [sys.executable, "-m", "playwright", "install", "chromium"]
            log("⚠️ El comando 'playwright' no está en el PATH. Intentando con Python...")
            try:
                result = subprocess.run(
                    fallback_cmd,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                if result.stdout:
                    log(result.stdout.strip())
                log("✅ Descarga de Chromium completada")
            except subprocess.CalledProcessError as e:
                if e.stdout:
                    log(e.stdout.strip())
                if e.stderr:
                    log(e.stderr.strip())
                log("❌ No se pudo descargar Chromium con Playwright.")
                log("   Asegúrate de instalar Playwright: pip install playwright")
                raise RuntimeError("No se pudo descargar Chromium con Playwright") from e
        except subprocess.CalledProcessError as e:
            if e.stdout:
                log(e.stdout.strip())
            if e.stderr:
                log(e.stderr.strip())
            raise RuntimeError("No se pudo descargar Chromium con Playwright") from e

        # Reiniciar Playwright con los binarios recién instalados
        if self.playwright:
            self.playwright.stop()
            self.playwright = None
        self._start_playwright(log)

    def _open_browser_for_profile(self, profile_name: str, log: Callable[[str], None]) -> Page:
        """
        Abre un contexto persistente de Playwright para el perfil indicado.

        Cada perfil usa su propio directorio de datos para mantener la sesión de Messages
        sin requerir escanear el QR cada vez.
        """

        profile_path = Path("profiles_storage") / profile_name
        profile_path.mkdir(parents=True, exist_ok=True)

        chromium = self.playwright.chromium
        try:
            context: BrowserContext = chromium.launch_persistent_context(
                user_data_dir=str(profile_path),
                headless=False,
                args=["--disable-blink-features=AutomationControlled"],
            )
        except PlaywrightError as e:
            error_message = str(e)
            if "Executable doesn't exist" in error_message or "executable doesn't exist" in error_message:
                self._install_browsers(log)
                context = self.playwright.chromium.launch_persistent_context(
                    user_data_dir=str(profile_path),
                    headless=False,
                    args=["--disable-blink-features=AutomationControlled"],
                )
            else:
                raise

        page: Page = context.pages[0] if context.pages else context.new_page()
        default_timeout_ms = 12000
        page.set_default_timeout(default_timeout_ms)

        startup_timeout_ms = 3000
        wait_strategies = ["domcontentloaded", "load"]
        log(
            "   ⏳ Cargando Messages Web con un tiempo de "
            f"{startup_timeout_ms / 1000:.0f}s..."
        )

        for attempt, wait_until in enumerate(wait_strategies, start=1):
            try:
                page.goto(
                    "https://messages.google.com/web",
                    wait_until=wait_until,
                    timeout=startup_timeout_ms,
                )
                break
            except PlaywrightTimeoutError:
                log(
                    "   ⚠️ El inicio tardó demasiado ("
                    f"intento {attempt}/{len(wait_strategies)} usando wait_until='{wait_until}')."
                )
                if attempt == len(wait_strategies):
                    raise

        self._ensure_messages_home(page)

        return page

    def _ensure_messages_home(self, page: Page) -> None:
        """
        Verifica que la página esté lista para iniciar un nuevo mensaje.

        Usa selectores robustos para ubicar el botón de nueva conversación y deja la pestaña
        preparada para ser usada en la siguiente llamada de envío.
        """

        new_message_selectors = [
            "button[aria-label='Start chat']",
            "button[aria-label='Nuevo mensaje']",
            "button[aria-label*='Nuevo chat']",
            "button[aria-label*='Start chat']",
            "div[role='button'][aria-label*='Nuevo']",
        ]

        for selector in new_message_selectors:
            try:
                page.wait_for_selector(selector, state="visible", timeout=3000)
                return
            except PlaywrightTimeoutError:
                continue

        # Si no se encuentra, intentar abrir directamente la URL de nueva conversación
        page.goto(
            "https://messages.google.com/web/conversations/new",
            wait_until="domcontentloaded",
            timeout=3000,
        )

    def _open_new_conversation(self, page: Page, log: Callable[[str], None]) -> None:
        """Abre rápidamente el flujo de nuevo mensaje sin recargar toda la app."""

        new_message_selectors = [
            "button[aria-label='Start chat']",
            "button[aria-label='Nuevo mensaje']",
            "button[aria-label*='Nuevo chat']",
            "button[aria-label*='Start chat']",
            "div[role='button'][aria-label*='Nuevo']",
        ]

        try:
            self._ensure_messages_home(page)
        except PlaywrightError:
            log("   ⚠️ No se pudo preparar la pantalla, recargando vista de conversación...")
            page.goto(
                "https://messages.google.com/web/conversations/new",
                wait_until="domcontentloaded",
                timeout=3000,
            )
            return

        for selector in new_message_selectors:
            try:
                button = page.locator(selector).first
                if button.is_visible():
                    button.click()
                    return
            except PlaywrightError:
                continue

        page.goto(
            "https://messages.google.com/web/conversations/new",
            wait_until="domcontentloaded",
            timeout=3000,
        )

    def _send_with_retry(self, page: Page, phone: str, message: str, log: Callable[[str], None], attempts: int = 2) -> bool:
        """Intenta enviar un mensaje con reintentos rápidos ante fallos puntuales."""

        for attempt in range(1, attempts + 1):
            if self._send_message_via_browser(page, phone, message, log):
                return True

            log(f"   🔁 Reintentando envío (intento {attempt}/{attempts})...")
            self._ensure_messages_home(page)

        return False

    def _send_message_via_browser(self, page: Page, phone: str, message: str, log: Callable[[str], None]) -> bool:
        """
        Envía un mensaje en Google Messages Web usando Playwright.

        Flujo:
        1. Abrir conversación nueva.
        2. Pegar número y confirmar.
        3. Esperar campo de texto del mensaje.
        4. Escribir y enviar.
        """

        try:
            log("   🔍 Abriendo nueva conversación sin recargar toda la página...")
            self._open_new_conversation(page, log)

            to_field_selectors = [
                "input[aria-label='Type a name, phone number, or email']",
                "input[aria-label='Escribe un nombre, número de teléfono o correo electrónico']",
                "input[placeholder='Type a name, phone number, or email']",
                "input[placeholder='Escribe un nombre, número de teléfono o correo electrónico']",
                "mw-text-input input",
                "input[type='text'][aria-label*='teléfono']",
            ]

            to_field = self._wait_first_visible(page, to_field_selectors, timeout=4500)

            if not to_field:
                log("   ❌ No se encontró el campo 'Para' para pegar el número")
                return False

            log(f"   📝 Ingresando número de teléfono: {phone}")
            to_field.click()
            to_field.fill(phone)
            to_field.press("Enter")

            self._confirm_recipient_selected(page, log)

            log("   🔎 Esperando el campo de mensaje...")
            text_field_selectors = [
                "div[contenteditable='true'][role='textbox']",
                "div[contenteditable='true'][aria-label*='Text']",
                "div[contenteditable='true'][aria-label*='Mensaje']",
                "div[aria-label='Escribe un mensaje']",
                "div[aria-label='Message']",
                "textarea[aria-label='Text message']",
                "textarea[aria-label='Mensaje de texto']",
                "mw-message-compose-editor div[contenteditable='true']",
                "div[aria-label*='mensaje'][contenteditable='true']",
                "textarea[aria-label*='mensaje']",
            ]

            compose_frame = self._find_messages_frame(page, log)

            message_target = None
            for attempt in range(2):
                message_target = self._wait_first_visible(
                    page, text_field_selectors, frame=compose_frame, timeout=4500
                )

                if message_target:
                    break

                log(
                    "   🔄 No se encontró el campo de mensaje; recargando conversación para reintentar..."
                )
                page.goto(
                    "https://messages.google.com/web/conversations/new",
                    wait_until="domcontentloaded",
                )

                to_field = self._wait_first_visible(page, to_field_selectors, timeout=4500)
                if not to_field:
                    log("   ❌ No se pudo localizar el campo de mensaje")
                    return False

                to_field.click()
                to_field.fill(phone)
                to_field.press("Enter")
                self._confirm_recipient_selected(page, log)
                compose_frame = self._find_messages_frame(page, log)

            if not message_target:
                log("   ❌ No se pudo localizar el campo de mensaje")
                return False

            message_target.click()
            message_target.fill(message)

            log("   ⏳ Confirmando envío...")
            try:
                message_target.press("Enter")
                page.wait_for_timeout(300)
                log("   ✅ Mensaje enviado con Enter")
            except PlaywrightError:
                log("   ⚠️ No se pudo usar Enter, probando botón 'Enviar'")
                send_button_selectors = [
                    "button[aria-label='Send message']",
                    "button[aria-label='Enviar mensaje']",
                    "button[aria-label*='Send']",
                    "button[aria-label*='Enviar']",
                    "mw-send-button button",
                ]

                send_button = self._wait_first_visible(
                    page,
                    send_button_selectors,
                    state="enabled",
                    frame=compose_frame,
                    timeout=2500,
                )

                if send_button:
                    send_button.click()
                    log("   ✅ Mensaje enviado con botón")
                else:
                    log("   ❌ No se encontró forma de enviar el mensaje")
                    return False

            page.wait_for_timeout(150)

            return True

        except PlaywrightTimeoutError:
            log("   ❌ Timeout esperando elementos en la página")
            return False
        except PlaywrightError as e:
            log(f"   ❌ Error de Playwright: {str(e)}")
            return False
        except Exception as e:  # Resguardo final ante cualquier otro fallo
            log(f"   ❌ Error enviando mensaje: {str(e)}")
            return False

    def _wait_first_visible(
        self,
        page: Page,
        selectors,
        state: str = "visible",
        timeout: int = 3000,
        frame: Optional[Frame] = None,
    ) -> Optional[object]:
        """
        Devuelve el primer locator disponible entre varios selectores.

        Esto mejora la compatibilidad con cambios menores de la UI, evitando fallos por
        pequeños ajustes en atributos de accesibilidad o idioma.
        """

        context = frame if frame else page

        total_timeout = max(0, timeout)
        per_selector_timeout = total_timeout / max(len(selectors), 1)
        started_at = monotonic()

        for selector in selectors:
            elapsed = (monotonic() - started_at) * 1000
            remaining = total_timeout - elapsed

            if remaining <= 0:
                break

            locator = context.locator(selector)
            try:
                locator.wait_for(
                    state=state,
                    timeout=min(per_selector_timeout, remaining),
                )
                return locator
            except PlaywrightTimeoutError:
                continue

        return None

    def _confirm_recipient_selected(self, page: Page, log: Callable[[str], None]) -> bool:
        """Intenta asegurar que el número pegado quede seleccionado."""

        chip_selectors = [
            "div[role='list'] mw-contact-chips",
            "div[role='listitem'][data-view-type='chips']",
            "div[aria-label*='Destinatario'] mw-contact-chip",
            "div[aria-label*='Recipient'] mw-contact-chip",
        ]

        for selector in chip_selectors:
            try:
                page.locator(selector).wait_for(state="visible", timeout=1200)
                log("   ✅ Número de destinatario listo")
                return True
            except PlaywrightTimeoutError:
                continue

        suggestion_selectors = [
            "ul[role='listbox'] li[role='option']",
            "div[role='listbox'] div[role='option']",
            "div[role='option'][data-entityid]",
        ]

        for selector in suggestion_selectors:
            options = page.locator(selector)
            try:
                options.first.wait_for(state="visible", timeout=1200)
                options.first.click()
                log("   ✅ Seleccionando número desde sugerencias")
                return True
            except PlaywrightTimeoutError:
                continue
            except PlaywrightError:
                continue

        try:
            page.keyboard.press("Enter")
            log("   ↩️ Confirmando número con Enter adicional")
        except PlaywrightError:
            return False

        return False

    def _find_messages_frame(
        self, page: Page, log: Callable[[str], None]
    ) -> Optional[Frame]:
        """Localiza el iframe de composición si existe."""

        iframe_selectors = [
            "iframe[title*='Messages']",
            "iframe[title*='Mensajes']",
            "iframe[src*='messages.google.com/web']",
        ]

        for selector in iframe_selectors:
            handles = page.locator(selector).element_handles()
            for handle in handles:
                try:
                    frame = handle.content_frame()
                    if frame:
                        log("   🧭 Usando iframe de composición detectado")
                        return frame
                except PlaywrightError:
                    continue

        for frame in page.frames:
            if (
                frame.url and "messages.google.com/web" in frame.url
            ) or (frame.name and "Messages" in frame.name):
                log("   🧭 Usando frame relacionado con Messages")
                return frame

        return None

    def _close_all_browsers(self):
        """Cierra todos los contextos de navegador abiertos y detiene Playwright."""
        for profile_name, session in self.sessions.items():
            context: BrowserContext = session.get("page").context  # type: ignore
            try:
                context.close()
            except Exception:
                pass

        self.sessions.clear()

        if self.playwright:
            try:
                self.playwright.stop()
            except Exception:
                pass
            self.playwright = None
