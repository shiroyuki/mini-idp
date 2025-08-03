import {ResponseInfo} from "../common/app-state";

export function parseJsonOrNull<T>(responseInfo?: ResponseInfo | null) {
    return responseInfo ? JSON.parse(responseInfo.body) : null as T;
}