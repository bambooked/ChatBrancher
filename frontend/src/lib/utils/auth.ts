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

/**
 * JWTトークンをデコードしてペイロードを取得
 */
function decodeToken(token: string): { exp?: number; sub?: string } | null {
	try {
		const parts = token.split('.');
		if (parts.length !== 3) return null;

		const payload = parts[1];
		const decoded = atob(payload.replace(/-/g, '+').replace(/_/g, '/'));
		return JSON.parse(decoded);
	} catch {
		return null;
	}
}

/**
 * トークンの有効期限が切れているかチェック
 */
export function isTokenExpired(token: string): boolean {
	const payload = decodeToken(token);
	if (!payload || !payload.exp) return true;

	// expはUNIXタイムスタンプ（秒）
	const now = Math.floor(Date.now() / 1000);
	return payload.exp < now;
}

/**
 * トークンの有効性をチェックし、無効ならログインページへリダイレクト
 */
export async function checkTokenValidityAndRedirect(): Promise<boolean> {
	const token = getAccessToken();
	if (!token || isTokenExpired(token)) {
		clearAccessToken();
		await redirectToLogin();
		return false;
	}
	return true;
}

export async function ensureAuthorizedResponse<T extends Response>(response: T): Promise<T> {
	// 401/403の場合、明示的な認証エラー
	if (UNAUTHORIZED_STATUS.has(response.status)) {
		clearAccessToken();
		await redirectToLogin();
		throw new Error('Unauthorized');
	}

	// 404などのエラーの場合も、念のためトークンの有効期限をチェック
	// 有効期限切れのトークンで404が返される可能性があるため
	if (!response.ok) {
		const token = getAccessToken();
		if (token && isTokenExpired(token)) {
			clearAccessToken();
			await redirectToLogin();
			throw new Error('Token expired');
		}
	}

	return response;
}
