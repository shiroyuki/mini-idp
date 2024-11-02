import styles from './loaders.module.css';
import classNames from "classnames";

interface LinearLoadingAnimationProps {
    label?: string;
    size?: "normal" | "large";
}

export const LinearLoadingAnimation = ({label, size}: LinearLoadingAnimationProps) => {
    let actualSize = size ? `linearLoader${size[0].toUpperCase() + size.slice(1)}` : "linearLoaderNormal";

    return (
        <div className={classNames(styles.linearLoader, styles[actualSize])}>
            <div></div>
            <div>{label ?? "Please wait."}</div>
        </div>
    );
};