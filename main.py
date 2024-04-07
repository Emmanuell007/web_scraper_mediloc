from flask import Flask, request, jsonify
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import re

app = Flask(__name__)

@app.route('/')
def root():
    return "huevos al furro"

def encontrar_cantidad(cadena):
    patron = r"(\d+)\s*(Tableta|Cápsula|Pastilla)s?"
    coincidencias = re.search(patron, cadena, re.IGNORECASE)
    if coincidencias:
        cantidad = int(coincidencias.group(1))
        palabra = coincidencias.group(2)
        return cantidad, palabra
    else:
        return 0, None

@app.route('/scrape', methods=['POST'])
def scrape_productos():
    search_term = request.json.get('medicamentos', '')
    
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_argument("--log-level=3") 
    driver = webdriver.Chrome(service=service, options=options)
    
    medicamentos_lista = search_term.split("\n")
    
    medicamento = {
        "Medicamentos": []
    }

    for product in medicamentos_lista:
        nombre = product.split(" ")
        medicamento_actual = {
            "Nombre": nombre[0],
            "Presentaciones": []
        }
        
        url = f"https://www.farmaciasanpablo.com.mx/search/?query={product}"
        driver.get(url)
        
        try:
            wait = WebDriverWait(driver, 10)
            wait.until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR, ".nameProduct")))
        except TimeoutException:
            pass
        
        results = driver.find_elements(By.CSS_SELECTOR, ".nameProduct")
        num_results = len(results)
        
        if num_results != 0:
            num_products = min(num_results, 3)
            
            for i in range(num_products):
                product_name = results[i].text
                product_desc = driver.find_elements(By.CSS_SELECTOR, ".custom-postop")[i].text
                product_cost = driver.find_elements(By.CSS_SELECTOR, ".price p")[i].text

                precio_num = "".join(c for c in product_cost if c.isdigit() or c == '.')
                precio_num = float(precio_num)

                cant1, tip1 = encontrar_cantidad(product_desc)
                cant2, tip2 = encontrar_cantidad(product_name)

                if cant1 != 0:
                    cantidad = f"{cant1} {tip1}s"
                    medicamento_actual["Presentaciones"].append({
                        "Precio": precio_num,
                        "Farmacia": "San Pablo",
                        "Cantidad": cantidad
                    })
                elif cant2 != 0:
                    cantidad = f"{cant2} {tip2}s"
                    medicamento_actual["Presentaciones"].append({
                        "Precio": precio_num,
                        "Farmacia": "San Pablo",
                        "Cantidad": cantidad
                    })
                else:
                    medicamento_actual["Presentaciones"].append({
                        "Precio": precio_num,
                        "Farmacia": "San Pablo",
                        "Cantidad": "No disponible"
                    })
        
        else:
            medicamento_actual["Presentaciones"].append({
                "Precio": 0,
                "Farmacia": "No disponible",
                "Cantidad": "No disponible"
            })
        
        medicamento["Medicamentos"].append(medicamento_actual)

    driver.quit()
    
    return jsonify(medicamento)

if __name__ == '__main__':
    app.run()
