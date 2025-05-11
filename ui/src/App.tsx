import {Outlet, useLocation, useNavigate} from 'react-router-dom';
import './App.scss';
import {useCallback, useEffect, useState} from "react";
import {AppState, BootingState, convertToResponseInfo, ResponseInfo} from "./common/app-state";
import {LinearLoadingAnimation} from "./components/loaders";
import {ejectToLoginScreen} from "./common/helpers";
import {useComputed} from "@headlessui/react/dist/hooks/use-computed";

const FEATURE_PERIODIC_SESSION_CHECK = false;

function parseJsonOrNull(responseInfo?: ResponseInfo | null) {
    return responseInfo ? JSON.parse(responseInfo.body) : null;
}

const fetchServiceInfo = () => {
    return fetch("/service-info")
        .then(async (response) => {
            return await convertToResponseInfo(response);
        });
};

const runSessionValidation = () => {
    return fetch("/oauth/me/session")
        .then(
            async (response) => {
                return await convertToResponseInfo(response);
            }
        );
}

function App() {
    const navigate = useNavigate();
    const location = useLocation();
    const currentRoute = location.pathname;
    const [periodicSessionVerificationTaskRef, setPeriodicSessionVerificationTaskRef] = useState<any>(null); // TODO replace with useRef.
    const [currentAppState, setCurrentAppState] = useState<AppState>({
        status: "idle",
        inFlightTaskCount: 0,
        errorTaskCount: 0,
        completeTaskCount: 0,
        totalTaskCount: 0,
        clearSession: () => {
            setCurrentAppState(prevState => {
                return {
                    ...prevState,
                    status: "idle",
                    inFlightTaskCount: 0,
                    errorTaskCount: 0,
                    completeTaskCount: 0,
                    totalTaskCount: 0,
                    sessionInfo: undefined,
                }
            })
        }
    });

    // Note: Not using the callback hook due to recursion.
    const verifySession = (runningPlan: "on-startup" | "periodic" | "manual") => {
        fetch("/oauth/me/session")
            .then(pingResponse => {
                convertToResponseInfo(pingResponse)
                    .then(response => {
                        const responseOk = response.status === 200
                        const updatedContent = parseJsonOrNull(response);
                        let newStatus: BootingState = "init";

                        if (responseOk) {
                            newStatus = "ready";
                        } else if (response.status === 401) {
                            if (currentAppState.status !== "login-required") {
                                newStatus = "login-required";

                                if (currentRoute !== '/login') {
                                    navigate('/login');
                                }
                            }
                        } else {
                            newStatus = "error";
                        }

                        setCurrentAppState(prevState => {
                            const newState: AppState = {
                                ...prevState,
                                status: newStatus,
                                sessionInfo: updatedContent,
                                runSessionValidation: () => verifySession("manual"),
                            };

                            if (runningPlan === "on-startup") {
                                newState.inFlightTaskCount = prevState.inFlightTaskCount - 1;
                                newState.errorTaskCount = prevState.errorTaskCount + (responseOk ? 0 : 1);
                                newState.completeTaskCount = prevState.completeTaskCount + (responseOk ? 1 : 0);
                            }

                            return newState;
                        });

                        return newStatus;
                    })
                    .then(newStatus => {
                        if (newStatus === "ready") {
                            if (periodicSessionVerificationTaskRef === null) {
                                if (FEATURE_PERIODIC_SESSION_CHECK) {
                                    setPeriodicSessionVerificationTaskRef(setInterval(() => verifySession("periodic"), 60000));
                                } else {
                                    console.warn("Periodic session verification: DRY-RUN: Presumably ACTIVATED");
                                    setPeriodicSessionVerificationTaskRef("faux-periodic-task-id");
                                }
                            } else {
                                // For debugging only
                                if (!FEATURE_PERIODIC_SESSION_CHECK) {
                                    console.warn("Periodic session verification: DRY-RUN: Already activated");
                                }
                            }
                        } else {
                            if (periodicSessionVerificationTaskRef === null) {
                                // For debugging only
                                if (!FEATURE_PERIODIC_SESSION_CHECK) {
                                    console.warn("Periodic session verification: DRY-RUN: Already deactivated");
                                }
                            } else {
                                if (!FEATURE_PERIODIC_SESSION_CHECK) {
                                    console.warn("Periodic session verification: DRY-RUN: Presumably DEACTIVATED");
                                } else {
                                    clearInterval(periodicSessionVerificationTaskRef);
                                }
                                setPeriodicSessionVerificationTaskRef(null);
                            }
                        }
                    });
            });
    };

    const getUpdatedServiceInfo = useCallback(() => {
        fetchServiceInfo()
            .then(response => {
                const responseOk = response.status === 200
                const updatedContent = parseJsonOrNull(response);

                setCurrentAppState(prevState => {
                    return {
                        ...prevState,
                        inFlightTaskCount: prevState.inFlightTaskCount - 1,
                        errorTaskCount: prevState.errorTaskCount + (responseOk ? 0 : 1),
                        completeTaskCount: prevState.completeTaskCount + (responseOk ? 1 : 0),
                        serviceInfo: updatedContent,
                    }
                });
            });
    }, []);

    useEffect(() => {
        if (currentAppState.status === "idle") {
            setCurrentAppState(prevState => {
                return {
                    ...prevState,
                    status: "init",
                    inFlightTaskCount: 2,
                    totalTaskCount: 2,
                }
            });

            getUpdatedServiceInfo();

            verifySession("on-startup");
        }
    });

    const progress = 100.0 * (currentAppState.completeTaskCount + currentAppState.errorTaskCount) / currentAppState.totalTaskCount;

    if (progress === 100) {
        if (currentAppState.status === "error") {
            return <>
                <h1>Unable to initialize the UI at the moment.</h1>
                <p>Please check the web console.</p>
            </>
        } else {
            return <Outlet context={currentAppState}/>;
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
