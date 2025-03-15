import {Navigation, UIFoundationHeader} from "../components/UIFoundationHeader";
import UIFoundation from "../components/UIFoundation";
import {AppState} from "../common/app-state";
import {useOutletContext} from "react-router-dom";
import {SoloResource} from "./ResourceManagerPage";
import {IAM_USER_SCHEMA} from "../common/resource-schema";

export const MyProfilePage = () => {
    const appState: AppState = useOutletContext<AppState>();
    const waypoints: Navigation[] = [
        {label: "My Account"},
        {label: "Profile"},
    ];

    return (
        <UIFoundation>
            <UIFoundationHeader
                navigation={waypoints}
            />
            <SoloResource
                id={appState.sessionInfo?.id}
                baseBackendUri={"/rest/users"}
                schema={IAM_USER_SCHEMA}
                getPermissions={() => ["read", "write"]}
            />
        </UIFoundation>
    );
}