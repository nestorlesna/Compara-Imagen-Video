import { useState } from 'react';
import axios from 'axios';

const API_URL = 'http://localhost:8000';

export default function Scanner({ onScanComplete }) {
  const [folderPath, setFolderPath] = useState('');
  const [threshold, setThreshold] = useState(5);
  const [isScanning, setIsScanning] = useState(false);
  const [error, setError] = useState('');

  const handleStartScan = async () => {
    if (!folderPath.trim()) {
      setError('Por favor ingresa una ruta de carpeta');
      return;
    }

    setError('');
    setIsScanning(true);

    try {
      await axios.post(`${API_URL}/api/scan`, {
        path: folderPath,
        similarity_threshold: threshold
      });

      if (onScanComplete) {
        onScanComplete(folderPath, threshold);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al iniciar el escaneo');
      setIsScanning(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <h2 className="text-2xl font-bold mb-4 text-gray-800">Escanear Directorio</h2>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Ruta de Carpeta
          </label>
          <input
            type="text"
            value={folderPath}
            onChange={(e) => setFolderPath(e.target.value)}
            placeholder="C:\Users\TuNombre\Imágenes"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={isScanning}
          />
          <p className="mt-1 text-sm text-gray-500">
            Ingresa la ruta completa de la carpeta que deseas escanear (incluye subcarpetas)
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Umbral de Similitud: {threshold}
          </label>
          <input
            type="range"
            min="0"
            max="15"
            value={threshold}
            onChange={(e) => setThreshold(parseInt(e.target.value))}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            disabled={isScanning}
          />
          <div className="flex justify-between text-xs text-gray-600 mt-1">
            <span>Idéntico (0)</span>
            <span>Similar (5)</span>
            <span>Flexible (15)</span>
          </div>
          <p className="mt-1 text-sm text-gray-500">
            Valores menores = coincidencia más estricta (0 = solo idénticos)
          </p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
            {error}
          </div>
        )}

        <button
          onClick={handleStartScan}
          disabled={isScanning}
          className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
        >
          {isScanning ? 'Escaneando...' : 'Iniciar Escaneo'}
        </button>
      </div>
    </div>
  );
}
