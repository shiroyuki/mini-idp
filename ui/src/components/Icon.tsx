import React from "react";

interface Prop {
  name: string;
}

const Icon: React.FC<Prop> = ({ name }) => {
  return (
    <span className="icon material-symbols-rounded">{ name }</span>
  );
};

export default Icon;