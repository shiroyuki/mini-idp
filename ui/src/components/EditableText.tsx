import {ReactNode, useState} from "react";
import classNames from "classnames";
import styles from "./Editable.module.css";
import Icon from "./Icon";

interface Props {
    mode: "inline" | "block";
    value: string | number | readonly string[] | undefined;
    readOnly?: boolean;
    classes?: string[];
    children?: ReactNode;
}

export default ({mode, value, classes, children}: Props) => {
    const activeClasses = [
        styles.editableText,
        mode === "inline" ? styles.inlineEditableText : styles.blockEditableText,
        ...(classes ?? [])
    ];
    const [newValue, setNewValue] = useState<string | number | readonly string[] | undefined>(value);
    const [isEditing, enableEditing] = useState<boolean>(false);

    return (
        <div className={classNames(activeClasses)}>
            {
                isEditing
                    ? (
                        children ?? (
                            <form className={styles.editableForm} onSubmit={(e) => e.preventDefault()}>
                                <input type="text" value={newValue} onChange={(e) => setNewValue(e.currentTarget.value)}/>
                                <div className={styles.editableFormActions}>
                                    <button type="submit" title="Edit"><Icon name="check" /></button>
                                    <button type="reset" title="Cancel" onClick={() => {
                                        setNewValue(value ?? "");
                                        enableEditing(false);
                                    }}><Icon name="close" /></button>
                                </div>
                            </form>
                        )
                    )
                    : (
                        <>
                            <div className={styles.editableTextValue}>
                                {newValue}
                            </div>
                            <button style={{fontSize: "12px"}} onClick={() => enableEditing(prev => !prev)}>Edit</button>
                        </>
                    )
            }
        </div>
    );
}