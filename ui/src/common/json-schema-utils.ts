import {Comparator, DataLoader, GenericModel} from "./definitions";
import {http, HttpError} from "./http-client";
import {ejectToLoginScreen} from "./helpers";
import {ListItemNormalizer} from "./json-schema-definitions";

export async function sendListRequestTo<T>(url: string) {
    return await http.sendAndMapAs<T[]>(
        "get",
        url,
        {
            handleError: async (response) => {
                if (response.status === 401) {
                    ejectToLoginScreen();
                } else if (response.status === 403) {
                    console.warn(`Unable to fetch the data from ${url} (error bypassed)`);
                } else {
                    response.text().then(content => {
                        throw new HttpError(response.status, content)
                    });
                }
            }
        }
    );
}

export function listItemsFrom<T>(listUrl: string): DataLoader<T> {
    return async () => {
        return (await sendListRequestTo<T>(listUrl)) || [];
    }
}

export function listFixedItems(fixtures: any[]) {
    return () => new Promise<any[]>((resolve, _) => {
        resolve(fixtures)
    });
}

export function createSimpleOptionFromObject<LoadedItemType extends GenericModel, KeyType>(valueField: string, labelField: string): ListItemNormalizer<LoadedItemType, KeyType> {
    return (selectedItems: KeyType[], iteratingLoadedItem: LoadedItemType) => {
        const typedItem = iteratingLoadedItem as LoadedItemType;
        const selections: KeyType[] = selectedItems || [];
        const value = typedItem[valueField] as KeyType;
        const label = typedItem[labelField] ?? value;
        const checked = selections.includes(value);

        return {
            checked: checked,
            label: label,
            value: value,
        };
    }
}

export function createComplexOptionFromObject<T extends GenericModel>(key: (x: T) => string, fieldNames?: string[]): ListItemNormalizer<T, T> {
    return (selectedItems: T[], iteratingLoadedItem: T) => {
        const typedItem = iteratingLoadedItem as T;
        const selections = (selectedItems || []).map(key);
        const selectionKey = key(typedItem);
        const checked = selections.includes(selectionKey);

        const copy: GenericModel = {};

        Object.keys(typedItem)
            .filter(p => fieldNames === undefined || fieldNames.includes(p))
            .forEach((p) => {
                copy[p] = typedItem[p];
            });

        return {
            checked: checked,
            value: copy as T,
        };
    }
}

export function createOptionFromPrimitiveValue<T>(): ListItemNormalizer<T, T> {
    return (selectedItems: T[], iteratingLoadedItem: T) => {
        const selectionList = (selectedItems || []) as T[];
        const iteratingId = iteratingLoadedItem as T;
        const checked = selectionList.includes(iteratingId);

        return {
            checked: checked,
            value: iteratingId,
        }
    }
}

export function compareItemsWith<T extends GenericModel>(valueField: string): Comparator<T> {
    return (a: T, b: T) => {
        if (a[valueField] === b[valueField]) {
            return 0;
        } else {
            return a[valueField] < b[valueField] ? -1 : 1;
        }
    }
}

export function compareItemsWithKey<T extends GenericModel>(key: (x: T) => any): Comparator<T> {
    return (a: T, b: T) => {
        if (key(a) === key(b)) {
            return 0;
        } else {
            return key(a) < key(b) ? -1 : 1;
        }
    }
}

export function comparePrimitiveValues() {
    return (a: any, b: any) => {
        if (a === b) {
            return 0;
        } else {
            return a < b ? -1 : 1;
        }
    }
}