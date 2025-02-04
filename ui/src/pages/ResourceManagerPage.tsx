import UIFoundation from "../components/UIFoundation";
import {FC} from "react";

type ListPageProps = {
    title: string;
}

type ResourceManagerPageProps = {
    baseUrl: string;
    listPage: ListPageProps;
}

export const ResourceManagerPage: FC<ResourceManagerPageProps> = ({baseUrl, listPage}) => {
    return (
        <UIFoundation>
            <h1>{listPage.title}</h1>
            <ResourceList baseUrl={baseUrl} listPage={listPage}/>
        </UIFoundation>
    );
}

const ResourceList = ({ baseUrl, listPage }: ResourceManagerPageProps) => {
    return (
        <table>
            <thead><tr><th>ABC</th></tr></thead>
        </table>
    );
}