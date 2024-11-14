import styles from "./ResourceView.module.css";

type dataType = "string" | "integer" | "float" | "boolean" | "object";

/**
 * JSON Schema (custom)
 */
type Schema = {
    title?: string;
    label?: string;
    type?: dataType;
    required?: boolean;
    items?: Schema;
    ///// Custom properties /////
    readOnly?: boolean;
    ///// For sensitive information, e.g. password /////
    sensitive?: boolean;
    requireRepeat?: boolean;
    ///// For custom rendering /////
    render?: (schema: Schema, data: any) => any;
};

type Data = {
    [k: string]: any,
};

const FieldInput = ({schema, data}: {schema: Schema, data: any}) => {
    if (schema.render) {
        return schema.render(schema, data);
    }

    const fieldLabel = <label htmlFor={schema.title}>{schema.label || schema.title}</label>
    const props = {
        disabled: schema.readOnly,
    }

    if (schema.type === "boolean") {
        return (
            <>
                <input id={schema.title} {...props} type="checkbox" checked={data || false}/>
                {fieldLabel}
            </>
        );
    } else {
        return (
            <>
                {fieldLabel}
                <input id={schema.title} {...props} type="text" value={data}/>
            </>
        );
    }
}

type ResourceProp = {
    fields: Schema[];
    data?: Data;
    initialMode?: "reader" | "editor";
    readOnly?: boolean;
}

export const ResourceView = ({fields, data}: ResourceProp) => {
    return (
        <form>
            {fields.map(f => (
                <div key={f.title} className={styles.controllers}>
                    {f.render ? f.render(f, data) : <FieldInput schema={f} data={data !== undefined ? data[f.title as string] : undefined}/>}
                </div>
            ))}
            <div className={styles.actions}>
                <button type={"submit"}>{data ? "Save" : "Create"}</button>
                <button type={"reset"}>Cancel</button>
            </div>
        </form>
    );
}