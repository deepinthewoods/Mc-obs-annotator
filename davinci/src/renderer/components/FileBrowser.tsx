import React, { useState } from 'react';

interface FileBrowserProps {
  videoFile: string;
  edlFile: string;
  onVideoFileChange: (file: string) => void;
  onEdlFileChange: (file: string) => void;
  onLoadFiles: () => void;
  isLoading: boolean;
}

export const FileBrowser: React.FC<FileBrowserProps> = ({
  videoFile,
  edlFile,
  onVideoFileChange,
  onEdlFileChange,
  onLoadFiles,
  isLoading,
}) => {
  const handleVideoFileSelect = async () => {
    // Use Electron dialog to select file
    const result = await (window as any).electron.openFileDialog({
      title: 'Select Video File',
      filters: [
        { name: 'Video Files', extensions: ['mp4', 'mov', 'avi', 'mkv'] },
        { name: 'All Files', extensions: ['*'] },
      ],
    });

    if (result && result.length > 0) {
      onVideoFileChange(result[0]);

      // Auto-detect matching EDL file
      const edlPath = result[0].replace(/\.[^.]+$/, '.edl');
      try {
        const exists = await (window as any).electron.fileExists(edlPath);
        if (exists) {
          onEdlFileChange(edlPath);
        }
      } catch (err) {
        // EDL not found, user will need to select manually
      }
    }
  };

  const handleEdlFileSelect = async () => {
    const result = await (window as any).electron.openFileDialog({
      title: 'Select EDL File',
      filters: [
        { name: 'EDL Files', extensions: ['edl'] },
        { name: 'All Files', extensions: ['*'] },
      ],
    });

    if (result && result.length > 0) {
      onEdlFileChange(result[0]);
    }
  };

  return (
    <div className="file-browser">
      <h3>📁 Load Files</h3>
      <div className="file-input-group">
        <div className="file-input-row">
          <label>Video File:</label>
          <input
            type="text"
            value={videoFile}
            onChange={(e) => onVideoFileChange(e.target.value)}
            placeholder="Select video file..."
          />
          <button onClick={handleVideoFileSelect}>Browse</button>
        </div>
        <div className="file-input-row">
          <label>EDL File:</label>
          <input
            type="text"
            value={edlFile}
            onChange={(e) => onEdlFileChange(e.target.value)}
            placeholder="Select EDL file..."
          />
          <button onClick={handleEdlFileSelect}>Browse</button>
        </div>
      </div>
      <div className="file-actions">
        <button
          onClick={onLoadFiles}
          disabled={!videoFile || !edlFile || isLoading}
          className="primary-button"
        >
          {isLoading ? 'Loading...' : 'Load Files'}
        </button>
      </div>
    </div>
  );
};
