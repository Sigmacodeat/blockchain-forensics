/**
 * Download Button with Authentication
 * ====================================
 * 
 * Secure download button that includes auth headers
 */

import React, { useState } from 'react';
import { Download, Loader2, AlertCircle } from 'lucide-react';

interface DownloadButtonProps {
  url: string;
  filename?: string;
  format: string;
  label?: string;
  className?: string;
}

export const DownloadButton: React.FC<DownloadButtonProps> = ({
  url,
  filename,
  format,
  label,
  className = ''
}) => {
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDownload = async () => {
    setDownloading(true);
    setError(null);

    try {
      // ✅ Get auth token
      const token = localStorage.getItem('auth_token');
      const userId = localStorage.getItem('user_id');

      if (!token) {
        throw new Error('Not authenticated');
      }

      // ✅ Fetch with auth headers
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'X-User-ID': userId || '',
        }
      });

      // ✅ Check authorization
      if (response.status === 403) {
        throw new Error('You do not have permission to download this file');
      }

      if (response.status === 401) {
        throw new Error('Authentication required. Please log in.');
      }

      if (!response.ok) {
        throw new Error(`Download failed: ${response.statusText}`);
      }

      // ✅ Download file
      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = filename || `report.${format}`;
      document.body.appendChild(a);
      a.click();
      
      // Cleanup
      window.URL.revokeObjectURL(downloadUrl);
      document.body.removeChild(a);

    } catch (err) {
      console.error('Download error:', err);
      setError(err instanceof Error ? err.message : 'Download failed');
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="inline-flex flex-col gap-2">
      <button
        onClick={handleDownload}
        disabled={downloading}
        className={`inline-flex items-center gap-2 px-4 py-2 
          bg-gradient-to-r from-primary-600 to-primary-700 
          hover:from-primary-700 hover:to-primary-800
          text-white rounded-lg font-medium
          disabled:opacity-50 disabled:cursor-not-allowed
          transition-all duration-200 shadow-lg hover:shadow-xl
          ${className}`}
      >
        {downloading ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>Downloading...</span>
          </>
        ) : (
          <>
            <Download className="w-4 h-4" />
            <span>{label || `Download ${format.toUpperCase()}`}</span>
          </>
        )}
      </button>

      {error && (
        <div className="flex items-center gap-2 text-sm text-red-600 dark:text-red-400">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
};
