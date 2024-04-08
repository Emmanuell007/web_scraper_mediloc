from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

def encontrar_cantidad(cadena):
    patron = r"(\d+)\s*(Tableta|Cápsula|Pastilla|ml)s?"
    coincidencias = re.search(patron, cadena, re.IGNORECASE)
    
    if coincidencias:
        cantidad = int(coincidencias.group(1))
        palabra = coincidencias.group(2)
        
        return cantidad, palabra
    else:
        return 0, None

@app.route('/scrape', methods=['POST'])
def scrape_productos():
    medicamento = {
        "Medicamentos": []
    }
    search_term = request.json.get('medicamentos', '')
    medicamentos_lista = search_term.split("\n")

    for product in medicamentos_lista:
        nombre = product.split(" ")
        if nombre[0].strip() == "":
            titulo = nombre[1]
        else:
            titulo = nombre[0]
        medicamento_actual = {
            "Nombre": titulo,
            "Presentaciones": []
        }
        
        url = f"https://farmaciasgi.com.mx/?s={product}&post_type=product&dgwt_wcas=1"
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        #woocommerce-Price-amount
        results = soup.select("h2.woocommerce-loop-product__title")
        num_results = len(results)
        
        if num_results != 0:
            num_products = min(num_results, 3)
            
            for i in range(num_products):
                product_name = results[i].get_text(strip=True)
                product_price_elements = soup.select("span.woocommerce-Price-amount")
                precio_num = product_price_elements[i].text

                product_cost = "".join(c for c in precio_num if c.isdigit() or c == '.')
                product_cost = float(product_cost)
                cant2, tip2 = encontrar_cantidad(product_name)

                if cant2 != 0:
                    if tip2 !="ml":
                        cantidad = f"{cant2} {tip2}s"
                        medicamento_actual["Presentaciones"].append({
                            "Precio": product_cost,
                            "Farmacia": "Gi",
                            "Cantidad": cantidad
                        })
                    else:
                        cantidad = f"{cant2} {tip2}"
                        medicamento_actual["Presentaciones"].append({
                            "Precio": product_cost,
                            "Farmacia": "Gi",
                            "Cantidad": cantidad
                        })
                else:
                    medicamento_actual["Presentaciones"].append({
                        "Precio": product_cost,
                        "Farmacia": "Gi",
                        "Cantidad": "No disponible"
                    })
        else:
            medicamento_actual["Presentaciones"].append({
                "Precio": 0,
                "Farmacia": "No disponible",
                "Cantidad": "No disponible"
            })
        
        medicamento["Medicamentos"].append(medicamento_actual)

    return jsonify(medicamento)
    
if __name__ == '__main__':
    app.run()


