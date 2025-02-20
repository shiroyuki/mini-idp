import styles from './UIFoundationHeader.module.css';
import {Link} from "react-router-dom";
import classNames from "classnames";

export type Navigation = {
    label: string;
    path?: string;
    onClick?: () => void;
}

type Options = {
    navigation: Navigation[];
}

export const UIFoundationHeader = ({navigation}: Options) => {
    if (navigation.length === 0) {
        throw new Error('The navigation list is empty');
    }

    const otherWaypoints = navigation.slice(0, navigation.length - 1);
    const currentWaypoint = navigation[navigation.length - 1];

    return (
        <div className={styles.foundationHeader}>
            {
                otherWaypoints.length > 0 && (
                    <ol className={styles.navigationBar}>
                        {
                            otherWaypoints.map((waypoint, index) => (
                                <li key={index} className={classNames([styles.navigationItem, (waypoint.path || waypoint.onClick) ? styles.navigatable : styles.unnavigatable ])}>
                                    {
                                        waypoint.onClick
                                            ? <a onClick={waypoint.onClick}>{waypoint.label}</a>
                                            : (
                                                waypoint.path
                                                    ? <Link to={waypoint.path}>{waypoint.label}</Link>
                                                    : <span>{waypoint.label}</span>
                                            )
                                    }
                                </li>
                            ))
                        }
                    </ol>
                )
            }
            <h1>{currentWaypoint.label}</h1>
        </div>
    );
}