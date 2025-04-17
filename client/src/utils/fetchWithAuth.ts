export const fetchWithAuth = async (
    url: string,
    options: RequestInit = {},
    onUnauthorized: () => void
): Promise<Response> => {
    const token = localStorage.getItem('authToken');
    const headers = new Headers(options.headers || {});

    if (options.method && options.method !== 'GET' && !(options.body instanceof FormData)) {
        headers.set('Content-Type', 'application/json');
    }

    if (token) {
        headers.set('Authorization', `Bearer ${token}`);
    }

    const finalOptions: RequestInit = {
        ...options,
        headers: headers
    };

    try {
        const response = await fetch(url, finalOptions);

        if (response.status === 401) {
            console.warn(`Unauthorized (401) request to ${url}. Logging out.`);
            onUnauthorized();
            throw new Error('401 Unauthorized: Session expired or invalid.');
        }

        return response;

    } catch (error) {
        console.error(`Fetch error to ${url}:`, error);
        throw error;
    }
};