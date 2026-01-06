import { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = 'http://localhost:8000';

export default function Progress({ isActive, onComplete }) {
  const [status, setStatus] = useState(null);

  useEffect(() => {
    if (!isActive) return;

    const interval = setInterval(async () => {
      try {
        const response = await axios.get(`${API_URL}/api/scan/status`);
        setStatus(response.data);

        // Check if scan completed
        if (!response.data.is_scanning && response.data.end_time) {
          clearInterval(interval);
          if (onComplete) {
            onComplete();
          }
        }
      } catch (err) {
        console.error('Error fetching scan status:', err);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [isActive, onComplete]);

  if (!status || !isActive) return null;

  const progress = status.total_files > 0
    ? (status.processed_files / status.total_files) * 100
    : 0;

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <h3 className="text-xl font-bold mb-4 text-gray-800">Progreso del Escaneo</h3>

      <div className="space-y-4">
        <div>
          <div className="flex justify-between text-sm text-gray-600 mb-1">
            <span>Progreso</span>
            <span>{status.processed_files} / {status.total_files} archivos</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-4">
            <div
              className="bg-blue-600 h-4 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
          <div className="text-right text-sm text-gray-600 mt-1">
            {progress.toFixed(1)}%
          </div>
        </div>

        {status.current_file && (
          <div className="text-sm text-gray-600">
            <span className="font-medium">Archivo actual:</span> {status.current_file}
          </div>
        )}

        {status.is_scanning && (
          <div className="flex items-center justify-center space-x-2 text-blue-600">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
            <span>Escaneando...</span>
          </div>
        )}

        {!status.is_scanning && status.end_time && (
          <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded">
            ¡Escaneo completado exitosamente!
          </div>
        )}

        {status.errors && status.errors.length > 0 && (
          <div className="bg-yellow-50 border border-yellow-200 rounded p-3">
            <p className="text-sm font-medium text-yellow-800 mb-2">
              Errores encontrados ({status.errors.length}):
            </p>
            <div className="max-h-32 overflow-y-auto text-xs text-yellow-700 space-y-1">
              {status.errors.slice(0, 10).map((error, idx) => (
                <div key={idx}>• {error}</div>
              ))}
              {status.errors.length > 10 && (
                <div className="text-yellow-600">
                  ... y {status.errors.length - 10} más
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
