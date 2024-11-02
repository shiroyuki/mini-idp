import {LinearLoadingAnimation} from "../components/loaders";
import {AppState} from "../common/app-state";
import {useNavigate, useOutletContext} from "react-router-dom";
import Scaffold from "../components/UIFoundation";
import Icon from "../components/Icon";
import {useEffect} from "react";

export const MainDashboardPage = () => {
    const appState: AppState = useOutletContext<AppState>();
    const navigate = useNavigate();

    if (appState.status === "authentication-required") {
        return navigate("/login");
    }

    useEffect(() => {
        fetch(
            '/rpc/iam/self/profile',
            {
                method: "get",
                headers: {
                    Authorization: `Bearer ${sessionStorage.getItem("access_token")}`,
                },
            }
        ).then(async (response) => {
            console.log(await response.json());
        });
    }, [appState.status]);

    return (
        <Scaffold>
            <h1><Icon name="face"/> {appState.sessionInfo.name}</h1>
            <dl>
                <dt>Username</dt>
                <dd>Username</dd>
            </dl>
        </Scaffold>
    );
};