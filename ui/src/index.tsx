import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import reportWebVitals from './reportWebVitals';
import {createHashRouter, RouterProvider} from 'react-router-dom';
import LoginComponent from "./components/LoginComponent";
import UIFoundation from "./components/UIFoundation";
import {ResourceManagerPage} from "./pages/ResourceManagerPage";
import {IAM_USER_SCHEMA} from "./common/resource-schema";
import {FrontPage} from "./pages/FrontPage";
import {MyProfilePage} from "./pages/SettingsPage";

const userManagerPage = (
    <ResourceManagerPage
        baseBackendUri={"/rest/users"}
        baseFrontendUri={"/users"}
        schema={IAM_USER_SCHEMA}
        listPage={{title: "Users"}}
    />
);

const router = createHashRouter([
    {
        path: '/',
        element: <App/>,
        errorElement: (
            <UIFoundation>
                <h1 style={{textTransform: "uppercase", fontSize: "2rem", paddingTop: "24px"}}>Not available</h1>
                <p style={{margin: "1rem 0"}}>
                    If you think this is our mistake, please file an issue on <a href="https://github.com/shiroyuki/mini-idp/issues">GitHub</a>.
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
                element: userManagerPage,
                children: [
                    {
                        path: ":id",
                        element: userManagerPage
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
