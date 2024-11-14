import AppLogo from "./AppLogo";
import styles from "./UIFoundation.module.css";
import {ReactNode} from "react";

export default ({children}: {children: ReactNode}) => {
    return (
        <article className={styles.scaffold}>
            <div className={styles.scaffoldController}>
                <header><AppLogo/></header>
                <h3>Personal Settings</h3>
                <nav>
                    <a className={styles.active}>Profile</a>
                    <a>Security</a>
                </nav>
                <h3>Identity and Access Management</h3>
                <nav>
                    <a>User</a>
                    <a>Roles</a>
                    <a>Scopes</a>
                    <a>API Clients</a>
                    <a>Policy</a>
                </nav>
            </div>
            <div className={styles.scaffoldBody}>
                {children}
            </div>
        </article>
    );
}