export const ejectToLoginScreen = () => {
    // @ts-ignore
    window.location = "#/login";
}

export class ListCollection<T> {
    constructor(protected data: T[]) {
    }

    exists(needle: T, matched?: (given: T, seeker: T) => boolean) {
        if (matched === undefined) {
            return this.data.includes(needle);
        } else {
            return this.data.filter(item => matched(item, needle)).length > 0;
        }
    }
}