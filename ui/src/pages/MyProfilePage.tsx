import {Navigation, UIFoundationHeader} from "../components/UIFoundationHeader";
import UIFoundation from "../components/UIFoundation";
import {AppState} from "../common/app-state";
import {useOutletContext} from "react-router-dom";
import {SoloResource} from "./ResourceManagerPage";
import {IAM_USER_SCHEMA} from "../common/resource-schema";
import {useSessionData} from "../components/sharedHooks";
import {LinearLoadingAnimation} from "../components/loaders";

export const MyProfilePage = () => {
    const appState: AppState = useOutletContext<AppState>();
    const sessionData = useSessionData();
    const waypoints: Navigation[] = [
        {label: "My Account"},
        {label: "Profile"},
    ];

    if (!sessionData) {
        return <LinearLoadingAnimation label={"Loading..."}/>;
    }

    return (
        <UIFoundation>
            <UIFoundationHeader
                navigation={waypoints}
            />
            <SoloResource
                id={sessionData.id}
                baseBackendUri={"/rest/iam/users"}
                schema={IAM_USER_SCHEMA}
                getPermissions={() => ["read", "write"]}
            />
        </UIFoundation>
    );
}