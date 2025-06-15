import React from 'react';
import './UploadBox.css';

function UploadBox({ setPdfFile }) {
  const handleUpload = (e) => {
    const file = e.target.files[0];
    if (file && file.type === 'application/pdf') {
      setPdfFile(file);
    } else {
      alert('Please upload a valid PDF file.');
    }
  };

  return (
    <div className="upload-box">
      {/* ✅ Upload illustration image at the top */}
      <img src="/bot logo.jpeg" alt="Upload" className="upload-img" />

      <div className="upload-text">
        <p>No need to hassle just upload the file and we got u covered</p>
      </div>
        {/* Custom upload button */}
        <label htmlFor="file-upload" className="custom-upload-button">
             Upload PDF
        </label>
        <input
            id="file-upload"
            type="file"
            accept="application/pdf"
            onChange={handleUpload}
            style={{ display: 'none' }}
        />
    </div>
  );
}

export default UploadBox;