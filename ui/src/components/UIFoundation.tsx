import AppLogo from "./AppLogo";
import styles from "./UIFoundation.module.css";
import {ReactNode, useCallback, useEffect, useMemo, useState} from "react";
import {Link, useLocation, useNavigate, useNavigation, useOutletContext} from "react-router-dom";
import classNames from "classnames";
import { http } from "../common/http-client";
import {LinearLoadingAnimation} from "./loaders";
import {AppState} from "../common/app-state";
import {storage} from "../common/storage";

type NavigationItem = {
    label: string;
    path: string;
    exactMatch?: boolean;
}
const NavigationItem = (nav: NavigationItem) => {
    const location = useLocation();
    const requestPath = location.pathname;
    const cssClasses: string[] = [];

    if ((nav.exactMatch && requestPath === nav.path) || (!nav.exactMatch && requestPath.startsWith(nav.path))) {
        cssClasses.push(styles.active);
    }

    return <Link key={nav.path} to={nav.path} className={classNames(cssClasses)}>{nav.label}</Link>
}

export default ({children}: { children: ReactNode }) => {
    const navigate = useNavigate();
    const appState = useOutletContext<AppState>();
    const [interruptionMessage, setInterruptionMessage] = useState<string|null>(null);
    const signOut = useCallback(
        () => {
            setInterruptionMessage("Signing out...");

            http.send("get", "/oauth/logout")
                .then(() => {
                    storage.remove("access_token"); // FIXME with Token
                    storage.remove("refresh_token"); // FIXME with Token
                    setInterruptionMessage(null);
                    appState.clearSession();
                    navigate("/login");
                })
        },
        [appState, navigate]
    );

    if (interruptionMessage !== null) {
        return <LinearLoadingAnimation label={interruptionMessage} />
    }

    const waypointGroups = useMemo(() => {
        return [
            {
                title: "Identity and Access Management",
                waypoints: [
                    {label: "Users", path: "/users"},
                    {label: "Roles", path: "/roles"},
                    {label: "Scopes", path: "/scopes"},
                    {label: "API Clients", path: "/clients"},
                    {label: "Policies", path: "/policies"},
                ]
            },
            {
                title: "My Account",
                waypoints: [
                    {label: "Profile", path: `/account/profile`, exactMatch: true},
                    {label: "Security Settings", path: "/account/security"},
                ]
            },
        ];
    }, [])

    return (
        <article className={styles.scaffold}>
            <div className={styles.foundationNavigation}>
                <header><AppLogo/></header>
                {
                    waypointGroups
                        .map(waypointGroup => (
                            <>
                                <h3>{waypointGroup.title}</h3>
                                <nav aria-label="nav">
                                    {waypointGroup.waypoints.map(waypoint => NavigationItem(waypoint))}
                                </nav>
                            </>
                        ))
                }
                <div style={{flex: 1}}></div>
                <nav>
                    <a onClick={signOut} className={styles.signOutButton}>Sign out</a>
                </nav>
            </div>
            <div className={styles.foundationMain}>
                {children}
            </div>
        </article>
    );
}