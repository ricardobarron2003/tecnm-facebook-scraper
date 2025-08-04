from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import hashlib
import re
import os

def crear_hash(texto):
    """Crea un hash MD5 único para el texto"""
    texto_limpio = re.sub(r'\s+', ' ', texto).strip()
    return hashlib.md5(texto_limpio.encode('utf-8')).hexdigest()

def iniciar_navegador():
    """Configura e inicia el navegador Chrome"""
    service = Service(r'C:/Users/richi/Downloads/chromedriver.exe')
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--start-maximized")
    return webdriver.Chrome(service=service, options=options)

def cerrar_popups(driver):
    """Función para cerrar popups emergentes"""
    popup_selectors = [
        "//div[@aria-label='Cerrar' and @role='button']",
        "//div[contains(@aria-label, 'Cerrar')]",
        "//div[text()='Cerrar']",
        "//div[@role='button' and .//*[local-name()='svg']",
        "//div[@aria-label='Cancelar']",
        "//div[@aria-label='No ahora']",
    ]
    
    for selector in popup_selectors:
        try:
            element = WebDriverWait(driver, 2).until(
                EC.element_to_be_clickable((By.XPATH, selector)))
            element.click()
            print(f"✅ Popup cerrado: {selector[:30]}...")
            time.sleep(0.5)
            return True
        except:
            continue
    return False

def manejar_popup_login(driver, user, password):
    """Maneja el popup de 'Ver más en Facebook'"""
    try:
        popup = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, 
                "//div[@role='dialog' and contains(.//text(), 'Ver más en Facebook')]"))
        )
        print("⚠️ Popup de login detectado. Intentando iniciar sesión...")
        
        # Esperar a que los campos sean interactuables
        email_input = WebDriverWait(popup, 5).until(
            EC.element_to_be_clickable((By.XPATH, ".//input[@name='email']")))
        email_input.clear()
        email_input.send_keys(user)
        
        password_input = WebDriverWait(popup, 5).until(
            EC.element_to_be_clickable((By.XPATH, ".//input[@name='pass']")))
        password_input.clear()
        password_input.send_keys(password)
        
        login_button = WebDriverWait(popup, 5).until(
            EC.element_to_be_clickable((By.XPATH, ".//div[@aria-label='Iniciar sesión'] | .//button[@name='login']")))
        login_button.click()
        print("✅ Credenciales ingresadas en el popup.")
        
        # Esperar a que el popup desaparezca
        WebDriverWait(driver, 10).until(
            EC.invisibility_of_element_located((By.XPATH, "//div[@role='dialog' and contains(.//text(), 'Ver más en Facebook')]")))
        
        return True
    except Exception as e:
        print(f"❌ Error en popup de login: {str(e)}")
        return False

def esperar_carga_completa(driver, tiempo_espera=5):
    """Espera a que la página termine de cargar"""
    try:
        WebDriverWait(driver, tiempo_espera).until(
            lambda d: d.execute_script("return document.readyState") == "complete")
    except:
        pass

def preparar_pagina(driver, user, password):
    """Prepara la página cerrando popups y haciendo scroll controlado"""
    print("🛠️ Preparando página...")
    
    # Esperar a que la página cargue completamente
    esperar_carga_completa(driver, 10)
    
    # Cerrar popups iniciales
    for _ in range(5):  # Más intentos para asegurar
        if cerrar_popups(driver) or manejar_popup_login(driver, user, password):
            break
        time.sleep(1)
    
    # Hacer scroll controlado para cargar contenido
    print("🔄 Realizando scroll controlado...")
    last_height = driver.execute_script("return document.body.scrollHeight")
    scroll_attempts = 0
    max_scroll_attempts = 3  # Máximo de 3 intentos de scroll
    
    while scroll_attempts < max_scroll_attempts:
        # Scroll suave en incrementos de 500px
        scroll_increment = 500
        current_pos = 0
        while current_pos < last_height:
            driver.execute_script(f"window.scrollTo(0, {current_pos});")
            current_pos += scroll_increment
            time.sleep(0.3)
        
        # Esperar a que cargue nuevo contenido
        time.sleep(2)
        
        # Cerrar posibles popups
        cerrar_popups(driver)
        
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            scroll_attempts += 1
            print(f"🔄 Intento de scroll {scroll_attempts}/{max_scroll_attempts}")
            time.sleep(1)
        else:
            scroll_attempts = 0  # Reiniciar contador si hubo cambio
            
        last_height = new_height
    
    print("✅ Página preparada")

def extraer_texto_unico(elemento):
    """Extrae texto único de una publicación evitando duplicados"""
    try:
        # Selector mejorado para evitar duplicados
        texto_elementos = elemento.find_elements(
            By.XPATH, ".//div[@dir='auto' and not(ancestor::div[contains(@class, 'x1n2onr6')])] | " +
                     ".//div[contains(@data-ad-preview, 'message')]//div[@dir='auto'] | " +
                     ".//div[contains(@class, 'x1iorvi4') and @dir='auto']")
        
        textos = []
        for elem in texto_elementos:
            texto = elem.text.strip()
            if texto and "Ver más" not in texto and texto not in textos:
                textos.append(texto)
        
        return "\n".join(textos) if textos else None
        
    except Exception as e:
        print(f"⚠️ Error extrayendo texto: {str(e)}")
        return None

def extraer_publicaciones(driver, max_publicaciones=10, timeout=60):
    """Extrae las publicaciones principales con timeout mejorado"""
    publicaciones = []
    hashes_vistos = set()
    start_time = time.time()
    
    print(f"\n🔍 Extrayendo hasta {max_publicaciones} publicaciones principales (timeout: {timeout}s)...")
    
    # Localizar publicaciones principales con selector mejorado
    publicaciones_locator = (By.XPATH, 
        "(//div[@role='article' and contains(@class, 'x1yztbdb') and not(contains(@class, 'x1n2onr6'))]) | " +
        "(//div[contains(@class, 'x1yztbdb') and .//div[contains(@class, 'x1iorvi4')]])")
    
    try:
        # Esperar a que haya al menos 3 publicaciones cargadas
        WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.XPATH, publicaciones_locator[1] + "[position() <= 3]")))
        
        # Obtener las publicaciones visibles
        elementos = driver.find_elements(*publicaciones_locator)
    except TimeoutException:
        print("❌ No se encontraron publicaciones principales después de esperar")
        return publicaciones
    
    elementos = elementos[:max_publicaciones]
    
    for i, elemento in enumerate(elementos, 1):
        # Verificar timeout
        if time.time() - start_time > timeout:
            print(f"⏰ Timeout alcanzado ({timeout}s). Terminando extracción...")
            break
        
        try:
            # Desplazar suavemente a la publicación
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", elemento)
            time.sleep(0.7)  # Tiempo suficiente para cargar
            
            # Intentar expandir "Ver más"
            try:
                boton_ver_mas = WebDriverWait(elemento, 2).until(
                    EC.element_to_be_clickable((By.XPATH, 
                        ".//div[contains(text(), 'Ver más') and @role='button']")))
                driver.execute_script("arguments[0].click();", boton_ver_mas)
                print(f"  ✅ Texto expandido para publicación {i}")
                time.sleep(0.5)
            except:
                pass
            
            # Extraer texto único
            texto = extraer_texto_unico(elemento)
            
            if texto:
                texto_hash = crear_hash(texto)
                if texto_hash not in hashes_vistos:
                    publicaciones.append(texto)
                    hashes_vistos.add(texto_hash)
                    print(f"  📝 Publicación {i} capturada ({len(texto)} caracteres)")
                else:
                    print(f"  ⚠️ Publicación {i} duplicada, omitiendo")
            else:
                print(f"  ⚠️ Publicación {i} sin texto capturable")
            
        except Exception as e:
            print(f"  ❌ Error procesando publicación {i}: {str(e)}")
            continue
    
    return publicaciones

def guardar_publicaciones(publicaciones, archivo="publicaciones_tec.txt"):
    """Guarda las publicaciones en un archivo de texto, evitando duplicados"""
    # Leer publicaciones existentes si el archivo existe
    publicaciones_existentes = set()
    if os.path.exists(archivo):
        with open(archivo, 'r', encoding='utf-8') as f:
            publicaciones_existentes = set(line.strip() for line in f if line.strip())
    
    # Filtrar publicaciones nuevas
    publicaciones_nuevas = [p for p in publicaciones if crear_hash(p) not in 
                          {crear_hash(existente) for existente in publicaciones_existentes}]
    
    if not publicaciones_nuevas:
        print("\nℹ️ No hay publicaciones nuevas para guardar.")
        return False
    
    # Guardar las publicaciones nuevas
    with open(archivo, 'a', encoding='utf-8') as f:
        for pub in publicaciones_nuevas:
            # Normalizar saltos de línea y espacios
            pub_limpia = ' '.join(pub.split()).replace('\n', ' ')
            f.write(pub_limpia + '\n')
    
    print(f"\n💾 Se guardaron {len(publicaciones_nuevas)} publicaciones nuevas en {archivo}")
    return True

def ejecutar_scraping(user, password, max_publicaciones=10):
    """Función principal que ejecuta todo el proceso de scraping"""
    driver = None
    try:
        driver = iniciar_navegador()
        print("🚀 Iniciando proceso de extracción de publicaciones...")

        # 1. Iniciar sesión en Facebook
        print("🔐 Iniciando sesión en Facebook...")
        driver.get("https://www.facebook.com/login/")
        
        # Esperar y llenar formulario de login principal
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.NAME, "email")))
        driver.find_element(By.NAME, "email").clear()
        driver.find_element(By.NAME, "email").send_keys(user)
        driver.find_element(By.NAME, "pass").clear()
        driver.find_element(By.NAME, "pass").send_keys(password)
        driver.find_element(By.NAME, "login").click()
        
        # Esperar a que el login se complete
        time.sleep(5)
        esperar_carga_completa(driver, 10)

        # 2. Navegar a la página objetivo
        print("🌐 Navegando a la página del TecNM León...")
        driver.get("https://www.facebook.com/TecNMLeon/")
        
        # Esperar a que la página cargue completamente
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//body")))
        time.sleep(3)
        esperar_carga_completa(driver, 10)

        # 3. Preparar la página (manejar popups y hacer scroll)
        preparar_pagina(driver, user, password)
        
        # 4. Extraer publicaciones principales con timeout generoso
        publicaciones = extraer_publicaciones(driver, max_publicaciones, 60)

        # Mostrar resultados en consola
        print("\n" + "="*80)
        print(f"📰 {len(publicaciones)} PUBLICACIONES PRINCIPALES DEL TECNM LEÓN")
        print("="*80)

        for i, texto in enumerate(publicaciones, 1):
            print(f"\n📌 Publicación {i}:\n{texto}\n")
            print("-"*80)
        
        # 5. Guardar publicaciones en archivo
        guardado_exitoso = guardar_publicaciones(publicaciones)
        
        return publicaciones if guardado_exitoso else []

    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO: {str(e)}")
        return []
    finally:
        if driver:
            driver.quit()
            print("\n✅ Proceso completado!")

if __name__ == "__main__":
    # Credenciales (deberías considerar usar variables de entorno para mayor seguridad)
    FACEBOOK_USER = "4772304137"
    FACEBOOK_PASSWORD = "pinto23"
    
    # Ejecutar el scraping
    ejecutar_scraping(FACEBOOK_USER, FACEBOOK_PASSWORD)