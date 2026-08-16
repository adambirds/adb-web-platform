export interface ApiClientOptions {
    baseUrl: string;
}

export function createApiUrl(path: string, options: ApiClientOptions): URL {
    return new URL(path, options.baseUrl.endsWith("/") ? options.baseUrl : `${options.baseUrl}/`);
}
