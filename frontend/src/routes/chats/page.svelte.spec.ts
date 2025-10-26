import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/svelte';
import { userEvent } from '@testing-library/user-event';
import ChatsPage from './+page.svelte';
import type { ChatResponse } from '$lib/types/api';

describe('Chats Page', () => {
	beforeEach(() => {
		vi.resetAllMocks();
		// localStorageのモック
		const localStorageMock = (() => {
			let store: Record<string, string> = {};
			return {
				getItem: (key: string) => store[key] || null,
				setItem: (key: string, value: string) => {
					store[key] = value;
				},
				clear: () => {
					store = {};
				}
			};
		})();
		vi.stubGlobal('localStorage', localStorageMock);
		localStorage.setItem('access_token', 'test-token');
	});

	it('should display list of chats', async () => {
		const mockChats: ChatResponse[] = [
			{
				uuid: 'chat-1',
				owner_uuid: 'user-1',
				created: '2024-01-01T00:00:00',
				updated: '2024-01-01T00:00:00'
			},
			{
				uuid: 'chat-2',
				owner_uuid: 'user-1',
				created: '2024-01-02T00:00:00',
				updated: '2024-01-02T00:00:00'
			}
		];

		vi.spyOn(global, 'fetch').mockResolvedValue({
			ok: true,
			json: async () => mockChats
		} as Response);

		render(ChatsPage);

		await waitFor(() => {
			expect(screen.getByText(/chat-1/i)).toBeDefined();
			expect(screen.getByText(/chat-2/i)).toBeDefined();
		});
	});

	it('should have a button to create new chat', async () => {
		vi.spyOn(global, 'fetch').mockResolvedValue({
			ok: true,
			json: async () => []
		} as Response);

		render(ChatsPage);

		expect(screen.getByRole('button', { name: /新規チャット作成/i })).toBeDefined();
	});

	it('should display error message when fetching chats fails', async () => {
		vi.spyOn(global, 'fetch').mockResolvedValue({
			ok: false,
			status: 401
		} as Response);

		render(ChatsPage);

		await waitFor(() => {
			expect(screen.getByText(/エラー/i)).toBeDefined();
		});
	});
});
