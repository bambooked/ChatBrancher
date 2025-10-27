import { browser } from '$app/environment';

/**
 * API Base URL設定
 *
 * 開発環境: http://localhost:8000
 * 本番環境: 空文字列（同一オリジン）
 */
export const API_BASE_URL = browser
	? import.meta.env.VITE_API_URL || ''
	: '';
