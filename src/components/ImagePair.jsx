import { useState } from 'react';
import axios from 'axios';
import FileInfo from './FileInfo';

const API_URL = 'http://localhost:8000';

export default function ImagePair({ pair, basePath, onDelete, selectedFiles, onFileSelect, onOpenModal }) {
  const [deleting, setDeleting] = useState(null);
  const [error, setError] = useState('');

  const isFile1Selected = selectedFiles?.has(pair.file1.path) || false;
  const isFile2Selected = selectedFiles?.has(pair.file2.path) || false;

  const handleDelete = async (filePath, pairIndex) => {
    if (!confirm(`¿Estás seguro de que quieres eliminar este archivo?\n\n${filePath}`)) {
      return;
    }

    setDeleting(pairIndex);
    setError('');

    try {
      await axios.post(`${API_URL}/api/delete`, {
        file_path: filePath,
        scan_base_path: basePath
      });

      if (onDelete) {
        onDelete(pair);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al eliminar el archivo');
    } finally {
      setDeleting(null);
    }
  };

  const getImageUrl = (path) => {
    // Use backend API to serve the file securely
    return `${API_URL}/api/preview?file_path=${encodeURIComponent(path)}`;
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <div className="mb-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-bold text-gray-800">
            Par de Duplicados
          </h3>
          <div className="text-sm">
            <span className="px-3 py-1 rounded-full bg-blue-100 text-blue-800 font-medium">
              {pair.similarity_percentage.toFixed(1)}% similares
            </span>
            <span className="ml-2 text-gray-500">
              (distancia: {pair.similarity_score})
            </span>
          </div>
        </div>
      </div>

      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* File 1 */}
        <div className="border border-gray-200 rounded-lg p-4">
          {/* Selection checkbox */}
          {onFileSelect && (
            <div className="mb-3 flex items-center">
              <input
                type="checkbox"
                id={`select-file1-${pair.file1.path}`}
                checked={isFile1Selected}
                onChange={(e) => onFileSelect(pair.file1.path, e.target.checked)}
                className="w-5 h-5 text-blue-600 rounded focus:ring-2 focus:ring-blue-500 cursor-pointer"
              />
              <label
                htmlFor={`select-file1-${pair.file1.path}`}
                className="ml-2 text-sm font-medium text-gray-700 cursor-pointer"
              >
                Seleccionar para eliminar
              </label>
            </div>
          )}

          <div
            className="mb-4 bg-gray-100 rounded-lg flex items-center justify-center cursor-pointer hover:bg-gray-200 transition-colors"
            style={{ minHeight: '200px' }}
            onClick={() => onOpenModal && onOpenModal(pair.file1)}
            title="Click para ver en tamaño completo"
          >
            {pair.file1.file_type === 'image' ? (
              <img
                src={getImageUrl(pair.file1.path)}
                alt={pair.file1.filename}
                className="max-w-full max-h-64 object-contain"
                onError={(e) => {
                  e.target.style.display = 'none';
                  e.target.nextSibling.style.display = 'block';
                }}
              />
            ) : (
              <video
                src={getImageUrl(pair.file1.path)}
                className="max-w-full max-h-64"
                onError={(e) => {
                  e.target.style.display = 'none';
                  e.target.nextSibling.style.display = 'flex';
                }}
                onClick={(e) => e.stopPropagation()}
              >
                Tu navegador no soporta la reproducción de video.
              </video>
            )}
            <div style={{ display: 'none' }} className="text-gray-500 text-center flex-col items-center justify-center">
              <svg className="w-16 h-16 mx-auto mb-2" fill="currentColor" viewBox="0 0 20 20">
                <path d="M2 6a2 2 0 012-2h6a2 2 0 012 2v8a2 2 0 01-2 2H4a2 2 0 01-2-2V6zm12.553 1.106A1 1 0 0014 8v4a1 1 0 00.553.894l2 1A1 1 0 0018 13V7a1 1 0 00-1.447-.894l-2 1z" />
              </svg>
              <span>Vista previa no disponible</span>
              <p className="text-xs mt-2">Usa el visor de archivos local</p>
            </div>
          </div>

          <FileInfo file={pair.file1} />

          <button
            onClick={() => handleDelete(pair.file1.path, 1)}
            disabled={deleting !== null}
            className="mt-4 w-full bg-red-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-red-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            {deleting === 1 ? 'Eliminando...' : 'Eliminar Este Archivo'}
          </button>
        </div>

        {/* File 2 */}
        <div className="border border-gray-200 rounded-lg p-4">
          {/* Selection checkbox */}
          {onFileSelect && (
            <div className="mb-3 flex items-center">
              <input
                type="checkbox"
                id={`select-file2-${pair.file2.path}`}
                checked={isFile2Selected}
                onChange={(e) => onFileSelect(pair.file2.path, e.target.checked)}
                className="w-5 h-5 text-blue-600 rounded focus:ring-2 focus:ring-blue-500 cursor-pointer"
              />
              <label
                htmlFor={`select-file2-${pair.file2.path}`}
                className="ml-2 text-sm font-medium text-gray-700 cursor-pointer"
              >
                Seleccionar para eliminar
              </label>
            </div>
          )}

          <div
            className="mb-4 bg-gray-100 rounded-lg flex items-center justify-center cursor-pointer hover:bg-gray-200 transition-colors"
            style={{ minHeight: '200px' }}
            onClick={() => onOpenModal && onOpenModal(pair.file2)}
            title="Click para ver en tamaño completo"
          >
            {pair.file2.file_type === 'image' ? (
              <img
                src={getImageUrl(pair.file2.path)}
                alt={pair.file2.filename}
                className="max-w-full max-h-64 object-contain"
                onError={(e) => {
                  e.target.style.display = 'none';
                  e.target.nextSibling.style.display = 'block';
                }}
              />
            ) : (
              <video
                src={getImageUrl(pair.file2.path)}
                className="max-w-full max-h-64"
                onError={(e) => {
                  e.target.style.display = 'none';
                  e.target.nextSibling.style.display = 'flex';
                }}
                onClick={(e) => e.stopPropagation()}
              >
                Tu navegador no soporta la reproducción de video.
              </video>
            )}
            <div style={{ display: 'none' }} className="text-gray-500 text-center flex-col items-center justify-center">
              <svg className="w-16 h-16 mx-auto mb-2" fill="currentColor" viewBox="0 0 20 20">
                <path d="M2 6a2 2 0 012-2h6a2 2 0 012 2v8a2 2 0 01-2 2H4a2 2 0 01-2-2V6zm12.553 1.106A1 1 0 0014 8v4a1 1 0 00.553.894l2 1A1 1 0 0018 13V7a1 1 0 00-1.447-.894l-2 1z" />
              </svg>
              <span>Vista previa no disponible</span>
              <p className="text-xs mt-2">Usa el visor de archivos local</p>
            </div>
          </div>

          <FileInfo file={pair.file2} />

          <button
            onClick={() => handleDelete(pair.file2.path, 2)}
            disabled={deleting !== null}
            className="mt-4 w-full bg-red-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-red-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            {deleting === 2 ? 'Eliminando...' : 'Eliminar Este Archivo'}
          </button>
        </div>
      </div>
    </div>
  );
}
