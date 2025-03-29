export type FormError = {
    path: string;
    type?: "validation"; // more types to be implemented
    message: string;
}

export type AppConfig = {
    defaultAudienceUri: string;
}