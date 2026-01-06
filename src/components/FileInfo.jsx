export default function FileInfo({ file }) {
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  };

  return (
    <div className="space-y-2 text-sm">
      <div className="font-medium text-gray-900 truncate" title={file.filename}>
        {file.filename}
      </div>

      <div className="grid grid-cols-2 gap-2 text-gray-600">
        <div>
          <span className="font-medium">Tamaño:</span> {file.size_mb.toFixed(2)} MB
        </div>
        <div>
          <span className="font-medium">Tipo:</span> {file.file_type}
        </div>

        {file.width && file.height && (
          <div className="col-span-2">
            <span className="font-medium">Dimensiones:</span> {file.width} × {file.height}
          </div>
        )}

        <div className="col-span-2">
          <span className="font-medium">Modificado:</span> {formatDate(file.modified_at)}
        </div>

        <div className="col-span-2">
          <span className="font-medium">Creado:</span> {formatDate(file.created_at)}
        </div>
      </div>

      <div className="pt-2 border-t border-gray-200">
        <div className="text-xs text-gray-500 break-all">
          {file.path}
        </div>
      </div>
    </div>
  );
}
