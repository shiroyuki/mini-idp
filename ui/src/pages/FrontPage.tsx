import {AppState} from "../common/app-state";
import {useNavigate, useOutletContext} from "react-router-dom";
import UIFoundation from "../components/UIFoundation";

export const FrontPage = () => {
    const appState: AppState = useOutletContext<AppState>();
    const navigate = useNavigate();

    if (appState.status === "authentication-required") {
        return navigate("/login");
    } else {
        return navigate("/users");
    }
};