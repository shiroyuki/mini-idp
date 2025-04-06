/*
 * Validators
 */
import {ErrorFeedback} from "./definitions";

export type ValidationResult = ErrorFeedback | null;
export type Validator<T> = (value: T, ...options: any[]) => ValidationResult;

const drainRegExpResultIterator = (iterator: { next(): { value: any, done: boolean, [k: string]: any } }) => {
    const collection = [];
    while (true) {
        const item = iterator.next();
        if (item.done) {
            break;
        } else {
            collection.push(item.value);
        }
    }
    return collection;
}

export const validAlternativeId = (minCharacters?: number, maxCharacters?: number) => {
    return (value: string): ValidationResult => {
        if (!value.match(/^[a-zA-Z][a-zA-Z0-9\-_.]+[a-zA-Z0-9]$/)) {
            return {
                error: "invalid_alternative_id.pattern",
                error_description: "Must start and end with characters (A-Z). Anything else in between can be alphanumerics (characters and numbers), dashes, underscores, and dots.",
            }
        } else {
            return null;
        }
    }
};

export const validEmailAddress = () => {
    return (value: string): ValidationResult => {
        if (value.match(/^[^@]+@[^@]+$/)) {
            return null;
        } else {
            return {
                error: "invalid_email",
                error_description: "Invalid email address",
            }
        }
    }
};

export const validUri = () => {
    return (value: string): ValidationResult => {
        if (value.match(/^https?:\/\/.+$/)) {
            return null;
        } else {
            return {
                error: "invalid_uri",
                error_description: "Invalid URI",
            }
        }
    }
}

export const securePassword = () => {
    return (value: string): ValidationResult => {
        let reasons: string[] = [];

        if (value.length < 8) {
            reasons.push("min_length")
        }

        // @ts-ignore
        let uppercaseLetterCount = drainRegExpResultIterator(value.matchAll(/[a-z]/g)).length;
        if (uppercaseLetterCount === 0) {
            reasons.push("no_uppercase_letter");
        }

        // @ts-ignore
        let lowercaseLetterCount = drainRegExpResultIterator(value.matchAll(/[A-Z]/g)).length;
        if (lowercaseLetterCount === 0) {
            reasons.push("no_lowercase_letter");
        }

        // @ts-ignore
        let numberCount = drainRegExpResultIterator(value.matchAll(/[0-9]/g)).length;
        if (numberCount === 0) {
            reasons.push("no_number");
        }

        // @ts-ignore
        let symbolCount = drainRegExpResultIterator(value.matchAll(/[,;:=!-_.+?#@$%^&*()\[\]|{}<>/]/g)).length;
        if (symbolCount === 0) {
            reasons.push("no_symbol");
        }

        if (reasons.length === 0) {
            return null;
        } else {
            return {
                error: "insecure_password",
                error_description: {
                    reasons: reasons,
                },
            }
        }
    }
}

export const hasPattern = (pattern: RegExp, error_code: string, error_description: string) => {
    return (value: string): ValidationResult => {
        if (value.match(pattern)) {
            return null;
        } else {
            return {
                error: error_code,
                error_description: error_description,
            }
        }
    }
};

export const maximumSizeOf = (limit: number, quantifier?: string) => {
    return (value: string | any[]): ValidationResult => {
        if (value.length <= limit) {
            return null;
        } else {
            return {
                error: "too_many",
                error_description: {
                    current: value.length,
                    limit: limit,
                    quantifier: quantifier,
                },
            };
        }
    };
};

export const minimumSizeOf = (limit: number, quantifier?: string) => {
    return (value: string | any[]): ValidationResult => {
        if (value.length >= limit) {
            return null;
        } else {
            return {
                error: "too_few",
                error_description: {
                    current: value.length,
                    limit: limit,
                    quantifier: quantifier,
                },
            };
        }
    };
};

export const mustBeAlternativeId = (minCharacters?: number, maxCharacters?: number): Validator<string>[] => {
    return [
        minimumSizeOf(minCharacters || 2),
        maximumSizeOf(maxCharacters || 48),
        validAlternativeId(),
    ]
}

export const mustBeEmailAddress = (): Validator<string>[] => {
    return [
        minimumSizeOf(8),
        validEmailAddress(),
    ]
}
