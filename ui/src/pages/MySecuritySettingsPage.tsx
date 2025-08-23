import UIFoundation from "../components/UIFoundation";
import {Navigation, UIFoundationHeader} from "../components/UIFoundationHeader";
import {useSessionData} from "../components/sharedHooks";
import styles from "./MySecuritySettingsPage.module.css"

export const MySecuritySettingsPage = () => {
    const sessionData = useSessionData();
    const waypoints: Navigation[] = [
        {label: "My Account"},
        {label: "Security Settings"},
    ];

    return (
        <UIFoundation>
            <UIFoundationHeader navigation={waypoints}/>
            <div className={styles.passwordChangingSection}>
                <form onSubmit={(e) => {
                    console.log('Received');
                    e.preventDefault()
                }}>
                    <h2>Change the password</h2>
                    <div className={"field"}>
                        <label htmlFor="current">Current Password</label>
                        <input id="current" name="current" type={"password"}/>
                    </div>
                    <div className={"field"}>
                        <label htmlFor="updated_1">New Password</label>
                        <input id="updated_1" name="updated_1" type={"password"}/>
                    </div>
                    <div className={"field"}>
                        <label htmlFor="updated_2">Repeat the new password</label>
                        <input id="updated_2" name="updated_2" type={"password"}/>
                    </div>
                    <div className={"actions"}>
                        <button type={"submit"}>Update</button>
                    </div>
                </form>
            </div>
        </UIFoundation>
    );
}