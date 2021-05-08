import React from "react";
import { Button, Spinner } from "grommet";
import { get } from "lodash";

const AnimatingButton = ({animating, ...props}) => {
    if (animating) {
        return <Button {...props} alignSelf="center" label={null} disabled={true}><Spinner color={get(props, "background.dark", false) ? "#FFF" : "brand"}/></Button>;
    } else {
        return <Button {...props}>{props.children}</Button>;
    }
}

export default AnimatingButton;