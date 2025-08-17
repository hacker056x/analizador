from flask import Flask, request, render_template, send_file, Response
import os
import ast
import uuid
from io import StringIO

app = Flask(__name__)

# Lista parcial de módulos estándar de Python (basada en Python 3.11+)
STANDARD_MODULES = {
    'sys', 'os', 'platform', 're', 'logging', 'urllib', 'argparse', 'datetime', 'time',
    'math', 'random', 'json', 'csv', 'collections', 'itertools', 'functools', 'threading'
}

def get_install_instructions(module):
    """
    Devuelve la instrucción de instalación para un módulo.
    """
    if module.lower() in STANDARD_MODULES:
        return f"{module}: Módulo estándar de Python, incluido con la instalación de Python."
    else:
        return f"{module}: Instalar con 'pip install {module}'."

def get_imported_modules(file_content):
    """
    Analiza un script Python y devuelve una lista de módulos importados.
    """
    try:
        tree = ast.parse(file_content)
        modules = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    modules.add(name.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    modules.add(node.module.split('.')[0])
        return sorted(list(modules))
    except SyntaxError:
        return []
    except Exception:
        return []

@app.route('/', methods=['GET', 'POST'])
def index():
    modules = []
    error = None
    output_filename = None

    if request.method == 'POST':
        if 'file' not in request.files:
            error = "No se seleccionó ningún archivo."
        else:
            file = request.files['file']
            if file.filename == '':
                error = "No se seleccionó ningún archivo."
            elif not file.filename.endswith('.py'):
                error = "Por favor, selecciona un archivo Python (.py)."
            else:
                # Leer el contenido del archivo
                file_content = file.read().decode('utf-8')
                modules = get_imported_modules(file_content)
                if not modules:
                    error = "No se encontraron módulos importados o el archivo contiene errores de sintaxis."
                else:
                    # Guardar resultados temporalmente para descarga
                    output_filename = f"modules_{uuid.uuid4().hex}.txt"
                    with open(os.path.join('static', output_filename), 'w', encoding='utf-8') as f:
                        f.write("Módulos importados encontrados:\n")
                        for module in modules:
                            f.write(f"- {get_install_instructions(module)}\n")

    return render_template('index.html', modules=modules, error=error, output_filename=output_filename)

@app.route('/download/<filename>')
def download_file(filename):
    try:
        file_path = os.path.join('static', filename)
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        # Eliminar el archivo después de leerlo
        os.remove(file_path)
        return Response(
            content,
            mimetype='text/plain',
            headers={'Content-Disposition': f'attachment; filename={os.path.splitext(filename)[0]}_modules.txt'}
        )
    except FileNotFoundError:
        return "Archivo no encontrado.", 404

if __name__ == '__main__':
    # Crear directorio static si no existe
    os.makedirs('static', exist_ok=True)
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))