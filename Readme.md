## 🚀 Guía rápida de uso

### 1. Crear y editar conjuntos
* **Crear conjunto**: Haz clic en el botón **`+ Add Set`** en la barra superior.
* **Configuración**: Define el nombre visible y añade sus elementos separados por comas (por ejemplo: `1, 2, 3, 4`).
* **Editar o borrar**: Haz clic directamente sobre el **título de cualquier conjunto** dentro del lienzo para modificar sus datos, cambiar su color o eliminarlo junto a sus relaciones.

### 2. Poner y quitar flechas
* **Flechas entre elementos**: Haz clic en el **nodo de origen** y luego en el **nodo de destino**.
  * Si la flecha no existe, se **creará**.
  * Si la flecha ya existe, se **eliminará** (comportamiento *toggle*).
* **Flechas bidireccionales**: Si dos elementos se apuntan mutuamente, las flechas se curvan automáticamente en sentidos opuestos para diferenciarse y no solaparse.
* **Auto-apuntado (Bucles)**: Haz clic **dos veces sobre el mismo nodo** para crear una flecha circular de auto-relación.

### 3. Añadir título al diagrama
* Escribe la notación matemática en el campo **`Title:`** de la barra superior.
* Puedes añadir nombres formales o relaciones como:
  * `G ⊆ A × B`
  * `f: A → B`
  * `R = {(1, a), (2, b)}`
* **Comportamiento**: Se actualiza en tiempo real en la parte superior. Si dejas el campo vacío, el espacio se ajustará automáticamente sin mostrar ningún título en la imagen exportada.

### 4. Guardar y exportar
* **`💾 Save`**: Guarda el diagrama en un archivo `.json`.
* **`📂 Open`**: Carga un diagrama `.json` guardado previamente para continuar editándolo.
* **`🖼️ PNG`**: Exporta el diagrama directamente a una imagen.

---

## 💻 Requisitos e Instalación

Asegúrate de tener instalado Python 3.8+ y las siguientes librerías:

```bash
pip install matplotlib numpy

Ejecucion

```bash
python3 gui_sagital.py