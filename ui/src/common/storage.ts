class Storage {
    get(key: string): any {
        const rawData = sessionStorage.getItem(key);
        return rawData === null ? null : JSON.parse(rawData);
    }

    set(key: string, value: any) {
        sessionStorage.setItem(key, JSON.stringify(value));
        return this;
    }

    remove(key: string) {
        sessionStorage.removeItem(key);
        return this;
    }
}

export const storage = new Storage();