export const ejectToLoginScreen = () => {
    // @ts-ignore
    window.location = "#/login";
}

export class ListCollection<T> {
    /**
     * @param data
     * @param compare returns -1 for less, 0 for equal, and 1 for greater
     */
    constructor(protected data: T[],
                protected compare: (given: T, seeker: T) => number) {
    }

    contains(needle: T) {
        return this.data.filter(item => this.compare(item, needle) === 0).length > 0;
    }

    add(item: T) {
        this.data.push(item);

        return this;
    }

    remove(needle: T, offset?: number, limit?: number) {
        const updated: T[] = [];
        let actualOffset = offset || 0;
        let removedCount = 0;

        for (let i = 0; i < this.data.length; i++) {
            const item = this.data[i];

            if (i < actualOffset) {
                updated.push(item);
            } else if (this.compare(this.data[i], needle) === 0
                && (limit === undefined || removedCount < limit)) {
                // NOOP --- Exclude from the list.
                removedCount++;
            } else {
                updated.push(item);
            }
        }

        this.data = updated

        return this;
    }

    isEmpty() {
        return this.data.length === 0;
    }

    size() {
        return this.data.length;
    }

    toArray() {
        return [...this.data];
    }
}