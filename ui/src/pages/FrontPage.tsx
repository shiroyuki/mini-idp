import {AppState} from "../common/app-state";
import {useOutletContext} from "react-router-dom";
import UIFoundation from "../components/UIFoundation";
import {Navigation, UIFoundationHeader} from "../components/UIFoundationHeader";
import styles from './FrontPage.module.css';

export const FrontPage = () => {
    const appState: AppState = useOutletContext<AppState>();
    const waypoints: Navigation[] = [
        {label: "Welcome"},
    ];

    return (
        <UIFoundation>
            <UIFoundationHeader
                navigation={waypoints}
            />
            <p className="hero-text">Welcome to Mini IDP, a simple open-source identity provider service.</p>
            <p>When you are ready, you can start by selecting the menu from the left.</p>
        </UIFoundation>
    );
};