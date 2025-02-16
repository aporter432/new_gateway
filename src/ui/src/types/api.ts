// Basic types for MVP
export enum NetworkType {
    ISATDATA_PRO = 0,
    OGX = 1
}

export interface Message {
    id: string;
    network: NetworkType;
    payload: Record<string, unknown>;
    status: string;
}

export interface MessageSubmission {
    networkType: NetworkType;
    payload: Record<string, unknown>;
    destinationId: string;
}

export interface MessageResponse {
    id: string;
    status: string;
    error?: string;
    timestamp: string;
}
