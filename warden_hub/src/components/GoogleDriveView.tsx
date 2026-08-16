import React, { useState, useEffect, useRef } from 'react';
import { 
  Cloud, 
  Search, 
  Upload, 
  Trash2, 
  ExternalLink, 
  FileText, 
  Music, 
  Folder, 
  Image, 
  RefreshCw, 
  LogOut, 
  AlertTriangle,
  Zap,
  Check,
  File as FileIcon
} from 'lucide-react';
import { User } from 'firebase/auth';
import { googleSignIn, logout, getAccessToken, initAuth } from '../lib/firebase';
import { cn } from '../lib/utils';

interface DriveFile {
  id: string;
  name: string;
  mimeType: string;
  size?: string;
  createdTime?: string;
  modifiedTime?: string;
  iconLink?: string;
  webViewLink?: string;
  thumbnailLink?: string;
}

export function GoogleDriveView({ onImportAudio }: { onImportAudio?: (file: File) => void }) {
  const [user, setUser] = useState<User | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [needsAuth, setNeedsAuth] = useState(true);
  const [isLoggingIn, setIsLoggingIn] = useState(false);
  const [loginError, setLoginError] = useState<string | null>(null);

  const [files, setFiles] = useState<DriveFile[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFilter, setSelectedFilter] = useState<'all' | 'audio' | 'docs' | 'folders'>('all');
  
  // Upload State
  const [isUploading, setIsUploading] = useState(false);
  const uploadInputRef = useRef<HTMLInputElement>(null);

  // Modal State for Delete Confirmation (MANDATORY per Workspace Skill guidelines)
  const [fileToDelete, setFileToDelete] = useState<DriveFile | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // Status message
  const [statusMsg, setStatusMsg] = useState<{ text: string; type: 'success' | 'error' } | null>(null);
  const [importingFileId, setImportingFileId] = useState<string | null>(null);

  const handleImportFromDrive = async (file: DriveFile) => {
    const token = getAccessToken() || accessToken;
    if (!token) {
      setNeedsAuth(true);
      return;
    }

    setImportingFileId(file.id);
    try {
      showStatus(`Downloading "${file.name}" from Google Drive...`, 'success');
      const res = await fetch(`https://www.googleapis.com/drive/v3/files/${file.id}?alt=media&supportsAllDrives=true`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });

      if (!res.ok) {
        throw new Error(`Failed to fetch file content from Drive (${res.status})`);
      }

      const blob = await res.blob();
      const audioFile = new window.File([blob], file.name, { type: file.mimeType || 'audio/mpeg' });

      const formData = new FormData();
      formData.append('audio', audioFile);

      showStatus(`Analyzing Audio DNA for "${file.name}" in Python engine...`, 'success');
      const uploadRes = await fetch('/api/upload', {
        method: 'POST',
        body: formData
      });

      if (!uploadRes.ok) {
        const text = await uploadRes.text();
        let errMsg = 'Failed to analyze audio';
        try {
          const errJson = JSON.parse(text);
          errMsg = errJson.error || errMsg;
        } catch {
          if (text.includes('<!doctype') || text.includes('<html')) {
            errMsg = `Server returned invalid response (${uploadRes.status})`;
          } else if (text) {
            errMsg = text;
          }
        }
        throw new Error(errMsg);
      }

      const rawText = await uploadRes.text();
      let dnaResult: any;
      try {
        dnaResult = JSON.parse(rawText);
      } catch (e) {
        throw new Error("Server response was not valid JSON");
      }
      showStatus(`Successfully analyzed "${file.name}"! BPM: ${dnaResult.bpm}, Key: ${dnaResult.musical_key}`, 'success');
    } catch (err: any) {
      console.error('Import audio error:', err);
      showStatus(err.message || 'Failed to import audio file from Drive', 'error');
    } finally {
      setImportingFileId(null);
    }
  };

  useEffect(() => {
    const unsubscribe = initAuth(
      (currentUser, token) => {
        setUser(currentUser);
        setAccessToken(token);
        setNeedsAuth(false);
      },
      () => {
        setUser(null);
        setAccessToken(null);
        setNeedsAuth(true);
      }
    );
    return () => unsubscribe();
  }, []);

  useEffect(() => {
    if (accessToken && !needsAuth) {
      fetchDriveFiles();
    }
  }, [accessToken, needsAuth, selectedFilter]);

  const parseAuthError = (err: any): string => {
    const code = err?.code || '';
    const message = err?.message || '';

    if (code === 'auth/popup-blocked') {
      return 'Sign-in popup was blocked by your browser. Please allow popups for this app to connect Google Drive.';
    }
    if (code === 'auth/popup-closed-by-user') {
      return 'Sign-in window was closed before completing authentication.';
    }
    if (code === 'auth/cancelled-popup-request') {
      return 'Previous sign-in attempt was cancelled.';
    }
    if (code === 'auth/network-request-failed') {
      return 'Network connection error. Please check your internet connectivity and try again.';
    }
    if (message.includes('popup')) {
      return 'Unable to open sign-in popup window. Please enable popups in your browser.';
    }
    return message || 'Failed to authenticate with Google Drive.';
  };

  const handleLogin = async () => {
    setIsLoggingIn(true);
    setLoginError(null);
    try {
      const res = await googleSignIn();
      if (res) {
        setUser(res.user);
        setAccessToken(res.accessToken);
        setNeedsAuth(false);
      }
    } catch (err: any) {
      console.error('Google Sign-In failed:', err);
      setLoginError(parseAuthError(err));
    } finally {
      setIsLoggingIn(false);
    }
  };

  const handleLogout = async () => {
    try {
      await logout();
    } catch (e) {
      console.error('Logout error:', e);
    } finally {
      setUser(null);
      setAccessToken(null);
      setNeedsAuth(true);
      setFiles([]);
    }
  };

  const fetchDriveFiles = async () => {
    const token = getAccessToken() || accessToken;
    if (!token) {
      setNeedsAuth(true);
      return;
    }

    setIsLoading(true);
    try {
      let qClause = "trashed = false";

      if (selectedFilter === 'audio') {
        qClause += " and (mimeType contains 'audio/' or name contains '.mp3' or name contains '.wav' or name contains '.flac' or name contains '.m4a' or name contains '.ogg' or name contains '.aac')";
      } else if (selectedFilter === 'docs') {
        qClause += " and (mimeType contains 'document' or mimeType contains 'text' or mimeType contains 'pdf' or mimeType contains 'spreadsheet' or mimeType contains 'presentation')";
      } else if (selectedFilter === 'folders') {
        qClause += " and mimeType = 'application/vnd.google-apps.folder'";
      }

      if (searchQuery.trim()) {
        const sanitized = searchQuery.trim().replace(/'/g, "\\'");
        qClause += ` and name contains '${sanitized}'`;
      }

      const url = `https://www.googleapis.com/drive/v3/files?fields=files(id,name,mimeType,size,createdTime,modifiedTime,iconLink,webViewLink,thumbnailLink)&pageSize=100&supportsAllDrives=true&includeItemsFromAllDrives=true&orderBy=modifiedTime%20desc&q=${encodeURIComponent(qClause)}`;

      const response = await fetch(url, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });

      if (response.status === 401) {
        setNeedsAuth(true);
        setAccessToken(null);
        showStatus('Google Drive session expired. Please sign in again.', 'error');
        return;
      }

      if (response.status === 403) {
        throw new Error('Google Drive API permission denied or quota exceeded (403).');
      }

      if (!response.ok) {
        throw new Error(`Drive API error (${response.status}): ${response.statusText}`);
      }

      const data = await response.json();
      setFiles(data.files || []);
    } catch (err: any) {
      console.error('Fetch files error:', err);
      showStatus(err.message || 'Error fetching Drive files', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 50 * 1024 * 1024) {
      showStatus('File size exceeds 50MB limit for direct upload.', 'error');
      if (uploadInputRef.current) uploadInputRef.current.value = '';
      return;
    }

    const token = getAccessToken() || accessToken;
    if (!token) {
      setNeedsAuth(true);
      return;
    }

    setIsUploading(true);
    try {
      const metadata = {
        name: file.name,
        mimeType: file.type || 'application/octet-stream'
      };

      const formData = new FormData();
      formData.append(
        'metadata',
        new Blob([JSON.stringify(metadata)], { type: 'application/json' })
      );
      formData.append('file', file);

      const response = await fetch(
        'https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&fields=id,name,mimeType,size,createdTime,modifiedTime,webViewLink',
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${token}`
          },
          body: formData
        }
      );

      if (response.status === 401) {
        setNeedsAuth(true);
        setAccessToken(null);
        throw new Error('Session expired during upload. Please sign in again.');
      }

      if (!response.ok) {
        throw new Error(`Upload failed (${response.status}): ${response.statusText}`);
      }

      const uploadedFile = await response.json();
      setFiles(prev => [uploadedFile, ...prev]);
      showStatus(`Successfully uploaded "${file.name}" to Google Drive!`, 'success');
    } catch (err: any) {
      console.error('Upload error:', err);
      showStatus(err.message || 'Failed to upload file to Drive', 'error');
    } finally {
      setIsUploading(false);
      if (uploadInputRef.current) uploadInputRef.current.value = '';
    }
  };

  const confirmDeleteFile = async () => {
    if (!fileToDelete) return;

    const token = getAccessToken() || accessToken;
    if (!token) {
      setNeedsAuth(true);
      return;
    }

    setIsDeleting(true);
    try {
      const response = await fetch(
        `https://www.googleapis.com/drive/v3/files/${fileToDelete.id}`,
        {
          method: 'DELETE',
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      );

      if (response.status === 401) {
        setNeedsAuth(true);
        setAccessToken(null);
        throw new Error('Session expired. Please sign in again.');
      }

      if (response.status === 404) {
        setFiles(prev => prev.filter(f => f.id !== fileToDelete.id));
        showStatus(`File "${fileToDelete.name}" was already deleted from Drive.`, 'success');
        setFileToDelete(null);
        return;
      }

      if (!response.ok && response.status !== 204) {
        throw new Error(`Delete failed (${response.status}): ${response.statusText}`);
      }

      setFiles(prev => prev.filter(f => f.id !== fileToDelete.id));
      showStatus(`Deleted "${fileToDelete.name}" from Google Drive.`, 'success');
      setFileToDelete(null);
    } catch (err: any) {
      console.error('Delete error:', err);
      showStatus(err.message || 'Failed to delete file from Drive', 'error');
    } finally {
      setIsDeleting(false);
    }
  };

  const showStatus = (text: string, type: 'success' | 'error') => {
    setStatusMsg({ text, type });
    setTimeout(() => setStatusMsg(null), 4000);
  };

  const formatFileSize = (bytes?: string) => {
    if (!bytes) return 'N/A';
    const num = parseInt(bytes, 10);
    if (isNaN(num)) return 'N/A';
    if (num < 1024) return `${num} B`;
    if (num < 1024 * 1024) return `${(num / 1024).toFixed(1)} KB`;
    return `${(num / (1024 * 1024)).toFixed(1)} MB`;
  };

  const getFileIcon = (mimeType: string) => {
    if (mimeType.includes('folder')) return <Folder size={18} className="text-amber-400" />;
    if (mimeType.includes('audio')) return <Music size={18} className="text-cyan-400" />;
    if (mimeType.includes('image')) return <Image size={18} className="text-purple-400" />;
    if (mimeType.includes('document') || mimeType.includes('text') || mimeType.includes('pdf')) return <FileText size={18} className="text-blue-400" />;
    return <FileIcon size={18} className="text-white/40" />;
  };

  const filteredFiles = files.filter(file => {
    const matchesSearch = file.name.toLowerCase().includes(searchQuery.toLowerCase());
    if (!matchesSearch) return false;

    if (selectedFilter === 'audio') return file.mimeType.includes('audio');
    if (selectedFilter === 'docs') return file.mimeType.includes('document') || file.mimeType.includes('text') || file.mimeType.includes('pdf') || file.mimeType.includes('spreadsheet');
    if (selectedFilter === 'folders') return file.mimeType.includes('folder');
    return true;
  });

  return (
    <div className="flex-1 flex flex-col w-full h-full rounded-2xl border border-white/10 overflow-hidden bg-[#0a0a0a]">
      {/* Header */}
      <div className="p-4 bg-white/5 border-b border-white/10 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400">
            <Cloud size={20} />
          </div>
          <div>
            <h3 className="text-sm font-semibold tracking-wide flex items-center gap-2">
              Google Drive Cloud Files
            </h3>
            <p className="text-[10px] text-white/40">
              {user ? `Connected as ${user.email}` : 'Sign in with Google to access your Drive files'}
            </p>
          </div>
        </div>

        {user && (
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 border border-white/10 text-xs">
              {user.photoURL ? (
                <img src={user.photoURL} alt={user.displayName || 'User'} className="w-5 h-5 rounded-full" />
              ) : (
                <div className="w-5 h-5 rounded-full bg-cyan-500/30 flex items-center justify-center text-[10px] font-bold">
                  {user.email?.[0].toUpperCase()}
                </div>
              )}
              <span className="text-white/80 font-medium text-[11px] truncate max-w-[120px]">{user.displayName || user.email}</span>
            </div>
            <button
              onClick={handleLogout}
              className="p-2 rounded-lg bg-white/5 hover:bg-white/10 text-white/50 hover:text-white transition-all"
              title="Sign Out"
            >
              <LogOut size={16} />
            </button>
          </div>
        )}
      </div>

      {/* Main Content */}
      <div className="flex-1 p-6 flex flex-col overflow-hidden relative">
        {/* Status Toast */}
        {statusMsg && (
          <div className={cn(
            "mb-4 p-3 rounded-xl text-xs font-medium flex items-center gap-2 border animate-fadeIn",
            statusMsg.type === 'success' ? "bg-green-500/10 text-green-300 border-green-500/20" : "bg-red-500/10 text-red-300 border-red-500/20"
          )}>
            {statusMsg.type === 'success' ? <Check size={16} /> : <AlertTriangle size={16} />}
            <span>{statusMsg.text}</span>
          </div>
        )}

        {/* Not Authenticated View */}
        {needsAuth ? (
          <div className="flex-1 flex flex-col items-center justify-center text-center p-8">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500/20 to-cyan-500/20 border border-white/10 flex items-center justify-center mb-6 shadow-xl">
              <Cloud size={32} className="text-cyan-400" />
            </div>
            <h4 className="text-xl font-bold mb-2">Connect Google Drive</h4>
            <p className="text-xs text-white/50 max-w-md leading-relaxed mb-8">
              Sign in with your Google account to view, upload, and organize your Drive files directly within the workspace.
            </p>

            {loginError && (
              <div className="mb-6 p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-300 text-xs max-w-md">
                {loginError}
              </div>
            )}

            {/* Official Material Standard Google Sign In Button */}
            <button
              onClick={handleLogin}
              disabled={isLoggingIn}
              className="gsi-material-button bg-white hover:bg-neutral-100 text-neutral-800 font-semibold px-6 py-3 rounded-full flex items-center gap-3 transition-all hover:scale-105 active:scale-95 shadow-lg border border-neutral-200"
            >
              <div className="w-5 h-5">
                <svg version="1.1" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" className="w-full h-full">
                  <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"></path>
                  <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"></path>
                  <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"></path>
                  <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"></path>
                </svg>
              </div>
              <span className="text-sm tracking-wide">{isLoggingIn ? 'Connecting...' : 'Sign in with Google'}</span>
            </button>
          </div>
        ) : (
          /* Authenticated Drive Explorer View */
          <div className="flex-1 flex flex-col overflow-hidden">
            {/* Action Bar */}
            <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
              {/* Search Bar */}
              <div className="relative flex-1 min-w-[240px]">
                <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-white/30" />
                <input
                  type="text"
                  placeholder="Search files in Google Drive..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full bg-white/5 border border-white/10 rounded-xl pl-9 pr-4 py-2 text-xs focus:outline-none focus:border-cyan-500/50 transition-all placeholder:text-white/20"
                />
              </div>

              {/* Filters & Refresh */}
              <div className="flex items-center gap-2">
                <div className="flex bg-white/5 p-1 rounded-xl border border-white/10 text-xs">
                  {(['all', 'audio', 'docs', 'folders'] as const).map(filter => (
                    <button
                      key={filter}
                      onClick={() => setSelectedFilter(filter)}
                      className={cn(
                        "px-3 py-1 rounded-lg capitalize transition-all text-[11px]",
                        selectedFilter === filter ? "bg-cyan-500 text-black font-semibold" : "text-white/50 hover:text-white"
                      )}
                    >
                      {filter}
                    </button>
                  ))}
                </div>

                <button
                  onClick={fetchDriveFiles}
                  disabled={isLoading}
                  className="p-2 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-white/60 hover:text-white transition-all disabled:opacity-30"
                  title="Refresh Files"
                >
                  <RefreshCw size={16} className={cn(isLoading && "animate-spin")} />
                </button>

                {/* Upload Button */}
                <input
                  type="file"
                  ref={uploadInputRef}
                  onChange={handleFileUpload}
                  className="hidden"
                />
                <button
                  onClick={() => uploadInputRef.current?.click()}
                  disabled={isUploading}
                  className="px-4 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-black font-semibold text-xs transition-all flex items-center gap-2 shadow-lg shadow-cyan-500/20 disabled:opacity-50"
                >
                  <Upload size={14} />
                  {isUploading ? 'Uploading...' : 'Upload to Drive'}
                </button>
              </div>
            </div>

            {/* File List */}
            <div className="flex-1 overflow-y-auto pr-2">
              {isLoading && files.length === 0 ? (
                <div className="p-12 text-center text-white/40 font-mono text-xs">
                  Loading Google Drive files...
                </div>
              ) : filteredFiles.length === 0 ? (
                <div className="p-12 text-center rounded-2xl bg-white/[0.02] border border-white/5">
                  <Cloud size={32} className="mx-auto mb-3 text-white/20" />
                  <p className="text-sm font-medium text-white/60">No files found</p>
                  <p className="text-xs text-white/30 mt-1">Try clearing your search query or uploading a file to Drive.</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {filteredFiles.map(file => (
                    <div
                      key={file.id}
                      className="p-4 rounded-xl bg-white/5 border border-white/10 hover:bg-white/[0.08] transition-all flex items-start justify-between gap-3 group"
                    >
                      <div className="flex items-start gap-3 min-w-0">
                        <div className="p-2.5 rounded-lg bg-black/40 border border-white/10 flex-shrink-0">
                          {getFileIcon(file.mimeType)}
                        </div>
                        <div className="min-w-0">
                          <h5 className="font-semibold text-xs text-white/90 truncate group-hover:text-cyan-400 transition-colors">
                            {file.name}
                          </h5>
                          <div className="flex items-center gap-3 mt-1 text-[10px] text-white/40 font-mono">
                            <span>{formatFileSize(file.size)}</span>
                            {file.modifiedTime && (
                              <span>• {new Date(file.modifiedTime).toLocaleDateString()}</span>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* File Action Controls */}
                      <div className="flex items-center gap-1 opacity-80 group-hover:opacity-100 transition-opacity">
                        {(file.mimeType.includes('audio') || file.name.match(/\.(mp3|wav|flac|m4a|ogg|aac)$/i)) && (
                          <button
                            onClick={() => handleImportFromDrive(file)}
                            disabled={importingFileId === file.id}
                            className="p-1.5 rounded-lg bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 border border-cyan-500/20 transition-all flex items-center gap-1 text-[10px] font-semibold"
                            title="Analyze Audio DNA in Workspace"
                          >
                            <Zap size={13} className={cn(importingFileId === file.id && "animate-bounce")} />
                            <span>{importingFileId === file.id ? 'Analyzing...' : 'Analyze DNA'}</span>
                          </button>
                        )}

                        {file.webViewLink && (
                          <a
                            href={file.webViewLink}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="p-1.5 rounded-lg hover:bg-white/10 text-white/50 hover:text-white transition-all"
                            title="Open in Drive"
                          >
                            <ExternalLink size={14} />
                          </a>
                        )}

                        <button
                          onClick={() => setFileToDelete(file)}
                          className="p-1.5 rounded-lg hover:bg-red-500/20 text-white/30 hover:text-red-400 transition-all"
                          title="Delete File"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Mandatory Explicit Confirmation Dialog for Delete Operation */}
      {fileToDelete && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#121212] border border-white/10 rounded-2xl p-6 max-w-md w-full shadow-2xl animate-scaleIn">
            <div className="flex items-center gap-3 mb-4 text-amber-400">
              <div className="p-2 rounded-lg bg-amber-500/10">
                <AlertTriangle size={20} />
              </div>
              <h4 className="font-bold text-sm text-white">Confirm Delete File</h4>
            </div>

            <p className="text-xs text-white/70 leading-relaxed mb-4">
              Are you sure you want to permanently delete <strong className="text-white">{fileToDelete.name}</strong> from your Google Drive account?
            </p>

            <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-[11px] text-red-300 mb-6">
              This action cannot be undone and will remove the file from your Google Cloud storage.
            </div>

            <div className="flex items-center justify-end gap-3">
              <button
                onClick={() => setFileToDelete(null)}
                disabled={isDeleting}
                className="px-4 py-2 rounded-xl bg-white/5 hover:bg-white/10 text-xs font-semibold text-white/70 hover:text-white transition-all"
              >
                Cancel
              </button>
              <button
                onClick={confirmDeleteFile}
                disabled={isDeleting}
                className="px-4 py-2 rounded-xl bg-red-500 hover:bg-red-600 text-xs font-semibold text-white transition-all flex items-center gap-2"
              >
                {isDeleting ? 'Deleting...' : 'Delete File'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
