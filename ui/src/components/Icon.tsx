import React from "react";

interface Prop {
  name: string;
}

const Icon: React.FC<Prop> = ({ name }) => {
  // Check https://fonts.google.com/icons for reference
  return (
    <span className="icon material-symbols-rounded">{ name }</span>
  );
};

export default Icon;