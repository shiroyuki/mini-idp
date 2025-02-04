import AppLogo from "./AppLogo";
import styles from "./UIFoundation.module.css";
import {ReactNode, useEffect, useState} from "react";
import {Link, useLocation, useNavigation} from "react-router-dom";
import classNames from "classnames";

type NavigationItem = {
    label: string;
    path: string;
    exactMatch?: boolean;
}

const LinkTo = (label: string, path: string, exactMatch?: boolean) => {
    const location = useLocation();
    const requestPath = location.pathname;
    const cssClasses: string[] = [];

    if ((exactMatch && requestPath === path) || (!exactMatch && requestPath.startsWith(path))) {
        cssClasses.push(styles.active);
    }

    return <Link to={path} className={classNames(cssClasses)}>{label}</Link>
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
    return (
        <article className={styles.scaffold}>
            <div className={styles.scaffoldController}>
                <header><AppLogo/></header>
                <h3>Personal Settings</h3>
                <nav>
                    {
                        [
                            {label: "Profile", path: "/", exactMatch: true},
                            {label: "Security", path: "/my-security"},
                        ].map(item => NavigationItem(item))
                    }
                </nav>
                <h3>Identity and Access Management</h3>
                <nav>
                    {
                        [
                            {label: "Users", path: "/users"},
                            {label: "Roles", path: "/roles"},
                            {label: "Scopes", path: "/scopes"},
                            {label: "API Clients", path: "/clients"},
                            {label: "Policies", path: "/policies"},
                        ].map(item => NavigationItem(item))
                    }
                </nav>
            </div>
            <div className={styles.scaffoldBody}>
                {children}
            </div>
        </article>
    );
}