import {IAM_SCOPE_SCHEMA} from "../common/resource-schema";
import {IAMScope} from "../common/models";
import {ResourceManagerPage} from "./ResourceManagerPage";
import React from "react";
import {GenericModel} from "../common/definitions";

export const ScopeManagementPage = () => {
    return (
        <ResourceManagerPage
            baseBackendUri={"/rest/scopes"}
            baseFrontendUri={"/scopes"}
            schema={IAM_SCOPE_SCHEMA}
            listPage={
                {
                    title: "Scopes",
                    assertResourceIsReadOnly: (item: GenericModel) => {
                        return (item as IAMScope).fixed || false;
                    }
                }
            }
        />
    );
}