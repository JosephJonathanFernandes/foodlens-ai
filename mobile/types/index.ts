export type ScanImage = {
  id: string;
  uri: string;
  type: 'front' | 'back' | 'side' | 'closeup' | 'other';
  preview?: string;
  width?: number;
  height?: number;
};

export type ScanStatus = 'idle' | 'capturing' | 'reviewing' | 'processing' | 'completed' | 'error';

export interface ScanSession {
  id: string;
  productName?: string;
  brand?: string;
  images: ScanImage[];
  status: ScanStatus;
  createdAt: string;
}

export interface Language {
  code: string;
  name: string;
  nativeName: string;
}

export interface ApiError {
  message: string;
  statusCode?: number;
}
