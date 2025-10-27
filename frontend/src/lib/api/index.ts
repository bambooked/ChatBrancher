import { ApiClient } from './client';
import { API_BASE_URL } from '$lib/config';

/**
 * APIクライアントのシングルトンインスタンス
 */
export const apiClient = new ApiClient(API_BASE_URL);

export * from './client';
