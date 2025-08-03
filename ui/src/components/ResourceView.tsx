import styles from "./ResourceView.module.css";
import React, {CSSProperties, useCallback} from "react";
import {LinearLoadingAnimation} from "./loaders";
import {ErrorFeedback, GenericModel} from "../common/definitions";
import {ResourceSchema} from "../common/json-schema-definitions";
import {FinalValidationResult, isFinalValidationResultOk} from "../common/validation";
import {ResourceFieldControl} from "./ResourceFieldControl";

export type ResourceViewMode = "read-only" | "reader" | "editor" | "writing" | "creator";

type ResourceProp = {
    data?: GenericModel;
    schema: ResourceSchema;
    style?: CSSProperties;
    initialMode?: ResourceViewMode;
    finalValidationResult?: FinalValidationResult | null; // If this is null or undefined, it is considered "valid".
    isDirty?: () => boolean;
    switchToMode: (mode: ResourceViewMode) => void;
    onCancel?: () => void;
    onSubmit?: () => Promise<ErrorFeedback[]>;
    onUpdate?: (key: string, value: any) => any;
}

/**
 * Resource View
 *
 * This represents ONE resource in both read-only and the edit mode.
 */
export const ResourceView = ({
                                 schema,
                                 data,
                                 style,
                                 initialMode,
                                 finalValidationResult,
                                 isDirty,
                                 switchToMode,
                                 onUpdate,
                                 onCancel,
                                 onSubmit
                             }: ResourceProp) => {

    if (onUpdate && !onCancel) {
        console.warn("The event listener for cancelling the editor mode SHOULD be defined");
    }

    const submitFormData = useCallback(
        async () => {
            if (onSubmit) {
                switchToMode("writing");
                const errors: ErrorFeedback[] = (await onSubmit()) || [];
                if (errors.length === 0) {
                    switchToMode("reader");
                } else {
                    switchToMode("editor");
                    // TODO: Implement the form error feedback.
                    console.log(errors);
                }
            }
        },
        [onSubmit, switchToMode]
    )

    const handleFormSubmission = useCallback(
        // @ts-ignore
        async (e) => {
            e.preventDefault();
            e.stopPropagation();
            if (isFinalValidationResultOk(finalValidationResult)) {
                console.log("A");
                await submitFormData();
            } else {
                console.warn("Form submission blocked due to", finalValidationResult);
            }
        },
        [submitFormData, finalValidationResult]
    );

    // @ts-ignore
    const startEditing = useCallback((e) => {
        e.preventDefault();
        e.stopPropagation();
        switchToMode("editor");
    }, [switchToMode]);

    const abortEditing = useCallback(() => {
        const cleanCancellation = isDirty && !isDirty();

        if (initialMode === "creator") {
            if (confirm("Are you sure you want to discard all changes?")) {
                if (onCancel) onCancel();
                else alert("The cancellation of creation is not implemented.");
            }
        } else {
            if (cleanCancellation || confirm("Are you sure you want to discard all changes?")) {
                switchToMode("reader");
                if (onCancel) onCancel();
            }
        }
    }, [onCancel, switchToMode, isDirty, initialMode]);

    const inWritingMode = initialMode === "editor" || initialMode === "creator";
    const showActions = (initialMode === "reader" || inWritingMode) && onUpdate !== undefined;
    const cancelLabel = (isDirty && isDirty()) ? "Discard changes" : "Stop editing";

    if (initialMode === "writing") {
        return <LinearLoadingAnimation label={"Please wait..."}/>;
    }

    return (
        <form className={styles.resourceForm} style={style} onSubmit={handleFormSubmission} autoComplete="off">
            <div className={styles.controllers}>
                {
                    Object.entries(schema.properties as { [key: string]: ResourceSchema })
                        .filter(([_, f]) => {
                            if (f.autoGenerationCapability === "full:post" || f.autoGenerationCapability === "full:pre") {
                                return false; // the fully generated field will not be editable.
                            } else if (initialMode === "creator") {
                                return true; // show all fields
                            } else return !f.hidden;
                        })
                        .map(([fn, f]) => (
                            <ResourceFieldControl
                                key={fn}
                                schema={f}
                                data={(data !== undefined && data !== null) ? data[fn] : undefined}
                                onUpdate={inWritingMode ? onUpdate : undefined}
                            />
                        ))
                }
            </div>
            {
                showActions && (
                    <div className={styles.actions}>
                        {
                            initialMode === "reader"
                                ? (
                                    <>
                                        <button type={"button"} onClick={startEditing}>Edit</button>
                                    </>
                                )
                                : (
                                    <>
                                        <button type={"submit"}>
                                            {initialMode === "editor" ? "Save" : "Create"}
                                        </button>
                                        <button type={"reset"}
                                                onClick={abortEditing}
                                                title={cancelLabel}>
                                            {initialMode === "editor" ? cancelLabel : "Cancel"}
                                        </button>
                                    </>
                                )
                        }
                    </div>
                )
            }
        </form>
    );
}