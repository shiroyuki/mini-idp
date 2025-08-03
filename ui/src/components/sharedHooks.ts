import {convertToResponseInfo} from "../common/app-state";
import {useEffect, useState} from "react";
import {parseJsonOrNull} from "./helpers";
import {SessionInfo} from "../common/session-info";

export function useSessionData() {
    const [sessionData, setSessionData] = useState<SessionInfo | null>(null);

    useEffect(() => {
        if (sessionData !== null) {
            return;
        }

        fetch("/oauth/me/session")
            .then(convertToResponseInfo)
            .then(response => {
                const responseOk = response.status === 200
                const updatedContent = parseJsonOrNull<SessionInfo>(response);

                if (responseOk) {
                    setSessionData(updatedContent);
                } else {
                    throw new Error(`HTTP ${response.status}: ${response.body}`);
                }
            });
    });

    return sessionData;
}