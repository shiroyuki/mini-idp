import styles from './loaders.module.css';
import classNames from "classnames";

interface LinearLoadingAnimationProps {
    label?: string;
    size?: "normal" | "large";
    style?: React.CSSProperties;
}

export const LinearLoadingAnimation = ({label, size, style}: LinearLoadingAnimationProps) => {
    let actualSize = size ? `linearLoader${size[0].toUpperCase() + size.slice(1)}` : "linearLoaderNormal";

    return (
        <div className={classNames(styles.linearLoader, styles[actualSize])} style={style}>
            <div></div>
            {label && <div>{label}</div>}
        </div>
    );
};