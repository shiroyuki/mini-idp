import {Outlet, useNavigate} from 'react-router-dom';
import './App.scss';
import {useEffect, useMemo, useState} from "react";
import {BootingState, AppState, BootingStateMap, convertToResponseInfo, ResponseInfo} from "./common/app-state";
import {ServiceInfo} from "./common/service-info";
import {LinearLoadingAnimation} from "./components/loaders";
import {SessionInfo} from "./common/session-info";

function parseJsonOrNull(responseInfo?: ResponseInfo | null) {
    return responseInfo ? JSON.parse(responseInfo.body) : null;
}

function App() {
    const nagivate = useNavigate();
    const [overallStatus, setOverallStatus] = useState<BootingState>("idle")
    const [bootingStateMap, setBootingStateMap] = useState<BootingStateMap>({
        serviceInfo: undefined,
        sessionInfo: undefined,
    });

    const fetchServiceInfo = () => {
        fetch("/service-info")
            .then(async (response) => {
                let responseInfo = await convertToResponseInfo(response);
                setBootingStateMap(prevState => ({
                    ...prevState,
                    serviceInfo: responseInfo,
                }));
            });
    };

    const runSessionValidation = () => {
        fetch("/oauth/me/session")
            .then(async (response) => {
                let responseInfo = await convertToResponseInfo(response);
                setBootingStateMap(prevState => ({
                    ...prevState,
                    sessionInfo: responseInfo,
                }));
            });
    }

    useEffect(() => {
        if (overallStatus === "idle") {
            setOverallStatus("init");

            fetchServiceInfo();
            runSessionValidation();

            // setInterval(() => runSessionValidation(), 60000);
        }
    });

    const appState: AppState = useMemo<AppState>(() => {
        const appState: AppState = {
            status: "init",
            inFlightTaskCount: 0,
            errorTaskCount: 0,
            completeTaskCount: 0,
            totalTaskCount: 0,
            serviceInfo: parseJsonOrNull(bootingStateMap.serviceInfo) satisfies ServiceInfo,
            sessionInfo: parseJsonOrNull(bootingStateMap.sessionInfo) satisfies SessionInfo,
            runSessionValidation: () => {
                if (bootingStateMap.sessionInfo) {
                    console.log("Run the session validation where the session info is AVAILABLE.");
                    setBootingStateMap(ps => ({
                        ...ps,
                        sessionInfo: undefined,
                    }));
                } else {
                    console.log("Run the session validation where the session info is NOT available.");
                    // NOOP
                }
                runSessionValidation();
            },
        };

        const knownStates = Object.keys(bootingStateMap)
            .map(key => {
                let response: ResponseInfo = bootingStateMap[key] as ResponseInfo;

                appState.totalTaskCount++;

                if (response === undefined) {
                    appState.inFlightTaskCount++;
                    return "idle";
                } else if (response === null) {
                    appState.inFlightTaskCount++;
                    return "init";
                } else if (response.status === 401) {
                    appState.completeTaskCount++;
                    return "authentication-required";
                } else if (response.status === 200) {
                    appState.completeTaskCount++;
                    return "ready";
                } else {
                    appState.errorTaskCount++;
                    return "error";
                }
            });

        if (knownStates.includes("error")) {
            appState.status = "error";
        } else if (knownStates.includes("authentication-required")) {
            appState.status = "authentication-required";
        } else if (knownStates.includes("init")) {
            appState.status = "init";
        } else if (knownStates.includes("idle")) {
            appState.status = "idle";
        } else {
            appState.status = "ready";
        }

        setOverallStatus(appState.status);

        return appState;
    }, [
        bootingStateMap,
    ]);

    const progress = 100.0 * (appState.completeTaskCount + appState.errorTaskCount) / appState.totalTaskCount;

    if (progress === 100) {
        if (appState.status === "error") {
            return <>
                <h1>Unable to initialize the UI at the moment.</h1>
                <p>Please check the web console.</p>
            </>
        } else {
            return <Outlet context={appState}/>;
        }
    } else {
        return <div style={{
            display: "flex",
            width: "100vw",
            height: "100vh",
            justifyContent: "center",
            alignItems: "center",
        }}>
            <LinearLoadingAnimation
                label={`Mini IDP (${Math.floor(progress)}%)`}
                size={"large"}/>
        </div>;
    }
}

export default App;
