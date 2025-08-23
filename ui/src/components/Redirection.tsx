import {LinearLoadingAnimation} from "./loaders";
import {useEffect} from "react";
import {useNavigate} from "react-router-dom";

export const Redirection = ({to}: {to: string}) => {
    const navigate = useNavigate();
    useEffect(() => {
        navigate(to);
    }, []);
    return (
        <LinearLoadingAnimation/>
    )
}