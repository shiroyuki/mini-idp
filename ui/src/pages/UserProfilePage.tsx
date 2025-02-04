import {AppState} from "../common/app-state";
import {useLocation, useNavigate, useOutletContext} from "react-router-dom";
import UIFoundation from "../components/UIFoundation";
import {useEffect} from "react";
import {UserProfile} from "../components/UserProfile";

export const UserProfilePage = () => {
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
        <UIFoundation>
            <UserProfile />
        </UIFoundation>
    );
};