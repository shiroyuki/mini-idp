import {FormEvent, useCallback, useMemo, useState} from "react";
import style from './LoginComponent.module.css';
import Icon from "./Icon";
import {useNavigate, useOutletContext} from "react-router-dom";
import {AppState} from "../common/app-state";
import {LinearLoadingAnimation} from "./loaders";
import LargeAppLogo from "./LargeAppLogo";

interface LoginComponentProps {
}

interface Feedback {
    type: string;
    message?: string | null;
}

interface LoginComponentState {
    inFlight: boolean;
    feedback: Feedback | null;
}

interface Principle {
    id: string
    name: string
    email: string
    full_name: string | null
    roles: string[]
}

interface AuthenticationResponse {
    error?: string | null;
    error_description?: string | null;
    session_id: string | null;
    access_token: string | null;
    refresh_token: string | null;
    principle?: Principle | null;
    already_exists: boolean;
}

type FormFunctionalityType = "input" | "submission";

const LoginComponent: React.FC<LoginComponentProps> = ({}) => {
    const appState = useOutletContext<AppState>();
    const navigate = useNavigate();
    const [inFlight, setInFlight] = useState(false);
    const [feedback, setFeedback] = useState<Feedback | null>(null);
    const [formData, setFormData] = useState({username: '', password: ''});

    const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
        const {name, value} = e.target;

        setFormData((prevData) => ({
            ...prevData,
            [name]: value
        }));
    }, [formData]);

    const formFunctionalities = useMemo<FormFunctionalityType[]>(() => {
        let canSubmit = false;
        let canProvideInput = true;

        if (inFlight) {
            canSubmit = false;
            canProvideInput = false;
        } else {
            if (formData.username.trim().length > 0 && formData.password.trim().length > 0) {
                canSubmit = true;
            }
        }

        return [
            canSubmit ? "submission" : null,
            canProvideInput ? "input" : null,
        ].filter(t => t !== null) as FormFunctionalityType[];
    }, [formData, inFlight]);

    const initiateLogin = useCallback(async (e: FormEvent) => {
        e.preventDefault();
        e.stopPropagation();

        setInFlight(true);

        const postData = new FormData();
        postData.append('password', formData.password);
        postData.append('username', formData.username);

        const response = await fetch(
            '/oauth/login',
            {
                method: 'post',
                headers: {'Accept': 'application/json'},
                body: postData,
            }
        );

        const responseBody = await response.text();

        if (response.status === 200) {
            const result: AuthenticationResponse = JSON.parse(responseBody);

            if (result.error === null) {
                if (result.access_token !== null && result.access_token !== "") {
                    sessionStorage.setItem("access_token", result.access_token);
                } else {
                    sessionStorage.removeItem("access_token");
                }

                if (result.refresh_token !== null && result.refresh_token !== "") {
                    sessionStorage.setItem("refresh_token", result.refresh_token);
                } else {
                    sessionStorage.removeItem("refresh_token");
                }
            }

            appState.runSessionValidation && appState.runSessionValidation();
            navigate("/");
        } else {
            if (response.status < 500) {
                setFeedback({
                    type: "api.error",
                    message: `${response.status}: ${responseBody}`,
                });
            } else {
                setFeedback({
                    type: "connection.error",
                    message: `${response.status}: ${responseBody}`,
                });
            }
            setInFlight(false);
        }
    }, [formData, setFeedback]);

    const inFlightIndicator = <LinearLoadingAnimation label={"Authenticating..."}/>;

    return (
        <article className={style.componentContainer}>
            <div className={style.appName}>
                <LargeAppLogo/>
            </div>
            <div className={style.deploymentName}>{appState.serviceInfo?.deployment.name}</div>
            {inFlight ? inFlightIndicator : (
                <div className={style.formContainer + " form-container"}>
                    {feedback
                        ? (
                            <>
                                <h3>Unable to log in</h3>
                                <p>{feedback.type}: {feedback.message}</p>
                                <button onClick={() => {
                                    setFeedback(null);
                                }}>
                                    Try again
                                </button>
                            </>
                        ) : (
                            <form method="post"
                                  action="#"
                                  onSubmit={formFunctionalities.includes("submission") ? initiateLogin : undefined}>
                                <div className="field">
                                    <label htmlFor="username">Username or Email Address</label>
                                    <input
                                        type="text"
                                        id="username"
                                        name="username"
                                        required
                                        disabled={!formFunctionalities.includes("input")}
                                        value={formData.username}
                                        onChange={handleChange}/>
                                </div>

                                <div className="field">
                                    <label htmlFor="password">Password</label>
                                    <input
                                        type="password"
                                        id="password"
                                        name="password"
                                        required
                                        disabled={!formFunctionalities.includes("input")}
                                        value={formData.password}
                                        onChange={handleChange}/>
                                </div>

                                <div className="actions">
                                    <button type="submit"
                                            disabled={!formFunctionalities.includes("submission")}>
                                        Sign in
                                    </button>
                                </div>
                            </form>
                        )
                    }

                </div>
            )}
        </article>
    )
}

export default LoginComponent;