# Detector de Duplicados de Imágenes y Videos

Una aplicación web para detectar y eliminar imágenes y videos duplicados o similares en tu sistema de archivos local. Utiliza hashing perceptual para encontrar contenido visualmente similar, no solo archivos idénticos.

## Características

- 🔍 **Escaneo Recursivo**: Escanea carpetas y todas las subcarpetas
- 🎯 **Hashing Perceptual**: Encuentra imágenes similares, no solo idénticas
- 🎬 **Soporte de Videos**: Extrae frames representativos de videos para comparación
- 💾 **Caché Inteligente**: Base de datos SQLite almacena resultados para evitar reprocesamiento
- 🎚️ **Umbral Configurable**: Ajusta la sensibilidad de detección de similitud
- 🖼️ **Comparación Lado a Lado**: Interfaz visual para comparar y elegir qué archivo conservar
- 🔒 **Seguridad**: Previene eliminación accidental fuera del directorio escaneado
- 📊 **Estadísticas**: Visualiza totales y ahorro potencial de espacio

## Formatos Soportados

**Imágenes**: `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.webp`, `.tiff`
**Videos**: `.mp4`, `.avi`, `.mov`, `.mkv`, `.webm`, `.flv`, `.wmv`

## Arquitectura

### Backend (Python + FastAPI)
- **FastAPI**: Servidor de API REST
- **Pillow**: Procesamiento de imágenes
- **imagehash**: Hashing perceptual (pHash, dHash, aHash)
- **OpenCV**: Extracción de frames de video
- **SQLite**: Caché de resultados
- **aiosqlite**: Operaciones asíncronas de base de datos

### Frontend (React + Vite)
- **React 19**: Framework de interfaz de usuario
- **Vite**: Herramienta de compilación y servidor de desarrollo
- **Tailwind CSS**: Estilos
- **Axios**: Comunicación con API

## Instalación

### Requisitos Previos

- Python 3.8 o superior
- Node.js 16 o superior
- npm o yarn

### Configuración del Backend

1. Navega al directorio backend:
```bash
cd backend
```

2. Crea un entorno virtual (recomendado):
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. Instala las dependencias de Python:
```bash
pip install -r requirements.txt
```

### Configuración del Frontend

1. Instala las dependencias de Node.js (desde la raíz del proyecto):
```bash
npm install
```

## Uso

### 1. Iniciar el Servidor Backend

Desde el directorio `backend`:

```bash
python main.py
```

La API estará disponible en `http://localhost:8000`

Puedes verificar que está funcionando visitando `http://localhost:8000` en tu navegador.

### 2. Iniciar el Servidor de Desarrollo Frontend

Desde la raíz del proyecto:

```bash
npm run dev
```

La interfaz web se abrirá en `http://localhost:5173`

### 3. Usando la Aplicación

1. **Ingresar Ruta de Carpeta**: Ingresa la ruta completa de la carpeta que deseas escanear
   - Ejemplo (Windows): `C:\Users\TuNombre\Imágenes`
   - Ejemplo (Linux/Mac): `/home/tunombre/Imágenes`

2. **Ajustar Umbral de Similitud** (opcional):
   - `0` = Solo archivos idénticos
   - `5` = Muy similares (predeterminado, recomendado)
   - `10` = Algo similares
   - `15` = Similitud flexible

3. **Clic en "Iniciar Escaneo"**: La aplicación:
   - Escaneará recursivamente todos los archivos
   - Extraerá metadatos y calculará hashes perceptuales
   - Almacenará resultados en caché en base de datos SQLite

4. **Revisar Resultados**:
   - Ver pares de duplicados lado a lado
   - Ver detalles de archivos (tamaño, dimensiones, fechas)
   - Porcentaje de similitud para cada par

5. **Eliminar Archivos**:
   - Clic en "Eliminar Este Archivo" bajo el archivo que deseas eliminar
   - Confirmar la eliminación
   - El archivo se elimina permanentemente del disco

## Endpoints de la API

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Información de la API |
| POST | `/api/scan` | Iniciar escaneo de directorio |
| GET | `/api/scan/status` | Obtener progreso del escaneo |
| GET | `/api/duplicates?threshold=5` | Obtener pares de duplicados |
| POST | `/api/delete` | Eliminar un archivo |
| GET | `/api/stats` | Obtener estadísticas de la base de datos |
| GET | `/api/preview?file_path=<ruta>` | Servir archivo para vista previa (imágenes/videos) |
| DELETE | `/api/cache` | Limpiar caché (reiniciar) |

## Configuración

### Configuración del Backend

Edita `backend/config.py` para personalizar:

- Extensiones de archivo soportadas
- Tamaño máximo de archivo
- Parámetros del algoritmo de hash
- Umbrales de similitud
- Posición de extracción de frame de video

### Configuración del Frontend

Edita `src/components/Scanner.jsx` para cambiar:

- URL de la API (si no es localhost)
- Valor de umbral predeterminado

## Cómo Funciona

### Algoritmo de Hashing Perceptual (pHash)

A diferencia del hashing tradicional MD5/SHA que solo detecta archivos **idénticos** byte por byte, el hashing perceptual crea una "huella digital" del **contenido visual**, permitiendo la detección de imágenes similares incluso con diferentes resoluciones, formatos o modificaciones leves.

#### Para Imágenes (Implementación en `backend/scanner.py:88-106`):

1. **Preprocesamiento**:
   - Redimensiona la imagen a 8x8 píxeles (configurable vía `HASH_SIZE` en config)
   - Convierte a escala de grises para eliminar variaciones de color
   - Esto reduce la imagen a su estructura visual esencial

2. **DCT (Transformada Discreta del Coseno)**:
   - Aplica transformación en el dominio de frecuencia
   - Separa la imagen en componentes de alta frecuencia (detalles, ruido) y baja frecuencia (estructura, formas)
   - Se enfoca en componentes de baja frecuencia que representan el contenido perceptual
   - Por esto el algoritmo detecta imágenes similares a pesar de compresión o ediciones menores

3. **Generación del Hash**:
   - Calcula la mediana de todos los coeficientes DCT
   - Genera un hash binario de 64 bits:
     - Bit = `1` si coeficiente > mediana
     - Bit = `0` si coeficiente ≤ mediana
   - Resultado: Una huella compacta como `a8f3c2d1b4e7f9a2` (hexadecimal)

4. **Ejemplo**:
   ```
   Imagen Original (1920x1080 JPG) → Hash: 1010101010101010...
   Misma Imagen (640x480 PNG)      → Hash: 1010111010101010...
   Imagen Diferente                → Hash: 0101011101010101...
   ```

#### Para Videos (Implementación en `backend/scanner.py:140-165`):

1. Abre el archivo de video usando OpenCV (`cv2.VideoCapture`)
2. Extrae **un frame al 50% de duración** (`VIDEO_FRAME_POSITION = 0.5`)
   - Usa el frame del medio como muestra representativa
   - Configurable en `backend/config.py`
3. Convierte el frame a imagen PIL
4. Aplica el **mismo algoritmo pHash** que para imágenes
5. Compara videos basándose en este único frame representativo

### Detección de Similitud (Implementación en `backend/comparator.py:14-28`)

#### Cálculo de Distancia de Hamming:

El algoritmo compara dos hashes usando la **distancia de Hamming**: el conteo de bits diferentes.

```python
# Ejemplo de comparación
hash1 = "1010101010101010..."  # 64 bits
hash2 = "1010111010101010..."  # 64 bits

# Operación XOR revela diferencias
difference = hash1 XOR hash2
# Resultado: 0000010000000000... (solo el bit 5 difiere)

hamming_distance = count_ones(difference)  # = 1
```

#### Interpretación del Umbral:

| Umbral | Significado | Caso de Uso |
|--------|-------------|-------------|
| **0** | Idéntico | Solo coincidencias píxel a píxel |
| **1-3** | Casi idéntico | Compresión/redimensión menor |
| **5** (predeterminado) | Muy similar | Misma foto, diferente calidad |
| **8-10** | Similar | Misma escena, diferente ángulo/recorte |
| **12-15** | Similitud flexible | Composición/sujeto similar |

#### Complejidad de Comparación:

- **Algoritmo**: Comparación por pares O(n²)
- **Para 1,000 archivos**: ~500,000 comparaciones
- **Optimización**: Cada comparación es solo XOR de enteros de 64 bits (extremadamente rápido)
- **Rendimiento**: 10,000 archivos ≈ 50M comparaciones ≈ pocos segundos

### Por Qué Funciona

✅ **Detecta similitud a través de**:
- Diferentes resoluciones (4K vs HD vs miniatura)
- Diferentes formatos (JPG vs PNG vs WebP)
- Artefactos de compresión (JPG alta calidad vs baja calidad)
- Ajustes menores de color/brillo
- Recortes pequeños o bordes

❌ **No puede detectar**:
- **Rotaciones** (giros de 90°, 180°, 270°)
- **Volteos** (espejo horizontal/vertical)
- **Recortes significativos** (>30% de la imagen removida)
- **Cambios de perspectiva** (diferentes ángulos de cámara)
- **Cambios de contenido** (agregar/quitar objetos)

### Estrategia de Caché (Implementación en `backend/database.py`)

Para evitar reprocesamiento:
1. Después de calcular un hash, lo almacena en SQLite con metadatos del archivo
2. Antes de recalcular, verifica si cambió el timestamp `modified_at` del archivo
3. Si no cambió, reutiliza el hash en caché (**~1000x más rápido**)
4. El esquema de base de datos incluye columnas `hash` y `path` indexadas

### Librerías Utilizadas

- **`imagehash`** (Python): Implementación de pHash lista para producción
- **`Pillow`** (PIL): Entrada/salida y preprocesamiento de imágenes
- **`OpenCV`** (cv2): Extracción de frames de video
- **`numpy`**: Cálculo de DCT y operaciones numéricas

### Referencias de Código

- **Cálculo de hash**: `backend/scanner.py:88-106` (imágenes), `140-165` (videos)
- **Lógica de comparación**: `backend/comparator.py:14-28` (distancia de Hamming)
- **Caché de base de datos**: `backend/database.py:59-68` (búsqueda en caché)
- **Configuración**: `backend/config.py` (umbrales, tamaño de hash, posición de frame)

## Características de Seguridad

- **Validación de Rutas**: Solo permite eliminación dentro del directorio escaneado
- **Confirmación**: Requiere confirmación del usuario antes de eliminar
- **Sin Acceso a Red**: Todas las operaciones son 100% locales
- **Escaneo de Solo Lectura**: El escaneo no modifica archivos

## Solución de Problemas

### El backend no inicia

**Problema**: `ModuleNotFoundError`
**Solución**: Asegúrate de haber activado el entorno virtual e instalado las dependencias

**Problema**: `Permission denied`
**Solución**: Ejecuta con los permisos apropiados o escanea una carpeta de tu propiedad

### El frontend no puede conectarse al backend

**Problema**: Errores de `Network Error` o CORS
**Solución**: Asegúrate de que el backend esté corriendo en el puerto 8000 y el frontend en el 5173

### Las imágenes o videos no se muestran

**Problema**: Los archivos no aparecen en la vista previa
**Solución**: Asegúrate de que el archivo exista en la base de datos (fue parte de un escaneo). El endpoint `/api/preview` solo sirve archivos escaneados por seguridad.

### El escaneo tarda demasiado

**Problema**: Carpetas grandes con muchos archivos
**Solución**:
- Usa el caché de SQLite (escaneos subsiguientes son más rápidos)
- Aumenta `MAX_FILE_SIZE_MB` para omitir archivos grandes
- Escanea subdirectorios más pequeños

## Desarrollo

### Estructura del Proyecto

```
.
├── backend/
│   ├── main.py              # Aplicación FastAPI
│   ├── scanner.py           # Lógica de escaneo de archivos
│   ├── comparator.py        # Comparación de imágenes
│   ├── database.py          # Operaciones SQLite
│   ├── models.py            # Modelos Pydantic
│   ├── config.py            # Configuración
│   └── requirements.txt     # Dependencias de Python
├── src/
│   ├── components/
│   │   ├── Scanner.jsx      # Inicio de escaneo
│   │   ├── Progress.jsx     # Seguimiento de progreso
│   │   ├── ImagePair.jsx    # Vista de comparación de pares
│   │   ├── FileInfo.jsx     # Visualización de metadatos de archivo
│   │   └── Stats.jsx        # Panel de estadísticas
│   ├── App.jsx              # Aplicación principal
│   └── main.jsx             # Punto de entrada
├── data/                    # Ubicación de base de datos SQLite
└── README.md
```

### Ejecutar Pruebas

```bash
# Backend
cd backend
pytest

# Frontend
npm run test
```

### Compilar para Producción

```bash
# Frontend
npm run build

# Backend
# Usar gunicorn o uvicorn con workers apropiados
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Limitaciones

- **Detección de rotación/volteo**: No detecta versiones rotadas o en espejo de la misma imagen
- **Archivos grandes**: Imágenes/videos muy grandes (>100MB) pueden requerir tiempo de procesamiento significativo
- **Comparación de videos**: Solo compara un único frame (medio del video), puede perder diferencias en otras partes
- **Cambios de perspectiva**: No puede detectar el mismo sujeto fotografiado desde diferentes ángulos
- **Rendimiento**: Para 10,000+ archivos, la fase de comparación puede tomar varios minutos (complejidad O(n²))

## Mejoras Futuras

- Detección de rotación/volteo
- Operaciones de eliminación por lotes
- Exportar resultados a CSV
- Funcionalidad de deshacer eliminación
- Escaneo multi-hilo
- Persistencia de progreso entre sesiones

## Licencia

Licencia MIT - Ver archivo LICENSE para detalles

## Contribuciones

¡Las contribuciones son bienvenidas! Por favor abre un issue o envía un pull request.

## Agradecimientos

- [imagehash](https://github.com/JohannesBuchner/imagehash) - Librería de hashing perceptual
- [FastAPI](https://fastapi.tiangolo.com/) - Framework web moderno de Python
- [React](https://react.dev/) - Librería de UI
- [Tailwind CSS](https://tailwindcss.com/) - Framework de estilos
