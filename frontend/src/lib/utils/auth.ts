import { browser } from '$app/environment';
import { goto } from '$app/navigation';

const ACCESS_TOKEN_KEY = 'access_token';
const UNAUTHORIZED_STATUS = new Set([401, 403]);

export function getAccessToken(): string | null {
	if (!browser) return null;
	return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function clearAccessToken(): void {
	if (!browser) return;
	localStorage.removeItem(ACCESS_TOKEN_KEY);
}

export async function redirectToLogin(): Promise<void> {
	if (!browser) return;
	await goto('/login');
}

export async function ensureAuthorizedResponse<T extends Response>(response: T): Promise<T> {
	if (UNAUTHORIZED_STATUS.has(response.status)) {
		clearAccessToken();
		await redirectToLogin();
		throw new Error('Unauthorized');
	}

	return response;
}
