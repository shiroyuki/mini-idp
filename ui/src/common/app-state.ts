import {ServiceInfo} from "./service-info";
import {SessionInfo} from "./session-info";

/**
 * Booting state
 *
 * - idle = the default state
 * - init = the initialization in progress
 * - ready = the UI is ready
 * - error = the error state
 * - login-required = the login-required state
 */
export type BootingState = "idle" | "init" | "ready" | "error" | "login-required";

export interface ResponseInfo {
    status: number;
    headers: Headers;
    body: string;
}

export const convertToResponseInfo = async (response: Response) => {
    return {
        status: response.status,
        headers: response.headers,
        body: await response.text(),
    } satisfies ResponseInfo;
};

export interface AppState {
    status: BootingState;
    // Stat Info
    inFlightTaskCount: number;
    errorTaskCount: number;
    completeTaskCount: number;
    totalTaskCount: number;
    // Parsed Info
    serviceInfo?: ServiceInfo | null;
    sessionInfo?: SessionInfo | null;
    // Callbacks
    runSessionValidation?: () => void;
    clearSession: () => void;
}