import { useState } from 'react';
import Scanner from './components/Scanner';
import Progress from './components/Progress';
import ImagePair from './components/ImagePair';
import Stats from './components/Stats';
import axios from 'axios';

const API_URL = 'http://localhost:8000';

function App() {
  const [isScanning, setIsScanning] = useState(false);
  const [scanBasePath, setScanBasePath] = useState('');
  const [currentThreshold, setCurrentThreshold] = useState(5);
  const [duplicates, setDuplicates] = useState([]);
  const [totalSavings, setTotalSavings] = useState(0);
  const [loading, setLoading] = useState(false);

  const handleScanStart = (path, threshold) => {
    setIsScanning(true);
    setScanBasePath(path);
    setCurrentThreshold(threshold);
    setDuplicates([]);
  };

  const handleScanComplete = async () => {
    setIsScanning(false);
    await loadDuplicates();
  };

  const loadDuplicates = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_URL}/api/duplicates`, {
        params: { threshold: currentThreshold }
      });
      setDuplicates(response.data.pairs);
      setTotalSavings(response.data.total_potential_savings_mb);
    } catch (err) {
      console.error('Error cargando duplicados:', err);
      alert('Error al cargar duplicados: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (deletedPair) => {
    // Remove the deleted pair from the list
    setDuplicates(prev => prev.filter(p => p !== deletedPair));
    // Recalculate savings
    await loadDuplicates();
  };

  return (
    <div className="min-h-screen bg-gray-100 py-8">
      <div className="container mx-auto px-4 max-w-7xl">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Detector de Duplicados de Imágenes y Videos
          </h1>
          <p className="text-gray-600">
            Encuentra y elimina imágenes y videos duplicados o similares
          </p>
        </div>

        {/* Stats */}
        <Stats />

        {/* Scanner */}
        <Scanner onScanComplete={handleScanStart} />

        {/* Progress */}
        {isScanning && (
          <Progress isActive={isScanning} onComplete={handleScanComplete} />
        )}

        {/* Results Summary */}
        {!isScanning && duplicates.length > 0 && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-xl font-bold text-gray-800">
                  {duplicates.length} par{duplicates.length !== 1 ? 'es' : ''} de duplicados encontrado{duplicates.length !== 1 ? 's' : ''}
                </h3>
                <p className="text-gray-600 mt-1">
                  Ahorro potencial: <span className="font-bold text-green-600">
                    {totalSavings.toFixed(2)} MB
                  </span>
                </p>
              </div>
              <button
                onClick={loadDuplicates}
                className="bg-blue-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-blue-700 transition-colors"
              >
                Actualizar Resultados
              </button>
            </div>
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <p className="mt-4 text-gray-600">Cargando duplicados...</p>
          </div>
        )}

        {/* No results message */}
        {!isScanning && !loading && duplicates.length === 0 && scanBasePath && (
          <div className="bg-white rounded-lg shadow-md p-12 text-center">
            <svg className="w-16 h-16 mx-auto mb-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <h3 className="text-xl font-bold text-gray-800 mb-2">
              No se Encontraron Duplicados
            </h3>
            <p className="text-gray-600">
              No se encontraron archivos duplicados o similares con el umbral actual.
              Intenta aumentar el umbral para una coincidencia más flexible.
            </p>
          </div>
        )}

        {/* Duplicate Pairs */}
        {!loading && duplicates.length > 0 && (
          <div className="space-y-6">
            {duplicates.map((pair, index) => (
              <ImagePair
                key={index}
                pair={pair}
                basePath={scanBasePath}
                onDelete={handleDelete}
              />
            ))}
          </div>
        )}

        {/* Footer */}
        <div className="mt-12 text-center text-sm text-gray-500">
          <p>Detector de Duplicados v1.0.0</p>
          <p className="mt-1">Todas las operaciones se realizan localmente en tu computadora</p>
        </div>
      </div>
    </div>
  );
}

export default App;
