import React from "react";
import styles from "./Icon.module.css";
import classNames from "classnames";

interface Prop {
  name: "arrow_back" | "check_box_outline_blank" | "check_box" | "add" | "remove" | "delete" | "toggle_on" | "toggle_off" | "visibility" | "visibility_off" | string;
  classes?: string[];
}

const Icon: React.FC<Prop> = ({ name, classes }) => {
  // Check https://fonts.google.com/icons for reference
  return (
    <span className={ classNames(["icon", "material-symbols-rounded", styles.icon, ...(classes ?? [])]) }>{ name }</span>
  );
};

export default Icon;