import React, { useState, useCallback } from 'react';

interface FileBrowserProps {
  videoFile: string;
  edlFile: string;
  onVideoFileChange: (file: string) => void;
  onEdlFileChange: (file: string) => void;
  onLoadFiles: () => void;
  loading?: boolean;
  videoInfo?: string;
  markerCount?: number;
}

export const FileBrowser: React.FC<FileBrowserProps> = ({
  videoFile,
  edlFile,
  onVideoFileChange,
  onEdlFileChange,
  onLoadFiles,
  loading = false,
  videoInfo,
  markerCount,
}) => {
  const handleVideoBrowse = useCallback(() => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'video/*,.mp4,.mov,.avi,.mkv';
    input.onchange = (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (file) {
        onVideoFileChange(file.path);
      }
    };
    input.click();
  }, [onVideoFileChange]);

  const handleEdlBrowse = useCallback(() => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.edl';
    input.onchange = (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (file) {
        onEdlFileChange(file.path);
      }
    };
    input.click();
  }, [onEdlFileChange]);

  return (
    <div className="file-browser">
      <h2>📁 Load Files</h2>
      <div className="file-browser-content">
        <div className="file-input-row">
          <label>Video File:</label>
          <input
            type="text"
            value={videoFile}
            onChange={(e) => onVideoFileChange(e.target.value)}
            placeholder="Select video file..."
            className="file-input"
          />
          <button onClick={handleVideoBrowse} className="browse-button">
            Browse
          </button>
        </div>

        <div className="file-input-row">
          <label>EDL File:</label>
          <input
            type="text"
            value={edlFile}
            onChange={(e) => onEdlFileChange(e.target.value)}
            placeholder="Select EDL file..."
            className="file-input"
          />
          <button onClick={handleEdlBrowse} className="browse-button">
            Browse
          </button>
        </div>

        {videoInfo && (
          <div className="info-text">
            ℹ️ Video: {videoInfo}
          </div>
        )}

        {markerCount !== undefined && (
          <div className="info-text">
            ℹ️ Markers: {markerCount} total events
          </div>
        )}

        <div className="button-row">
          <button
            onClick={onLoadFiles}
            disabled={loading || !videoFile || !edlFile}
            className="load-button"
          >
            {loading ? 'Loading...' : 'Load Files'}
          </button>
        </div>
      </div>
    </div>
  );
};
