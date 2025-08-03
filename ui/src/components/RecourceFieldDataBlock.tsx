import React, {useCallback} from "react";
import styles from "./ResourceView.module.css";

type DataBlockProps = {
    data: any;
    href?: string;
    onClick?: (data: any) => void;
}
export const RecourceFieldDataBlock = ({data, href, onClick}: DataBlockProps) => {
    if (data === undefined || data === null) {
        return <div className={"value-placeholder"}>null</div>;
    }

    // TODO Instead of guessing the data type, request for the schema.
    const dataType = typeof data;
    let renderedValue: any;

    // @ts-ignore
    const handleClickOnContent = useCallback((e) => {
        e.preventDefault();
        e.stopPropagation();

        if (onClick) {
            onClick(data);
        }
    }, [onClick]);

    if (dataType === "object") {
        // TODO Currently, this part only handles one level-depth object.
        return (
            <table className={styles.dataBlockObject}>
                <tbody>
                {
                    Object.keys(data)
                        .map((key: string) => {
                            return (
                                <tr key={key}>
                                    <th>{key}</th>
                                    <td><RecourceFieldDataBlock data={data[key]} onClick={onClick}/></td>
                                </tr>
                            )
                        })
                }
                </tbody>
            </table>
        )
    } else {
        switch (dataType) {
            case "string":
            case "number":
                renderedValue = data;
                break;
            case "boolean":
                renderedValue = data ? "✅ true" : "❌ false";
                break;
            default:
                throw new Error(`Unknown data type of ${dataType}`);
        }

        if (onClick) {
            return (
                <a className={styles.dataBlockReferenceLink}
                   href={href}
                   onClick={handleClickOnContent}>{renderedValue}</a>
            );
        } else {
            return renderedValue;
        }
    }
}