import {IAM_SCOPE_SCHEMA} from "../common/resource-schema";
import {GenericModel, IAMScope} from "../common/models";
import {ResourceManagerPage} from "./ResourceManagerPage";
import React from "react";

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