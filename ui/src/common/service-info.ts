export interface ServiceInfo {
    deployment: { name: string };
    release: { artifact: string, version: string };
}