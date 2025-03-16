export type ComparatorResult = -1 | 0 | 1
export type Comparator<T> = (a: T, b: T) => ComparatorResult;
export type DataLoader<T> = () => Promise<T[]>

export interface GenericModel {
    [k: string]: any;
}

export interface ErrorFeedback extends GenericModel {
    error: string;
}