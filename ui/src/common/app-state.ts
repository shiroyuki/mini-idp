import {ServiceInfo} from "./service-info";
import {SessionInfo} from "./session-info";

export type BootingState = "idle" | "init" | "ready" | "error" | "authentication-required";

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

export interface BootingStateMap {
    [k: string]: ResponseInfo | null | undefined;
}

export interface AppState {
    status: BootingState;
    // Stat Info
    inFlightTaskCount: number;
    errorTaskCount: number;
    completeTaskCount: number;
    totalTaskCount: number;
    // Parsed Info
    serviceInfo: ServiceInfo;
    sessionInfo: SessionInfo;
    // Callbacks
    runSessionValidation?: () => void;
}