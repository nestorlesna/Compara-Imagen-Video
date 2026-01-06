import { useEffect, useState, useRef } from 'react';

const API_URL = 'http://localhost:8000';

export default function MediaModal({ file, onClose }) {
  const [zoom, setZoom] = useState(1);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const imageRef = useRef(null);

  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    // Prevent body scroll when modal is open
    document.body.style.overflow = 'hidden';

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [onClose]);

  const handleZoomIn = () => {
    setZoom(prev => Math.min(prev + 0.5, 5));
  };

  const handleZoomOut = () => {
    setZoom(prev => Math.max(prev - 0.5, 0.5));
  };

  const handleResetZoom = () => {
    setZoom(1);
    setPosition({ x: 0, y: 0 });
  };

  const handleWheel = (e) => {
    if (file.file_type !== 'image') return;

    e.preventDefault();
    const delta = e.deltaY > 0 ? -0.1 : 0.1;
    setZoom(prev => Math.max(0.5, Math.min(5, prev + delta)));
  };

  const handleMouseDown = (e) => {
    if (file.file_type !== 'image' || zoom <= 1) return;

    setIsDragging(true);
    setDragStart({
      x: e.clientX - position.x,
      y: e.clientY - position.y
    });
    e.preventDefault();
  };

  const handleMouseMove = (e) => {
    if (!isDragging) return;

    setPosition({
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y
    });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isDragging, dragStart]);

  if (!file) return null;

  const getFileUrl = (path) => {
    return `${API_URL}/api/preview?file_path=${encodeURIComponent(path)}`;
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-90 p-4"
      onClick={onClose}
    >
      {/* Close button */}
      <button
        onClick={onClose}
        className="absolute top-4 right-4 text-white hover:text-gray-300 transition-colors z-10"
        aria-label="Cerrar"
      >
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>

      {/* Zoom controls for images */}
      {file.file_type === 'image' && (
        <div className="absolute top-4 left-4 flex flex-col gap-2 z-10">
          <button
            onClick={handleZoomIn}
            className="bg-black bg-opacity-75 text-white p-2 rounded-lg hover:bg-opacity-90 transition-colors"
            title="Zoom In (+)"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v6m3-3H7" />
            </svg>
          </button>
          <button
            onClick={handleZoomOut}
            className="bg-black bg-opacity-75 text-white p-2 rounded-lg hover:bg-opacity-90 transition-colors"
            title="Zoom Out (-)"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM13 10H7" />
            </svg>
          </button>
          <button
            onClick={handleResetZoom}
            className="bg-black bg-opacity-75 text-white p-2 rounded-lg hover:bg-opacity-90 transition-colors"
            title="Resetear Zoom"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
          <div className="bg-black bg-opacity-75 text-white px-3 py-1 rounded-lg text-sm text-center">
            {Math.round(zoom * 100)}%
          </div>
        </div>
      )}

      <div
        className="max-w-7xl max-h-full w-full h-full flex flex-col items-center justify-center"
        onClick={(e) => e.stopPropagation()}
      >
        {/* File info header */}
        <div className="bg-black bg-opacity-75 text-white px-6 py-3 rounded-t-lg mb-2 w-full max-w-4xl">
          <h3 className="text-lg font-semibold truncate">{file.filename}</h3>
          <p className="text-sm text-gray-300">
            {file.width && file.height ? `${file.width} × ${file.height} • ` : ''}
            {file.size_mb.toFixed(2)} MB
            {file.file_type === 'image' && zoom > 1 && (
              <span className="ml-2 text-blue-300">• Arrastra para mover</span>
            )}
          </p>
        </div>

        {/* Media content */}
        <div
          className="flex-1 flex items-center justify-center w-full max-h-[80vh] overflow-hidden"
          onWheel={handleWheel}
        >
          {file.file_type === 'image' ? (
            <img
              ref={imageRef}
              src={getFileUrl(file.path)}
              alt={file.filename}
              className="rounded-lg shadow-2xl select-none"
              style={{
                transform: `scale(${zoom}) translate(${position.x / zoom}px, ${position.y / zoom}px)`,
                transition: isDragging ? 'none' : 'transform 0.1s ease-out',
                cursor: zoom > 1 ? (isDragging ? 'grabbing' : 'grab') : 'default',
                maxWidth: '100%',
                maxHeight: '100%',
                objectFit: 'contain'
              }}
              onMouseDown={handleMouseDown}
              onClick={(e) => e.stopPropagation()}
              draggable={false}
            />
          ) : (
            <video
              src={getFileUrl(file.path)}
              controls
              autoPlay
              className="max-w-full max-h-full rounded-lg shadow-2xl"
              onClick={(e) => e.stopPropagation()}
            >
              Tu navegador no soporta la reproducción de video.
            </video>
          )}
        </div>

        {/* Path info */}
        <div className="bg-black bg-opacity-75 text-white px-6 py-3 rounded-b-lg mt-2 w-full max-w-4xl">
          <p className="text-xs text-gray-400 break-all">{file.path}</p>
        </div>
      </div>
    </div>
  );
}
