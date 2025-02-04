import styles from './AppLogo.module.css';
import {useOutletContext} from "react-router-dom";
import {AppState} from "../common/app-state";

export default () => {
    const appState = useOutletContext<AppState>();
    return (
        <div className={styles.appLogo}>
            <div className={styles.appName}>Mini IDP</div>

            <div className={styles.appVersion}>
                <span></span>
                {
                    appState
                        ? <span>{appState.serviceInfo.release.version}</span>
                        : <span>(x x)</span>
                }
            </div>
        </div>
    );
};