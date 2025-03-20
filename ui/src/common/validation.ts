/*
 * Validators
 */
import {ErrorFeedback} from "./definitions";

export type ValidationResult = ErrorFeedback | null;
export type Validator<T> = (value: T, ...options: any[]) => ValidationResult;

export const isNotNull = () => {
    return (value: any): ValidationResult => {
        if (value === undefined || value === null) {
            return {
                error: "undefined_mandatory_field",
                error_description: "Missing required field",
            }
        } else {
            return null;
        }
    }
};

export const isAlternativeId = (error_code?: string, error_description?: string) => {
    return (value: string): ValidationResult => {
        if (value.match(/^[a-zA-Z0-9][a-zA-Z0-9\-_.]+[a-zA-Z0-9]$/)) {
            return null;
        } else {
            return {
                error: error_code || "invalid_alternative_id",
                error_description: error_description || "Invalid alternative ID",
            }
        }
    }
};

export const isEmailAddress = () => {
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

export const maximumSizeOf = (limit: number) => {
    return (value: string|any[]): ValidationResult => {
        if (value.length <= limit) {
            return null;
        } else if (Array.isArray(value)) {
            return {
                error: "list_too_long",
                error_description: `Must have at most ${limit}`,
            }
        } else {
            return {
                error: "string_too_long",
                error_description: `Must be at most ${limit} character(s)`,
            }
        }
    };
};

export const minimumSizeOf = (limit: number) => {
    return (value: string|any[]): ValidationResult => {
        if (value.length >= limit) {
            return null;
        } else if (Array.isArray(value)) {
            return {
                error: "list_too_short",
                error_description: `Must have at least ${limit}`,
            }
        } else {
            return {
                error: "string_too_short",
                error_description: `Must be at least ${limit} character(s)`,
            }
        }
    };
};