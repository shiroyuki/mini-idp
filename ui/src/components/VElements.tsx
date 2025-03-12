import styles from './VElements.module.css';
import Icon from "./Icon";
import {useCallback, useMemo} from "react";
import classNames from "classnames";

type VCheckboxProps = {
    checked: boolean | "indeterminate";
    value?: any;
    style?: React.CSSProperties;
    disabled?: boolean;
    onClick: (value: any, checked: boolean) => void;
    onKeyUp: (value: any, checked: boolean) => void;
}

export const VCheckbox = ({checked, value, disabled, style, onClick, onKeyUp}: VCheckboxProps) => {
    const interactable = useMemo(() => !disabled, [disabled]);
    const iconName = useMemo(
        () => checked === "indeterminate"
            ? "indeterminate_check_box"
            : (checked ? "check_box" : "check_box_outline_blank"),
        [checked]
    );
    const checkingStyleClass = useMemo(
        () => checked === "indeterminate"
            ? styles.vCheckboxIntermediate
            : (checked ? styles.vCheckboxYes : styles.vCheckboxNo),
        [checked]
    );
    const cssClasses = useMemo(
        () => [
            styles.vCheckbox,
            checkingStyleClass,
            (interactable) ? null : styles.vCheckboxDisabled,
        ]
            .filter(c => c !== null),
        [interactable, checkingStyleClass]
    );

    // @ts-ignore
    const toggleWithClick = useCallback((e) => {
        e.preventDefault();
        e.stopPropagation();
        const nextChecked = checked === "indeterminate" ? true : !checked;
        onClick(value, nextChecked);
    }, [onClick, value, checked]);

    // @ts-ignore
    const toggleWithKeyboard = useCallback((e) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.keyCode === 32) {
            const nextChecked = checked === "indeterminate" ? true : !checked;
            onKeyUp(value, nextChecked);
        }
    }, [onKeyUp, value, checked])

    if (interactable) {
        return (
            <a href={"#"}
               className={classNames(cssClasses)}
               style={style}
               onClick={toggleWithClick}
               onKeyUp={toggleWithKeyboard}>
                <Icon name={iconName}/>
            </a>
        );
    } else {
        return (
            <span className={classNames(cssClasses)}
                  style={style}>
                <Icon name={iconName}/>
            </span>
        );
    }
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