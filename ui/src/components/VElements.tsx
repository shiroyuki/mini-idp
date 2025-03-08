import styles from './VElements.module.css';
import Icon from "./Icon";
import {MouseEventHandler, useCallback, useMemo, useState} from "react";
import classNames from "classnames";

type VCheckboxProps = {
    checked: boolean | "indeterminate";
    value?: any;
    style?: React.CSSProperties;
    onClick: (value: any, checked: boolean) => void;
    onKeyUp: (value: any, checked: boolean) => void;
}

export const VCheckbox = ({checked, value, style, onClick, onKeyUp}: VCheckboxProps) => {
    const [inFlight, setInFlight] = useState(false);

    const cssClasses = useMemo(
        () => [styles.vCheckbox, inFlight ? styles.vCheckboxInFlight : null]
            .filter(c => c !== null),
        [inFlight]
    );

    // @ts-ignore
    const toggleWithClick = useCallback((e) => {
        e.preventDefault();
        e.stopPropagation();
        setInFlight(true);
        const nextChecked = checked === "indeterminate" ? true : !checked;
        onClick(value, nextChecked);
    }, [onClick, value, checked]);

    // @ts-ignore
    const toggleWithKeyboard = useCallback((e) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.keyCode === 32) {
            setInFlight(true);
            const nextChecked = checked === "indeterminate" ? true : !checked;
            onKeyUp(value, nextChecked);
        }
    }, [onKeyUp, value, checked])

    return (
        <a href={"#"}
           className={classNames(cssClasses)}
           style={style}
           onClick={toggleWithClick}
           onKeyUp={toggleWithKeyboard}>
            <Icon
                name={
                    checked === true
                        ? "check_box"
                        : (
                            checked === "indeterminate"
                                ? "indeterminate_check_box"
                                : "check_box_outline_blank"
                        )
                }
            />
        </a>
    );
}

type VSwitchProps = {
    active: boolean;
    value?: any;
    style?: React.CSSProperties;
    onClick: (value: any, checked: boolean) => void;
    onKeyUp: (value: any, checked: boolean) => void;
    label: string;
}

export const VSwitch = ({active, value, label, style, onClick, onKeyUp}: VSwitchProps) => {
    return (
        <button
            className={classNames([styles.vSwitch, active ? styles.vSwitchActive : null].filter(i => i !== null))}
        >
            <Icon name={active ? "toggle_on" : "toggle_off"}/>{label}
        </button>
    );
}