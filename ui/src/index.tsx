import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import reportWebVitals from './reportWebVitals';
import {createHashRouter, RouterProvider} from 'react-router-dom';
import LoginComponent from "./components/LoginComponent";
import UIFoundation from "./components/UIFoundation";
import {PerResourcePermission, PerResourcePermissionFetcher, ResourceManagerPage} from "./pages/ResourceManagerPage";
import {IAM_ROLE_SCHEMA, IAM_SCOPE_SCHEMA, IAM_USER_SCHEMA} from "./common/resource-schema";
import {FrontPage} from "./pages/FrontPage";
import {MyProfilePage} from "./pages/SettingsPage";
import {GenericModel, IAMPolicy, IAMRole, IAMScope, IAMUser} from "./common/models";
import {storage} from "./common/storage";

const getPermissionPerPolicy: PerResourcePermissionFetcher = (item: GenericModel) => {
    // TODO Check if the roles also permit.
    return !((item as IAMPolicy).fixed || false)
        ? ["read", "write", "delete"]
        : [];
}
const getPermissionPerRole: PerResourcePermissionFetcher = (item: GenericModel) => {
    // TODO Check if the roles also permit.
    return !((item as IAMRole).fixed || false)
        ? ["read", "write", "delete"]
        : [];
}
const getPermissionPerScope: PerResourcePermissionFetcher = (item: GenericModel) => {
    // TODO Check if the roles also permit.
    return !((item as IAMScope).fixed || false)
        ? ["read", "write", "delete"]
        : [];
}
const getPermissionPerUser: PerResourcePermissionFetcher = (item: GenericModel) => {
    const user = item as IAMUser;
    const accessToken = storage.get("access_token");
    const encodedClaims = accessToken.split(".")[1];
    const claims = JSON.parse(atob(encodedClaims)) as {sub: string};

    const currentUserId = claims.sub;

    const permissions: PerResourcePermission[] = ["read"];

    if (true /* TODO replace with the role check */) {
        permissions.push("write");
    }

    if (currentUserId !== user.id /* TODO or the roles permit */) {
        permissions.push("delete");
    }

    return permissions;
}

function makeUserManagerPage() {
    return <ResourceManagerPage
        baseBackendUri={"/rest/users"}
        baseFrontendUri={"/users"}
        schema={IAM_USER_SCHEMA}
        listPage={
            {
                title: "Users",
            }
        }
        getPermissions={getPermissionPerUser}
    />;
}

function makeRoleManagerPage() {
    return <ResourceManagerPage
        baseBackendUri={"/rest/roles"}
        baseFrontendUri={"/roles"}
        schema={IAM_ROLE_SCHEMA}
        listPage={
            {
                title: "Roles",
            }
        }
        getPermissions={getPermissionPerRole}
    />;
}

function makeScopeManagerPage() {
    return <ResourceManagerPage
        baseBackendUri={"/rest/scopes"}
        baseFrontendUri={"/scopes"}
        schema={IAM_SCOPE_SCHEMA}
        listPage={
            {
                title: "Scopes",
            }
        }
        getPermissions={getPermissionPerScope}
    />;
}

const router = createHashRouter([
    {
        path: '/',
        element: <App/>,
        errorElement: (
            <UIFoundation>
                <h1 style={{textTransform: "uppercase", fontSize: "2rem", paddingTop: "24px"}}>Not available</h1>
                <p style={{margin: "1rem 0"}}>
                    If you think this is our mistake, please file an issue on <a
                    href="https://github.com/shiroyuki/mini-idp/issues">GitHub</a>.
                </p>
            </UIFoundation>
        ),
        children: [
            {
                path: 'login',
                element: <LoginComponent/>,
            },
            {
                path: 'users',
                // @ts-ignore
                element: makeUserManagerPage(),
                children: [
                    {
                        path: ":id",
                        element: makeUserManagerPage(),

                    }
                ]
            },
            {
                path: 'roles',
                // @ts-ignore
                element: makeRoleManagerPage(),
                children: [
                    {
                        path: ":id",
                        element: makeRoleManagerPage(),
                    }
                ]
            },
            {
                path: 'scopes',
                // @ts-ignore
                element: makeScopeManagerPage(),
                children: [
                    {
                        path: ":id",
                        element: makeScopeManagerPage(),
                    }
                ]
            },
            {
                path: 'account/profile',
                // @ts-ignore
                element: <MyProfilePage/>,
            },
            {
                path: '',
                // @ts-ignore
                element: <FrontPage/>,
            },
        ]
    },
])

const root = ReactDOM.createRoot(
    document.getElementById('root') as HTMLElement
);

root.render(
    <React.StrictMode>
        <RouterProvider router={router}/>
    </React.StrictMode>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
